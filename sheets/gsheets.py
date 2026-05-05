"""
Google Sheets helpers using gspread + service account from st.secrets.
"""

from __future__ import annotations

import pandas as pd
import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


@st.cache_resource(show_spinner=False)
def get_client() -> gspread.Client:
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=SCOPES,
    )
    return gspread.authorize(creds)


def read_sheet(worksheet_name: str = "holdings") -> pd.DataFrame:
    client = get_client()
    spreadsheet_id = st.secrets["sheets"]["spreadsheet_id"]
    sh = client.open_by_key(spreadsheet_id)
    ws = sh.worksheet(worksheet_name)
    records = ws.get_all_records()
    return pd.DataFrame(records)


def upsert_holdings(df: pd.DataFrame, worksheet_name: str = "holdings") -> None:
    """
    Overwrite the target worksheet with the full holdings DataFrame.
    The sheet is cleared first, then rewritten from row 1.
    """
    client = get_client()
    spreadsheet_id = st.secrets["sheets"]["spreadsheet_id"]
    sh = client.open_by_key(spreadsheet_id)

    try:
        ws = sh.worksheet(worksheet_name)
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=worksheet_name, rows=1000, cols=20)

    ws.clear()
    ws.update(
        [df.columns.tolist()] + df.fillna("").astype(str).values.tolist()
    )
