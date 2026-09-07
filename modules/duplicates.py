"""
modules/duplicates.py — Module 5: Duplicate Detection

Exact duplicate handling (remove / keep first / keep last / don't remove)
plus an optional fuzzy-matching pass (rapidfuzz) to catch near-duplicates
like "Anand (Surat)" vs "ANAND (Surat)".
"""

import pandas as pd


def count_duplicates(df: pd.DataFrame, subset=None) -> int:
    return int(df.duplicated(subset=subset, keep=False).sum())


def remove_duplicates(df: pd.DataFrame, subset=None, keep="first", logger=None) -> pd.DataFrame:
    """
    keep: 'first', 'last', or False (don't remove — just report)
    """
    before = len(df)
    if keep is False:
        if logger:
            logger.log(f"Duplicate check: {count_duplicates(df, subset)} duplicate rows found (not removed)")
        return df

    cleaned = df.drop_duplicates(subset=subset, keep=keep)
    removed = before - len(cleaned)
    if logger and removed:
        logger.log(f"Removed {removed} duplicate rows (keep={keep})")
    return cleaned


def find_fuzzy_duplicates(df: pd.DataFrame, column: str, threshold: int = 90):
    """
    Returns a list of (index_a, index_b, value_a, value_b, score) tuples for
    near-duplicate text values in `column`, using RapidFuzz if available.
    This is presented to the user for review — never auto-merged.
    """
    try:
        from rapidfuzz import fuzz
    except ImportError:
        return []

    values = df[column].dropna().astype(str)
    matches = []
    items = list(values.items())
    for i in range(len(items)):
        idx_a, val_a = items[i]
        for j in range(i + 1, len(items)):
            idx_b, val_b = items[j]
            if val_a.strip().lower() == val_b.strip().lower():
                continue  # already an exact/case duplicate, not "fuzzy"
            score = fuzz.ratio(val_a.lower(), val_b.lower())
            if score >= threshold:
                matches.append((idx_a, idx_b, val_a, val_b, score))
    return matches
