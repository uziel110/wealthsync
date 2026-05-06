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

# ═════════════════════════════════════════════════════════════════════════════
# קונפיגורציה
# ═════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="WealthSync",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
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

/* ─── Inputs ─────────────────────────────────────────── */
.stTextInput label, .stNumberInput label, .stSelectbox label,
.stFileUploader label, .stSlider label, .stRadio > label,
.stForm label, .stMultiSelect label, p {
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
    margin=dict(t=24, b=24, l=16, r=16),
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
}

TYPE_COLORS = {
    "etf":     "#2563EB",
    "fund":    "#D97706",
    "pension": "#7C3AED",
    "stock":   "#059669",
}


def classify_asset(row: pd.Series) -> str:
    if str(row.get("source", "")).strip() == "ידני":
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
        ["📊 לוח מחוונים", "📈 היסטוריה", "📤 העלאה", "🤖 המלצות AI", "⚙️ הגדרות"],
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

    accounts   = sorted(df["account"].unique().tolist())
    type_opts  = sorted(df["asset_type"].unique().tolist())
    type_labels = {k: TYPE_HE.get(k, k) for k in type_opts}

    with st.container():
        st.markdown('<div class="ws-filter-bar">', unsafe_allow_html=True)
        fc1, fc2 = st.columns([1, 1])
        with fc1:
            sel_accounts = st.multiselect(
                "סינון לפי חשבון",
                options=accounts,
                default=accounts,
                key="filter_accounts",
            )
        with fc2:
            sel_types = st.multiselect(
                "סינון לפי סוג נכס",
                options=list(type_labels.values()),
                default=list(type_labels.values()),
                key="filter_types",
            )
        st.markdown('</div>', unsafe_allow_html=True)

    # reverse-map Hebrew labels → keys
    rev = {v: k for k, v in type_labels.items()}
    sel_type_keys = [rev[l] for l in sel_types if l in rev]

    filtered = df[
        df["account"].isin(sel_accounts) &
        df["asset_type"].isin(sel_type_keys)
    ]
    return filtered


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
        by_type = (
            df.groupby("asset_type")["market_value"].sum()
            .reset_index()
            .sort_values("market_value", ascending=False)
        )
        by_type["label"] = by_type["asset_type"].map(TYPE_HE)
        by_type["color"] = by_type["asset_type"].map(TYPE_COLORS)

        fig_type = go.Figure(go.Pie(
            labels=by_type["label"],
            values=by_type["market_value"],
            hole=0.52,
            marker_colors=by_type["color"].tolist(),
            textinfo="percent",
            textposition="inside",
            hovertemplate="<b>%{label}</b><br>₪%{value:,.0f}<br>%{percent}<extra></extra>",
        ))
        fig_type.update_layout(
            **PLOTLY_LAYOUT,
            height=300,
            showlegend=True,
            legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.12, font_size=11),
            annotations=[dict(
                text=f"₪{total/1e6:.1f}M" if total >= 1e6 else f"₪{total:,.0f}",
                font_size=15, font_color="#1E293B", showarrow=False,
            )],
        )
        st.plotly_chart(fig_type, use_container_width=True)

    with col_r:
        section_header("הקצאה לפי חשבון")
        by_acc = (
            df.groupby("account")["market_value"].sum()
            .reset_index()
            .sort_values("market_value", ascending=False)
        )
        fig_acc = go.Figure(go.Pie(
            labels=by_acc["account"],
            values=by_acc["market_value"],
            hole=0.52,
            marker_colors=PALETTE[:len(by_acc)],
            textinfo="percent",
            textposition="inside",
            hovertemplate="<b>%{label}</b><br>₪%{value:,.0f}<br>%{percent}<extra></extra>",
        ))
        fig_acc.update_layout(
            **PLOTLY_LAYOUT,
            height=300,
            showlegend=True,
            legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.12, font_size=11),
            annotations=[dict(
                text=f"{df['account'].nunique()} חשבונות",
                font_size=13, font_color="#64748B", showarrow=False,
            )],
        )
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
    section_header("רווח / הפסד לפי נייר ערך")

    df_gl = df.sort_values("gain_loss")
    colors_gl = [TYPE_COLORS.get(t, "#94A3B8") if v >= 0 else "#EF4444"
                 for v, t in zip(df_gl["gain_loss"], df_gl["asset_type"])]

    fig_gl = go.Figure(go.Bar(
        x=df_gl["gain_loss"],
        y=df_gl["asset_name"],
        orientation="h",
        marker_color=colors_gl,
        text=[
            f"₪{v:,.0f}  ({p:+.1f}%)"
            for v, p in zip(df_gl["gain_loss"], df_gl["gain_pct"].fillna(0))
        ],
        textposition="auto",
        textfont_size=11,
        hovertemplate="<b>%{y}</b><br>₪%{x:,.0f}<extra></extra>",
    ))
    fig_gl.update_layout(
        **PLOTLY_LAYOUT,
        height=max(320, len(df_gl) * 36),
        xaxis=dict(
            showgrid=True, gridcolor="#F1F5F9",
            zeroline=True, zerolinecolor="#94A3B8", zerolinewidth=1.5,
            tickformat="₪,.0f",
        ),
        yaxis=dict(showgrid=False),
    )
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
        yaxis=dict(title="שווי (₪)", showgrid=True, gridcolor="#F1F5F9",
                   tickformat="₪,.0f"),
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
            "תמונות מצב נשמרות אוטומטית בכל פעם שמעלים קובץ או מזינים נתונים. "
            "לחץ על הכפתור למטה כדי לצלם את המצב הנוכחי."
        )
        _snapshot_button()
        return

    # ── record today manually if needed ──────────────────────────────────────
    _snapshot_button()

    # ── validate structure ────────────────────────────────────────────────────
    if "snapshot_date" not in df_snap.columns:
        st.error(
            "גיליון ה-snapshots אינו תקין (חסרה עמודת snapshot_date).\n"
            "לחץ על 📸 צלם תמונת מצב היום כדי לאתחל מחדש."
        )
        _snapshot_button()
        return

    # ── parse & validate dates ────────────────────────────────────────────────
    df_snap["snapshot_date"] = pd.to_datetime(df_snap["snapshot_date"], errors="coerce")
    df_snap = df_snap.dropna(subset=["snapshot_date"])
    if df_snap.empty:
        st.warning("נתוני תאריכים לא תקינים בהיסטוריה.")
        return

    # ── filter bar ────────────────────────────────────────────────────────────
    section_header("סינון")
    fc1, fc2, fc3 = st.columns(3)

    all_accounts = sorted(df_snap["account"].dropna().unique().tolist())
    all_types    = sorted(df_snap["asset_type"].dropna().unique().tolist())
    date_min     = df_snap["snapshot_date"].min().date()
    date_max     = df_snap["snapshot_date"].max().date()

    with fc1:
        sel_accounts = st.multiselect("חשבון", all_accounts, default=all_accounts, key="hist_acc")
    with fc2:
        type_labels  = {k: TYPE_HE.get(k, k) for k in all_types}
        sel_type_lbl = st.multiselect(
            "סוג נכס",
            list(type_labels.values()),
            default=list(type_labels.values()),
            key="hist_type",
        )
        rev = {v: k for k, v in type_labels.items()}
        sel_types = [rev[l] for l in sel_type_lbl if l in rev]
    with fc3:
        date_range = st.date_input(
            "טווח תאריכים",
            value=(date_min, date_max),
            min_value=date_min,
            max_value=date_max,
            key="hist_dates",
        )

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
            fillcolor=color.replace("#", "rgba(").rstrip(")") + ",0.6)"
                if color.startswith("#") else color,
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

    # ── Chart 4: gain/loss over time ──────────────────────────────────────────
    section_header("רווח / הפסד לא ממומש לאורך זמן")

    colors_gl = ["#059669" if v >= 0 else "#DC2626" for v in daily_total["gain_loss"]]
    fig_gl = go.Figure(go.Bar(
        x=daily_total["snapshot_date"],
        y=daily_total["gain_loss"],
        marker_color=colors_gl,
        hovertemplate="%{x|%d/%m/%Y}<br>₪%{y:,.0f}<extra></extra>",
    ))
    fig_gl.update_layout(
        **PLOTLY_LAYOUT,
        height=260,
        xaxis=dict(showgrid=False, tickformat="%d/%m/%y"),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickformat="₪,.0f",
                   zeroline=True, zerolinecolor="#94A3B8"),
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


