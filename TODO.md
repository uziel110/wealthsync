# WealthSync — Development Roadmap

## Phase 1: Environment Setup & Google Sheets Auth
- [ ] Create Google Cloud project and enable Sheets + Drive APIs
- [ ] Generate a service account and download the JSON key
- [ ] Share the target Google Sheet with the service account email
- [ ] Configure `.streamlit/secrets.toml` with credentials
- [ ] Verify `gspread` connection: read/write a test cell
- [ ] Add `.gitignore` entries for secrets and credentials
- [ ] Set up a virtual environment (`venv`) and install `requirements.txt`

## Phase 2: Excel Parsers for IBI & Bank Formats
- [x] Scaffold `parsers/ibi_parser.py` with Hebrew header mapping
- [ ] Handle Hebrew encoding edge cases (UTF-8 / Windows-1255)
- [ ] Add RTL-safe column normalisation (strip BOM, whitespace)
- [ ] Scaffold `parsers/leumi_parser.py`
- [ ] Scaffold `parsers/hapoalim_parser.py`
- [ ] Write unit tests for each parser against sample files
- [ ] Implement manual-entry form for Harel pension data
- [ ] Push parsed DataFrames to Google Sheets (`sheets/gsheets.py`)

## Phase 3: Dashboard UI (Value, Allocation, Performance)
- [x] Main navigation sidebar (Upload / Dashboard / Settings)
- [ ] Portfolio total value card (ILS, auto USD→ILS conversion)
- [ ] Asset allocation pie chart (Plotly / Altair)
- [ ] Holdings table with live prices via `yfinance`
- [ ] Historical performance line chart (cost basis vs. current value)
- [ ] Mobile-responsive layout (single-column on small screens)
- [ ] RTL text rendering for Hebrew labels

## Phase 4: Investment Insights (Rebalancing, Fee Tracking)
- [ ] Target allocation input (user-defined % per asset class)
- [ ] Rebalancing engine: compute buy/sell amounts to reach target
- [ ] Fee tracker: record management fees per account
- [ ] "Future Value" projection calculator (FV formula, configurable CAGR)
- [ ] Gain/Loss summary per position
- [ ] Export report to Excel / CSV

## Phase 5: Deployment & Security
- [ ] Final `.gitignore` audit — confirm no secrets committed
- [ ] Push repo to GitHub (private)
- [ ] Connect to Streamlit Cloud, add secrets via the UI
- [ ] Smoke-test live deployment end-to-end
- [ ] Set up Streamlit Cloud scheduled re-runs (if needed)
- [ ] Document deployment steps in README.md
