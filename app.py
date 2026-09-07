"""
app.py — Data Cleaning Automation Tool (Streamlit)

Two experiences in one app:
  - Simple mode (default): one upload box, one "Clean My Data" button,
    plain-English results. Built for someone with no technical background.
  - Advanced mode (opt-in via sidebar): the full toolkit — column-by-column
    control, business-rule validation, AI recommendations, custom rules,
    database connections, and large-file chunked processing.

Run with:
    streamlit run app.py
"""

import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from modules import (
    file_handler,
    profiling,
    missing_values,
    duplicates,
    text_cleaning,
    standardization,
    date_cleaning,
    type_conversion,
    outlier_detection,
    validation,
    report,
    db_handler,
    ai_recommendations,
    large_file_handler,
    rules_manager,
    auto_clean,
)
from utils.logger import CleaningLogger

st.set_page_config(page_title="Data Cleaning Tool", layout="wide", page_icon="🧹")

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
defaults = {
    "logger": CleaningLogger(),
    "original_df": None,
    "df": None,
    "filename": None,
    "validation_errors": 0,
    "simple_actions": None,
    "ai_recs": None,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

logger: CleaningLogger = st.session_state.logger


# ---------------------------------------------------------------------------
# Simple mode — plain-English, one-click experience
# ---------------------------------------------------------------------------
def render_simple(df: pd.DataFrame):
    st.subheader("Step 1: Here's what we found in your file")

    scan = auto_clean.scan_issues(df)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", f"{scan['rows']:,}")
    c2.metric("Columns", scan["columns"])
    c3.metric("Duplicate rows", f"{scan['duplicate_rows']:,}")
    c4.metric("Missing values", f"{scan['missing_cells']:,}")

    issues_found = (
        scan["duplicate_rows"] or scan["missing_cells"] or scan["messy_text_total"]
        or scan["invalid_dates_total"] or scan["numeric_candidate_columns"]
    )

    if issues_found:
        st.write("")
        if scan["duplicate_rows"]:
            st.warning(f"🔁 **{scan['duplicate_rows']} duplicate row(s)** — the same entry appears more than once.")
        if scan["missing_cells"]:
            st.warning(f"🕳️ **{scan['missing_cells']} missing value(s)** — some cells are empty, 'N/A', or similar.")
        if scan["messy_text_total"]:
            cols_list = ", ".join(scan["messy_text_columns"].keys())
            st.warning(f"✏️ **Inconsistent spelling/capitalization** in: {cols_list} (e.g. 'ahmedabad' vs 'AHMEDABAD').")
        if scan["numeric_candidate_columns"]:
            cols_list = ", ".join(scan["numeric_candidate_columns"])
            st.warning(f"🔢 **Numbers stored as text** in: {cols_list}.")
        if scan["invalid_dates_total"]:
            st.warning(f"📅 **{scan['invalid_dates_total']} date(s) look invalid or inconsistently formatted.**")
    else:
        st.success("✅ No major issues found — your data already looks clean!")

    st.write("")
    st.subheader("Step 2: Clean it")
    st.caption(
        "One click applies safe, sensible fixes: removes exact duplicates, trims stray spaces, "
        "fixes inconsistent spelling/capitalization, converts numbers and dates stored as text, "
        "and fills in missing values sensibly. Nothing risky (like deleting unusual values) "
        "happens without you seeing it first."
    )

    if st.button("✨ Clean My Data Now", type="primary", use_container_width=True):
        with st.spinner("Cleaning your data..."):
            cleaned_df, actions, stats = auto_clean.auto_clean(df, logger=logger)
        st.session_state.df = cleaned_df
        st.session_state.simple_actions = actions
        st.session_state.simple_stats = stats
        st.rerun()

    if st.session_state.simple_actions is not None:
        st.write("")
        st.subheader("Step 3: Results")
        st.success("🎉 Done! Here's what changed:")

        for action in st.session_state.simple_actions:
            st.write(f"- {action}")

        cleaned = st.session_state.df
        ba = report.before_after_summary(st.session_state.original_df, cleaned)
        bcol1, bcol2, bcol3, bcol4, bcol5 = st.columns(5)
        for col_widget, (_, row) in zip([bcol1, bcol2, bcol3, bcol4, bcol5], ba.iterrows()):
            col_widget.metric(row["Metric"], row["AFTER"], delta=int(row["AFTER"]) - int(row["BEFORE"]))

        scores = report.quality_score(cleaned, validation_error_count=st.session_state.validation_errors)
        rating = "Excellent 🌟" if scores["Overall"] >= 90 else "Good 👍" if scores["Overall"] >= 75 else "Needs review ⚠️"
        st.write("")
        st.metric("Overall data quality score", f"{scores['Overall']}%", help="How complete, consistent, and clean your data is, from 0-100%.")
        st.write(f"**Rating: {rating}**")

        with st.expander("See the technical details (optional)"):
            st.dataframe(pd.DataFrame([scores]), use_container_width=True)
            st.write("Full cleaning log:")
            st.code(logger.as_text())

        st.write("")
        st.subheader("Step 4: Download your clean file")
        summary_for_report = file_handler.file_summary(cleaned, st.session_state.filename)
        dl1, dl2, dl3 = st.columns(3)
        dl1.download_button(
            "⬇️ Download as Excel", data=report.export_cleaned_data(cleaned, "xlsx"),
            file_name="cleaned_data.xlsx", use_container_width=True,
        )
        dl2.download_button(
            "⬇️ Download as CSV", data=report.export_cleaned_data(cleaned, "csv"),
            file_name="cleaned_data.csv", use_container_width=True,
        )
        dl3.download_button(
            "⬇️ Download report (Excel)",
            data=report.export_report_excel(summary_for_report, scores, ba, logger.as_list()),
            file_name="cleaning_report.xlsx", use_container_width=True,
        )


# ---------------------------------------------------------------------------
# Advanced mode — full toolkit for power users
# ---------------------------------------------------------------------------
def render_advanced(df: pd.DataFrame):
    summary = file_handler.file_summary(df, st.session_state.filename)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", f"{summary['Rows']:,}")
    c2.metric("Columns", summary["Columns"])
    c3.metric("Missing", f"{summary['Missing']:,}")
    c4.metric("Duplicate", f"{summary['Duplicate']:,}")

    with st.expander("📋 Data Profile", expanded=True):
        st.dataframe(profiling.profile_dataframe(df), use_container_width=True)

    with st.expander("🔍 Preview data"):
        st.dataframe(df.head(50), use_container_width=True)

    with st.expander("📊 Charts", expanded=False):
        profile_df = profiling.profile_dataframe(df)
        chart1, chart2 = st.columns(2)
        with chart1:
            fig_missing = px.bar(profile_df.sort_values("Missing", ascending=False), x="Column", y="Missing", title="Missing values by column")
            fig_missing.update_layout(height=320, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_missing, use_container_width=True)
        with chart2:
            type_counts = profile_df["Type"].value_counts().reset_index()
            type_counts.columns = ["Type", "Count"]
            fig_types = px.pie(type_counts, names="Type", values="Count", title="Column type distribution")
            fig_types.update_layout(height=320, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_types, use_container_width=True)

        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        if len(numeric_cols) >= 2:
            corr = df[numeric_cols].corr(numeric_only=True)
            fig_corr = px.imshow(corr, text_auto=".2f", title="Correlation between numeric columns", color_continuous_scale="Blues")
            fig_corr.update_layout(height=380, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_corr, use_container_width=True)

    st.divider()
    st.header("Cleaning Options")
    left, right = st.columns(2)

    with left:
        do_trim = st.checkbox("Trim extra spaces", value=True)
        do_dupes = st.checkbox("Remove duplicates", value=True)
        dupe_keep = st.selectbox("Duplicate handling", ["first", "last", "Don't remove"], index=0)

        st.subheader("Missing values")
        missing_col = st.selectbox("Column", ["(none)"] + list(df.columns), key="missing_col")
        missing_strategy = st.selectbox("Strategy", ["remove", "mean", "median", "mode", "custom"], key="missing_strategy")
        custom_val = None
        if missing_strategy == "custom":
            custom_val = st.text_input("Custom fill value", value="Unknown")

    with right:
        st.subheader("Type conversion")
        type_col = st.selectbox("Column", ["(none)"] + list(df.columns), key="type_col")
        type_target = st.selectbox("Convert to", ["integer", "float", "text"], key="type_target")

        st.subheader("Date standardization")
        date_col = st.selectbox("Date column", ["(none)"] + list(df.columns), key="date_col")

        st.subheader("Outlier detection")
        outlier_col = st.selectbox("Numeric column", ["(none)"] + list(df.columns), key="outlier_col")
        outlier_method = st.selectbox("Method", ["iqr", "zscore", "percentile"], key="outlier_method")

    st.subheader("Text standardization")
    std_col = st.selectbox("Column to standardize", ["(none)"] + list(df.columns), key="std_col")
    if std_col != "(none)":
        suggestions = standardization.suggest_case_variants(df, std_col)
        if suggestions:
            st.write(f"Potential inconsistencies found in **{std_col}**:")
            for variant, canonical in list(suggestions.items())[:10]:
                st.write(f"`{variant}` → `{canonical}`")
            if st.button(f"Apply standardization to '{std_col}'"):
                df = standardization.apply_rules(df, std_col, suggestions, logger=logger)
                st.session_state.df = df
                st.rerun()
        else:
            st.caption("No case/spacing inconsistencies detected.")

    st.divider()
    st.header("Custom Rules")
    st.caption("Build your own find-and-replace rules per column. Saved to config/cleaning_rules.json.")
    if "custom_rules" not in st.session_state:
        st.session_state.custom_rules = rules_manager.load_rules()

    rc1, rc2, rc3, rc4 = st.columns([2, 2, 2, 1])
    rule_col = rc1.selectbox("Column", ["(none)"] + list(df.columns), key="rule_col")
    rule_from = rc2.text_input("From value", key="rule_from")
    rule_to = rc3.text_input("To value", key="rule_to")
    if rc4.button("Add rule") and rule_col != "(none)" and rule_from:
        st.session_state.custom_rules = rules_manager.add_rule(st.session_state.custom_rules, rule_col, rule_from, rule_to)
        rules_manager.save_rules(st.session_state.custom_rules)
        st.rerun()

    if st.session_state.custom_rules:
        for col_name, mapping in st.session_state.custom_rules.items():
            st.write(f"**{col_name}**")
            for from_v, to_v in mapping.items():
                rcol1, rcol2 = st.columns([5, 1])
                rcol1.write(f"`{from_v}` → `{to_v}`")
                if rcol2.button("Remove", key=f"rm_{col_name}_{from_v}"):
                    st.session_state.custom_rules = rules_manager.remove_rule(st.session_state.custom_rules, col_name, from_v)
                    rules_manager.save_rules(st.session_state.custom_rules)
                    st.rerun()
        if st.button("Apply all custom rules now"):
            for col_name, mapping in st.session_state.custom_rules.items():
                if col_name in df.columns:
                    df = standardization.apply_rules(df, col_name, mapping, logger=logger)
            st.session_state.df = df
            st.rerun()
    else:
        st.caption("No custom rules yet — add one above.")

    st.divider()
    st.header("🤖 AI Recommendations")
    api_key_input = st.text_input("Anthropic API key (optional — or set ANTHROPIC_API_KEY env var)", type="password", key="anthropic_key")
    if st.button("Analyze with AI"):
        try:
            profile_df = profiling.profile_dataframe(df)
            payload = ai_recommendations.build_profile_summary(df, profile_df)
            with st.spinner("Asking Claude to review the data profile..."):
                recs = ai_recommendations.get_recommendations(payload, api_key=api_key_input or None)
            st.session_state.ai_recs = recs
        except Exception as e:
            st.error(f"AI recommendation failed: {e}")

    if st.session_state.get("ai_recs"):
        st.write(f"Found {len(st.session_state.ai_recs)} potential data-quality problem(s):")
        for i, rec in enumerate(st.session_state.ai_recs, start=1):
            st.write(f"{i}. **{rec.get('issue', 'Issue')}** — {rec.get('reason', '')} (column: `{rec.get('column') or 'dataset-wide'}`, action: `{rec.get('action')}`)")
        if st.button("Clean Recommended Issues"):
            for rec in st.session_state.ai_recs:
                action, col = rec.get("action"), rec.get("column")
                try:
                    if action == "remove_duplicates":
                        df = duplicates.remove_duplicates(df, keep="first", logger=logger)
                    elif action == "trim_spaces":
                        df = text_cleaning.trim_spaces(df, logger=logger)
                    elif action in ("fill_missing_mean", "fill_missing_median", "fill_missing_mode") and col in df.columns:
                        df = missing_values.handle_missing(df, col, action.replace("fill_missing_", ""), logger=logger)
                    elif action == "standardize_text" and col in df.columns:
                        suggestions = standardization.suggest_case_variants(df, col)
                        df = standardization.apply_rules(df, col, suggestions, logger=logger)
                    elif action == "convert_type_integer" and col in df.columns:
                        df = type_conversion.convert_column(df, col, "integer", logger=logger)
                    elif action == "convert_type_float" and col in df.columns:
                        df = type_conversion.convert_column(df, col, "float", logger=logger)
                    elif action == "standardize_dates" and col in df.columns:
                        df, _ = date_cleaning.standardize_dates(df, col, logger=logger)
                except Exception as e:
                    st.warning(f"Skipped '{action}' on '{col}': {e}")
            st.session_state.df = df
            st.success("Applied AI-recommended cleaning actions via the deterministic modules.")
            st.rerun()

    st.divider()
    st.header("Business Rule Validation")
    bc1, bc2, bc3, bc4 = st.columns(4)
    col_a = bc1.selectbox("Column A", ["(none)"] + list(df.columns), key="rule_a")
    operator = bc2.selectbox("Operator", ["*", "+", "-", "/"], key="rule_op")
    col_b = bc3.selectbox("Column B", ["(none)"] + list(df.columns), key="rule_b")
    col_result = bc4.selectbox("Should equal", ["(none)"] + list(df.columns), key="rule_result")
    if st.button("Run validation check"):
        if "(none)" not in (col_a, col_b, col_result):
            mismatches = validation.validate_formula(df, col_a, operator, col_b, col_result)
            st.session_state.validation_errors = len(mismatches)
            if len(mismatches):
                st.warning(f"⚠️ {len(mismatches)} row(s) failed: {col_a} {operator} {col_b} != {col_result}")
                st.dataframe(mismatches, use_container_width=True)
                logger.log(f"Validation: {len(mismatches)} mismatch(es) in {col_a}{operator}{col_b}={col_result}")
            else:
                st.success("All rows satisfy the business rule ✅")
                logger.log("Validation: all rows passed business rule check")
        else:
            st.info("Select all four fields to run a check.")

    st.divider()
    if st.button("🚀 CLEAN DATA", type="primary"):
        working = missing_values.normalize_missing(df)
        if do_trim:
            working = text_cleaning.trim_spaces(working, logger=logger)
        if missing_col != "(none)":
            working = missing_values.handle_missing(working, missing_col, missing_strategy, custom_value=custom_val, logger=logger)
        if do_dupes:
            keep = False if dupe_keep == "Don't remove" else dupe_keep
            working = duplicates.remove_duplicates(working, keep=keep, logger=logger)
        if type_col != "(none)":
            working = type_conversion.convert_column(working, type_col, type_target, logger=logger)
        if date_col != "(none)":
            working, invalid_dates = date_cleaning.standardize_dates(working, date_col, logger=logger)
            if invalid_dates:
                st.warning(f"⚠️ {len(invalid_dates)} invalid date(s) found in '{date_col}': {invalid_dates[:5]}")
        if outlier_col != "(none)":
            flags = outlier_detection.detect_outliers(working, outlier_col, method=outlier_method)
            n_flagged = int(flags.sum())
            if n_flagged:
                st.warning(f"⚠️ {n_flagged} possible outlier(s) detected in '{outlier_col}' ({outlier_method})")
                st.dataframe(working.loc[flags], use_container_width=True)
                logger.log(f"Detected {n_flagged} outlier(s) in '{outlier_col}' using {outlier_method}")
        st.session_state.df = working
        st.success("Cleaning pipeline complete.")
        st.rerun()

    st.divider()
    st.header("Data Quality Score")
    scores = report.quality_score(df, validation_error_count=st.session_state.validation_errors)
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=scores["Overall"], title={"text": "Overall Quality"},
        gauge={"axis": {"range": [0, 100]}, "bar": {"color": "#2b6cb0"}},
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=10))
    sc1, sc2 = st.columns([1, 2])
    with sc1:
        st.plotly_chart(fig, use_container_width=True)
    with sc2:
        for k in ["Completeness", "Accuracy", "Consistency", "Uniqueness", "Validity"]:
            st.progress(min(int(scores[k]), 100), text=f"{k}: {scores[k]}%")

    st.divider()
    st.header("Before vs After")
    ba = report.before_after_summary(st.session_state.original_df, df)
    st.dataframe(ba, use_container_width=True)

    st.divider()
    st.header("Cleaning Log")
    if logger.entries:
        st.code(logger.as_text())
    else:
        st.caption("No actions logged yet — run the cleaning pipeline above.")

    st.divider()
    st.header("Export")
    e1, e2, e3, e4 = st.columns(4)
    e1.download_button("⬇️ Cleaned data (.xlsx)", data=report.export_cleaned_data(df, "xlsx"), file_name="cleaned_data.xlsx")
    e2.download_button("⬇️ Cleaned data (.csv)", data=report.export_cleaned_data(df, "csv"), file_name="cleaned_data.csv")
    e3.download_button("⬇️ Report (Excel)", data=report.export_report_excel(summary, scores, ba, logger.as_list()), file_name="cleaning_report.xlsx")
    try:
        pdf_bytes = report.export_report_pdf(summary, scores, ba, logger.as_list())
        e4.download_button("⬇️ Report (PDF)", data=pdf_bytes, file_name="cleaning_report.pdf")
    except ImportError:
        e4.caption("Install `reportlab` for PDF export")

    with st.expander("🗄️ Save cleaned data to database"):
        save_url = st.text_input("Connection URL", value=st.session_state.get("db_conn_url", ""), placeholder="sqlite:///data/mydata.db", key="save_db_url")
        save_table = st.text_input("Table name", value=st.session_state.get("db_table_name", "cleaned_data"))
        if_exists = st.selectbox("If table exists", ["replace", "append", "fail"])
        if st.button("Write to database"):
            try:
                n = db_handler.write_table(save_url, df, save_table, if_exists=if_exists, logger=logger)
                st.success(f"Wrote {n} rows to table '{save_table}'.")
            except Exception as e:
                st.error(f"Could not write to database: {e}")


