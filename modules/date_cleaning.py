"""
modules/date_cleaning.py — Module 9: Date Cleaning

Parses messy real-world date strings (05/09/2026, 05-09-2026, 2026/09/05,
"Sep 5, 2026" ...) and standardizes to ISO format YYYY-MM-DD. Invalid
dates (e.g. 32/15/2026) are flagged rather than silently dropped.
"""

import re
import pandas as pd
from dateutil import parser as dateutil_parser

# Matches unambiguous ISO-style dates: 2026-09-05, 2026/09/05, 2026.09.05
_ISO_PATTERN = re.compile(r"^\s*(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})\s*$")


def _try_parse(value):
    if pd.isna(value):
        return None
    if isinstance(value, (pd.Timestamp,)):
        return value

    text = str(value).strip()

    # ISO-style (YYYY-MM-DD) is unambiguous — parse it directly rather than
    # through dayfirst=True, which incorrectly swaps month/day for these
    # (e.g. dateutil.parser.parse('2026-09-05', dayfirst=True) wrongly
    # returns 2026-05-09 — a real bug we hit and want to avoid).
    iso_match = _ISO_PATTERN.match(text)
    if iso_match:
        year, month, day = (int(g) for g in iso_match.groups())
        try:
            return pd.Timestamp(year=year, month=month, day=day)
        except (ValueError, OverflowError):
            return None

    # Everything else (05/09/2026, "Sep 5, 2026", 05-09-2026, ...) is
    # genuinely ambiguous between day-first and month-first conventions,
    # so we fall back to the dayfirst heuristic.
    try:
        return dateutil_parser.parse(text, dayfirst=True, fuzzy=False)
    except (ValueError, OverflowError, TypeError):
        return None


def standardize_dates(df: pd.DataFrame, column: str, logger=None):
    """
    Returns (df, invalid_rows) where invalid_rows is a list of the original
    values that could not be parsed at all (so the UI can flag them,
    e.g. 32/15/2026 ❌).
    """
    df = df.copy()
    invalid_rows = []
    converted = 0

    def _convert(v):
        nonlocal converted
        if pd.isna(v):
            return v
        parsed = _try_parse(v)
        if parsed is None:
            invalid_rows.append(v)
            return v  # leave as-is, flagged separately
        converted += 1
        return parsed.strftime("%Y-%m-%d")

    df[column] = df[column].apply(_convert)

    if logger:
        logger.log(f"Converted {converted} values in '{column}' to YYYY-MM-DD format")
        if invalid_rows:
            logger.log(f"Detected {len(invalid_rows)} invalid date(s) in '{column}'")

    return df, invalid_rows
