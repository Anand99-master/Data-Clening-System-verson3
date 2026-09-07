"""
modules/type_conversion.py — Module 8: Data Type Detection & Conversion

Detects the "real" type of a text column (integer / float / currency / text)
and converts it. Handles currency-formatted numbers like ₹29,600.
"""

import pandas as pd
from utils.helpers import safe_numeric_series


def detect_best_type(series: pd.Series) -> str:
    """Heuristic type guess for a column currently stored as text/object."""
    non_null = series.dropna()
    if non_null.empty:
        return "text"

    numeric = safe_numeric_series(non_null)
    numeric_ratio = numeric.notna().mean()

    if numeric_ratio >= 0.95:
        # integer if every parsed value has no fractional part
        if (numeric.dropna() % 1 == 0).all():
            return "integer"
        return "float"
    return "text"


def convert_column(df: pd.DataFrame, column: str, target_type: str, logger=None) -> pd.DataFrame:
    df = df.copy()
    before_dtype = df[column].dtype

    if target_type == "integer":
        numeric = safe_numeric_series(df[column])
        df[column] = numeric.round().astype("Int64")
    elif target_type == "float":
        df[column] = safe_numeric_series(df[column])
    elif target_type == "text":
        df[column] = df[column].astype(str)
    else:
        raise ValueError(f"Unsupported target_type '{target_type}'")

    if logger:
        logger.log(f"Converted '{column}' from {before_dtype} to {target_type}")
    return df


def auto_detect_all(df: pd.DataFrame) -> dict:
    """Returns {column: suggested_type} for every object-dtype column."""
    suggestions = {}
    for col in df.select_dtypes(include="object").columns:
        suggestions[col] = detect_best_type(df[col])
    return suggestions