def render_large_file_mode():
    st.header("📦 Large CSV — Chunked Processing")
    st.caption(
        "For CSVs too big to load fully into memory. Streams the file in chunks; "
        "supports trimming spaces and filling missing numeric values with the column mean. "
        "Exact duplicate removal and outlier detection need the full dataset and aren't available "
        "in this mode."
    )
    big_file = st.file_uploader("Upload large CSV", type=["csv"], key="big_csv")
    chunk_size = st.number_input("Chunk size (rows)", min_value=1000, max_value=500_000, value=50_000, step=1000)
    trim_big = st.checkbox("Trim extra spaces", value=True)
    fill_big = st.checkbox("Fill missing numeric values with column mean", value=True)

    if big_file is not None and st.button("Run chunked profile + clean"):
        input_path = os.path.join("data", "input", big_file.name)
        os.makedirs(os.path.dirname(input_path), exist_ok=True)
        with open(input_path, "wb") as f:
            f.write(big_file.getbuffer())

        with st.spinner("Streaming profile pass..."):
            profile = large_file_handler.profile_large_csv(input_path, chunksize=chunk_size)
        st.metric("Rows", f"{profile['rows']:,}")
        st.write("Missing values per column:")
        st.dataframe(pd.DataFrame([profile["missing_counts"]]).T.rename(columns={0: "Missing"}))

        output_path = os.path.join("data", "output", f"cleaned_{big_file.name}")
        with st.spinner("Streaming clean pass..."):
            result = large_file_handler.clean_large_csv(
                input_path, output_path, trim=trim_big, fill_missing_numeric=fill_big,
                chunksize=chunk_size, logger=logger,
            )
        st.success(f"Wrote {result['rows_written']:,} cleaned rows to {output_path}")
        with open(output_path, "rb") as f:
            st.download_button("⬇️ Download cleaned CSV", data=f.read(), file_name=f"cleaned_{big_file.name}")


