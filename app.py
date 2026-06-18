"""
WealthSync — מאגד השקעות אישי
עיצוב: Claude Design System · Hebrew-first · RTL · Heebo font
"""

from __future__ import annotations
import io
from datetime import datetime
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from parsers.ibi_parser import parse_ibi
from parsers.hapoalim_parser import parse_hapoalim
from parsers.leumi_parser import parse_leumi
from parsers.gamel_pdf_parser import parse_gamel_pdf

# ═════════════════════════════════════════════════════════════════════════════
# קונפיגורציה
# ═════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="WealthSync",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="auto",
)

# ═════════════════════════════════════════════════════════════════════════════
# Design System — CSS
# ═════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ─── Heebo — Hebrew + Latin ─────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;600;700;800;900&display=swap');

/* ─── Design Tokens ──────────────────────────────────── */
:root {
  --bg:         #F0F4F8;
  --surface:    #FFFFFF;
  --sidebar-bg: #0F172A;
  --primary:    #2563EB;
  --primary-lt: #EFF6FF;
  --gain:       #059669;
  --gain-lt:    #ECFDF5;
  --loss:       #DC2626;
  --loss-lt:    #FEF2F2;
  --warn:       #D97706;
  --warn-lt:    #FFFBEB;
  --text:       #1E293B;
  --muted:      #64748B;
  --border:     #E2E8F0;
  --radius:     12px;
  --shadow:     0 1px 3px rgba(0,0,0,.08), 0 4px 12px rgba(0,0,0,.05);
  --font:       "Heebo", "Arial Hebrew", "Helvetica Neue", Arial, sans-serif;
}

/* ─── RTL base ───────────────────────────────────────── */
html, body, [class*="css"], .stApp {
  direction: rtl !important;
  font-family: var(--font) !important;
  background: var(--bg) !important;
  color: var(--text) !important;
}
.block-container {
  padding: 2rem 2.5rem 3rem !important;
  max-width: 1400px !important;
}

