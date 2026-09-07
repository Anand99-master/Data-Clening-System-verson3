"""
modules/validation.py — Module 13 (Invalid Values) & Module 14 (Business Rule Validation)

Two kinds of checks:
1. Range/allowed-value rules per column, e.g. Age must be 0-120.
2. Formula rules across columns, e.g. Quantity * Price == Sales,
   flagging rows where the expected value doesn't match the actual one.
"""

import pandas as pd
from utils.helpers import safe_numeric_series


def validate_range(df: pd.DataFrame, column: str, min_value=None, max_value=None) -> pd.DataFrame:
    """Returns the subset of rows where `column` falls outside [min_value, max_value]."""
    numeric = safe_numeric_series(df[column])
    mask = pd.Series(False, index=df.index)
    if min_value is not None:
        mask |= numeric < min_value
    if max_value is not None:
        mask |= numeric > max_value
    return df.loc[mask]


def validate_allowed_values(df: pd.DataFrame, column: str, allowed: list) -> pd.DataFrame:
    """Returns rows where `column` is not in the allowed set (and not null)."""
    mask = ~df[column].isin(allowed) & df[column].notna()
    return df.loc[mask]


def validate_formula(df: pd.DataFrame, col_a: str, operator: str, col_b: str,
                      result_col: str, tolerance: float = 0.01) -> pd.DataFrame:
    """
    Checks result_col == col_a <operator> col_b within a tolerance.
    operator: '*', '+', '-', '/'
    Returns a DataFrame of mismatched rows with Expected/Actual/Difference columns.
    """
    a = safe_numeric_series(df[col_a])
    b = safe_numeric_series(df[col_b])
    actual = safe_numeric_series(df[result_col])

    if operator == "*":
        expected = a * b
    elif operator == "+":
        expected = a + b
    elif operator == "-":
        expected = a - b
    elif operator == "/":
        expected = a / b
    else:
        raise ValueError(f"Unsupported operator '{operator}'")

    diff = (actual - expected).abs()
    mismatched = diff > tolerance

    result = df.loc[mismatched].copy()
    result["Expected"] = expected[mismatched]
    result["Actual"] = actual[mismatched]
    result["Difference"] = (actual[mismatched] - expected[mismatched])
    return result