def render_database_loader():
    st.header("🗄️ Load from Database")
    conn_url = st.text_input("Connection URL", placeholder="sqlite:///data/mydata.db  or  postgresql+psycopg2://user:pass@host:5432/dbname")
    if conn_url and st.button("Connect & list tables"):
        try:
            st.session_state.db_tables = db_handler.list_tables(conn_url)
            st.session_state.db_conn_url = conn_url
        except Exception as e:
            st.error(f"Could not connect: {e}")

    if st.session_state.get("db_tables"):
        table = st.selectbox("Table", st.session_state.db_tables)
        if st.button("Load table"):
            try:
                loaded = db_handler.read_table(st.session_state.db_conn_url, table)
                st.session_state.original_df = loaded.copy()
                st.session_state.df = loaded.copy()
                st.session_state.filename = f"{table} (database)"
                st.session_state.db_table_name = table
                logger.clear()
                logger.log(f"Loaded table '{table}' from database ({len(loaded)} rows)")
                st.session_state.validation_errors = 0
                st.session_state.simple_actions = None
                st.rerun()
            except Exception as e:
                st.error(f"Could not load table: {e}")


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------
st.title("🧹 Data Cleaning Tool")
st.caption("Upload a spreadsheet, click Clean, download the tidy version. No coding needed.")