/* ─── Sidebar ────────────────────────────────────────── */
[data-testid="stSidebar"] {
  background: var(--sidebar-bg) !important;
  direction: rtl !important;
  overflow: hidden !important;
}
[data-testid="stSidebar"] * { color: #CBD5E1 !important; direction: rtl !important; }
[data-testid="stSidebar"] .stRadio label {
  font-size: .95rem !important; padding: .5rem .75rem !important;
  border-radius: 8px; cursor: pointer; transition: background .15s;
}
[data-testid="stSidebar"] .stRadio label:hover { background: rgba(255,255,255,.08) !important; }
[data-testid="stSidebarNav"] { display: none; }

/* ─── Headings ───────────────────────────────────────── */
h1,h2,h3,h4 { direction: rtl !important; text-align: right !important;
  color: var(--text) !important; font-weight: 700 !important; font-family: var(--font) !important; }
h1 { font-size: 1.8rem !important; }
h2 { font-size: 1.35rem !important; margin-top: 1.5rem !important; }

/* ─── Metric ─────────────────────────────────────────── */
[data-testid="stMetric"] {
  background: var(--surface); border-radius: var(--radius);
  box-shadow: var(--shadow); padding: 1.1rem 1.25rem !important;
  border: 1px solid var(--border);
  min-height: 100px;
  display: flex !important; flex-direction: column !important; justify-content: center !important;
}
[data-testid="stMetricLabel"] {
  direction: rtl !important; text-align: right !important;
  color: var(--muted) !important; font-size: .82rem !important;
  font-weight: 600 !important; text-transform: uppercase; letter-spacing: .04em;
}
[data-testid="stMetricValue"] {
  direction: rtl !important; text-align: right !important;
  font-size: 1.6rem !important; font-weight: 800 !important; color: var(--text) !important;
}
[data-testid="stMetricDelta"] { direction: rtl !important; text-align: right !important; font-weight: 600 !important; }

/* ─── Buttons ────────────────────────────────────────── */
.stButton > button {
  direction: rtl !important; border-radius: 8px !important;
  font-family: var(--font) !important; font-weight: 600 !important;
  font-size: .9rem !important; transition: all .15s !important;
}
.stButton > button[kind="primary"] { background: var(--primary) !important; border: none !important; }
.stButton > button[kind="primary"]:hover {
  background: #1D4ED8 !important; box-shadow: 0 4px 12px rgba(37,99,235,.35) !important;
}
/* ── filter action buttons (הכל / נקה) — targeted by widget key ─────── */
.st-key-acc_all  button, .st-key-acc_none  button,
.st-key-type_all button, .st-key-type_none button {
  min-height: 30px !important; height: 30px !important;
  padding: 0 .8rem !important; font-size: .72rem !important;
  border-radius: 999px !important; font-weight: 600 !important;
  background: var(--surface) !important;
  border: 1.5px solid var(--border) !important;
  color: var(--muted) !important; box-shadow: none !important;
  line-height: 1 !important; width: auto !important; white-space: nowrap !important;
}
/* the four filter-button columns shrink to their content so the pills get the
   space and the buttons never wrap (desktop: avoids the narrow-column squeeze) */
[data-testid="stColumn"]:has(.st-key-acc_all),
[data-testid="stColumn"]:has(.st-key-acc_none),
[data-testid="stColumn"]:has(.st-key-type_all),
[data-testid="stColumn"]:has(.st-key-type_none) {
  flex: 0 0 auto !important;
}
.st-key-acc_all  button:hover, .st-key-acc_none  button:hover,
.st-key-type_all button:hover, .st-key-type_none button:hover {
  border-color: var(--primary) !important; color: var(--primary) !important;
  background: var(--primary-lt) !important;
}

/* ─── Global RTL text ────────────────────────────────── */
p, li, span, label, caption, small,
[data-testid="stText"], [data-testid="stCaptionContainer"],
[data-testid="stMarkdownContainer"] p,
[data-testid="stExpander"] summary,
[data-testid="stCheckbox"] label,
[data-testid="stRadio"] label,
[data-testid="stWidgetLabel"],
.stSuccess p, .stError p, .stWarning p, .stInfo p {
  direction: rtl !important; text-align: right !important;
}

/* ─── Inputs ─────────────────────────────────────────── */
.stTextInput label, .stNumberInput label, .stSelectbox label,
.stFileUploader label, .stSlider label, .stRadio > label,
.stForm label, .stMultiSelect label {
  direction: rtl !important; text-align: right !important;
}
.stTextInput input, .stNumberInput input {
  direction: rtl !important; text-align: right !important;
  border-radius: 8px !important; border: 1.5px solid var(--border) !important;
  background: var(--surface) !important; font-family: var(--font) !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
  border-color: var(--primary) !important; box-shadow: 0 0 0 3px rgba(37,99,235,.15) !important;
}
.stSelectbox > div > div, .stMultiSelect > div > div {
  direction: rtl !important; border-radius: 8px !important;
  border: 1.5px solid var(--border) !important; background: var(--surface) !important;
}

/* ─── File uploader ──────────────────────────────────── */
[data-testid="stFileUploader"] { direction: rtl !important; }
[data-testid="stFileUploadDropzone"] {
  border-radius: var(--radius) !important; border: 2px dashed var(--border) !important;
  background: var(--primary-lt) !important; direction: rtl !important;
}

/* ─── DataFrames ─────────────────────────────────────── */
.stDataFrame { border-radius: var(--radius) !important; overflow: hidden !important;
  border: 1px solid var(--border) !important; box-shadow: var(--shadow) !important; }
.stDataFrame td, .stDataFrame th {
  direction: rtl !important; text-align: right !important; font-family: var(--font) !important;
}
.stDataFrame th {
  background: #F8FAFC !important; font-weight: 700 !important;
  color: var(--muted) !important; font-size: .78rem !important;
  text-transform: uppercase; letter-spacing: .05em;
}

/* ─── Alerts ─────────────────────────────────────────── */
[data-testid="stAlert"] {
  direction: rtl !important; text-align: right !important;
  border-radius: var(--radius) !important; font-family: var(--font) !important;
}

/* ─── Divider ────────────────────────────────────────── */
hr { border-color: var(--border) !important; margin: 1.5rem 0 !important; }

/* ─── Spinner ────────────────────────────────────────── */
[data-testid="stSpinner"] { direction: rtl !important; }

/* ─── Slider — forced LTR internally ────────────────── */
.stSlider, .stSlider *, .stSlider [data-testid="stTickBar"],
.stSlider [data-baseweb="slider"], .stSlider input[type="range"] {
  direction: ltr !important;
}
.stSlider label, .stSlider [data-testid="stWidgetLabel"] {
  direction: rtl !important; text-align: right !important; display: block !important;
}

/* ─── Form ───────────────────────────────────────────── */
[data-testid="stForm"] {
  background: var(--surface) !important; border-radius: var(--radius) !important;
  border: 1px solid var(--border) !important; padding: 1.5rem !important;
  box-shadow: var(--shadow) !important;
}

/* ─── Plotly ─────────────────────────────────────────── */
.js-plotly-plot { direction: ltr !important; }

/* ─── Mobile ─────────────────────────────────────────── */
@media (max-width: 768px) {
  .block-container { padding: 1rem .75rem !important; }
  [data-testid="stMetricValue"] { font-size: 1.25rem !important; }
  [data-testid="stMetric"] { padding: .85rem 1rem !important; min-height: 80px; }
  [data-testid="stAppDeployButton"], [data-testid="stMainMenu"] { display: none !important; }
  .ws-page-header { padding: 1rem 1.1rem !important; gap: .5rem !important; flex-wrap: wrap !important; }
  .ws-page-header-icon { font-size: 1.3rem !important; }
  .ws-page-header-title { font-size: 1.1rem !important; }
  .ws-card { padding: 1rem !important; }
  h1 { font-size: 1.4rem !important; }
  h2 { font-size: 1.15rem !important; }
  .stButton > button { min-height: 42px !important; }
  [data-testid="stSidebar"] { width: 85vw !important; min-width: 0 !important; }
  /* filter action buttons (הכל/נקה) sit inline instead of each filling its own
     stacked row — scoped to the four filter buttons by widget key. Falls back
     to stacking on browsers without :has(). */
  [data-testid="stColumn"]:has(.st-key-acc_all),
  [data-testid="stColumn"]:has(.st-key-acc_none),
  [data-testid="stColumn"]:has(.st-key-type_all),
  [data-testid="stColumn"]:has(.st-key-type_none) {
    min-width: auto !important; flex: 0 0 auto !important; width: auto !important;
  }
}

/* ═══════════════════════════════════════════════════════
   WealthSync Components
   ═══════════════════════════════════════════════════════ */

/* ws-card */
.ws-card {
  background: var(--surface); border-radius: var(--radius);
  box-shadow: var(--shadow); border: 1px solid var(--border);
  padding: 1.5rem; margin-bottom: 1rem;
}
.ws-card-title {
  font-size: .82rem; font-weight: 700; color: var(--muted);
  text-transform: uppercase; letter-spacing: .06em; margin-bottom: .5rem;
}

/* ws-page-header */
.ws-page-header {
  background: var(--surface); border-radius: var(--radius);
  border: 1px solid var(--border); box-shadow: var(--shadow);
  padding: 1.25rem 1.5rem; margin-bottom: 1.75rem;
  display: flex; align-items: center; gap: .75rem; direction: rtl;
}
.ws-page-header-icon  { font-size: 1.6rem; }
.ws-page-header-title { font-size: 1.35rem; font-weight: 800; color: var(--text); margin: 0; }
.ws-page-header-sub   { font-size: .82rem; color: var(--muted); margin: 0; }

/* ws-badge */
.ws-badge {
  display: inline-block; padding: .2rem .65rem;
  border-radius: 999px; font-size: .75rem; font-weight: 700;
}
.ws-badge-gain { background: var(--gain-lt); color: var(--gain); }
.ws-badge-loss { background: var(--loss-lt); color: var(--loss); }
.ws-badge-info { background: var(--primary-lt); color: var(--primary); }
.ws-badge-warn { background: var(--warn-lt); color: var(--warn); }

/* ws-section-header */
.ws-section-header {
  font-size: 1.05rem; font-weight: 700; color: var(--muted);
  text-transform: uppercase; letter-spacing: .06em;
  margin: 1.5rem 0 .75rem;
  border-right: 3px solid var(--primary); padding-right: .6rem;
  direction: rtl;
}

/* ws-filter-bar */
.ws-filter-bar {
  background: var(--surface); border-radius: var(--radius);
  border: 1px solid var(--border); box-shadow: var(--shadow);
  padding: .9rem 1.25rem; margin-bottom: 1.25rem;
  display: flex; align-items: center; gap: .5rem;
  direction: rtl;
}
.ws-filter-label {
  font-size: .78rem; font-weight: 700; color: var(--muted);
  text-transform: uppercase; letter-spacing: .05em; white-space: nowrap;
}

/* ws-type-pill */
.ws-type-pill {
  display: inline-flex; align-items: center; gap: .3rem;
  padding: .18rem .55rem; border-radius: 999px;
  font-size: .75rem; font-weight: 700; font-family: var(--font);
}
.ws-type-etf    { background: #EFF6FF; color: #2563EB; }
.ws-type-stock  { background: #ECFDF5; color: #059669; }
.ws-type-fund   { background: #FFFBEB; color: #D97706; }
.ws-type-pension{ background: #F5F3FF; color: #7C3AED; }
</style>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# Design helpers
# ═════════════════════════════════════════════════════════════════════════════

def page_header(icon: str, title: str, subtitle: str = "") -> None:
    sub = f"<p class='ws-page-header-sub'>{subtitle}</p>" if subtitle else ""
    st.markdown(f"""
    <div class="ws-page-header">
      <span class="ws-page-header-icon">{icon}</span>
      <div><p class="ws-page-header-title">{title}</p>{sub}</div>
    </div>""", unsafe_allow_html=True)


def section_header(title: str) -> None:
    st.markdown(f'<div class="ws-section-header">{title}</div>', unsafe_allow_html=True)


def badge(text: str, kind: str = "info") -> str:
    return f'<span class="ws-badge ws-badge-{kind}">{text}</span>'


PLOTLY_LAYOUT = dict(
    font_family="Heebo, Arial Hebrew, Arial",
    font_color="#1E293B",
    paper_bgcolor="white",
    plot_bgcolor="white",
    margin=dict(t=24, b=24, l=80, r=24),
    hoverlabel=dict(bgcolor="white", font_family="Heebo, Arial Hebrew, Arial", font_size=13),
)

# Chart color palette — brand colors only (per design system)
PALETTE = ["#2563EB", "#059669", "#F59E0B", "#8B5CF6", "#EC4899", "#06B6D4", "#84CC16", "#EF4444"]


# ═════════════════════════════════════════════════════════════════════════════
# Asset-type classification
# ═════════════════════════════════════════════════════════════════════════════

_ETF_KEYWORDS   = {"etf", "ucits", "invesco", "ishares", "spdr", "vanguard", "xtrackers", "lyxor"}
_FUND_KEYWORDS  = {"מחקה", "mtf", "סל", "קרן", "מדד"}
_PENSION_KEYWORDS = {"הראל", "מגדל", "כלל", "פניקס", "מנורה", "אלטשולר", "פסגות", "אנליסט"}

TYPE_LABELS = {
    "etf":     "קרן סל / ETF",
    "fund":    "קרן מחקה / נאמנות",
    "pension": "פנסיה / גמל",
    "stock":   "מניה",
    "gamel":   "גמל להשקעה",
}

TYPE_COLORS = {
    "etf":     "#2563EB",
    "fund":    "#D97706",
    "pension": "#7C3AED",
    "stock":   "#059669",
    "gamel":   "#0891B2",
}


def classify_asset(row: pd.Series) -> str:
    src = str(row.get("source", "")).strip()
    if src == "גמל PDF":
        return "gamel"
    if src == "ידני":
        return "pension"
    name = str(row.get("asset_name", "")).lower()
    aid  = str(row.get("asset_id",   "")).strip()
    if any(k in name for k in _ETF_KEYWORDS):
        return "etf"
    if any(k in name for k in _FUND_KEYWORDS):
        return "fund"
    # pure-alpha ticker (e.g. AAPL, QTUM) → stock
    if aid.isalpha() and len(aid) <= 6:
        return "stock"
    # Israeli bond/stock numerics without fund keywords → stock
    return "stock"


def _to_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False), errors="coerce"
    )


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure all derived columns exist and are fully populated."""
    df = df.copy()

    # strip RTL/LTR unicode control chars from text columns
    for col in ("asset_name", "asset_id"):
        if col in df.columns:
            df[col] = (
                df[col].astype(str)
                .str.replace(r"[‎‏‪-‮⁦-⁩]", "", regex=True)
                .str.strip()
            )

    # numeric conversion — Sheets round-trips everything as strings
    for col in ("quantity", "cost_basis", "market_value", "gain_loss", "gain_pct"):
        if col in df.columns:
            df[col] = _to_num(df[col])

    # asset_type — classify rows that are missing or blank
    if "asset_type" not in df.columns:
        df["asset_type"] = df.apply(classify_asset, axis=1)
    else:
        blank = df["asset_type"].isna() | (df["asset_type"].astype(str).str.strip() == "")
        if blank.any():
            df.loc[blank, "asset_type"] = df[blank].apply(classify_asset, axis=1)

    # gain_loss — fill NaN rows (don't overwrite valid values)
    if "gain_loss" not in df.columns:
        df["gain_loss"] = df["market_value"] - df["cost_basis"]
    else:
        missing = df["gain_loss"].isna()
        if missing.any():
            df.loc[missing, "gain_loss"] = (
                df.loc[missing, "market_value"] - df.loc[missing, "cost_basis"]
            )

    # gain_pct — fill NaN rows
    if "gain_pct" not in df.columns:
        df["gain_pct"] = df["gain_loss"] / df["cost_basis"].replace(0, float("nan")) * 100
    else:
        missing = df["gain_pct"].isna()
        if missing.any():
            df.loc[missing, "gain_pct"] = (
                df.loc[missing, "gain_loss"]
                / df.loc[missing, "cost_basis"].replace(0, float("nan"))
                * 100
            )

    return df


# ═════════════════════════════════════════════════════════════════════════════
# Authentication — password gate
# ═════════════════════════════════════════════════════════════════════════════

def _check_auth() -> bool:
    """Return True if the user is authenticated."""
    return st.session_state.get("authenticated", False)


def _login_screen() -> None:
    st.markdown("""
    <style>
    /* מסך כניסה — ממורכז, ללא sidebar */
    [data-testid="stSidebar"] { display: none !important; }
    .block-container { max-width: 420px !important; padding-top: 8rem !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center; margin-bottom:2rem;">
      <div style="font-size:3rem;">💰</div>
      <div style="font-size:1.8rem; font-weight:900; color:#1E293B; font-family:Heebo,sans-serif;">
        WealthSync
      </div>
      <div style="font-size:.85rem; color:#64748B; margin-top:.3rem;">מאגד השקעות אישי</div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        password = st.text_input("סיסמה", type="password", placeholder="הזן סיסמה…")
        submitted = st.form_submit_button("כניסה", type="primary", use_container_width=True)

    if submitted:
        correct = st.secrets.get("auth", {}).get("password", "")
        if password == correct:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("סיסמה שגויה.")


if not _check_auth():
    _login_screen()
    st.stop()

# ═════════════════════════════════════════════════════════════════════════════
# Session state + auto-load from Sheets
# ═════════════════════════════════════════════════════════════════════════════
if "holdings" not in st.session_state:
    st.session_state.holdings: pd.DataFrame = pd.DataFrame()

if "sheets_loaded" not in st.session_state:
    st.session_state.sheets_loaded = False

if not st.session_state.sheets_loaded:
    try:
        from sheets.gsheets import read_sheet
        _raw = read_sheet("holdings")
        if not _raw.empty:
            for _c in ("quantity", "cost_basis", "market_value", "gain_loss", "gain_pct",
                       "last_price", "change_pct", "avg_cost_price", "total_gl_ils"):
                if _c in _raw.columns:
                    _raw[_c] = pd.to_numeric(
                        _raw[_c].astype(str).str.replace(",", "", regex=False), errors="coerce"
                    )
            st.session_state.holdings = _raw
    except Exception:
        pass
    finally:
        st.session_state.sheets_loaded = True


def _save_holdings(df: pd.DataFrame) -> None:
    if not df.empty:
        df = enrich(df)
        df["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    st.session_state.holdings = df
    try:
        from sheets.gsheets import upsert_holdings, append_snapshot
        upsert_holdings(df)
        if not df.empty:
            append_snapshot(df)
    except Exception:
        pass


COL_LABELS = {
    "account":      "חשבון",
    "asset_name":   "שם נייר",
    "asset_id":     "מספר נייר",
    "asset_type":   "סוג",
    "quantity":     "כמות",
    "cost_basis":   "עלות (₪)",
    "market_value": "שווי נוכחי (₪)",
    "gain_loss":    "רווח/הפסד (₪)",
    "gain_pct":     "תשואה %",
    "updated_at":   "עדכון אחרון",
    "source":       "מקור",
}

TYPE_HE = {
    "etf":     "קרן סל / ETF",
    "fund":    "קרן מחקה",
    "pension": "פנסיה",
    "stock":   "מניה",
    "gamel":   "גמל להשקעה",
}


def _display(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    df = df[cols].copy()
    if "asset_type" in df.columns:
        df["asset_type"] = df["asset_type"].map(TYPE_HE).fillna(df["asset_type"])
    return df.rename(columns=COL_LABELS)


# ═════════════════════════════════════════════════════════════════════════════
# Sidebar
# ═════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="padding:1.25rem 0 .5rem;text-align:right;">
      <div style="font-size:1.6rem;font-weight:900;color:#F8FAFC;letter-spacing:-.5px;font-family:Heebo,sans-serif;">
        💰 WealthSync
      </div>
      <div style="font-size:.78rem;color:#94A3B8;margin-top:.2rem;">מאגד השקעות אישי</div>
    </div>""", unsafe_allow_html=True)

    st.divider()

    page = st.radio(
        "ניווט",
        ["📊 לוח מחוונים", "📈 היסטוריה", "📤 העלאה", "🤖 המלצות AI",
         "🧭 ניתוח השקעות", "⚙️ הגדרות"],
        label_visibility="collapsed",
    )

    st.divider()

    _df_s = st.session_state.holdings
    if not _df_s.empty:
        _total = _df_s["market_value"].sum()
        _cost  = _df_s["cost_basis"].sum()
        _gl    = _total - _cost
        _glp   = (_gl / _cost * 100) if _cost else 0.0
        _clr   = "#059669" if _gl >= 0 else "#EF4444"
        _sign  = "▲" if _gl >= 0 else "▼"
        _df_e  = enrich(_df_s)
        _types = _df_e["asset_type"].map(TYPE_HE).value_counts()

        _last_update = ""
        if "updated_at" in _df_s.columns:
            _last_update = _df_s["updated_at"].dropna().max() or ""

        st.markdown(f"""
        <div style="background:rgba(255,255,255,.07);border-radius:10px;padding:.9rem 1rem;margin:.5rem 0;">
          <div style="font-size:.68rem;color:#94A3B8;text-align:right;margin-bottom:.4rem;
            text-transform:uppercase;letter-spacing:.06em;">סיכום תיק</div>
          <div style="font-size:1.45rem;font-weight:800;color:#F8FAFC;text-align:right;font-family:Heebo,sans-serif;">
            ₪{_total:,.0f}
          </div>
          <div style="font-size:.82rem;color:{_clr};text-align:right;margin-top:.2rem;font-weight:600;">
            {_sign} ₪{abs(_gl):,.0f} &nbsp;({_glp:+.1f}%)
          </div>
          <div style="font-size:.72rem;color:#94A3B8;text-align:right;margin-top:.6rem;line-height:1.6;">
            {len(_df_s)} ניירות · {_df_s['account'].nunique()} חשבונות
            {f'<br>עדכון אחרון: {_last_update}' if _last_update else ''}
          </div>
        </div>
        <div style="margin-top:.5rem;">
          {"".join(
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'padding:.25rem 0;border-bottom:1px solid rgba(255,255,255,.06);">'
            f'<span style="font-size:.72rem;color:#94A3B8;">{t}</span>'
            f'<span style="font-size:.72rem;color:#CBD5E1;font-weight:600;">{n}</span></div>'
            for t, n in _types.items()
          )}
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="font-size:.82rem;color:#475569;text-align:right;padding:.5rem 0;">
          טרם נטענו נתונים
        </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div style="position:fixed;bottom:1rem;font-size:.68rem;color:#334155;text-align:right;">
      גרסה 1.0 · WealthSync
    </div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# Filter bar — shared between dashboard sections
# ═════════════════════════════════════════════════════════════════════════════
def filter_bar(df: pd.DataFrame) -> pd.DataFrame:
    df = enrich(df)

    accounts    = sorted(df["account"].unique().tolist())
    type_opts   = sorted(df["asset_type"].unique().tolist())
    type_labels = {k: TYPE_HE.get(k, k) for k in type_opts}
    type_he_list = list(type_labels.values())

    _LBL = (
        "font-size:.75rem;font-weight:700;color:#64748B;"
        "text-transform:uppercase;letter-spacing:.04em;"
        "padding-top:.45rem;text-align:right"
    )
    with st.container(border=True):
        # ── accounts row: label | pills | הכל | נקה ──────────────────────────
        lc, pc, ac, nc = st.columns([0.65, 5, 0.45, 0.45])
        lc.markdown(f"<div style='{_LBL}'>חשבון</div>", unsafe_allow_html=True)
        with pc:
            sel_accounts = st.pills(
                "חשבונות", accounts, selection_mode="multi",
                default=accounts, key="filter_accounts",
                label_visibility="collapsed",
            ) or []
        with ac:
            if st.button("הכל ✓", key="acc_all"):
                st.session_state["filter_accounts"] = accounts; st.rerun()
        with nc:
            if st.button("נקה ✗", key="acc_none"):
                st.session_state["filter_accounts"] = []; st.rerun()

        # ── asset-type row: label | pills | הכל | נקה ────────────────────────
        lc2, pc2, ac2, nc2 = st.columns([0.65, 5, 0.45, 0.45])
        lc2.markdown(f"<div style='{_LBL}'>סוג נכס</div>", unsafe_allow_html=True)
        with pc2:
            sel_types = st.pills(
                "סוגי נכסים", type_he_list, selection_mode="multi",
                default=type_he_list, key="filter_types",
                label_visibility="collapsed",
            ) or []
        with ac2:
            if st.button("הכל ✓", key="type_all"):
                st.session_state["filter_types"] = type_he_list; st.rerun()
        with nc2:
            if st.button("נקה ✗", key="type_none"):
                st.session_state["filter_types"] = []; st.rerun()

    rev = {v: k for k, v in type_labels.items()}
    sel_type_keys = [rev[l] for l in sel_types if l in rev]

    return df[
        df["account"].isin(sel_accounts) &
        df["asset_type"].isin(sel_type_keys)
    ]


# ═════════════════════════════════════════════════════════════════════════════
# דף: לוח מחוונים
# ═════════════════════════════════════════════════════════════════════════════
def page_dashboard() -> None:
    page_header("📊", "לוח מחוונים", "מבט כולל על תיק ההשקעות")

    raw = st.session_state.holdings
    if raw.empty:
        st.info("טרם נטענו נתונים — עבור ל-**📤 העלאה** כדי להוסיף חשבונות.")
        return

    df = filter_bar(raw)

    if df.empty:
        st.warning("אין נתונים התואמים לסינון הנבחר.")
        return

    # ── KPI strip ────────────────────────────────────────────────────────────
    total   = df["market_value"].sum()
    cost    = df["cost_basis"].sum()
    gl      = total - cost
    glp     = (gl / cost * 100) if cost else 0.0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("שווי תיק נוכחי",   f"₪{total:,.0f}")
    k2.metric("עלות כוללת",        f"₪{cost:,.0f}")
    k3.metric("רווח / הפסד",       f"₪{gl:,.0f}", f"{glp:+.1f}%")
    k4.metric("פוזיציות פתוחות",   len(df))

    st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)

    # ── Row 1: allocation by type + by account ────────────────────────────────
    col_l, col_r = st.columns(2, gap="large")

    with col_l:
        section_header("הקצאה לפי סוג נכס")

        type_totals = (
            df.groupby("asset_type")["market_value"].sum()
            .reset_index().sort_values("market_value", ascending=False)
        )
        type_totals["label"] = type_totals["asset_type"].map(TYPE_HE)
        type_totals["color"] = type_totals["asset_type"].map(
            lambda t: TYPE_COLORS.get(t, "#94A3B8"))

        drill_type = st.session_state.get("alloc_type_drill")

        if drill_type is None:
            # ── main view: asset types ────────────────────────────────────────
            fig_type = go.Figure(go.Pie(
                labels=type_totals["label"],
                values=type_totals["market_value"],
                hole=0.46,
                marker=dict(colors=type_totals["color"].tolist(),
                            line=dict(color="#fff", width=2.5)),
                textinfo="label+percent",
                textposition="inside",
                insidetextorientation="radial",
                hovertemplate="<b>%{label}</b><br>₪%{value:,.0f}"
                              "<br>%{percent}<extra></extra>",
                direction="clockwise",
            ))
            center_txt = f"₪{total/1e6:.1f}M" if total >= 1e6 else f"₪{total:,.0f}"
            fig_type.update_layout(**PLOTLY_LAYOUT, height=360, showlegend=False)
            fig_type.update_layout(
                margin=dict(t=8, b=8, l=8, r=8),
                annotations=[dict(text=center_txt, font_size=14,
                                  font_color="#1E293B", showarrow=False)],
            )
            event = st.plotly_chart(
                fig_type, use_container_width=True,
                on_select="rerun", key="alloc_type_main",
            )
            if event and event.selection and event.selection.points:
                clicked = event.selection.points[0].get("label", "")
                rev_he = {v: k for k, v in TYPE_HE.items()}
                clicked_key = rev_he.get(clicked)
                if clicked_key:
                    st.session_state["alloc_type_drill"] = clicked_key
                    st.rerun()
            st.caption("לחץ על פרוסה לצפייה בניירות הבודדים")

        else:
            # ── drill-down: individual assets within selected type ────────────
            type_label = TYPE_HE.get(drill_type, drill_type)
            base_color = TYPE_COLORS.get(drill_type, "#94A3B8")
            r, g, b = (int(base_color[i:i+2], 16) for i in (1, 3, 5))

            subset = (df[df["asset_type"] == drill_type]
                      .groupby("asset_name")["market_value"].sum()
                      .reset_index().sort_values("market_value", ascending=False))
            n = len(subset)
            drill_colors = [
                f"rgba({r},{g},{b},{0.45 + 0.55*(n-i)/max(n-1,1):.2f})"
                for i in range(n)
            ]

            if st.button("← חזור לסוגי נכסים", key="alloc_type_back"):
                st.session_state["alloc_type_drill"] = None
                st.rerun()

            fig_drill = go.Figure(go.Pie(
                labels=subset["asset_name"],
                values=subset["market_value"],
                hole=0.46,
                marker=dict(colors=drill_colors,
                            line=dict(color="#fff", width=2)),
                textinfo="label+percent",
                textposition="inside",
                insidetextorientation="radial",
                hovertemplate="<b>%{label}</b><br>₪%{value:,.0f}"
                              "<br>%{percent}<extra></extra>",
            ))
            type_total = subset["market_value"].sum()
            center_txt = f"₪{type_total/1e6:.1f}M" if type_total >= 1e6 \
                         else f"₪{type_total:,.0f}"
            fig_drill.update_layout(**PLOTLY_LAYOUT, height=360, showlegend=False,
                                    title=dict(text=type_label, x=0.5, font_size=14))
            fig_drill.update_layout(
                margin=dict(t=32, b=8, l=8, r=8),
                annotations=[dict(text=center_txt, font_size=14,
                                  font_color="#1E293B", showarrow=False)],
            )
            st.plotly_chart(fig_drill, use_container_width=True,
                            key="alloc_type_drill_chart")

    with col_r:
        section_header("הקצאה לפי חשבון")
        by_acc = (
            df.groupby(["account", "asset_type"])["market_value"].sum()
            .reset_index()
        )
        acc_totals = (
            by_acc.groupby("account")["market_value"].sum()
            .reset_index()
            .sort_values("market_value", ascending=False)
        )

        # Treemap without a root node — accounts at top level, asset_types as children
        # branchvalues="total": account value = sum of its asset_type children (correct)
        tm_ids     = acc_totals["account"].tolist() \
                     + (by_acc["account"] + "||" + by_acc["asset_type"]).tolist()
        tm_labels  = acc_totals["account"].tolist() \
                     + by_acc["asset_type"].map(lambda t: TYPE_HE.get(t, t)).tolist()
        tm_parents = [""] * len(acc_totals) \
                     + by_acc["account"].tolist()
        tm_values  = acc_totals["market_value"].tolist() \
                     + by_acc["market_value"].tolist()
        tm_colors  = [PALETTE[i % len(PALETTE)] for i in range(len(acc_totals))] \
                     + [TYPE_COLORS.get(t, "#94A3B8") for t in by_acc["asset_type"]]

        fig_acc = go.Figure(go.Treemap(
            ids=tm_ids,
            labels=tm_labels,
            parents=tm_parents,
            values=tm_values,
            marker=dict(colors=tm_colors, line=dict(color="#fff", width=2)),
            branchvalues="total",
            hovertemplate="<b>%{label}</b><br>₪%{value:,.0f}<br>%{percentParent:.0%} מהחשבון · %{percentRoot:.0%} מהתיק<extra></extra>",
            textfont=dict(size=12),
            textinfo="label+percent root",
            maxdepth=2,
        ))
        fig_acc.update_layout(**PLOTLY_LAYOUT, height=360)
        fig_acc.update_layout(margin=dict(t=8, b=8, l=8, r=8))
        st.plotly_chart(fig_acc, use_container_width=True)

    # ── Row 2: bar by account (values) + breakdown by type within account ─────
    section_header("שווי לפי חשבון וסוג נכס")

    pivot = (
        df.groupby(["account", "asset_type"])["market_value"]
        .sum()
        .reset_index()
    )
    pivot["type_label"] = pivot["asset_type"].map(TYPE_HE)

    fig_stack = go.Figure()
    for atype, color in TYPE_COLORS.items():
        sub = pivot[pivot["asset_type"] == atype]
        if sub.empty:
            continue
        fig_stack.add_trace(go.Bar(
            name=TYPE_HE[atype],
            x=sub["account"],
            y=sub["market_value"],
            marker_color=color,
            hovertemplate=f"<b>%{{x}}</b> — {TYPE_HE[atype]}<br>₪%{{y:,.0f}}<extra></extra>",
            text=[f"₪{v:,.0f}" if v > total * 0.04 else "" for v in sub["market_value"]],
            textposition="inside",
            textfont_size=11,
        ))
    fig_stack.update_layout(
        **PLOTLY_LAYOUT,
        barmode="stack",
        height=300,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickformat="₪,.0f"),
        legend=dict(orientation="h", x=0.5, xanchor="center", y=1.12, font_size=11),
    )
    st.plotly_chart(fig_stack, use_container_width=True)

    # ── Row 3: gain/loss per asset ────────────────────────────────────────────
    gl_hdr_col, gl_toggle_col, gl_vline_col = st.columns([3, 1, 1])
    with gl_hdr_col:
        section_header("רווח / הפסד לפי נייר ערך")
    with gl_toggle_col:
        gl_mode = st.radio(
            "תצוגה", ["₪", "%"],
            horizontal=True,
            key="gl_display_mode",
            label_visibility="collapsed",
        )
    with gl_vline_col:
        show_vline = st.checkbox("קו סה״כ", value=True, key="gl_show_vline")

    df_gl = df.sort_values("gain_pct" if gl_mode == "%" else "gain_loss")
    gl_values = df_gl["gain_pct"].fillna(0) if gl_mode == "%" else df_gl["gain_loss"]
    colors_gl = [TYPE_COLORS.get(t, "#94A3B8") if v >= 0 else "#EF4444"
                 for v, t in zip(gl_values, df_gl["asset_type"])]

    if gl_mode == "%":
        bar_text = [f"{p:+.1f}%  (₪{v:,.0f})"
                    for p, v in zip(df_gl["gain_pct"].fillna(0), df_gl["gain_loss"])]
        hover_tmpl = "<b>%{y}</b><br>%{x:+.1f}%<extra></extra>"
        x_tickformat = "+.1f%"
    else:
        bar_text = [f"₪{v:,.0f}  ({p:+.1f}%)"
                    for v, p in zip(df_gl["gain_loss"], df_gl["gain_pct"].fillna(0))]
        hover_tmpl = "<b>%{y}</b><br>₪%{x:,.0f}<extra></extra>"
        x_tickformat = "₪,.0f"

    total_gl     = df["gain_loss"].sum()
    total_cost   = df["cost_basis"].sum()
    total_gl_pct = (total_gl / total_cost * 100) if total_cost else 0
    vline_x      = total_gl_pct if gl_mode == "%" else total_gl
    vline_label  = f"סה״כ: {vline_x:+.1f}%" if gl_mode == "%" else f"סה״כ: ₪{vline_x:+,.0f}"
    vline_color  = "#059669" if vline_x >= 0 else "#DC2626"

    # max label length → left margin so names aren't clipped
    max_name_len = df_gl["asset_name"].str.len().max() if not df_gl.empty else 10
    left_margin  = max(80, min(int(max_name_len * 7.5), 280))

    fig_gl = go.Figure(go.Bar(
        x=gl_values,
        y=df_gl["asset_name"],
        orientation="h",
        marker_color=colors_gl,
        text=bar_text,
        textposition="outside",
        cliponaxis=False,
        textfont_size=11,
        hovertemplate=hover_tmpl,
    ))
    if show_vline:
        fig_gl.add_vline(
            x=vline_x,
            line=dict(color=vline_color, width=2, dash="dash"),
            annotation_text=vline_label,
            annotation_position="top",
            annotation=dict(
                font=dict(size=12, color=vline_color),
                bgcolor="rgba(255,255,255,0.85)",
                bordercolor=vline_color,
                borderwidth=1,
            ),
        )
    fig_gl.update_layout(
        **PLOTLY_LAYOUT,
        height=max(360, len(df_gl) * 40),
        xaxis=dict(
            showgrid=True, gridcolor="#F1F5F9",
            zeroline=True, zerolinecolor="#94A3B8", zerolinewidth=1.5,
            tickformat=x_tickformat,
        ),
        yaxis=dict(showgrid=False, automargin=True),
    )
    fig_gl.update_layout(margin=dict(t=24, b=24, l=left_margin, r=24))
    st.plotly_chart(fig_gl, use_container_width=True)

    # ── Row 4: holdings table ─────────────────────────────────────────────────
    section_header("טבלת החזקות")

    show_cols = ["account", "asset_type", "asset_name", "asset_id",
                 "quantity", "cost_basis", "market_value", "gain_loss", "gain_pct"]
    if "updated_at" in df.columns:
        show_cols.append("updated_at")
    fmt = {
        "כמות":              "{:,.4f}",
        "עלות (₪)":          "₪{:,.2f}",
        "שווי נוכחי (₪)":    "₪{:,.2f}",
        "רווח/הפסד (₪)":     "₪{:,.2f}",
        "תשואה %":           "{:+.1f}%",
    }
    st.dataframe(
        _display(df, show_cols).style.format(fmt),
        use_container_width=True,
        height=380,
    )

    # ── Row 5: projection ─────────────────────────────────────────────────────
    st.markdown("<hr>", unsafe_allow_html=True)
    section_header("מחשבון תשואה עתידית")

    # ── פרמטרים ──────────────────────────────────────────────────────────────
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        years = st.slider("אופק השקעה (שנים)", 1, 30, 10)
    with col_b:
        cagr = st.slider("תשואה שנתית צפויה (%)", 0, 20, 7)
    with col_c:
        monthly_deposit = st.number_input(
            "הפקדה חודשית (₪)",
            min_value=0,
            max_value=100_000,
            value=0,
            step=500,
            help="סכום קבוע שמופקד כל חודש לתיק. 0 = ללא הפקדות.",
        )

    # ── חישוב FV עם הפקדות חודשיות ───────────────────────────────────────────
    # FV = PV·(1+r)^n  +  PMT·((1+r)^n - 1)/r
    # r = ריבית חודשית, n = מספר חודשים
    r_monthly = (1 + cagr / 100) ** (1 / 12) - 1
    n_months  = years * 12

    def _fv_at_year(y: int) -> tuple[float, float, float]:
        """Returns (total_fv, fv_from_initial, fv_from_deposits) at year y."""
        n   = y * 12
        fv_initial = total * (1 + r_monthly) ** n
        if r_monthly > 0:
            fv_deposits = monthly_deposit * ((1 + r_monthly) ** n - 1) / r_monthly
        else:
            fv_deposits = monthly_deposit * n
        return fv_initial + fv_deposits, fv_initial, fv_deposits

    fv_total, fv_initial, fv_deposits = _fv_at_year(years)
    total_deposited = monthly_deposit * n_months

    # ── KPI תחתון ─────────────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(f"שווי צפוי בעוד {years} שנים", f"₪{fv_total:,.0f}",
              f"+₪{fv_total - total:,.0f}")
    k2.metric("תשואה על הקרן הקיימת",  f"₪{fv_initial:,.0f}",
              f"+₪{fv_initial - total:,.0f}")
    k3.metric("צבירה מהפקדות חודשיות", f"₪{fv_deposits:,.0f}",
              f"מתוך ₪{total_deposited:,.0f} הפקדות")
    k4.metric("סך הפקדות נוספות",      f"₪{total_deposited:,.0f}",
              f"₪{monthly_deposit:,.0f} × {n_months:,} חודשים")

    # ── נתוני גרף שנה-אחר-שנה ────────────────────────────────────────────────
    years_range   = list(range(years + 1))
    fv_totals     = [_fv_at_year(y)[0] for y in years_range]
    fv_initials   = [_fv_at_year(y)[1] for y in years_range]
    fv_deps       = [_fv_at_year(y)[2] for y in years_range]
    deposited_cum = [monthly_deposit * y * 12 for y in years_range]
    baseline      = [total] * (years + 1)

    fig_proj = go.Figure()

    # שטח תחתון — הפקדות שנצברו (ללא תשואה)
    if monthly_deposit > 0:
        fig_proj.add_trace(go.Scatter(
            x=years_range, y=[total + d for d in deposited_cum],
            mode="lines", name="קרן + הפקדות (ללא תשואה)",
            line=dict(color="#CBD5E1", width=1.5, dash="dot"),
            hovertemplate="שנה %{x}<br>קרן + הפקדות: ₪%{y:,.0f}<extra></extra>",
        ))
        # שטח — תרומת הפקדות לתשואה
        fig_proj.add_trace(go.Scatter(
            x=years_range, y=fv_totals,
            mode="none", name="שווי כולל",
            fill="tonexty", fillcolor="rgba(5,150,105,.10)",
            showlegend=False,
            hoverinfo="skip",
        ))

    # קו הבסיס — ללא הפקדות ובלי תשואה
    fig_proj.add_trace(go.Scatter(
        x=years_range, y=baseline,
        mode="lines", name="ערך נוכחי",
        line=dict(color="#94A3B8", width=1.5, dash="dash"),
        hovertemplate="₪%{y:,.0f}<extra></extra>",
    ))

    # קו ראשי — שווי עם הפקדות ותשואה
    fig_proj.add_trace(go.Scatter(
        x=years_range, y=fv_totals,
        mode="lines+markers", name="שווי צפוי (עם הפקדות)" if monthly_deposit > 0 else "שווי צפוי",
        line=dict(color="#2563EB", width=2.5), marker=dict(size=5),
        fill="tozeroy", fillcolor="rgba(37,99,235,.07)",
        hovertemplate="שנה %{x}: ₪%{y:,.0f}<extra></extra>",
    ))

    fig_proj.update_layout(
        **PLOTLY_LAYOUT,
        height=340,
        xaxis=dict(title="שנה", showgrid=True, gridcolor="#F1F5F9",
                   dtick=max(1, years // 10)),
        yaxis=dict(title=dict(text="שווי (₪)", standoff=12),
                   showgrid=True, gridcolor="#F1F5F9",
                   tickformat="₪,.0f", automargin=True),
        legend=dict(orientation="h", x=0, y=1.16, font_size=11),
    )
    st.plotly_chart(fig_proj, use_container_width=True)

    # ── טבלת תחזית שנתית ─────────────────────────────────────────────────────
    with st.expander("טבלת תחזית מפורטת לפי שנה"):
        table_rows = []
        for y in years_range:
            fv_t, fv_i, fv_d = _fv_at_year(y)
            table_rows.append({
                "שנה":              y,
                "שווי צפוי (₪)":    round(fv_t),
                "מהקרן הקיימת (₪)": round(fv_i),
                "מהפקדות (₪)":      round(fv_d),
                "סך הפקדות (₪)":    monthly_deposit * y * 12,
                "תשואה נטו (₪)":    round(fv_t - total - monthly_deposit * y * 12),
            })
        df_table = pd.DataFrame(table_rows)
        st.dataframe(
            df_table.style.format({c: "₪{:,.0f}" for c in df_table.columns if c != "שנה"}),
            use_container_width=True,
            height=min(420, (years + 2) * 35 + 38),
            hide_index=True,
        )


# ═════════════════════════════════════════════════════════════════════════════
# דף: היסטוריה
# ═════════════════════════════════════════════════════════════════════════════
def page_history() -> None:
    page_header("📈", "היסטוריית תיק", "שינוי שווי לאורך זמן · מבוסס תמונות מצב יומיות")

    # ── load snapshots ────────────────────────────────────────────────────────
    with st.spinner("טוען היסטוריה…"):
        try:
            from sheets.gsheets import read_snapshots, append_snapshot
            df_snap = read_snapshots()
        except Exception as exc:
            st.error(f"שגיאה בטעינת היסטוריה: {exc}")
            return

    # ── no data yet ───────────────────────────────────────────────────────────
    if df_snap.empty:
        st.info(
            "עדיין אין נתוני היסטוריה.\n\n"
            "תמונות מצב נשמרות אוטומטית בכל פעם שמעלים קובץ או מזינים נתונים."
        )
        return

    # ── validate structure ────────────────────────────────────────────────────
    if "snapshot_date" not in df_snap.columns:
        st.error("גיליון ה-snapshots אינו תקין (חסרה עמודת snapshot_date).")
        return

    # ── parse & validate dates ────────────────────────────────────────────────
    df_snap["snapshot_date"] = pd.to_datetime(df_snap["snapshot_date"], errors="coerce")
    df_snap = df_snap.dropna(subset=["snapshot_date"])
    if df_snap.empty:
        st.warning("נתוני תאריכים לא תקינים בהיסטוריה.")
        return

    # ── filter bar ────────────────────────────────────────────────────────────
    all_accounts = sorted(df_snap["account"].dropna().unique().tolist())
    all_types    = sorted(df_snap["asset_type"].dropna().unique().tolist())
    type_labels  = {k: TYPE_HE.get(k, k) for k in all_types}
    type_he_hist = list(type_labels.values())
    date_min     = df_snap["snapshot_date"].min().date()
    date_max     = df_snap["snapshot_date"].max().date()

    with st.container(border=True):
        # date range — full width
        date_range = st.date_input(
            "טווח תאריכים",
            value=(date_min, date_max),
            min_value=date_min, max_value=date_max,
            key="hist_dates",
        )
        _LBL_H = (
            "font-size:.75rem;font-weight:700;color:#64748B;"
            "text-transform:uppercase;letter-spacing:.04em;"
            "padding-top:.45rem;text-align:right"
        )

        # accounts: label | pills | הכל | נקה
        hlc, hpa, haa, hna = st.columns([0.65, 5, 0.45, 0.45])
        hlc.markdown(f"<div style='{_LBL_H}'>חשבון</div>", unsafe_allow_html=True)
        with hpa:
            sel_accounts = st.pills(
                "חשבונות", all_accounts, selection_mode="multi",
                default=all_accounts, key="hist_acc",
                label_visibility="collapsed",
            ) or []
        with haa:
            st.markdown('<div class="ws-filter-btn">', unsafe_allow_html=True)
            if st.button("הכל ✓", key="hist_acc_all"):
                st.session_state["hist_acc"] = all_accounts; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with hna:
            st.markdown('<div class="ws-filter-btn">', unsafe_allow_html=True)
            if st.button("נקה ✗", key="hist_acc_none"):
                st.session_state["hist_acc"] = []; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # asset types: label | pills | הכל | נקה
        htlc, hpt, hat, hnt = st.columns([0.65, 5, 0.45, 0.45])
        htlc.markdown(f"<div style='{_LBL_H}'>סוג נכס</div>", unsafe_allow_html=True)
        with hpt:
            sel_type_lbl = st.pills(
                "סוגי נכסים", type_he_hist, selection_mode="multi",
                default=type_he_hist, key="hist_type",
                label_visibility="collapsed",
            ) or []
        with hat:
            st.markdown('<div class="ws-filter-btn">', unsafe_allow_html=True)
            if st.button("הכל ✓", key="hist_type_all"):
                st.session_state["hist_type"] = type_he_hist; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with hnt:
            st.markdown('<div class="ws-filter-btn">', unsafe_allow_html=True)
            if st.button("נקה ✗", key="hist_type_none"):
                st.session_state["hist_type"] = []; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    rev = {v: k for k, v in type_labels.items()}
    sel_types = [rev[l] for l in sel_type_lbl if l in rev]

    d_from = pd.Timestamp(date_range[0] if isinstance(date_range, (list, tuple)) else date_range)
    d_to   = pd.Timestamp(date_range[1] if isinstance(date_range, (list, tuple)) and len(date_range) > 1 else date_max)

    df_f = df_snap[
        df_snap["account"].isin(sel_accounts) &
        df_snap["asset_type"].isin(sel_types) &
        (df_snap["snapshot_date"] >= d_from) &
        (df_snap["snapshot_date"] <= d_to)
    ]

    if df_f.empty:
        st.warning("אין נתונים לפי הסינון הנבחר.")
        return

    # ── daily aggregates ──────────────────────────────────────────────────────
    daily_total = (
        df_f.groupby("snapshot_date")
        .agg(market_value=("market_value", "sum"), cost_basis=("cost_basis", "sum"))
        .reset_index()
        .sort_values("snapshot_date")
    )
    daily_total["gain_loss"] = daily_total["market_value"] - daily_total["cost_basis"]
    daily_total["gain_pct"]  = daily_total["gain_loss"] / daily_total["cost_basis"].replace(0, float("nan")) * 100

    # ── Chart 1: total portfolio value over time ──────────────────────────────
    section_header("שווי תיק כולל לאורך זמן")

    fig_total = go.Figure()
    fig_total.add_trace(go.Scatter(
        x=daily_total["snapshot_date"],
        y=daily_total["cost_basis"],
        name="עלות רכישה",
        line=dict(color="#94A3B8", width=1.5, dash="dot"),
        hovertemplate="%{x|%d/%m/%Y}<br>עלות: ₪%{y:,.0f}<extra></extra>",
    ))
    fig_total.add_trace(go.Scatter(
        x=daily_total["snapshot_date"],
        y=daily_total["market_value"],
        name="שווי שוק",
        line=dict(color="#2563EB", width=2.5),
        fill="tozeroy",
        fillcolor="rgba(37,99,235,.07)",
        hovertemplate="%{x|%d/%m/%Y}<br>שווי: ₪%{y:,.0f}<extra></extra>",
        mode="lines+markers",
        marker=dict(size=6),
    ))
    fig_total.update_layout(
        **PLOTLY_LAYOUT,
        height=320,
        xaxis=dict(title="תאריך", showgrid=True, gridcolor="#F1F5F9", tickformat="%d/%m/%y"),
        yaxis=dict(title="שווי (₪)", showgrid=True, gridcolor="#F1F5F9", tickformat="₪,.0f"),
        legend=dict(orientation="h", x=0, y=1.15, font_size=11),
    )
    st.plotly_chart(fig_total, use_container_width=True)

    # ── KPIs for selected range ───────────────────────────────────────────────
    if len(daily_total) >= 2:
        first_val = daily_total["market_value"].iloc[0]
        last_val  = daily_total["market_value"].iloc[-1]
        delta_abs = last_val - first_val
        delta_pct = (delta_abs / first_val * 100) if first_val else 0
        last_gl   = daily_total["gain_loss"].iloc[-1]
        last_glp  = daily_total["gain_pct"].iloc[-1]

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("שווי נוכחי",          f"₪{last_val:,.0f}")
        k2.metric("שינוי בתקופה",        f"₪{delta_abs:,.0f}", f"{delta_pct:+.1f}%")
        k3.metric("רווח/הפסד לא ממומש", f"₪{last_gl:,.0f}",   f"{last_glp:+.1f}%")
        k4.metric("מספר תמונות מצב",     len(daily_total))

        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    # ── Chart 2: by account ───────────────────────────────────────────────────
    if df_f["account"].nunique() > 1:
        section_header("שווי לפי חשבון לאורך זמן")

        daily_acc = (
            df_f.groupby(["snapshot_date", "account"])["market_value"]
            .sum()
            .reset_index()
            .sort_values("snapshot_date")
        )

        fig_acc = go.Figure()
        for i, acc in enumerate(sorted(daily_acc["account"].unique())):
            sub = daily_acc[daily_acc["account"] == acc]
            fig_acc.add_trace(go.Scatter(
                x=sub["snapshot_date"],
                y=sub["market_value"],
                name=acc,
                line=dict(color=PALETTE[i % len(PALETTE)], width=2),
                mode="lines+markers",
                marker=dict(size=5),
                hovertemplate=f"<b>{acc}</b><br>%{{x|%d/%m/%Y}}<br>₪%{{y:,.0f}}<extra></extra>",
            ))
        fig_acc.update_layout(
            **PLOTLY_LAYOUT,
            height=300,
            xaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickformat="%d/%m/%y"),
            yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickformat="₪,.0f"),
            legend=dict(orientation="h", x=0, y=1.15, font_size=11),
        )
        st.plotly_chart(fig_acc, use_container_width=True)

    # ── Chart 3: by asset type (stacked area) ────────────────────────────────
    section_header("הרכב תיק לאורך זמן לפי סוג נכס")

    daily_type = (
        df_f.groupby(["snapshot_date", "asset_type"])["market_value"]
        .sum()
        .reset_index()
        .sort_values("snapshot_date")
    )

    fig_type = go.Figure()
    for atype, color in TYPE_COLORS.items():
        sub = daily_type[daily_type["asset_type"] == atype]
        if sub.empty:
            continue
        fig_type.add_trace(go.Scatter(
            x=sub["snapshot_date"],
            y=sub["market_value"],
            name=TYPE_HE.get(atype, atype),
            line=dict(color=color, width=2),
            stackgroup="one",
            fillcolor=(
                "rgba({},{},{},0.6)".format(
                    int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
                ) if color.startswith("#") else color
            ),
            hovertemplate=f"<b>{TYPE_HE.get(atype, atype)}</b><br>%{{x|%d/%m/%Y}}<br>₪%{{y:,.0f}}<extra></extra>",
        ))
    fig_type.update_layout(
        **PLOTLY_LAYOUT,
        height=300,
        xaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickformat="%d/%m/%y"),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickformat="₪,.0f"),
        legend=dict(orientation="h", x=0, y=1.15, font_size=11),
    )
    st.plotly_chart(fig_type, use_container_width=True)

    # ── Chart 4: per holding over time ───────────────────────────────────────
    section_header("שווי אחזקות לאורך זמן")

    daily_holding = (
        df_f.groupby(["snapshot_date", "asset_name"])["market_value"]
        .sum()
        .reset_index()
        .sort_values("snapshot_date")
    )

    latest_date = daily_holding["snapshot_date"].max()
    top_names = (
        daily_holding[daily_holding["snapshot_date"] == latest_date]
        .nlargest(20, "market_value")["asset_name"]
        .tolist()
    )
    total_holdings = daily_holding["asset_name"].nunique()
    dh_top = daily_holding[daily_holding["asset_name"].isin(top_names)]

    if total_holdings > 20:
        st.caption(f"מוצגות 20 האחזקות הגדולות מתוך {total_holdings}")

    fig_hold = go.Figure()
    for i, name in enumerate(sorted(top_names)):
        sub = dh_top[dh_top["asset_name"] == name]
        fig_hold.add_trace(go.Scatter(
            x=sub["snapshot_date"],
            y=sub["market_value"],
            name=name,
            line=dict(color=PALETTE[i % len(PALETTE)], width=2),
            mode="lines+markers",
            marker=dict(size=5),
            hovertemplate=f"<b>{name}</b><br>%{{x|%d/%m/%Y}}<br>₪%{{y:,.0f}}<extra></extra>",
        ))
    fig_hold.update_layout(
        **PLOTLY_LAYOUT,
        height=380,
        xaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickformat="%d/%m/%y"),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickformat="₪,.0f"),
        legend=dict(orientation="h", x=0, y=1.15, font_size=10, traceorder="normal"),
    )
    st.plotly_chart(fig_hold, use_container_width=True)

    # ── Chart 5: gain/loss over time (filled area) ───────────────────────────
    section_header("רווח / הפסד לא ממומש לאורך זמן")

    gl_pos = daily_total["gain_loss"].clip(lower=0)
    gl_neg = daily_total["gain_loss"].clip(upper=0)

    fig_gl = go.Figure()
    # positive area (above zero)
    fig_gl.add_trace(go.Scatter(
        x=daily_total["snapshot_date"],
        y=gl_pos,
        name="רווח",
        mode="lines",
        line=dict(color="#059669", width=0),
        fill="tozeroy",
        fillcolor="rgba(5,150,105,0.18)",
        hoverinfo="skip",
    ))
    # negative area (below zero)
    fig_gl.add_trace(go.Scatter(
        x=daily_total["snapshot_date"],
        y=gl_neg,
        name="הפסד",
        mode="lines",
        line=dict(color="#DC2626", width=0),
        fill="tozeroy",
        fillcolor="rgba(220,38,38,0.18)",
        hoverinfo="skip",
    ))
    # main line with dynamic color marker per point
    last_gl = daily_total["gain_loss"].iloc[-1] if not daily_total.empty else 0
    line_color = "#059669" if last_gl >= 0 else "#DC2626"
    fig_gl.add_trace(go.Scatter(
        x=daily_total["snapshot_date"],
        y=daily_total["gain_loss"],
        name="רווח/הפסד",
        mode="lines+markers",
        line=dict(color=line_color, width=2.5),
        marker=dict(
            size=7,
            color=["#059669" if v >= 0 else "#DC2626" for v in daily_total["gain_loss"]],
            line=dict(width=1.5, color="#fff"),
        ),
        hovertemplate="%{x|%d/%m/%Y}<br>₪%{y:,.0f}<extra></extra>",
    ))
    fig_gl.update_layout(
        **PLOTLY_LAYOUT,
        height=300,
        showlegend=False,
        xaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickformat="%d/%m/%y"),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickformat="₪,.0f",
                   zeroline=True, zerolinecolor="#94A3B8", zerolinewidth=1.5),
    )
    st.plotly_chart(fig_gl, use_container_width=True)

    # ── raw data table ────────────────────────────────────────────────────────
    with st.expander("טבלת נתוני היסטוריה גולמיים"):
        st.dataframe(
            df_f.sort_values(["snapshot_date", "account", "asset_name"], ascending=[False, True, True])
            .rename(columns={
                "snapshot_date": "תאריך", "account": "חשבון", "asset_name": "שם נייר",
                "asset_type": "סוג", "market_value": "שווי (₪)", "cost_basis": "עלות (₪)",
                "gain_loss": "רווח/הפסד (₪)", "gain_pct": "תשואה %",
            })
            .style.format({
                "שווי (₪)": "₪{:,.0f}", "עלות (₪)": "₪{:,.0f}",
                "רווח/הפסד (₪)": "₪{:,.0f}", "תשואה %": "{:+.1f}%",
            }),
            use_container_width=True,
            height=320,
        )




