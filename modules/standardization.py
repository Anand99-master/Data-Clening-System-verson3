"""
modules/standardization.py — Module 7 (Text Standardization) &
Module 11 (Standardization Rules Engine)

Two layers:
1. `suggest_case_variants` — finds values that only differ by case/whitespace
   ("Ahmedabad" / "AHMEDABAD" / "ahmedabad") and proposes ONE canonical form.
   Nothing is silently changed — the caller applies suggestions explicitly
   (mirrors the "[Apply] [Ignore]" UX in the architecture doc).
2. `apply_rules` — applies an explicit mapping dict loaded from
   config/cleaning_rules.json, e.g. {"Ahemdabad": "Ahmedabad"}.
"""

import json
import pandas as pd
from collections import defaultdict


def suggest_case_variants(df: pd.DataFrame, column: str):
    """
    Groups values that are identical once lower-cased & stripped, and
    suggests the most frequent original form as the canonical value.
    Returns: {variant_value: suggested_canonical_value}
    """
    groups = defaultdict(list)
    for val in df[column].dropna().astype(str):
        key = val.strip().lower()
        groups[key].append(val)

    suggestions = {}
    for key, variants in groups.items():
        unique_variants = set(variants)
        if len(unique_variants) <= 1:
            continue
        # canonical = most frequent variant, tie-broken by title case
        counts = pd.Series(variants).value_counts()
        canonical = counts.index[0]
        for v in unique_variants:
            if v != canonical:
                suggestions[v] = canonical
    return suggestions


def apply_rules(df: pd.DataFrame, column: str, mapping: dict, logger=None) -> pd.DataFrame:
    df = df.copy()
    if column not in df.columns:
        return df

    changed = df[column].isin(mapping.keys()).sum()
    df[column] = df[column].replace(mapping)

    if logger and changed:
        logger.log(f"Standardized {changed} value(s) in '{column}' using rules engine")
    return df


def load_rules(path: str) -> dict:
    """Loads config/cleaning_rules.json — nested dict of {column: {from: to}}"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# Common built-in normalization used a lot in real datasets (Module 7 example)
GENDER_RULES = {
    "M": "Male", "MALE": "Male", "m": "Male", "male": "Male",
    "F": "Female", "FEMALE": "Female", "f": "Female", "female": "Female",
}
