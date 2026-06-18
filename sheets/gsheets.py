"""
Google Sheets helpers using gspread + service account from st.secrets.
"""

from __future__ import annotations

from datetime import datetime
import pandas as pd
import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

_SNAPSHOT_COLS = [
    "snapshot_date", "account", "asset_name", "asset_id",
    "asset_type", "market_value", "cost_basis", "gain_loss", "gain_pct",
]

_SYMBOL_OVERRIDE_COLS = ["name", "symbol", "asset_id", "added_at"]


@st.cache_resource(show_spinner=False)
def get_client() -> gspread.Client:
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=SCOPES,
    )
    return gspread.authorize(creds)


def _open_sheet(worksheet_name: str, rows: int = 1000, cols: int = 26):
    client = get_client()
    sh = client.open_by_key(st.secrets["sheets"]["spreadsheet_id"])
    try:
        return sh.worksheet(worksheet_name)
    except gspread.exceptions.WorksheetNotFound:
        return sh.add_worksheet(title=worksheet_name, rows=rows, cols=cols)


def read_sheet(worksheet_name: str = "holdings") -> pd.DataFrame:
    ws = _open_sheet(worksheet_name)
    records = ws.get_all_records()
    return pd.DataFrame(records)


def upsert_holdings(df: pd.DataFrame, worksheet_name: str = "holdings") -> None:
    """Overwrite the holdings worksheet with the full DataFrame."""
    ws = _open_sheet(worksheet_name)
    ws.clear()
    ws.update(
        [df.columns.tolist()] + df.fillna("").astype(str).values.tolist()
    )


def append_snapshot(df: pd.DataFrame, worksheet_name: str = "snapshots") -> None:
    """
    Append one row per security per day to the snapshots sheet.
    Skips accounts that already have a snapshot for today to avoid duplicates.
    """
    if df.empty:
        return

    today = datetime.now().strftime("%Y-%m-%d")
    ws = _open_sheet(worksheet_name, rows=10000, cols=len(_SNAPSHOT_COLS))

    # read existing data; check whether first row is our header
    existing_vals = ws.get_all_values()
    # filter out completely empty rows (new sheets may have thousands)
    existing_vals = [r for r in existing_vals if any(c.strip() for c in r)]

    if not existing_vals or existing_vals[0] != _SNAPSHOT_COLS:
        # write header first, then existing data (if any non-header rows present)
        data_rows = existing_vals if (existing_vals and existing_vals[0] != _SNAPSHOT_COLS) else []
        ws.clear()
        ws.update([_SNAPSHOT_COLS] + data_rows)
        existing_vals = [_SNAPSHOT_COLS] + data_rows

    header = existing_vals[0]
    existing_df = (
        pd.DataFrame(existing_vals[1:], columns=header)
        if len(existing_vals) > 1
        else pd.DataFrame(columns=header)
    )

    # find accounts that already have a snapshot today
    already_today: set = set()
    if not existing_df.empty and "snapshot_date" in existing_df.columns:
        already_today = set(
            existing_df.loc[existing_df["snapshot_date"] == today, "account"].unique()
        )

    # build new snapshot rows — only for accounts not yet captured today
    snap = df.copy()
    snap["snapshot_date"] = today
    snap = snap[[c for c in _SNAPSHOT_COLS if c in snap.columns]]
    for c in _SNAPSHOT_COLS:
        if c not in snap.columns:
            snap[c] = ""
    snap = snap[_SNAPSHOT_COLS]

    new_rows = snap[~snap["account"].isin(already_today)]
    if new_rows.empty:
        return

    ws.append_rows(new_rows.fillna("").astype(str).values.tolist())


def read_symbol_overrides(worksheet_name: str = "symbol_overrides") -> pd.DataFrame:
    """User-added name -> yfinance-ticker mappings, created from the app UI."""
    try:
        ws = _open_sheet(worksheet_name)
        records = ws.get_all_records()
        return pd.DataFrame(records) if records else pd.DataFrame(columns=_SYMBOL_OVERRIDE_COLS)
    except Exception:
        return pd.DataFrame(columns=_SYMBOL_OVERRIDE_COLS)


def save_symbol_override(name: str, symbol: str, asset_id: str = "",
                          worksheet_name: str = "symbol_overrides") -> None:
    """Upsert one row into symbol_overrides by name or asset_id (re-saving either replaces its mapping)."""
    ws = _open_sheet(worksheet_name, rows=1000, cols=len(_SYMBOL_OVERRIDE_COLS))
    existing_vals = ws.get_all_values()
    existing_vals = [r for r in existing_vals if any(c.strip() for c in r)]

    if not existing_vals or existing_vals[0] != _SYMBOL_OVERRIDE_COLS:
        data_rows = existing_vals if (existing_vals and existing_vals[0] != _SYMBOL_OVERRIDE_COLS) else []
        existing_vals = [_SYMBOL_OVERRIDE_COLS] + data_rows

    rows = [r for r in existing_vals[1:]
            if r and r[0] != name and not (asset_id and len(r) > 2 and r[2] == asset_id)]
    rows.append([name, symbol, asset_id, datetime.now().strftime("%Y-%m-%d %H:%M")])

    ws.clear()
    ws.update([_SYMBOL_OVERRIDE_COLS] + rows)


def read_snapshots(worksheet_name: str = "snapshots") -> pd.DataFrame:
    """Load full portfolio history from the snapshots sheet."""
    try:
        ws = _open_sheet(worksheet_name)
        records = ws.get_all_records()
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame(records)
        for col in ("market_value", "cost_basis", "gain_loss", "gain_pct"):
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace(",", "", regex=False), errors="coerce"
                )
        return df
    except Exception:
        return pd.DataFrame()
