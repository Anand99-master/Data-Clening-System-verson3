"""
modules/report.py — Module 15 (Data Quality Score), Module 16 (Before/After),
Module 17 (Cleaning Log) helpers + export to Excel / PDF.
"""

import io
import pandas as pd
from utils.helpers import is_missing_token


def quality_score(df: pd.DataFrame, validation_error_count: int = 0, expected_business_rules: int = 1) -> dict:
    """
    Computes 5 sub-scores (0-100) and an overall weighted score, matching
    the "DATA QUALITY SCORE 82%" panel in the architecture doc.
    """
    total_cells = df.shape[0] * df.shape[1] if df.size else 1

    missing_cells = int(df.apply(lambda col: col.apply(is_missing_token)).sum().sum())
    completeness = 100 * (1 - missing_cells / total_cells)

    dup_rows = int(df.duplicated().sum())
    uniqueness = 100 * (1 - dup_rows / max(len(df), 1))

    # Accuracy proxy: rows unaffected by business-rule mismatches
    accuracy = 100 * (1 - min(validation_error_count, len(df)) / max(len(df), 1))

    # Consistency proxy: fraction of text columns with no case/space variants left
    text_cols = df.select_dtypes(include="object").columns
    inconsistent_cols = 0
    for col in text_cols:
        variants = df[col].dropna().astype(str).str.strip().str.lower().nunique()
        raw_variants = df[col].dropna().astype(str).nunique()
        if raw_variants > variants:
            inconsistent_cols += 1
    consistency = 100 * (1 - inconsistent_cols / max(len(text_cols), 1)) if len(text_cols) else 100

    validity = accuracy  # simple proxy; can be split further with range-rule results

    scores = {
        "Completeness": round(max(completeness, 0), 1),
        "Accuracy": round(max(accuracy, 0), 1),
        "Consistency": round(max(consistency, 0), 1),
        "Uniqueness": round(max(uniqueness, 0), 1),
        "Validity": round(max(validity, 0), 1),
    }
    scores["Overall"] = round(sum(scores.values()) / len(scores), 1)
    return scores


def before_after_summary(before: pd.DataFrame, after: pd.DataFrame,
                          before_missing: int = None, after_missing: int = None,
                          before_invalid: int = 0, after_invalid: int = 0,
                          before_outliers: int = 0, after_outliers: int = 0) -> pd.DataFrame:
    if before_missing is None:
        before_missing = int(before.apply(lambda c: c.apply(is_missing_token)).sum().sum())
    if after_missing is None:
        after_missing = int(after.apply(lambda c: c.apply(is_missing_token)).sum().sum())

    rows = [
        {"Metric": "Rows", "BEFORE": len(before), "AFTER": len(after)},
        {"Metric": "Duplicates", "BEFORE": int(before.duplicated().sum()), "AFTER": int(after.duplicated().sum())},
        {"Metric": "Missing", "BEFORE": before_missing, "AFTER": after_missing},
        {"Metric": "Invalid", "BEFORE": before_invalid, "AFTER": after_invalid},
        {"Metric": "Outliers", "BEFORE": before_outliers, "AFTER": after_outliers},
    ]
    return pd.DataFrame(rows)


def export_cleaned_data(df: pd.DataFrame, fmt: str = "xlsx") -> bytes:
    buffer = io.BytesIO()
    if fmt == "xlsx":
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Cleaned Data")
    elif fmt == "csv":
        buffer.write(df.to_csv(index=False).encode("utf-8"))
    else:
        raise ValueError("fmt must be 'xlsx' or 'csv'")
    buffer.seek(0)
    return buffer.getvalue()


def export_report_excel(summary: dict, scores: dict, before_after: pd.DataFrame, log_entries: list) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame([summary]).to_excel(writer, index=False, sheet_name="Summary")
        pd.DataFrame([scores]).to_excel(writer, index=False, sheet_name="Quality Score")
        before_after.to_excel(writer, index=False, sheet_name="Before vs After")
        pd.DataFrame(log_entries).to_excel(writer, index=False, sheet_name="Cleaning Log")
    buffer.seek(0)
    return buffer.getvalue()


def export_report_pdf(summary: dict, scores: dict, before_after: pd.DataFrame, log_entries: list) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50

    def line(text, size=11, gap=16, bold=False):
        nonlocal y
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(50, y, text)
        y -= gap
        if y < 50:
            c.showPage()
            y = height - 50

    line("Data Cleaning Report", size=16, bold=True, gap=26)
    line("Summary", size=13, bold=True)
    for k, v in summary.items():
        line(f"{k}: {v}")

    line("")
    line("Data Quality Score", size=13, bold=True)
    for k, v in scores.items():
        line(f"{k}: {v}%")

    line("")
    line("Before vs After", size=13, bold=True)
    for _, row in before_after.iterrows():
        line(f"{row['Metric']}: {row['BEFORE']} -> {row['AFTER']}")

    line("")
    line("Cleaning Log", size=13, bold=True)
    for entry in log_entries:
        line(f"{entry['time']}  {entry['message']}", size=9, gap=13)

    c.save()
    buffer.seek(0)
    return buffer.getvalue()