# ═════════════════════════════════════════════════════════════════════════════
# דף: העלאה
# ═════════════════════════════════════════════════════════════════════════════
def page_upload() -> None:
    page_header("📤", "העלאת קובץ החזקות", "פרסר אקסל אוטומטי · IBI · פסגות · הפועלים · לאומי טרייד · הזנה ידנית")

    source = st.selectbox(
        "בחר מקור נתונים",
        ["IBI", "פסגות", "בנק הפועלים", "לאומי טרייד", "הראל — גמל להשקעה"],
    )
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    if source == "IBI":
        _upload_ibi(broker="IBI")
    elif source == "פסגות":
        _upload_ibi(broker="פסגות")
    elif source == "בנק הפועלים":
        _upload_generic(
            bank_name="בנק הפועלים",
            default_account="הפועלים",
            parser_fn=parse_hapoalim,
            tip="ייצא מהאתר: תיק ניירות ערך ← ייצוא ל-Excel",
        )
    elif source == "לאומי טרייד":
        _leumi_upload_or_manual()
    elif source == "הראל — גמל להשקעה":
        _upload_or_manual_harel()


def _leumi_upload_or_manual() -> None:
    section_header("לאומי טרייד — העלאה או הזנה ידנית")

    tab_upload, tab_manual = st.tabs(["📂 העלאת קובץ Excel", "✏️ הזנה ידנית"])

    with tab_upload:
        st.markdown("""
        <div class="ws-card" style="margin-bottom:1rem;">
          <div style="font-size:.82rem;color:#64748B;line-height:1.8;">
            ייצא מלאומי טרייד: <strong>תיק ניירות ערך ← ייצוא ל-Excel</strong><br>
            אם האפשרות אינה זמינה, השתמש בלשונית ההזנה הידנית.
          </div>
        </div>""", unsafe_allow_html=True)

        account_name = st.text_input("שם החשבון", value="לאומי", key="leumi_acc_upload")
        uploaded = st.file_uploader("קובץ Excel מלאומי טרייד", type=["xlsx", "xls"], key="leumi_file")

        if uploaded is not None:
            with st.spinner("מנתח…"):
                try:
                    df = parse_leumi(io.BytesIO(uploaded.read()), account_name=account_name)
                    df = enrich(df)
                except Exception as exc:
                    st.error(f"שגיאה בפענוח: {exc}")
                    df = None

            if df is not None:
                total_val  = df["market_value"].sum()
                total_cost = df["cost_basis"].sum()
                gain       = total_val - total_cost
                m1, m2, m3 = st.columns(3)
                m1.metric("ניירות שפוענחו", len(df))
                m2.metric("שווי כולל",      f"₪{total_val:,.0f}")
                m3.metric("רווח / הפסד",    f"₪{gain:,.0f}",
                          f"{(gain/total_cost*100) if total_cost else 0:+.1f}%")

                show_cols = ["account", "asset_type", "asset_name", "asset_id",
                             "quantity", "cost_basis", "market_value"]
                st.dataframe(
                    _display(df, show_cols).style.format({
                        "כמות": "{:,.4f}", "עלות (₪)": "₪{:,.2f}", "שווי נוכחי (₪)": "₪{:,.2f}",
                    }),
                    use_container_width=True, height=280,
                )
                if st.button("✅ הוסף לתיק ושמור", type="primary", key="leumi_save_upload"):
                    existing = st.session_state.holdings
                    if not existing.empty:
                        existing = existing[existing["account"] != account_name]
                    _save_holdings(pd.concat([existing, df], ignore_index=True))
                    st.success(f"✓ חשבון **{account_name}** נוסף לתיק ונשמר.")

    with tab_manual:
        _manual_entry_securities(account_name_default="לאומי", source_tag="לאומי", form_key="leumi")


