"""
modules/auto_clean.py — One-click "Quick Clean" pipeline for non-technical users.

Two entry points:
  scan_issues(df)  -> a plain-English summary of problems found, before touching data
  auto_clean(df)   -> applies sensible default fixes for all of them, returns
                      (cleaned_df, list_of_plain_english_actions_taken, stats)

Design principle: only apply changes here that are SAFE to do automatically
(trimming spaces, removing exact duplicate rows, fixing obvious case/spacing
spelling variants, filling missing values with median/mode, converting
obviously-numeric or obviously-date columns). Anything judgment-based
(which rows are "real" outliers, which duplicate to keep when they're not
byte-identical, custom business rules) stays in the Advanced tab where a
human decides.
"""

import re
import pandas as pd
from dateutil import parser as dateutil_parser

from modules import (
    missing_values,
    duplicates,
    text_cleaning,
    standardization,
    date_cleaning,
    type_conversion,
    outlier_detection,
)
from utils.helpers import is_missing_token, safe_numeric_series

_DATE_SHAPE = re.compile(
    r"^\s*\d{1,4}[/\-.]\d{1,2}[/\-.]\d{1,4}\s*$"          # 05/09/2026, 2026-09-05
    r"|^\s*\d{1,2}\s+[A-Za-z]{3,9}[,\s]+\d{2,4}\s*$"        # 5 September 2026, 5 Sep, 2026
    r"|^\s*[A-Za-z]{3,9}\s+\d{1,2}[,\s]+\d{2,4}\s*$",       # Sep 5, 2026 / September 5 2026
    re.IGNORECASE,
)


def _looks_like_date_column(series: pd.Series, col_name: str) -> bool:
    """Only treat a column as date-like if its NAME hints at it, or its
    VALUES actually look shaped like a date (not just any parseable number —
    dateutil will happily parse bare numbers like '24' or '3000' as dates,
    which is why we require a real date pattern here)."""
    name = col_name.lower()
    name_hints_date = any(word in name for word in ("date", "dob", "birthday", "timestamp"))

    sample = series.dropna().astype(str).head(30)
    if sample.empty:
        return name_hints_date

    shaped_like_date = sample.apply(lambda v: bool(_DATE_SHAPE.match(v.strip())))
    shape_ratio = shaped_like_date.mean()

    if shape_ratio > 0.7:
        return True
    # Name hints at "date" AND at least parses reasonably -> trust the name
    if name_hints_date and shape_ratio > 0.3:
        return True
    return False


def scan_issues(df: pd.DataFrame) -> dict:
    """Plain-English health check, run BEFORE any cleaning."""
    normalized = df.copy()
    for col in normalized.columns:
        mask = normalized[col].apply(is_missing_token)
        normalized.loc[mask, col] = pd.NA

    duplicate_rows = int(df.duplicated().sum())
    missing_cells = int(normalized.isna().sum().sum())

    messy_text_cols = {}
    for col in df.select_dtypes(include="object").columns:
        suggestions = standardization.suggest_case_variants(df, col)
        if suggestions:
            messy_text_cols[col] = len(suggestions)

    date_like_cols = [
        c for c in df.select_dtypes(include="object").columns
        if _looks_like_date_column(df[c], c)
    ]
    invalid_dates_total = 0
    for col in date_like_cols:
        _, invalid = date_cleaning.standardize_dates(df.copy(), col)
        invalid_dates_total += len(invalid)

    numeric_candidate_cols = []
    for col in normalized.select_dtypes(include="object").columns:
        if type_conversion.detect_best_type(normalized[col]) in ("integer", "float"):
            numeric_candidate_cols.append(col)

    return {
        "rows": len(df),
        "columns": len(df.columns),
        "duplicate_rows": duplicate_rows,
        "missing_cells": missing_cells,
        "messy_text_columns": messy_text_cols,
        "messy_text_total": sum(messy_text_cols.values()),
        "date_like_columns": date_like_cols,
        "invalid_dates_total": invalid_dates_total,
        "numeric_candidate_columns": numeric_candidate_cols,
    }


def auto_clean(df: pd.DataFrame, logger=None):
    """Runs a safe, sensible default cleaning pipeline. Returns (df, actions, stats)."""
    actions = []
    df = df.copy()

    # 1) Recognize missing markers (NULL, blank, N/A, -, Unknown, ? ...)
    df = missing_values.normalize_missing(df)

    # 2) Trim stray spaces from every text column
    before_trim = df.copy()
    df = text_cleaning.trim_spaces(df, logger=logger)
    trimmed_any = not df.equals(before_trim)
    if trimmed_any:
        actions.append("Removed extra spaces from text values")

    # 3) Remove exact duplicate rows, keeping the first occurrence
    dup_count = int(df.duplicated().sum())
    if dup_count:
        df = duplicates.remove_duplicates(df, keep="first", logger=logger)
        actions.append(f"Removed {dup_count} duplicate row(s)")

    # 4) Fix obvious spelling/capitalization variants in text columns
    #    (e.g. "Ahemdabad" / "AHMEDABAD" / "ahmedabad" -> one consistent value)
    for col in df.select_dtypes(include="object").columns:
        suggestions = standardization.suggest_case_variants(df, col)
        if suggestions:
            df = standardization.apply_rules(df, col, suggestions, logger=logger)
            actions.append(f"Fixed {len(suggestions)} inconsistent spelling/format value(s) in '{col}'")

    # 5) Convert columns that are clearly numbers-stored-as-text
    for col in df.select_dtypes(include="object").columns:
        target = type_conversion.detect_best_type(df[col])
        if target in ("integer", "float"):
            df = type_conversion.convert_column(df, col, target, logger=logger)
            actions.append(f"Converted '{col}' to {target} numbers")

    # 6) Standardize date-like columns to YYYY-MM-DD (only check columns that
    #    are still text after step 5 — numeric columns are never dates)
    for col in df.select_dtypes(include="object").columns:
        if _looks_like_date_column(df[col], col):
            df, invalid = date_cleaning.standardize_dates(df, col, logger=logger)
            actions.append(f"Standardized dates in '{col}' to YYYY-MM-DD format")
            if invalid:
                actions.append(f"Flagged {len(invalid)} invalid date value(s) in '{col}' for review")

    # 7) Fill remaining missing values: numeric -> median, text -> most common value
    for col in df.columns:
        missing_count = int(df[col].isna().sum())
        if not missing_count:
            continue
        numeric = safe_numeric_series(df[col])
        if numeric.notna().sum() >= numeric.isna().sum():
            df = missing_values.handle_missing(df, col, "median", logger=logger)
            actions.append(f"Filled {missing_count} missing value(s) in '{col}' with the typical (median) value")
        else:
            mode_series = df[col].mode(dropna=True)
            if not mode_series.empty:
                df = missing_values.handle_missing(df, col, "mode", logger=logger)
                actions.append(f"Filled {missing_count} missing value(s) in '{col}' with the most common value")
            else:
                df = missing_values.handle_missing(df, col, "custom", custom_value="Unknown", logger=logger)
                actions.append(f"Filled {missing_count} missing value(s) in '{col}' with 'Unknown'")

    # 8) Detect (but don't remove) unusual/outlier numeric values — flag only
    outlier_notes = []
    for col in df.select_dtypes(include="number").columns:
        flags = outlier_detection.detect_outliers(df, col, method="iqr")
        n = int(flags.sum())
        if n:
            outlier_notes.append((col, n))
            actions.append(f"Found {n} unusually high/low value(s) in '{col}' — left in place for your review")

    stats = {"outlier_notes": outlier_notes}
    return df, actions, stats
