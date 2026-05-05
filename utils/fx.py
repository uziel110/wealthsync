"""
USD → ILS exchange rate helper.
Primary source: yfinance (USDILS=X ticker).
Falls back to a hard-coded rate if the network call fails.
"""

from __future__ import annotations

import streamlit as st
import yfinance as yf

_FALLBACK_RATE = 3.70


@st.cache_data(ttl=3600, show_spinner=False)
def usd_to_ils(amount_usd: float = 1.0) -> float:
    """Return `amount_usd` converted to ILS at the current mid-market rate."""
    rate = _fetch_rate()
    return amount_usd * rate


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_rate() -> float:
    try:
        ticker = yf.Ticker("USDILS=X")
        hist = ticker.history(period="1d")
        if not hist.empty:
            return float(hist["Close"].iloc[-1])
    except Exception:
        pass
    return _FALLBACK_RATE