def _manual_entry_securities(
    account_name_default: str,
    source_tag: str,
    form_key: str,
) -> None:
    """Generic manual entry form for individual securities (stocks, ETFs, funds)."""
    st.markdown("""
    <div class="ws-card" style="margin-bottom:1rem;">
      <div style="font-size:.82rem;color:#64748B;line-height:1.8;">
        הזן כל נייר ערך בנפרד. ניתן להוסיף מספר ניירות ברצף.
      </div>
    </div>""", unsafe_allow_html=True)

    account_name = st.text_input("שם החשבון", value=account_name_default,
                                 key=f"{form_key}_acc_manual")

    existing_all = st.session_state.holdings
    existing_acc = (
        existing_all[existing_all["account"] == account_name]
        if not existing_all.empty else pd.DataFrame()
    )

    # ── mode toggle ────────────────────────────────────────────────────────────
    entry_mode = st.radio(
        "פעולה",
        ["➕ הוספה", "✏️ עדכון"],
        horizontal=True,
        key=f"{form_key}_entry_mode",
    )
    is_update = entry_mode == "✏️ עדכון"

    # defaults for the form
    default_name = default_id = ""
    default_qty = default_cost = default_mv = 0.0
    selected_idx = None  # index in existing_acc of the row being edited

    if is_update:
        if existing_acc.empty:
            st.info("אין ניירות ערך קיימים בחשבון זה לעדכון.")
            return

        # build label list for selector
        labels = [
            f"{row['asset_name']}  ({row.get('asset_id', '')})"
            for _, row in existing_acc.iterrows()
        ]
        chosen_label = st.selectbox("בחר נייר לעדכון", labels, key=f"{form_key}_sel_asset")
        selected_idx = labels.index(chosen_label)
        sel_row = existing_acc.iloc[selected_idx]
        default_name = sel_row.get("asset_name", "")
        default_id   = str(sel_row.get("asset_id", ""))
        default_qty  = float(sel_row.get("quantity", 0.0))
        default_cost = float(sel_row.get("cost_basis", 0.0))
        default_mv   = float(sel_row.get("market_value", 0.0))
    else:
        # show existing rows so user can see what's already there
        if not existing_acc.empty:
            st.caption(f"ניירות קיימים בחשבון {account_name}:")
            show_cols = ["asset_name", "asset_id", "cost_basis", "market_value"]
            st.dataframe(
                _display(existing_acc, [c for c in show_cols if c in existing_acc.columns])
                .style.format({
                    "עלות (₪)": "₪{:,.2f}", "שווי נוכחי (₪)": "₪{:,.2f}",
                }),
                use_container_width=True, height=min(200, len(existing_acc) * 35 + 38),
                hide_index=True,
            )

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    submit_label = "💾 עדכן נייר" if is_update else "➕ הוסף נייר לתיק"
    with st.form(f"{form_key}_manual_form", clear_on_submit=not is_update):
        c1, c2 = st.columns(2)
        with c1:
            asset_name = st.text_input("שם הנייר",
                                       value=default_name,
                                       placeholder="לדוגמה: מניות אפל / קרן מחקה ת\"א 125")
            asset_id   = st.text_input("מספר נייר / סימבול",
                                       value=default_id,
                                       placeholder="לדוגמה: 662577 / AAPL")
            quantity   = st.number_input("כמות", value=default_qty,
                                         min_value=0.0, step=1.0, format="%.4f")
        with c2:
            cost_basis   = st.number_input("עלות רכישה (₪)", value=default_cost,
                                           min_value=0.0, step=100.0,
                                           help="סך הכסף ששולם בעת הרכישה")
            market_value = st.number_input("שווי נוכחי (₪)", value=default_mv,
                                           min_value=0.0, step=100.0,
                                           help="שווי השוק היום")

        submitted = st.form_submit_button(submit_label, type="primary", use_container_width=True)

    if submitted and asset_name.strip():
        row = pd.DataFrame([{
            "account":      account_name,
            "asset_name":   asset_name.strip(),
            "asset_id":     asset_id.strip(),
            "quantity":     quantity,
            "cost_basis":   cost_basis,
            "market_value": market_value,
            "source":       source_tag,
        }])
        existing_other = existing_all[existing_all["account"] != account_name] \
            if not existing_all.empty else pd.DataFrame()

        if is_update and selected_idx is not None:
            # replace only the selected row; keep the rest of the account's holdings
            acc_without_selected = existing_acc.drop(existing_acc.index[selected_idx])
            new_acc = pd.concat([acc_without_selected, row], ignore_index=True)
            _save_holdings(pd.concat([existing_other, new_acc], ignore_index=True))
            st.success(f"✓ **{asset_name}** עודכן בחשבון {account_name}.")
        else:
            _save_holdings(pd.concat([existing_other, existing_acc, row], ignore_index=True))
            st.success(f"✓ **{asset_name}** נוסף לחשבון {account_name}.")
        st.rerun()
    elif submitted:
        st.warning("נא להזין שם נייר.")


