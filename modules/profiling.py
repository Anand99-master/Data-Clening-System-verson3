"""
modules/profiling.py — Module 3: Data Profiling

Produces the per-column health-check table:

    Column          Type      Missing   Unique
    Customer Name   Text      12        2,340
    Age             Integer   48        65
    ...
"""

import pandas as pd
from utils.helpers import is_missing_token


def _friendly_dtype(series: pd.Series) -> str:
    if pd.api.types.is_integer_dtype(series):
        return "Integer"
    if pd.api.types.is_float_dtype(series):
        return "Float"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "Date"
    if pd.api.types.is_bool_dtype(series):
        return "Boolean"
    return "Text"


def profile_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in df.columns:
        series = df[col]
        missing_count = int(series.apply(is_missing_token).sum())
        rows.append(
            {
                "Column": col,
                "Type": _friendly_dtype(series),
                "Missing": missing_count,
                "Missing %": round(100 * missing_count / len(df), 1) if len(df) else 0,
                "Unique": int(series.nunique(dropna=True)),
            }
        )
    return pd.DataFrame(rows)
