"""
modules/file_handler.py — Module 1: File Upload

Reads .xlsx / .xls / .csv into a pandas DataFrame and reports basic
file-level stats, as shown on the "Dashboard" panel in the UI mock-up:

    Rows: 12,450   Columns: 18   Missing: 1,280   Duplicate: 324
"""

import pandas as pd

ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}
MAX_FILE_SIZE_MB = 200  # Module 26 — security: enforce a size limit


def get_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def is_allowed_file(filename: str) -> bool:
    return get_extension(filename) in ALLOWED_EXTENSIONS


def read_file(file_like, filename: str) -> pd.DataFrame:
    """
    file_like: a file path or a file-like object (e.g. Streamlit's UploadedFile)
    filename:  original filename, used to decide the parser
    """
    ext = get_extension(filename)
    if not is_allowed_file(filename):
        raise ValueError(
            f"Unsupported file type '.{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    if ext == "csv":
        # Try common encodings; fall back gracefully on messy real-world files
        for encoding in ("utf-8", "utf-8-sig", "latin1"):
            try:
                return pd.read_csv(file_like, encoding=encoding)
            except UnicodeDecodeError:
                file_like.seek(0) if hasattr(file_like, "seek") else None
                continue
        raise ValueError("Could not decode CSV file with common encodings.")
    else:
        return pd.read_excel(file_like)


def file_summary(df: pd.DataFrame, filename: str, size_bytes: int = None) -> dict:
    """Basic structure summary shown immediately after upload."""
    summary = {
        "File": filename,
        "Rows": len(df),
        "Columns": len(df.columns),
        "Missing": int(df.isna().sum().sum()),
        "Duplicate": int(df.duplicated().sum()),
    }
    if size_bytes is not None:
        summary["File Size"] = f"{size_bytes / (1024 * 1024):.2f} MB"
    return summary