# ── File-upload sync diff helper ──────────────────────────────────────────────

def _show_upload_diff(existing_acc: pd.DataFrame, new_df: pd.DataFrame) -> None:
    """
    Display a before/after diff between existing account holdings and the
    newly parsed file.  Match rows by asset_id when available, else asset_name.
    """
    def _key(row):
        aid = str(row.get("asset_id", "")).strip()
        return aid if aid and aid not in ("nan", "") else str(row.get("asset_name", "")).strip()

    existing_map = {_key(r): r for _, r in existing_acc.iterrows()} if not existing_acc.empty else {}
    new_map      = {_key(r): r for _, r in new_df.iterrows()}

    added   = [k for k in new_map      if k not in existing_map]
    removed = [k for k in existing_map if k not in new_map]
    updated = []
    for k in new_map:
        if k not in existing_map:
            continue
        old, new = existing_map[k], new_map[k]
        for col in ("quantity", "market_value", "cost_basis"):
            if abs(float(old.get(col, 0) or 0) - float(new.get(col, 0) or 0)) > 0.01:
                updated.append(k)
                break

    has_changes = added or removed or updated
    if not has_changes and not existing_acc.empty:
        st.success("✓ הקובץ זהה לחלוטין להחזקות הקיימות — אין שינויים.")
        return

    if existing_acc.empty:
        st.info(f"חשבון חדש — {len(new_df)} ניירות ערך יתווספו.")
        return

    col_a, col_r, col_u = st.columns(3)
    col_a.metric("➕ חדשים מהקובץ",   len(added))
    col_r.metric("🗑️ יוסרו מהתיק",  len(removed))
    col_u.metric("🔄 מתעדכנים",       len(updated))

    if added:
        with st.expander(f"➕ ניירות חדשים שיתווספו ({len(added)})"):
            rows = [new_map[k] for k in added]
            _diff_table(rows, ["asset_name", "asset_id", "quantity", "cost_basis", "market_value"])

    if removed:
        with st.expander(f"🗑️ ניירות שיוסרו מהתיק ({len(removed)})"):
            rows = [existing_map[k] for k in removed]
            _diff_table(rows, ["asset_name", "asset_id", "quantity", "cost_basis", "market_value"])

    if updated:
        with st.expander(f"🔄 ניירות שיתעדכנו ({len(updated)})"):
            records = []
            for k in updated:
                old, new = existing_map[k], new_map[k]
                records.append({
                    "שם נייר":          new.get("asset_name", k),
                    "כמות (ישן)":       old.get("quantity", ""),
                    "כמות (חדש)":       new.get("quantity", ""),
                    "שווי ישן (₪)":     old.get("market_value", ""),
                    "שווי חדש (₪)":     new.get("market_value", ""),
                })
            st.dataframe(pd.DataFrame(records), use_container_width=True,
                         hide_index=True)


