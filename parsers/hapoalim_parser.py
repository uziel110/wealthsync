"""
Parser for Bank Hapoalim (בנק הפועלים) securities portfolio Excel exports.

Real export format (verified against "תיק עדכני.xlsx"):
  - Rows 0–10: metadata (title, account number, dates, portfolio summary)
  - Row 11: column headers
  - Row 12+: one row per security

Column mapping:
  שם נייר                  → asset_name
  מספר נייר                → asset_id
  כמות בתיק                → quantity
  שווי אחזקה (₪)           → market_value
  שינוי מעלות בש"ח         → total_gl_ils  →  cost_basis = market_value − total_gl_ils
  שער אחרון                → last_price (extra)
  שינוי יומי %             → change_pct (extra)
  שער עלות                 → avg_cost_price (extra, ILS securities in agorot)
"""

from __future__ import annotations

import pandas as pd
from io import BytesIO

# Required columns for detection
_REQUIRED = {"שם נייר", "מספר נייר", "כמות בתיק", 'שווי אחזקה (₪)'}

_COL_MAP = {
    "שם נייר":                  "asset_name",
    "מספר נייר":                "asset_id",
    "כמות בתיק":               "quantity",
    'שווי אחזקה (₪)':          "market_value",
    'שינוי מעלות בש"ח':        "total_gl_ils",
    "שער אחרון":               "last_price",
    "שינוי יומי %":            "change_pct",
    "שער עלות":                "avg_cost_price",
    "שינוי מעלות %":           "gain_pct_raw",
}


def _normalize_col(name: str) -> str:
    """Normalize typographic quotes to straight ASCII so matching is reliable."""
    return (
        name.replace("“", '"').replace("”", '"')
            .replace("‘", "'").replace("’", "'")
            .strip()
    )


def _to_numeric(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("−", "-", regex=False)
        .str.replace("(", "-", regex=False)
        .str.replace(")", "", regex=False)
        .pipe(pd.to_numeric, errors="coerce")
    )


def _find_header_row(df_raw: pd.DataFrame) -> int:
    """Find the row index that contains the required column headers."""
    for i, row in df_raw.head(25).iterrows():
        row_vals = {_normalize_col(str(v)) for v in row if pd.notna(v)}
        if _REQUIRED.issubset(row_vals):
            return int(i)
    raise ValueError(
        "לא זוהתה שורת כותרות תואמת ב-25 השורות הראשונות של קובץ הפועלים.\n"
        "ייצא את התיק מהאתר: תיק ניירות ערך ← ייצוא ל-Excel\n"
        f"עמודות נדרשות: {', '.join(sorted(_REQUIRED))}"
    )


def parse_hapoalim(file: "BytesIO | str", account_name: str = "בנק הפועלים") -> pd.DataFrame:
    """
    Parse a Bank Hapoalim securities Excel export (תיק עדכני).

    Returns a normalised DataFrame with columns:
        account, asset_name, asset_id, quantity, cost_basis, market_value, source
    """
    raw = pd.read_excel(file, header=None, engine="openpyxl")
    header_row = _find_header_row(raw)

    df = pd.read_excel(file, header=header_row, engine="openpyxl")
    # normalize column names (typographic quotes → straight ASCII)
    df.columns = [_normalize_col(c) for c in df.columns]

    # keep only known columns
    keep = {h: e for h, e in _COL_MAP.items() if h in df.columns}
    df = df[list(keep.keys())].rename(columns=keep).copy()

    # drop empty / summary rows
    df = df.dropna(subset=["asset_name", "quantity", "market_value"])
    df = df[df["asset_name"].astype(str).str.strip().ne("")]
    df = df[df["asset_name"].astype(str).str.strip().ne("nan")]

    # numeric conversion
    for col in ("quantity", "market_value", "total_gl_ils", "last_price",
                "change_pct", "avg_cost_price", "gain_pct_raw"):
        if col in df.columns:
            df[col] = _to_numeric(df[col])

    df = df[df["market_value"].notna() & (df["market_value"] != 0)]

    # cost_basis = market_value − gain/loss (same approach as IBI Format A)
    if "total_gl_ils" in df.columns:
        df["cost_basis"] = (df["market_value"] - df["total_gl_ils"]).round(2)
    else:
        df["cost_basis"] = df["market_value"]

    # canonical column order
    canonical = ["asset_name", "asset_id", "quantity", "cost_basis", "market_value"]
    extras    = [c for c in df.columns if c not in canonical]
    df = df[canonical + extras]

    df.insert(0, "account", account_name)
    df["source"] = "הפועלים"
    return df.reset_index(drop=True)
