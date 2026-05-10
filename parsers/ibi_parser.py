"""
Parser for Psagot / IBI Excel exports.

Supports two formats auto-detected by header content:

Format A — "Portfolio" (real Psagot export, e.g. "Portfolio - 150-XXXXXX - DD.MM.YYYY.xlsx"):
  שם                  → asset_name
  סימבול              → asset_id
  כמות                → quantity
  שווי כולל           → market_value
  שער עלות ממוצע      → avg_cost_price
  cost_basis computed as: quantity × avg_cost_price
  extra columns preserved: last_price, change_pct, daily_gl, total_gl, currency, portfolio_pct

Format B — legacy IBI template (manual / older exports):
  שם נייר             → asset_name
  מספר נייר           → asset_id
  כמות נוכחית         → quantity
  עלות                → cost_basis
  שווי נוכחי          → market_value
"""

from __future__ import annotations

import pandas as pd
from io import BytesIO

# ── Format A — real Psagot Portfolio export ───────────────────────────────────
_FORMAT_A_REQUIRED = {"שם", "סימבול", "כמות", "שווי כולל", "שער עלות ממוצע"}

_FORMAT_A_MAP = {
    "שם":               "asset_name",
    "סימבול":           "asset_id",
    "כמות":             "quantity",
    "שווי כולל":        "market_value",
    # cost_basis = market_value − total_gl (prices in ILS are in agorot, so avg_cost_price × qty is unreliable)
    "רווח/הפסד כולל":   "total_gl",
    # extra columns kept
    "שער אחרון":        "last_price",
    "% שינוי":          "change_pct",
    "רווח/הפסד יומי":   "daily_gl",
    "מטבע":             "currency",
    "אחוז מהתיק":       "portfolio_pct",
    "שער עלות ממוצע":   "avg_cost_price",
}

# ── Format B — legacy IBI template ───────────────────────────────────────────
_FORMAT_B_REQUIRED = {"שם נייר", "מספר נייר", "כמות נוכחית", "עלות", "שווי נוכחי"}

_FORMAT_B_MAP = {
    "שם נייר":      "asset_name",
    "מספר נייר":    "asset_id",
    "כמות נוכחית":  "quantity",
    "עלות":         "cost_basis",
    "שווי נוכחי":   "market_value",
}


# ── helpers ───────────────────────────────────────────────────────────────────

def _to_numeric(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("−", "-", regex=False)
        .pipe(pd.to_numeric, errors="coerce")
    )


def _detect_format(columns: set[str]) -> str:
    """Return 'A', 'B', or raise ValueError."""
    if _FORMAT_A_REQUIRED.issubset(columns):
        return "A"
    if _FORMAT_B_REQUIRED.issubset(columns):
        return "B"
    raise ValueError(
        "הקובץ אינו מזוהה כייצוא פסגות תקני.\n\n"
        "פורמט A (Portfolio הנוכחי) מצפה לעמודות: " + "  ·  ".join(sorted(_FORMAT_A_REQUIRED)) + "\n"
        "פורמט B (IBI ישן) מצפה לעמודות: "          + "  ·  ".join(sorted(_FORMAT_B_REQUIRED))
    )


def _find_header_row(df_raw: pd.DataFrame) -> int:
    """Scan first 15 rows for a row that satisfies either format."""
    for i, row in df_raw.head(15).iterrows():
        cols = set(str(c).strip() for c in row if pd.notna(c))
        if _FORMAT_A_REQUIRED.issubset(cols) or _FORMAT_B_REQUIRED.issubset(cols):
            return int(i)
    raise ValueError(
        "לא נמצאה שורת כותרות מוכרת ב-15 השורות הראשונות של הקובץ."
    )


# ── public API ────────────────────────────────────────────────────────────────

def parse_ibi(
    file: "BytesIO | str",
    account_name: str = "פסגות",
    source: str | None = None,
) -> pd.DataFrame:
    """
    Parse a Psagot / IBI Excel export into a normalised holdings DataFrame.

    Parameters
    ----------
    file        : path or BytesIO of the Excel file
    account_name: display name stored in the 'account' column
    source      : override the 'source' tag; auto-detected from format if None
                  (Format A → "פסגות", Format B → "IBI")

    Returns
    -------
    DataFrame with columns:
        account, asset_name, asset_id, quantity, cost_basis, market_value, source
        + optional: last_price, change_pct, daily_gl, total_gl, currency, portfolio_pct
    """
    raw = pd.read_excel(file, header=None, engine="openpyxl")
    header_row = _find_header_row(raw)

    df = pd.read_excel(file, header=header_row, engine="openpyxl")
    df.columns = df.columns.str.strip()

    fmt = _detect_format(set(df.columns))

    if fmt == "A":
        df = _parse_format_a(df)
        auto_source = "פסגות"
    else:
        df = _parse_format_b(df)
        auto_source = "IBI"

    df.insert(0, "account", account_name)
    df["source"] = source if source is not None else auto_source
    return df.reset_index(drop=True)


def _parse_format_a(df: pd.DataFrame) -> pd.DataFrame:
    """Real Psagot Portfolio export — cost_basis derived from avg_cost_price × quantity."""
    # keep only known columns that exist
    keep = {h: e for h, e in _FORMAT_A_MAP.items() if h in df.columns}
    df = df[list(keep.keys())].rename(columns=keep).copy()

    df = df.dropna(subset=["asset_name", "quantity", "market_value"])
    df = df[df["asset_name"].astype(str).str.strip() != ""]

    for col in ("quantity", "market_value", "total_gl", "avg_cost_price",
                "last_price", "change_pct", "daily_gl", "portfolio_pct"):
        if col in df.columns:
            df[col] = _to_numeric(df[col])

    # cost_basis = market_value − total_gl
    # (avg_cost_price for ILS securities is in agorot, making direct multiplication unreliable)
    df["cost_basis"] = (df["market_value"] - df["total_gl"]).round(2)

    # reorder to canonical schema first
    canonical = ["asset_name", "asset_id", "quantity", "cost_basis", "market_value"]
    extras    = [c for c in df.columns if c not in canonical]
    return df[canonical + extras]


def _parse_format_b(df: pd.DataFrame) -> pd.DataFrame:
    """Legacy IBI template export — cost_basis column exists directly."""
    missing = _FORMAT_B_REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f"עמודות חסרות בפורמט B: {missing}")

    df = df[list(_FORMAT_B_REQUIRED)].rename(columns=_FORMAT_B_MAP).copy()

    df = df.dropna(subset=["asset_name", "quantity", "market_value"])
    df = df[df["asset_name"].astype(str).str.strip() != ""]

    for col in ("quantity", "cost_basis", "market_value"):
        df[col] = _to_numeric(df[col])

    return df
