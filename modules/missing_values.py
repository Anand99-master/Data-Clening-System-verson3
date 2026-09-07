"""
modules/missing_values.py — Module 4: Missing Value Detection & Handling

Detects NULL/Blank/N/A/NA/-/Unknown/? style missing markers, then applies
one of: Remove, Mean, Median, Mode, or a Custom value — per column.
"""

import pandas as pd
from utils.helpers import is_missing_token, safe_numeric_series


def normalize_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Convert every recognized missing-marker into real NaN so pandas
    functions (mean/median/mode/dropna) work consistently."""
    df = df.copy()
    for col in df.columns:
        mask = df[col].apply(is_missing_token)
        df.loc[mask, col] = pd.NA
    return df


def handle_missing(df: pd.DataFrame, column: str, strategy: str, custom_value=None, logger=None) -> pd.DataFrame:
    """
    strategy: one of 'remove', 'mean', 'median', 'mode', 'custom'
    """
    df = df.copy()
    missing_count = int(df[column].isna().sum())
    if missing_count == 0:
        return df

    if strategy == "remove":
        df = df[df[column].notna()]
        msg = f"Removed {missing_count} rows with missing '{column}'"

    elif strategy in ("mean", "median"):
        numeric = safe_numeric_series(df[column])
        fill_value = numeric.mean() if strategy == "mean" else numeric.median()
        df[column] = numeric.fillna(fill_value)
        msg = f"Filled {missing_count} missing '{column}' values with {strategy} ({fill_value:.2f})"

    elif strategy == "mode":
        mode_series = df[column].mode(dropna=True)
        fill_value = mode_series.iloc[0] if not mode_series.empty else custom_value
        df[column] = df[column].fillna(fill_value)
        msg = f"Filled {missing_count} missing '{column}' values with mode ({fill_value})"

    elif strategy == "custom":
        df[column] = df[column].fillna(custom_value)
        msg = f"Filled {missing_count} missing '{column}' values with custom value '{custom_value}'"

    else:
        raise ValueError(f"Unknown strategy '{strategy}'")

    if logger:
        logger.log(msg)
    return df