def _snapshot_button() -> None:
    """Button to manually capture today's portfolio state as a snapshot."""
    df_cur = st.session_state.holdings
    if df_cur.empty:
        return
    c1, _ = st.columns([1, 4])
    with c1:
        if st.button("📸 צלם תמונת מצב היום", use_container_width=True):
            try:
                from sheets.gsheets import append_snapshot
                append_snapshot(enrich(df_cur))
                st.success("✓ תמונת מצב נשמרה.")
                st.rerun()
            except Exception as exc:
                st.error(f"שגיאה: {exc}")


# ═════════════════════════════════════════════════════════════════════════════
# דף: העלאה
# ═════════════════════════════════════════════════════════════════════════════
def page_upload() -> None:
    page_header("📤", "העלאת קובץ החזקות", "פרסר אקסל אוטומטי · IBI/פסגות · הפועלים · לאומי טרייד · הזנה ידנית")

    source = st.selectbox(
        "בחר מקור נתונים",
        ["IBI / פסגות", "בנק הפועלים", "לאומי טרייד", "הראל / גמל — הזנה ידנית"],
    )
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    if source == "IBI / פסגות":
        _upload_ibi()
    elif source == "בנק הפועלים":
        _upload_generic(
            bank_name="בנק הפועלים",
            default_account="הפועלים",
            parser_fn=parse_hapoalim,
            tip="ייצא מהאתר: תיק ניירות ערך ← ייצוא ל-Excel",
        )
    elif source == "לאומי טרייד":
        _leumi_upload_or_manual()
    elif source == "הראל / גמל — הזנה ידנית":
        _manual_entry_harel()


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

    # show existing rows for this account so user can see what's already entered
    existing_all = st.session_state.holdings
    existing_acc = (
        existing_all[existing_all["account"] == account_name]
        if not existing_all.empty else pd.DataFrame()
    )
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

    with st.form(f"{form_key}_manual_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            asset_name = st.text_input("שם הנייר", placeholder="לדוגמה: מניות אפל / קרן מחקה ת\"א 125")
            asset_id   = st.text_input("מספר נייר / סימבול", placeholder="לדוגמה: 662577 / AAPL")
            quantity   = st.number_input("כמות", min_value=0.0, step=1.0, format="%.4f")
        with c2:
            cost_basis   = st.number_input("עלות רכישה (₪)", min_value=0.0, step=100.0,
                                           help="סך הכסף ששולם בעת הרכישה")
            market_value = st.number_input("שווי נוכחי (₪)", min_value=0.0, step=100.0,
                                           help="שווי השוק היום")

        submitted = st.form_submit_button("➕ הוסף נייר לתיק", type="primary", use_container_width=True)

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
        _save_holdings(pd.concat([existing_other, existing_acc, row], ignore_index=True))
        st.success(f"✓ **{asset_name}** נוסף לחשבון {account_name}.")
        st.rerun()
    elif submitted:
        st.warning("נא להזין שם נייר.")


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
    st.dataframe(
        _display(df, show_cols).style.format({
            "כמות":           "{:,.4f}",
            "עלות (₪)":       "₪{:,.2f}",
            "שווי נוכחי (₪)": "₪{:,.2f}",
        }),
        use_container_width=True, height=300,
    )

    st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
    if st.button("✅ הוסף לתיק ושמור", type="primary", key=f"save_{bank_name}"):
        existing = st.session_state.holdings
        if not existing.empty:
            existing = existing[existing["account"] != account_name]
        _save_holdings(pd.concat([existing, df], ignore_index=True))
        st.success(f"✓ חשבון **{account_name}** נוסף לתיק ונשמר.")


