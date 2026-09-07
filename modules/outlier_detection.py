"""
modules/outlier_detection.py — Module 10: Outlier Detection

Methods: IQR, Z-score, Standard deviation, Percentile.
Outliers are only ever flagged here — removal is a separate, explicit
user decision ([Remove] [Keep] [Review]), never automatic.
"""

import numpy as np
import pandas as pd
from utils.helpers import safe_numeric_series


def detect_outliers(df: pd.DataFrame, column: str, method: str = "iqr", threshold: float = 1.5) -> pd.Series:
    """
    Returns a boolean Series aligned to df.index: True where the value is
    flagged as a possible outlier.

    method: 'iqr' | 'zscore' | 'std' | 'percentile'
    threshold:
        iqr        -> multiplier on the IQR (default 1.5)
        zscore/std -> number of std-deviations away from the mean (default use 3)
        percentile -> tail fraction, e.g. 0.01 flags bottom/top 1%
    """
    numeric = safe_numeric_series(df[column])
    flags = pd.Series(False, index=df.index)

    if method == "iqr":
        q1, q3 = numeric.quantile(0.25), numeric.quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - threshold * iqr, q3 + threshold * iqr
        flags = (numeric < lower) | (numeric > upper)

    elif method in ("zscore", "std"):
        z_threshold = threshold if threshold != 1.5 else 3.0
        mean, std = numeric.mean(), numeric.std()
        if std and not np.isnan(std):
            z = (numeric - mean) / std
            flags = z.abs() > z_threshold

    elif method == "percentile":
        tail = threshold if threshold != 1.5 else 0.01
        lower = numeric.quantile(tail)
        upper = numeric.quantile(1 - tail)
        flags = (numeric < lower) | (numeric > upper)

    else:
        raise ValueError(f"Unknown method '{method}'")

    return flags.fillna(False)


def outlier_report(df: pd.DataFrame, column: str, method: str = "iqr", threshold: float = 1.5) -> pd.DataFrame:
    flags = detect_outliers(df, column, method, threshold)
    return df.loc[flags, [column]].assign(flagged_by=method)
