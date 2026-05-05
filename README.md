# WealthSync

A personal investment aggregator for Israeli accounts — consolidates holdings from Psagot IBI, Bank Leumi, Hapoalim, and Harel into a single Streamlit dashboard backed by Google Sheets.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Streamlit UI                         │
│   Upload Excel │ Dashboard │ Allocation │ Projections       │
└──────────────────────────┬──────────────────────────────────┘
                           │
              ┌────────────▼─────────────┐
              │      app.py (Python)     │
              │  Parser │ Sync │ Charts  │
              └──┬───────────────────┬───┘
                 │                   │
    ┌────────────▼──────┐  ┌─────────▼──────────┐
    │   Google Sheets   │  │  yfinance / FX API  │
    │  (gspread + pandas│  │  (live prices/rates) │
    └───────────────────┘  └─────────────────────┘
```

## Supported Data Sources

| Source      | Format        | Method         |
|-------------|---------------|----------------|
| Psagot IBI  | Excel (.xlsx) | File upload    |
| Bank Leumi  | Excel (.xlsx) | File upload    |
| Hapoalim    | Excel (.xlsx) | File upload    |
| Harel       | —             | Manual entry   |

## Quick Start

### 1. Clone & install

```bash
git clone <your-repo>
cd wealthsync
pip install -r requirements.txt
```

### 2. Configure Google Sheets credentials

Create `.streamlit/secrets.toml`:

```toml
[gcp_service_account]
type = "service_account"
project_id = "YOUR_PROJECT_ID"
private_key_id = "..."
private_key = "-----BEGIN RSA PRIVATE KEY-----\n..."
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."

[sheets]
spreadsheet_id = "YOUR_GOOGLE_SHEET_ID"
```

### 3. Run locally

```bash
streamlit run app.py
```

### 4. Deploy to Streamlit Cloud

Push to GitHub, connect your repo at [share.streamlit.io](https://share.streamlit.io), and paste your secrets in the Streamlit Cloud Secrets editor.

## Project Structure

```
wealthsync/
├── app.py                  # Main Streamlit application
├── parsers/
│   ├── __init__.py
│   ├── ibi_parser.py       # IBI / Psagot Excel parser
│   ├── leumi_parser.py     # Bank Leumi parser
│   └── hapoalim_parser.py  # Hapoalim parser
├── sheets/
│   ├── __init__.py
│   └── gsheets.py          # Google Sheets read/write helpers
├── utils/
│   ├── __init__.py
│   ├── fx.py               # Currency conversion (USD → ILS)
│   └── market.py           # yfinance price fetching
├── ibi_template.xlsx       # Test template mimicking IBI export
├── requirements.txt
├── .gitignore
├── README.md
└── TODO.md
```

## Security

- Service account credentials are stored **only** in `st.secrets` / `.streamlit/secrets.toml`, which is excluded from version control.
- `.gitignore` excludes all `.json`, `.env`, and `secrets.toml` files.
- No credentials are ever hard-coded in source files.