with st.sidebar:
    st.header("Settings")
    advanced_mode = st.toggle("🛠️ Advanced / power-user mode", value=False,
                               help="Turn this on for column-by-column control, business-rule checks, AI suggestions, database connections, and support for very large files.")
    if advanced_mode:
        st.divider()
        st.subheader("Data source")
        source_mode = st.radio("Load data from", ["File upload", "Database", "Large CSV (chunked mode)"], label_visibility="collapsed")
    else:
        source_mode = "File upload"

if advanced_mode and source_mode == "Large CSV (chunked mode)":
    render_large_file_mode()
    st.stop()

if advanced_mode and source_mode == "Database":
    render_database_loader()
    if st.session_state.df is None:
        st.info("Connect to a database and load a table to get started.")
        st.stop()
else:
    uploaded = st.file_uploader("📤 Upload your Excel or CSV file", type=["csv", "xlsx", "xls"])
    if uploaded is not None and (st.session_state.filename != uploaded.name):
        try:
            new_df = file_handler.read_file(uploaded, uploaded.name)
            st.session_state.original_df = new_df.copy()
            st.session_state.df = new_df.copy()
            st.session_state.filename = uploaded.name
            st.session_state.simple_actions = None
            logger.clear()
            logger.log(f"Uploaded '{uploaded.name}' ({len(new_df)} rows, {len(new_df.columns)} columns)")
            st.session_state.validation_errors = 0
        except Exception as e:
            st.error(f"Could not read file: {e}")

    if st.session_state.df is None:
        st.info("👆 Upload a CSV or Excel file to get started.")
        st.stop()

df = st.session_state.df

if advanced_mode:
    tab_simple, tab_advanced = st.tabs(["🚀 Simple", "🛠️ Advanced"])
    with tab_simple:
        render_simple(df)
    with tab_advanced:
        render_advanced(st.session_state.df)
else:
    render_simple(df)