def _diff_table(rows: list, cols: list) -> None:
    df = pd.DataFrame(rows)[cols]
    df = _display(df, [c for c in cols if c in df.columns])
    fmt = {"עלות (₪)": "₪{:,.2f}", "שווי נוכחי (₪)": "₪{:,.2f}", "כמות": "{:,.4f}"}
    st.dataframe(df.style.format({k: v for k, v in fmt.items() if k in df.columns}),
                 use_container_width=True, hide_index=True)


def _upload_generic(
    bank_name: str,
    default_account: str,
    parser_fn,
    tip: str = "",
) -> None:
    section_header(f"העלאת קובץ — {bank_name}")

    if tip:
        st.markdown(f"""
        <div class="ws-card" style="margin-bottom:1rem;">
          <div style="font-size:.82rem;color:#64748B;line-height:1.8;">
            {tip}<br>
            המערכת מזהה אוטומטית את מבנה הקובץ ומנרמלת את הנתונים.
          </div>
        </div>""", unsafe_allow_html=True)

    account_name = st.text_input("שם החשבון", value=default_account,
                                 help="השם שיופיע בלוח המחוונים.")
    uploaded = st.file_uploader("גרור לכאן קובץ Excel או לחץ לבחירה", type=["xlsx", "xls"],
                                key=f"upload_{bank_name}")

    if uploaded is None:
        return

    with st.spinner("מנתח ומנרמל נתונים…"):
        try:
            df = parser_fn(io.BytesIO(uploaded.read()), account_name=account_name)
            df = enrich(df)
        except Exception as exc:
            st.error(f"שגיאה בפענוח: {exc}")
            st.caption(
                "אם הקובץ לא מזוהה, נסה להעתיק את הנתונים לתבנית ידנית "
                "או צור קשר עם התמיכה."
            )
            return

    total_val  = df["market_value"].sum()
    total_cost = df["cost_basis"].sum()
    gain       = total_val - total_cost

    m1, m2, m3 = st.columns(3)
    m1.metric("ניירות ערך שפוענחו", len(df))
    m2.metric("שווי כולל בקובץ",   f"₪{total_val:,.0f}")
    m3.metric("רווח / הפסד",       f"₪{gain:,.0f}",
              f"{(gain/total_cost*100) if total_cost else 0:+.1f}%")

    show_cols = ["account", "asset_type", "asset_name", "asset_id",
                 "quantity", "cost_basis", "market_value"]
    with st.expander("📋 כל הנתונים מהקובץ", expanded=False):
        st.dataframe(
            _display(df, show_cols).style.format({
                "כמות":           "{:,.4f}",
                "עלות (₪)":       "₪{:,.2f}",
                "שווי נוכחי (₪)": "₪{:,.2f}",
            }),
            use_container_width=True, height=300,
        )

    # diff vs current holdings for this account
    existing_all = st.session_state.holdings
    existing_acc = (
        existing_all[existing_all["account"] == account_name]
        if not existing_all.empty else pd.DataFrame()
    )
    st.markdown("---")
    section_header("סנכרון עם התיק הקיים")
    _show_upload_diff(existing_acc, df)

    st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
    if st.button("✅ סנכרן ושמור", type="primary", key=f"save_{bank_name}"):
        existing_other = existing_all[existing_all["account"] != account_name] \
            if not existing_all.empty else pd.DataFrame()
        _save_holdings(pd.concat([existing_other, df], ignore_index=True))
        st.success(f"✓ חשבון **{account_name}** סונכרן ונשמר.")


def _upload_ibi(broker: str = "פסגות") -> None:
    section_header(f"העלאת קובץ {broker}")

    broker_tips = {
        "IBI":   "ייצא את תיק ההשקעות מפלטפורמת IBI כקובץ Excel והעלה אותו כאן.",
        "פסגות": "ייצא את תיק ההשקעות מפלטפורמת פסגות כקובץ Excel (Portfolio) והעלה אותו כאן.",
    }
    st.markdown(f"""
    <div class="ws-card" style="margin-bottom:1rem;">
      <div style="font-size:.82rem;color:#64748B;line-height:1.8;">
        {broker_tips.get(broker, '')}<br>
        המערכת מזהה אוטומטית את הפורמט ומנרמלת את הנתונים.
      </div>
    </div>""", unsafe_allow_html=True)

    account_name = st.text_input("שם החשבון", value=broker,
                                 help="השם שיופיע בלוח המחוונים.")
    uploaded = st.file_uploader("גרור לכאן קובץ Excel או לחץ לבחירה", type=["xlsx"],
                                key=f"upload_{broker}")

    if uploaded is None:
        return

    with st.spinner("מנתח ומנרמל נתונים…"):
        try:
            df = parse_ibi(io.BytesIO(uploaded.read()),
                           account_name=account_name,
                           source=broker)
            df = enrich(df)
        except Exception as exc:
            st.error(f"שגיאה בפענוח: {exc}")
            st.caption(
                "וודא שהקובץ יוצא ישירות מהפלטפורמה ולא עבר עריכה ידנית. "
                "במידת הצורך השתמש בהזנה ידנית."
            )
            return

    total_val  = df["market_value"].sum()
    total_cost = df["cost_basis"].sum()
    gain       = total_val - total_cost

    m1, m2, m3 = st.columns(3)
    m1.metric("ניירות ערך שפוענחו", len(df))
    m2.metric("שווי כולל בקובץ",   f"₪{total_val:,.0f}")
    m3.metric("רווח / הפסד",       f"₪{gain:,.0f}",
              f"{(gain/total_cost*100) if total_cost else 0:+.1f}%")

    show_cols = ["account", "asset_type", "asset_name", "asset_id",
                 "quantity", "cost_basis", "market_value"]
    with st.expander("📋 כל הנתונים מהקובץ", expanded=False):
        st.dataframe(
            _display(df, show_cols).style.format({
                "כמות":           "{:,.4f}",
                "עלות (₪)":       "₪{:,.2f}",
                "שווי נוכחי (₪)": "₪{:,.2f}",
            }),
            use_container_width=True, height=300,
        )

    # diff vs current holdings for this account
    existing_all = st.session_state.holdings
    existing_acc = (
        existing_all[existing_all["account"] == account_name]
        if not existing_all.empty else pd.DataFrame()
    )
    st.markdown("---")
    section_header("סנכרון עם התיק הקיים")
    _show_upload_diff(existing_acc, df)

    st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
    if st.button("✅ סנכרן ושמור", type="primary", key=f"save_{broker}"):
        existing_other = existing_all[existing_all["account"] != account_name] \
            if not existing_all.empty else pd.DataFrame()
        _save_holdings(pd.concat([existing_other, df], ignore_index=True))
        st.success(f"✓ חשבון **{account_name}** סונכרן ונשמר.")


