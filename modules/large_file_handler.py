"""
modules/large_file_handler.py — Phase 4: Large Files

For CSVs too big to comfortably load in one shot, this processes the file
in chunks: a cheap streaming pass computes profiling stats (row count,
missing counts, min/max, fill values) and a second streaming pass applies
a fixed set of row-independent cleaning operations (trim spaces, fill
missing with precomputed stats, basic type coercion) and writes the result
straight to an output CSV — the full cleaned dataset never has to fit in
RAM at once.

Row-dependent operations (exact/fuzzy duplicate removal across the whole
file, global outlier detection) are NOT supported in chunked mode — those
genuinely need the full dataset, or a different algorithm (e.g. hashing
for duplicates). This module intentionally sticks to what can be done
correctly one chunk at a time.
"""

import pandas as pd
from utils.helpers import is_missing_token, safe_numeric_series

DEFAULT_CHUNK_SIZE = 50_000


def estimate_row_count(path: str, chunksize: int = DEFAULT_CHUNK_SIZE) -> int:
    total = 0
    for chunk in pd.read_csv(path, chunksize=chunksize):
        total += len(chunk)
    return total


def profile_large_csv(path: str, chunksize: int = DEFAULT_CHUNK_SIZE) -> dict:
    """
    Streaming profile pass: row count, per-column missing counts, and
    per-column numeric mean/median (Welford-free, two-pass-safe since we
    just accumulate sums) for later use as fill values.
    """
    total_rows = 0
    missing_counts = {}
    numeric_sums = {}
    numeric_counts = {}
    columns = None

    for chunk in pd.read_csv(path, chunksize=chunksize):
        if columns is None:
            columns = list(chunk.columns)
            missing_counts = {c: 0 for c in columns}
            numeric_sums = {c: 0.0 for c in columns}
            numeric_counts = {c: 0 for c in columns}

        total_rows += len(chunk)
        for col in columns:
            missing_counts[col] += int(chunk[col].apply(is_missing_token).sum())
            numeric = safe_numeric_series(chunk[col])
            numeric_sums[col] += float(numeric.sum(skipna=True))
            numeric_counts[col] += int(numeric.notna().sum())

    means = {
        c: (numeric_sums[c] / numeric_counts[c]) if numeric_counts[c] else None
        for c in (columns or [])
    }

    return {
        "rows": total_rows,
        "columns": columns or [],
        "missing_counts": missing_counts,
        "numeric_means": means,
    }


def clean_large_csv(input_path: str, output_path: str, trim=True, fill_missing_numeric=True,
                     chunksize: int = DEFAULT_CHUNK_SIZE, logger=None) -> dict:
    """
    Streams `input_path` -> `output_path`, applying trim-spaces and
    mean-fill-for-numeric-columns chunk by chunk. Returns basic stats
    about what was written.
    """
    profile = profile_large_csv(input_path, chunksize=chunksize)
    means = profile["numeric_means"]

    total_written = 0
    first_chunk = True

    for chunk in pd.read_csv(input_path, chunksize=chunksize):
        chunk = chunk.copy()

        if trim:
            for col in chunk.select_dtypes(include="object").columns:
                chunk[col] = chunk[col].apply(lambda v: v.strip() if isinstance(v, str) else v)

        if fill_missing_numeric:
            for col in chunk.columns:
                if means.get(col) is not None:
                    numeric = safe_numeric_series(chunk[col])
                    chunk[col] = numeric.fillna(means[col])

        chunk.to_csv(output_path, mode="w" if first_chunk else "a",
                      header=first_chunk, index=False)
        first_chunk = False
        total_written += len(chunk)

    if logger:
        logger.log(
            f"Large-file mode: streamed {total_written} rows from "
            f"'{input_path}' to '{output_path}' (chunk size {chunksize})"
        )

    return {"rows_written": total_written, "profile": profile}
