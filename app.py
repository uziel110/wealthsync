"""
WealthSync — מאגד השקעות אישי
עיצוב: Claude Design System · Hebrew-first · RTL · Heebo font
"""

from __future__ import annotations
import io
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from parsers.ibi_parser import parse_ibi

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


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Add asset_type + gain_loss columns if not present."""
    df = df.copy()
    if "asset_type" not in df.columns:
        df["asset_type"] = df.apply(classify_asset, axis=1)
    if "gain_loss" not in df.columns:
        df["gain_loss"] = df["market_value"] - df["cost_basis"]
    if "gain_pct" not in df.columns:
        df["gain_pct"] = df["gain_loss"] / df["cost_basis"].replace(0, float("nan")) * 100
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
            for _c in ("quantity", "cost_basis", "market_value"):
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
    st.session_state.holdings = df
    try:
        from sheets.gsheets import upsert_holdings
        upsert_holdings(df)
    except Exception:
        pass


COL_LABELS = {
    "account":    "חשבון",
    "asset_name": "שם נייר",
    "asset_id":   "מספר נייר",
    "asset_type": "סוג",
    "quantity":   "כמות",
    "cost_basis": "עלות (₪)",
    "market_value": "שווי נוכחי (₪)",
    "gain_loss":  "רווח/הפסד (₪)",
    "gain_pct":   "תשואה %",
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
        ["📊 לוח מחוונים", "📤 העלאה", "⚙️ הגדרות"],
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

    col_a, col_b, col_c = st.columns([2, 2, 3])
    with col_a:
        years = st.slider("אופק השקעה (שנים)", 1, 30, 10)
    with col_b:
        cagr = st.slider("תשואה שנתית צפויה (%)", 1, 20, 7)
    with col_c:
        fv = total * ((1 + cagr / 100) ** years)
        st.metric(
            f"שווי צפוי בעוד {years} שנים",
            f"₪{fv:,.0f}",
            f"+₪{fv - total:,.0f}  ({((fv/total)-1)*100:.1f}%)",
        )

    proj = pd.DataFrame({
        "שנה":  range(years + 1),
        "שווי צפוי": [total * ((1 + cagr/100)**y) for y in range(years + 1)],
        "ערך נוכחי": [total] * (years + 1),
    })
    fig_proj = go.Figure()
    fig_proj.add_trace(go.Scatter(
        x=proj["שנה"], y=proj["שווי צפוי"],
        mode="lines+markers", name="שווי צפוי",
        line=dict(color="#2563EB", width=2.5), marker=dict(size=5),
        fill="tozeroy", fillcolor="rgba(37,99,235,.08)",
        hovertemplate="שנה %{x}: ₪%{y:,.0f}<extra></extra>",
    ))
    fig_proj.add_trace(go.Scatter(
        x=proj["שנה"], y=proj["ערך נוכחי"],
        mode="lines", name="ערך נוכחי",
        line=dict(color="#94A3B8", width=1.5, dash="dash"),
        hovertemplate="₪%{y:,.0f}<extra></extra>",
    ))
    fig_proj.update_layout(
        **PLOTLY_LAYOUT,
        height=300,
        xaxis=dict(title="שנה", showgrid=True, gridcolor="#F1F5F9", dtick=max(1, years//10)),
        yaxis=dict(title="שווי (₪)", showgrid=True, gridcolor="#F1F5F9", tickformat="₪,.0f"),
        legend=dict(orientation="h", x=0, y=1.14, font_size=12),
    )
    st.plotly_chart(fig_proj, use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# דף: העלאה
# ═════════════════════════════════════════════════════════════════════════════
def page_upload() -> None:
    page_header("📤", "העלאת קובץ החזקות", "פרסר אקסל אוטומטי מ-IBI/פסגות · הזנה ידנית")

    source = st.selectbox(
        "בחר מקור נתונים",
        ["IBI / פסגות", "בנק לאומי (בקרוב)", "בנק הפועלים (בקרוב)", "הראל — הזנה ידנית"],
    )
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    if source == "IBI / פסגות":
        _upload_ibi()
    elif source == "הראל — הזנה ידנית":
        _manual_entry_harel()
    else:
        st.info(f"הפרסר עבור **{source}** עדיין בפיתוח.")


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
    section_header("קרן פנסיה / גמל — הזנה ידנית")

    with st.form("harel_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            asset_name   = st.text_input("שם הקרן / המסלול")
            quantity     = st.number_input("יחידות / יתרה צבורה", min_value=0.0, step=0.01)
        with c2:
            cost_basis   = st.number_input("סך הפקדות (₪)", min_value=0.0, step=100.0)
            market_value = st.number_input("שווי נוכחי (₪)", min_value=0.0, step=100.0)
        submitted = st.form_submit_button("➕ הוסף לתיק", type="primary", use_container_width=True)

    if submitted and asset_name:
        row = pd.DataFrame([{
            "account": "הראל", "asset_name": asset_name, "asset_id": "",
            "quantity": quantity, "cost_basis": cost_basis,
            "market_value": market_value, "source": "ידני",
        }])
        _save_holdings(pd.concat([st.session_state.holdings, row], ignore_index=True))
        st.success(f"✓ הקרן **{asset_name}** נוספה ונשמרה.")
    elif submitted:
        st.warning("נא להזין שם קרן.")


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
# ניתוב
# ═════════════════════════════════════════════════════════════════════════════
if page == "📊 לוח מחוונים":
    page_dashboard()
elif page == "📤 העלאה":
    page_upload()
elif page == "⚙️ הגדרות":
    page_settings()