def _upload_or_manual_harel() -> None:
    section_header("הראל — גמל להשקעה")

    tab_pdf, tab_manual = st.tabs(["📂 העלאת PDF", "✏️ הזנה ידנית"])

    with tab_pdf:
        st.markdown("""
        <div class="ws-card" style="margin-bottom:1rem;">
          <div style="font-size:.82rem;color:#64748B;line-height:1.8;">
            הורד את דוח <strong>מידע אישי — תכנית גמל להשקעה</strong> מאתר הראל ביטוח ופיננסים<br>
            ← <strong>אזור אישי ← גמל להשקעה ← הדפסת דוח</strong><br>
            ניתן להעלות <strong>מספר מסלולים בבת אחת</strong> — כולם ישמרו תחת אותו חשבון.
          </div>
        </div>""", unsafe_allow_html=True)

        account_name = st.text_input("שם החשבון", value="הראל",
                                     help="כל המסלולים שמועלים יישמרו תחת שם זה.",
                                     key="harel_acc_pdf")
        uploaded_files = st.file_uploader(
            "גרור לכאן קבצי PDF או לחץ לבחירה",
            type=["pdf"],
            accept_multiple_files=True,
            key="upload_gamel_pdf",
        )

        if not uploaded_files:
            return

        all_dfs: list[pd.DataFrame] = []
        errors: list[str] = []

        with st.spinner(f"מנתח {len(uploaded_files)} קבצים…"):
            for f in uploaded_files:
                try:
                    df_raw = parse_gamel_pdf(io.BytesIO(f.read()), account_name=account_name)
                    df_raw = enrich(df_raw)
                    all_dfs.append(df_raw)
                except Exception as exc:
                    errors.append(f"{f.name}: {exc}")

        for err in errors:
            st.error(f"שגיאה בפענוח: {err}")

        if not all_dfs:
            return

        df = pd.concat(all_dfs, ignore_index=True)

        total_val  = df["market_value"].sum()
        total_cost = df["cost_basis"].sum()
        gain       = total_val - total_cost

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("תכניות שזוהו",   len(uploaded_files) - len(errors))
        m2.metric("צבירה כוללת",    f"₪{total_val:,.0f}")
        m3.metric("עלות רכישה",     f"₪{total_cost:,.0f}")
        m4.metric("רווח לא ממומש",  f"₪{gain:,.0f}",
                  f"{(gain/total_cost*100) if total_cost else 0:+.1f}%")

        show_cols = ["asset_name", "cost_basis", "market_value"]
        with st.expander("📋 כל הנתונים מהקובץ", expanded=False):
            st.dataframe(
                _display(df, show_cols).style.format({
                    "עלות (₪)":       "₪{:,.2f}",
                    "שווי נוכחי (₪)": "₪{:,.2f}",
                }),
                use_container_width=True,
            )

        existing_all = st.session_state.holdings
        existing_acc = (
            existing_all[existing_all["account"] == account_name]
            if not existing_all.empty else pd.DataFrame()
        )
        st.markdown("---")
        section_header("סנכרון עם התיק הקיים")
        _show_upload_diff(existing_acc, df)

        st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
        if st.button("✅ סנכרן ושמור", type="primary", key="save_gamel_pdf"):
            existing_other = existing_all[existing_all["account"] != account_name] \
                if not existing_all.empty else pd.DataFrame()
            _save_holdings(pd.concat([existing_other, df], ignore_index=True))
            st.success(f"✓ חשבון **{account_name}** סונכרן ונשמר.")

    with tab_manual:
        _manual_entry_securities(account_name_default="הראל", source_tag="ידני", form_key="harel")


# ═════════════════════════════════════════════════════════════════════════════
# דף: הגדרות
# ═════════════════════════════════════════════════════════════════════════════
def page_settings() -> None:
    page_header("⚙️", "הגדרות", "חיבור Google Sheets · ייצוא · ניהול נתונים")

    section_header("חיבור Google Sheets")
    st.markdown("""
    <div class="ws-card">
      <div style="font-size:.85rem;color:#64748B;line-height:1.8;">
        פרטי הגישה מוגדרים בקובץ <code>.streamlit/secrets.toml</code> (מקומי)<br>
        או דרך ממשק ה-Secrets של Streamlit Cloud (ייצור).
      </div>
    </div>""", unsafe_allow_html=True)

    c1, _ = st.columns([1, 4])
    with c1:
        if st.button("🔌 בדוק חיבור", use_container_width=True):
            try:
                from sheets.gsheets import get_client
                get_client()
                st.success("✓ החיבור ל-Google Sheets תקין")
            except Exception as exc:
                st.error(f"החיבור נכשל: {exc}")

    st.markdown("<hr>", unsafe_allow_html=True)
    section_header("ייצוא נתונים")

    if not st.session_state.holdings.empty:
        c1, _ = st.columns([1, 4])
        with c1:
            csv = st.session_state.holdings.to_csv(index=False).encode("utf-8-sig")
            st.download_button("⬇️ הורד CSV", data=csv,
                               file_name="wealthsync_holdings.csv",
                               mime="text/csv", use_container_width=True)
    else:
        st.caption("אין החזקות טעונות.")

    st.markdown("<hr>", unsafe_allow_html=True)
    section_header("ניהול נתונים")
    st.warning("פעולה זו תמחק את כל ההחזקות — גם מה-Google Sheets.")
    if st.button("🗑️ מחק את כל הנתונים", type="secondary"):
        _save_holdings(pd.DataFrame())
        st.session_state.sheets_loaded = True
        st.success("✓ הנתונים נמחקו.")


# ═════════════════════════════════════════════════════════════════════════════
# דף: המלצות AI
# ═════════════════════════════════════════════════════════════════════════════

_SYSTEM_PROMPT = """אתה יועץ השקעות מקצועי המתמחה בשוק ההון הישראלי.
אתה מנתח תיקי השקעות ומספק המלצות מבוססות נתונים, תמציתיות ומעשיות.

כללים שאתה תמיד מכבד:
- מס רווחי הון בישראל: 25% על רווח ריאלי (לאחר ניכוי אינפלציה) לאדם פרטי.
  מכירה של נייר ברווח גוררת אירוע מס — יש לקחת זאת בחשבון לפני כל המלצת מכירה.
- עמלות מסחר: בין 0.1% ל-0.5% לעסקה בממוצע בברוקרים ישראליים.
  החלפת פוזיציות קטנות עשויה לעלות יותר מהתועלת.
- פיזור: אל תמליץ על ריכוז יתר בנייר בודד.
- אין לך גישה לנתוני שוק בזמן אמת — ציין זאת בגלוי.
- הוסף תמיד הסתייגות: "אין לראות בכך ייעוץ השקעות מוסמך."

פורמט תשובה:
- כותרות ב-Markdown (##, ###)
- נקודות (•) לרשימות
- מספרים בפורמט ישראלי (₪X,XXX)
- תשובה בעברית בלבד
"""


def _build_portfolio_prompt(
    df: pd.DataFrame,
    horizon_years: int,
    monthly_deposit: int,
    risk: str,
    free_text: str,
) -> str:
    df = enrich(df)
    total_val  = df["market_value"].sum()
    total_cost = df["cost_basis"].sum()
    total_gl   = total_val - total_cost
    gl_pct     = (total_gl / total_cost * 100) if total_cost else 0

    # סיכום לפי סוג
    by_type = (
        df.groupby("asset_type")
        .agg(market_value=("market_value", "sum"), count=("asset_name", "count"))
        .reset_index()
    )
    by_type["pct"]   = by_type["market_value"] / total_val * 100
    by_type["label"] = by_type["asset_type"].map(TYPE_HE)

    type_summary = "\n".join(
        f"  • {r['label']}: ₪{r['market_value']:,.0f} ({r['pct']:.1f}%, {r['count']} ניירות)"
        for _, r in by_type.iterrows()
    )

    # פירוט ניירות
    holdings_lines = []
    for _, r in df.sort_values("market_value", ascending=False).iterrows():
        gl      = r["market_value"] - r["cost_basis"]
        gl_p    = (gl / r["cost_basis"] * 100) if r["cost_basis"] else 0
        gl_str  = f"רווח ₪{gl:,.0f} ({gl_p:+.1f}%)" if gl >= 0 else f"הפסד ₪{abs(gl):,.0f} ({gl_p:+.1f}%)"
        currency = r.get("currency", "")
        cur_str  = f" [{currency}]" if currency else ""
        holdings_lines.append(
            f"  • {r['asset_name']} ({r['asset_id']}){cur_str} | "
            f"שווי ₪{r['market_value']:,.0f} | {gl_str} | סוג: {TYPE_HE.get(r['asset_type'], r['asset_type'])}"
        )
    holdings_text = "\n".join(holdings_lines)

    risk_map = {"נמוכה": "שמרני", "בינונית": "מאוזן", "גבוהה": "אגרסיבי"}

    prompt = f"""## פרטי המשקיע

- **אופק השקעה:** {horizon_years} שנים
- **הפקדה חודשית מתוכננת:** ₪{monthly_deposit:,}
- **רמת סיכון מועדפת:** {risk} ({risk_map.get(risk, risk)})
{f'- **הערות נוספות מהמשקיע:** {free_text}' if free_text.strip() else ''}

## מצב התיק הנוכחי

- **שווי כולל:** ₪{total_val:,.0f}
- **עלות כוללת:** ₪{total_cost:,.0f}
- **רווח/הפסד לא ממומש:** ₪{total_gl:,.0f} ({gl_pct:+.1f}%)

### הרכב לפי סוג נכס
{type_summary}

### פירוט ניירות ערך
{holdings_text}

---

## בקשה

נתח את התיק ותן המלצות מפורטות:

1. **הערכת התיק הנוכחי** — חוזקות, חולשות, ריכוזים בעייתיים
2. **המלצות לפעולה** — מה לקנות, מה לשקול למכור (תוך התחשבות במס ועמלות), מה להשאיר
3. **להיכן להפנות את ההפקדה החודשית** של ₪{monthly_deposit:,}
4. **אסטרטגיה לאופק של {horizon_years} שנים** — כיצד לנהל את התיק לקראת מועד המשיכה
5. **אזהרות ספציפיות** — ניירות שדורשים תשומת לב מיוחדת
"""
    return prompt


def page_ai() -> None:
    page_header("🤖", "המלצות AI", "ניתוח תיק אישי מבוסס Google Gemini · חינמי")

    # ── בדיקת API key ─────────────────────────────────────────────────────────
    api_key = st.secrets.get("gemini", {}).get("api_key", "")
    if not api_key:
        st.warning(
            "נדרש API Key של Google Gemini.\n\n"
            "1. היכנס ל-[aistudio.google.com](https://aistudio.google.com) → **Get API key**\n"
            "2. הוסף ל-Streamlit Cloud Secrets:\n"
            "```toml\n[gemini]\napi_key = \"AIza...\"\n```"
        )
        st.stop()

    # ── כלי אבחון ────────────────────────────────────────────────────────────
    with st.expander("🔧 אבחון חיבור Gemini"):
        st.caption(f"API key: `{api_key[:8]}...{api_key[-4:]}` ({len(api_key)} תווים)")
        if st.button("בדוק אילו מודלים זמינים", key="diag_models"):
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                available = [
                    m.name for m in genai.list_models()
                    if "generateContent" in m.supported_generation_methods
                ]
                if available:
                    st.success("מודלים זמינים:")
                    for name in available:
                        st.code(name)
                else:
                    st.error("לא נמצאו מודלים זמינים עם ה-key הזה.")
            except Exception as exc:
                st.error(f"שגיאה: {exc}")

    df = st.session_state.holdings
    if df.empty:
        st.info("טרם נטענו נתונים — עבור ל-**📤 העלאה** תחילה.")
        return

    # ── קלטי משתמש ───────────────────────────────────────────────────────────
    section_header("פרמטרי השקעה")

    c1, c2, c3 = st.columns(3)
    with c1:
        horizon = st.number_input("אופק השקעה (שנים)", min_value=1, max_value=40, value=10,
                                  help="עוד כמה שנים תזדקק לכסף?")
    with c2:
        monthly = st.number_input("הפקדה חודשית מתוכננת (₪)", min_value=0,
                                  max_value=100_000, value=2_000, step=500)
    with c3:
        risk = st.select_slider("רמת סיכון", options=["נמוכה", "בינונית", "גבוהה"], value="בינונית")

    free_text = st.text_area(
        "הערות / שאלות ספציפיות (אופציונלי)",
        placeholder="לדוגמה: שוקל לעבור לברוקר זול יותר, מתעניין בחשיפה לטכנולוגיה, חושש מתנודתיות...",
        height=90,
    )

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    # ── סיכום תיק לפני שליחה ─────────────────────────────────────────────────
    df_e = enrich(df)
    total = df_e["market_value"].sum()
    cost  = df_e["cost_basis"].sum()
    gl    = total - cost

    col1, col2, col3 = st.columns(3)
    col1.metric("שווי תיק",    f"₪{total:,.0f}")
    col2.metric("רווח לא ממומש", f"₪{gl:,.0f}", f"{(gl/cost*100) if cost else 0:+.1f}%")
    col3.metric("ניירות ערך",  len(df_e))

    st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)

    if not st.button("🤖 נתח את התיק וקבל המלצות", type="primary", use_container_width=False):
        st.caption("הניתוח נשלח ל-Gemini Flash ומוחזר בסטרימינג · בד״כ 10-20 שניות")
        return

    # ── קריאה ל-Gemini ────────────────────────────────────────────────────────
    try:
        import google.generativeai as genai
    except ImportError:
        st.error("חסר חבילה: `pip install google-generativeai`")
        return

    genai.configure(api_key=api_key)

    # Preferred models in order — pick the first one available for this key
    _PREFERRED = [
        "gemini-2.0-flash-lite",
        "gemini-2.0-flash",
        "gemini-2.5-flash",
        "gemini-flash-lite-latest",
        "gemini-flash-latest",
    ]

    try:
        _available = {
            m.name.replace("models/", "")
            for m in genai.list_models()
            if "generateContent" in m.supported_generation_methods
        }
    except Exception as exc:
        st.error(f"לא ניתן לאחזר רשימת מודלים: {exc}")
        return

    used_model = next((m for m in _PREFERRED if m in _available), None)
    if used_model is None:
        # fallback: just take the first available model that contains "flash"
        used_model = next((m for m in sorted(_available) if "flash" in m), None)
    if used_model is None:
        st.error(
            "לא נמצא מודל Gemini זמין עבור ה-API key הזה.\n\n"
            f"מודלים זמינים: {', '.join(sorted(_available)[:5])}"
        )
        return

    model = genai.GenerativeModel(model_name=used_model, system_instruction=_SYSTEM_PROMPT)

    prompt = _build_portfolio_prompt(df_e, horizon, monthly, risk, free_text)

    st.markdown("<hr>", unsafe_allow_html=True)
    section_header(f"ניתוח AI — המלצות מותאמות אישית ({used_model})")

    st.markdown("""
    <div class="ws-card" style="margin-bottom:1rem; border-right: 3px solid #F59E0B;">
      <div style="font-size:.8rem; color:#92400E; line-height:1.7;">
        ⚠️ <strong>הסתייגות:</strong> הניתוח מבוסס על הנתונים שהעלית ועל מודל AI כללי.
        אין לראות בכך ייעוץ השקעות מוסמך. התייעץ עם יועץ השקעות מורשה לפני כל פעולה.
      </div>
    </div>
    """, unsafe_allow_html=True)

    response_box = st.empty()
    full_text = ""

    with st.spinner(f"{used_model} מנתח את התיק…"):
        try:
            stream = model.generate_content(prompt, stream=True)
            for chunk in stream:
                if chunk.text:
                    full_text += chunk.text
                    response_box.markdown(full_text)
        except Exception as exc:
            st.error(f"שגיאה בקריאה ל-Gemini: {exc}")
            return

    # כפתור להעתקה
    st.download_button(
        "⬇️ שמור ניתוח כקובץ טקסט",
        data=full_text.encode("utf-8"),
        file_name="wealthsync_ai_analysis.txt",
        mime="text/plain",
    )


