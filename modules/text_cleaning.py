"""
modules/text_cleaning.py — Module 6: Extra Spaces Cleaning

Trims leading/trailing/inner-repeated whitespace from text columns:
" Anand", "Anand ", " Anand " -> "Anand"
"""

import re
import pandas as pd


def trim_spaces(df: pd.DataFrame, columns=None, logger=None) -> pd.DataFrame:
    df = df.copy()
    text_columns = columns or df.select_dtypes(include="object").columns.tolist()

    total_changed = 0
    for col in text_columns:
        if col not in df.columns:
            continue

        def _clean(v):
            nonlocal total_changed
            if isinstance(v, str):
                new_v = re.sub(r"\s+", " ", v).strip()
                if new_v != v:
                    total_changed += 1
                return new_v
            return v

        df[col] = df[col].apply(_clean)

    if logger and total_changed:
        logger.log(f"Trimmed extra spaces in {total_changed} values across {len(text_columns)} text column(s)")
    return df
