"""
utils/helpers.py

Small shared helpers: safe numeric coercion, currency stripping, etc.
"""

import re
import pandas as pd

MISSING_TOKENS = {
    "", "na", "n/a", "null", "none", "-", "?", "unknown", "nan", "nil", "#n/a"
}

CURRENCY_CHARS = re.compile(r"[₹$€£,\s]")


def is_missing_token(value) -> bool:
    """Detect blanks/NULL/NA/-/Unknown/? style missing markers (Module 4)."""
    if pd.isna(value):
        return True
    if isinstance(value, str) and value.strip().lower() in MISSING_TOKENS:
        return True
    return False


def strip_currency(value):
    """Convert '₹29,600' / '$1,200.50' style strings into floats."""
    if isinstance(value, str):
        cleaned = CURRENCY_CHARS.sub("", value)
        try:
            return float(cleaned)
        except ValueError:
            return value
    return value


def safe_numeric_series(series: pd.Series) -> pd.Series:
    """Best-effort conversion of a text column to numeric, currency-aware."""
    cleaned = series.apply(strip_currency)
    return pd.to_numeric(cleaned, errors="coerce")