def _upload_ibi() -> None:
    section_header("העלאת קובץ IBI / פסגות")

    st.markdown("""
    <div class="ws-card" style="margin-bottom:1rem;">
      <div style="font-size:.82rem;color:#64748B;line-height:1.8;">
        ייצא את תיק ההשקעות מפלטפורמת IBI/פסגות כקובץ Excel והעלה אותו כאן.<br>
        המערכת מזהה אוטומטית את הפורמט (Portfolio החדש או IBI הישן) ומנרמלת את הנתונים.
      </div>
    </div>""", unsafe_allow_html=True)

    account_name = st.text_input("שם החשבון", value="פסגות",
                                 help="השם שיופיע בלוח המחוונים.")
    uploaded = st.file_uploader("גרור לכאן קובץ Excel או לחץ לבחירה", type=["xlsx"])

    if uploaded is None:
        return

    with st.spinner("מנתח ומנרמל נתונים…"):
        try:
            df = parse_ibi(io.BytesIO(uploaded.read()), account_name=account_name)
            df = enrich(df)
        except Exception as exc:
            st.error(f"שגיאה בפענוח: {exc}")
            return

    total_val  = df["market_value"].sum()
    total_cost = df["cost_basis"].sum()
    gain       = total_val - total_cost

    m1, m2, m3 = st.columns(3)
    m1.metric("ניירות ערך שפוענחו", len(df))
    m2.metric("שווי כולל בקובץ",   f"₪{total_val:,.0f}")
    m3.metric("רווח / הפסד",       f"₪{gain:,.0f}",
              f"{(gain/total_cost*100) if total_cost else 0:+.1f}%")

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    show_cols = ["account", "asset_type", "asset_name", "asset_id",
                 "quantity", "cost_basis", "market_value"]
    st.dataframe(
        _display(df, show_cols).style.format({
            "כמות":           "{:,.4f}",
            "עלות (₪)":       "₪{:,.2f}",
            "שווי נוכחי (₪)": "₪{:,.2f}",
        }),
        use_container_width=True, height=300,
    )

    st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
    if st.button("✅ הוסף לתיק ושמור", type="primary"):
        existing = st.session_state.holdings
        if not existing.empty:
            existing = existing[existing["account"] != account_name]
        _save_holdings(pd.concat([existing, df], ignore_index=True))
        st.success(f"✓ חשבון **{account_name}** נוסף לתיק ונשמר.")


def _manual_entry_harel() -> None:
    section_header("פנסיה / גמל — הזנה ידנית")
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
elif page == "⚙️ הגדרות":
    page_settings()
