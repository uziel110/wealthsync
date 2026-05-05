"""
Run this script ONCE after you fill in .streamlit/secrets.toml.
It will:
  1. Verify the Google Sheets connection.
  2. Create the 'holdings' and 'manual_entries' worksheets if they don't exist.
  3. Write the correct column headers to each sheet.
  4. Print the Sheet URL so you can bookmark it.

Usage:
    python setup_sheets.py
"""

import sys
import tomllib
from pathlib import Path

# ── Load secrets from .streamlit/secrets.toml ────────────────────────────────
secrets_path = Path(".streamlit/secrets.toml")
if not secrets_path.exists():
    sys.exit("ERROR: .streamlit/secrets.toml not found. Copy the .template file and fill in your credentials.")

with open(secrets_path, "rb") as f:
    secrets = tomllib.load(f)

sa_info = secrets.get("gcp_service_account", {})
sheet_id = secrets.get("sheets", {}).get("spreadsheet_id", "")

if "YOUR_PROJECT_ID" in sa_info.get("project_id", "YOUR_PROJECT_ID"):
    sys.exit(
        "ERROR: secrets.toml still contains placeholder values.\n"
        "Please fill in your real Google Cloud service account credentials."
    )

if not sheet_id or sheet_id == "YOUR_GOOGLE_SHEET_ID":
    sys.exit(
        "ERROR: [sheets] spreadsheet_id is not set in secrets.toml.\n"
        "Create a Google Sheet, copy its ID from the URL, and paste it in secrets.toml."
    )

# ── Connect ───────────────────────────────────────────────────────────────────
print("Connecting to Google Sheets…")
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

creds = Credentials.from_service_account_info(sa_info, scopes=SCOPES)
gc = gspread.authorize(creds)
print("  ✓ Authenticated successfully")

sh = gc.open_by_key(sheet_id)
print(f"  ✓ Opened spreadsheet: '{sh.title}'")
print(f"  ✓ URL: https://docs.google.com/spreadsheets/d/{sheet_id}")

# ── Create / verify worksheets ────────────────────────────────────────────────
SHEETS_CONFIG = {
    "holdings": [
        "account", "asset_name", "asset_id",
        "quantity", "cost_basis", "market_value", "source", "updated_at",
    ],
    "manual_entries": [
        "account", "asset_name", "quantity",
        "cost_basis", "market_value", "notes", "updated_at",
    ],
}

existing = {ws.title for ws in sh.worksheets()}

for sheet_name, headers in SHEETS_CONFIG.items():
    if sheet_name in existing:
        ws = sh.worksheet(sheet_name)
        print(f"  ✓ Worksheet '{sheet_name}' already exists")
    else:
        ws = sh.add_worksheet(title=sheet_name, rows=1000, cols=len(headers))
        print(f"  + Created worksheet '{sheet_name}'")

    # Write headers only if row 1 is blank
    first_row = ws.row_values(1)
    if not any(first_row):
        ws.update("A1", [headers])
        print(f"    → Headers written: {headers}")
    else:
        print(f"    → Headers already present, skipped")

print("\nSetup complete. You can now run:  streamlit run app.py")