# ═════════════════════════════════════════════════════════════════════════════
# דף: ניתוח השקעות (analysis/ — חינמי, yfinance בלבד)
# ═════════════════════════════════════════════════════════════════════════════

_ANALYSIS_VERDICT_HE = {"buy": ("קנייה", "gain"), "wait": ("המתנה", "warn"),
                         "skip": ("דילוג", "loss"), "no_data": ("אין נתונים", "warn")}
_ANALYSIS_ACTION_HE = {"hold": ("להחזיק", "info"), "add": ("להוסיף", "gain"),
                        "trim": ("לקצץ חלקית", "warn"), "sell": ("למכור", "loss"),
                        "no_data": ("אין נתונים", "warn")}


def _analysis_disclaimer() -> None:
    st.markdown("""
    <div class="ws-card" style="border-right:3px solid #D97706;">
      <div style="font-size:.8rem;color:#92400E;">
        ⚠️ למחקר אישי בלבד — לא ייעוץ השקעות מוסמך. מבוסס נתוני yfinance בלבד.
      </div>
    </div>""", unsafe_allow_html=True)


@st.cache_data(ttl=900, show_spinner=False)
def _cached_buy_analysis(query: str) -> dict:
    from analysis.portfolio_bridge import run_buy_analysis
    return run_buy_analysis(query)


@st.cache_data(ttl=900, show_spinner=False)
def _cached_review_portfolio(df: pd.DataFrame) -> dict:
    from analysis.portfolio_bridge import review_portfolio
    return review_portfolio(df)


@st.cache_data(ttl=900, show_spinner=False)
def _cached_allocate_deposit(amount: float, candidates: tuple[str, ...]) -> dict:
    from analysis.portfolio_bridge import run_allocate_deposit
    return run_allocate_deposit(amount, list(candidates))


@st.cache_data(ttl=900, show_spinner=False)
def _cached_list_unmapped(df: pd.DataFrame) -> list[dict]:
    from analysis.portfolio_bridge import list_unmapped_assets
    return list_unmapped_assets(df)


def page_invest_analysis() -> None:
    page_header("🧭", "ניתוח השקעות",
                "ניתוח טכני חינמי מעל yfinance · RSI · MACD · בולינגר · ATR")
    _analysis_disclaimer()

    tab_buy, tab_review, tab_deposit, tab_mapping = st.tabs(
        ["📈 ניתוח קנייה", "🗓️ סקירה שבועית", "💰 הקצאת הפקדה", "🔗 מיפוי טיקרים"]
    )

    # ── ניתוח קנייה ──────────────────────────────────────────────────────────
    with tab_buy:
        section_header("בדיקת מניה")
        query = st.text_input(
            "סימבול או שם נייר ממופה",
            placeholder="לדוגמה: AAPL, ISCD.TA, ישראכרט",
            key="analysis_buy_query",
        )
        if st.button("נתח", type="primary", key="analysis_buy_btn") and query.strip():
            with st.spinner("מאחזר נתוני שוק…"):
                result = _cached_buy_analysis(query.strip())

            if result.get("verdict", "no_data") == "no_data":
                st.warning("אין נתוני שוק עבור הסימבול הזה — בדוק את הטיקר או הוסף מיפוי ב-`analysis/symbols.py`.")
            else:
                verdict_label, verdict_kind = _ANALYSIS_VERDICT_HE[result["verdict"]]
                lo, hi = result["entry_zone"]
                st.markdown(
                    f"### {result['symbol']} — {badge(verdict_label, verdict_kind)}",
                    unsafe_allow_html=True,
                )
                m1, m2, m3 = st.columns(3)
                m1.metric("מחיר נוכחי", result["price"])
                m2.metric("ניקוד", f"{result['score']}/100")
                m3.metric("תזמון", result["timing"])
                m4, m5, m6 = st.columns(3)
                m4.metric("אזור כניסה", f"{lo} – {hi}")
                m5.metric("סטופ מוצע", result["stop"])
                m6.metric("יעד מוצע", result["target"])
                st.markdown("**נימוקים:**\n" + "\n".join(f"- {r}" for r in result["reasons"]))

    # ── סקירה שבועית ─────────────────────────────────────────────────────────
    with tab_review:
        section_header("סקירת התיק הנוכחי")
        holdings = st.session_state.holdings
        if holdings.empty:
            st.info("טרם נטענו נתונים — עבור ל-**📤 העלאה** כדי להוסיף חשבונות.")
        elif st.button("🔄 הרץ סקירה", type="primary", key="analysis_review_btn"):
            with st.spinner("מנתח את כל ההחזקות…"):
                review = _cached_review_portfolio(holdings)

            if not review["reviewed"]:
                st.warning("אין החזקות שניתן למפות לטיקר yfinance.")
            for r in review["reviewed"]:
                action_label, action_kind = _ANALYSIS_ACTION_HE.get(r.get("action", "no_data"),
                                                                     ("?", "info"))
                pnl = f"{r['pnl_pct']:+.1f}%" if r.get("pnl_pct") is not None else "—"
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([2, 1, 1, 2])
                    c1.markdown(f"**{r.get('asset_name', r.get('symbol'))}** ({r.get('symbol', '')})")
                    c2.markdown(badge(action_label, action_kind), unsafe_allow_html=True)
                    c3.markdown(f"רווח/הפסד: {pnl}")
                    c4.markdown(
                        f"סטופ מוצע: {r.get('suggested_stop', '—')} · יעד מוצע: {r.get('suggested_target', '—')}"
                    )
                    if r.get("reasons"):
                        st.caption(" · ".join(r["reasons"]))

            if review["unresolved"]:
                with st.expander(f"⚠️ {len(review['unresolved'])} ניירות לא נותחו (אין מיפוי טיקר)"):
                    st.dataframe(pd.DataFrame(review["unresolved"]), use_container_width=True, hide_index=True)
                    st.caption("עבור לטאב '🔗 מיפוי טיקרים' כדי להוסיף מיפוי לניירות אלה.")

    # ── הקצאת הפקדה ──────────────────────────────────────────────────────────
    with tab_deposit:
        section_header("חלוקת הפקדה חדשה")
        c1, c2 = st.columns([1, 2])
        with c1:
            amount = st.number_input("סכום ההפקדה (₪)", min_value=0.0, value=2000.0, step=500.0,
                                     key="analysis_deposit_amount")
        with c2:
            candidates_raw = st.text_input(
                "מועמדים (שמות ממופים או טיקרים, מופרדים בפסיק)",
                placeholder="לדוגמה: ישראכרט, נקסט ויזן, AAPL",
                key="analysis_deposit_candidates",
            )
        if st.button("חשב הקצאה", type="primary", key="analysis_deposit_btn") and candidates_raw.strip():
            candidates = tuple(c.strip() for c in candidates_raw.split(",") if c.strip())
            with st.spinner("מנתח מועמדים…"):
                allocation = _cached_allocate_deposit(amount, candidates)

            if allocation["allocations"]:
                rows = [{
                    "סימבול": a["symbol"], "סכום (₪)": a["amount"], "מניות": a["shares"],
                    "אזור כניסה": f"{a['entry_zone'][0]}–{a['entry_zone'][1]}",
                    "סטופ": a["stop"], "יעד": a["target"],
                } for a in allocation["allocations"]]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                st.metric("נשאר במזומן", f"₪{allocation['cash_left']:,.0f}")
            else:
                st.info(allocation.get("note", "אין מועמדות אטרקטיביות כרגע."))

            if allocation.get("waiting"):
                st.caption("בהמתנה: " + " · ".join(f"{s} ({t})" for s, t in allocation["waiting"]))
            if allocation.get("unresolved"):
                st.warning(f"לא נפתרו לטיקר: {', '.join(allocation['unresolved'])}")

    # ── מיפוי טיקרים ─────────────────────────────────────────────────────────
    with tab_mapping:
        section_header("ניירות בתיק שלא נפתרו לטיקר yfinance")
        holdings = st.session_state.holdings
        if holdings.empty:
            st.info("טרם נטענו נתונים — עבור ל-**📤 העלאה** כדי להוסיף חשבונות.")
        else:
            unmapped = _cached_list_unmapped(holdings)
            if not unmapped:
                st.success("כל הניירות בתיק נפתרו לטיקר — אין צורך במיפוי נוסף.")
            for i, item in enumerate(unmapped):
                name = item.get("asset_name", "") or ""
                asset_id = item.get("asset_id", "") or ""
                with st.container(border=True):
                    mv = item.get("market_value")
                    st.markdown(
                        f"**{name}** · חשבון: {item.get('account', '—')}"
                        + (f" · שווי: ₪{mv:,.0f}" if mv else "")
                        + (f" · מספר נייר: {asset_id}" if asset_id else "")
                    )
                    c1, c2 = st.columns([2, 1])
                    ticker = c1.text_input(
                        "טיקר yfinance", key=f"map_ticker_{i}", placeholder="לדוגמה: ISCD.TA",
                    )
                    if c2.button("בדוק טיקר", key=f"map_check_{i}") and ticker.strip():
                        from analysis.symbols import verify_symbol
                        st.session_state[f"map_result_{i}"] = verify_symbol(ticker.strip())

                    check = st.session_state.get(f"map_result_{i}")
                    if check:
                        if check["ok"]:
                            st.success(
                                f"✅ {check['company_name']} · מחיר אחרון: {check['last_price']:.2f} "
                                "— בדוק שזו החברה הנכונה לפני השמירה."
                            )
                            if st.button("שמור מיפוי", key=f"map_save_{i}", type="primary"):
                                from analysis.portfolio_bridge import add_symbol_mapping
                                add_symbol_mapping(name, ticker.strip(), asset_id)
                                st.session_state.pop(f"map_result_{i}", None)
                                st.cache_data.clear()
                                st.success("המיפוי נשמר.")
                                st.rerun()
                        else:
                            st.error(f"❌ לא נמצאו נתונים לטיקר הזה: {check.get('error', '')}")


# ═════════════════════════════════════════════════════════════════════════════
# ניתוב
# ═════════════════════════════════════════════════════════════════════════════
if page == "📊 לוח מחוונים":
    page_dashboard()
elif page == "📈 היסטוריה":
    page_history()
elif page == "📤 העלאה":
    page_upload()
elif page == "🤖 המלצות AI":
    page_ai()
elif page == "🧭 ניתוח השקעות":
    page_invest_analysis()
elif page == "⚙️ הגדרות":
    page_settings()
