"""
Parser for Bank Hapoalim (פועלים) securities portfolio Excel exports.

Bank Hapoalim offers several export formats from their online banking portal.
This parser tries multiple known column name variants and falls back gracefully.

Expected export path (online banking):
  תיק ניירות ערך → ייצוא ל-Excel

Known column variants across Hapoalim portal versions:
  asset_name  : שם נייר | שם הנייר | תיאור נייר | שם ני"ע
  asset_id    : מספר נייר | מס' נייר | מספר ני"ע | קוד נייר
  quantity    : כמות | יחידות | כמות יחידות
  cost_basis  : עלות | עלות כוללת | עלות רכישה | מחיר עלות כולל | עלות ממוצעת × כמות
  market_value: שווי שוק | ערך שוק | שווי נוכחי | שווי שוק כולל
"""

from __future__ import annotations

import pandas as pd
from io import BytesIO

# Each tuple = ordered list of candidates; first match wins
_NAME_CANDIDATES  = ["שם נייר", "שם הנייר", 'שם ני"ע', "תיאור נייר", "שם"]
_ID_CANDIDATES    = ["מספר נייר", 'מס\' נייר', 'מספר ני"ע', "קוד נייר", "סמל"]
_QTY_CANDIDATES   = ["כמות", "יחידות", "כמות יחידות", "כמות נייר"]
_COST_CANDIDATES  = ["עלות", "עלות כוללת", "עלות רכישה", "מחיר עלות", "עלות ממוצעת כוללת"]
_MV_CANDIDATES    = ["שווי שוק", "ערך שוק", "שווי נוכחי", "שווי שוק כולל", "שווי"]


def _first_match(columns: list[str], candidates: list[str]) -> str | None:
    col_set = {c.strip() for c in columns}
    for c in candidates:
        if c in col_set:
            return c
    return None


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
    """Scan first 20 rows for one containing ≥ 2 known asset-column names."""
    all_candidates = set(
        _NAME_CANDIDATES + _ID_CANDIDATES + _QTY_CANDIDATES +
        _COST_CANDIDATES + _MV_CANDIDATES
    )
    for i, row in df_raw.head(20).iterrows():
        row_vals = {str(v).strip() for v in row if pd.notna(v)}
        if len(row_vals & all_candidates) >= 2:
            return int(i)
    raise ValueError(
        "לא זוהתה שורת כותרות מוכרת ב-20 השורות הראשונות של קובץ הפועלים.\n"
        "ייצא את התיק מהאתר: תיק ניירות ערך ← ייצוא ל-Excel"
    )


def parse_hapoalim(file: "BytesIO | str", account_name: str = "בנק הפועלים") -> pd.DataFrame:
    """
    Parse a Bank Hapoalim securities Excel export.

    Returns a normalised DataFrame with columns:
        account, asset_name, asset_id, quantity, cost_basis, market_value, source
    """
    raw = pd.read_excel(file, header=None, engine="openpyxl")
    header_row = _find_header_row(raw)

    df = pd.read_excel(file, header=header_row, engine="openpyxl")
    df.columns = df.columns.str.strip()
    cols = df.columns.tolist()

    name_col = _first_match(cols, _NAME_CANDIDATES)
    id_col   = _first_match(cols, _ID_CANDIDATES)
    qty_col  = _first_match(cols, _QTY_CANDIDATES)
    cost_col = _first_match(cols, _COST_CANDIDATES)
    mv_col   = _first_match(cols, _MV_CANDIDATES)

    missing = [label for label, col in [
        ("שם נייר", name_col), ("כמות", qty_col), ("שווי שוק", mv_col)
    ] if col is None]
    if missing:
        raise ValueError(
            f"לא נמצאו עמודות חיוניות: {', '.join(missing)}\n"
            f"עמודות שנמצאו בקובץ: {', '.join(cols)}"
        )

    rename_map = {name_col: "asset_name", qty_col: "quantity", mv_col: "market_value"}
    if id_col:
        rename_map[id_col] = "asset_id"
    if cost_col:
        rename_map[cost_col] = "cost_basis"

    keep = [c for c in rename_map if c in df.columns]
    df = df[keep].rename(columns=rename_map).copy()

    df = df.dropna(subset=["asset_name", "quantity", "market_value"])
    df = df[df["asset_name"].astype(str).str.strip().ne("")]
    df = df[df["asset_name"].astype(str).str.strip().ne("nan")]

    for col in ("quantity", "market_value", "cost_basis"):
        if col in df.columns:
            df[col] = _to_numeric(df[col])

    df = df[df["market_value"].notna() & (df["market_value"] != 0)]

    if "asset_id" not in df.columns:
        df["asset_id"] = ""
    if "cost_basis" not in df.columns:
        df["cost_basis"] = df["market_value"]

    df.insert(0, "account", account_name)
    df["source"] = "הפועלים"
    return df.reset_index(drop=True)
