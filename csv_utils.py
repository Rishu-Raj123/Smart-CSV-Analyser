from io import BytesIO
import numpy as np
import pandas as pd

def read_uploaded_csv(uploaded_file) -> pd.DataFrame:
    """Read an uploaded CSV, trying common encodings."""
    raw = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else uploaded_file.read()
    if not raw:
        raise ValueError("The uploaded file is empty.")
    last_error = None
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return pd.read_csv(BytesIO(raw), encoding=encoding, low_memory=False)
        except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as exc:
            last_error = exc
    raise ValueError(f"CSV parsing failed: {last_error}")

def get_overview(df: pd.DataFrame) -> dict:
    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "missing_cells": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
    }

def build_column_profile(df: pd.DataFrame) -> pd.DataFrame:
    missing = df.isna().sum()
    rows = len(df)
    missing_pct = (missing / rows * 100).round(2) if rows else missing.astype(float)
    return pd.DataFrame({
        "Column": [str(c) for c in df.columns],
        "Data type": [str(dtype) for dtype in df.dtypes],
        "Missing": missing.astype(int).values,
        "Missing %": missing_pct.values,
        "Unique values": [int(df[c].nunique(dropna=True)) for c in df.columns],
    })

def get_numeric_summary(df: pd.DataFrame) -> pd.DataFrame:
    numeric = df.select_dtypes(include=np.number)
    if numeric.empty:
        return pd.DataFrame()
    return numeric.describe().T.reset_index(names="Column").round(3)

def clean_dataframe(
    df: pd.DataFrame,
    drop_duplicates: bool = True,
    fill_missing: bool = False,
    fill_strategy: str = "Median for numeric / mode for text",
    trim_text: bool = True,
) -> pd.DataFrame:
    """Return a cleaned copy. Never mutate the original dataframe."""
    cleaned = df.copy()
    if trim_text:
        for col in cleaned.select_dtypes(include=["object", "string"]).columns:
            cleaned[col] = cleaned[col].map(
                lambda value: value.strip() if isinstance(value, str) else value
            )
    if drop_duplicates:
        cleaned = cleaned.drop_duplicates()
    if fill_missing:
        numeric_cols = cleaned.select_dtypes(include=np.number).columns
        categorical_cols = cleaned.columns.difference(numeric_cols)
        for col in numeric_cols:
            if cleaned[col].isna().any():
                if fill_strategy == "Zero for numeric / empty text":
                    replacement = 0
                else:
                    median = cleaned[col].median()
                    replacement = median if pd.notna(median) else 0
                cleaned[col] = cleaned[col].fillna(replacement)

        for col in categorical_cols:
            if cleaned[col].isna().any():
                if fill_strategy == "Zero for numeric / empty text":
                    replacement = ""
                else:
                    modes = cleaned[col].mode(dropna=True)
                    replacement = modes.iloc[0] if not modes.empty else ""
                cleaned[col] = cleaned[col].fillna(replacement)
    return cleaned

def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")