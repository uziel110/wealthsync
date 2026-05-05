"""
Live price fetching via yfinance.
Prices are cached for 15 minutes to avoid rate-limiting.
"""

from __future__ import annotations

import streamlit as st
import yfinance as yf


@st.cache_data(ttl=900, show_spinner=False)
def get_price(ticker: str) -> float | None:
    """
    Return the latest closing price for `ticker`, or None if unavailable.
    Israeli securities on TASE end with '.TA' (e.g. 'TEVA.TA').
    """
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="1d")
        if not hist.empty:
            return float(hist["Close"].iloc[-1])
    except Exception:
        pass
    return None
