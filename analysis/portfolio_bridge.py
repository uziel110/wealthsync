# -*- coding: utf-8 -*-
"""
analysis/portfolio_bridge.py — שכבת חיבור בין נתוני התיק האמיתיים (Google
Sheets, דרך sheets.gsheets) לבין מנוע הניתוח (analysis.engine).

קריאה בלבד מהתיק — לא כותב, לא נוגע ב-app.py ובלוגיקת השמירה הקיימת.
"""
from __future__ import annotations

import pandas as pd

import re

from . import engine
from .symbols import resolve_symbol

_TICKER_RE = re.compile(r"[A-Za-z0-9.\-]{1,10}")


def _looks_like_ticker(s: str) -> bool:
    """True if s is already shaped like a yfinance ticker (e.g. AAPL, POLI.TA)."""
    s = s.strip()
    return bool(s) and bool(_TICKER_RE.fullmatch(s))


def _to_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False), errors="coerce"
    )


def load_holdings(worksheet_name: str = "holdings") -> pd.DataFrame:
    """טוען את גיליון ה-holdings מ-Google Sheets (מקור האמת היחיד)."""
    from sheets.gsheets import read_sheet
    df = read_sheet(worksheet_name)
    if df.empty:
        return df
    for col in ("quantity", "cost_basis", "market_value"):
        if col in df.columns:
            df[col] = _to_num(df[col])
    return df


def entry_price(row: pd.Series) -> float | None:
    """מחיר כניסה ממוצע = עלות / כמות (אין שדה entry_price נפרד בסכימה)."""
    qty = row.get("quantity")
    cost = row.get("cost_basis")
    if not qty or pd.isna(qty) or qty == 0 or cost is None or pd.isna(cost):
        return None
    return float(cost) / float(qty)


def with_symbols(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    מפצל את התיק לשתי טבלאות: ניירות שנפתרו לטיקר yfinance (resolved)
    וניירות שלא ניתן למפות (unresolved — בד"כ פנסיה/גמל/מספר נייר ת"א בלי
    מיפוי שם ב-analysis/symbols.py).
    """
    if df.empty:
        return df, df
    symbols = df.apply(
        lambda r: resolve_symbol(r.get("asset_name", ""), r.get("asset_id")), axis=1
    )
    resolved = df.assign(symbol=symbols)
    return resolved[resolved["symbol"].notna()].copy(), resolved[resolved["symbol"].isna()].copy()


def suggest_stop_target(snap: dict, entry: float) -> tuple[float, float]:
    """
    מציע סטופ/יעד לפי ATR — אין בסכימה הקיימת שדות stop/target מאוחסנים,
    אז הכלי מציע אותם בכל ריצה (באותה לוגיקה כמו buy_analysis).
    """
    atr = snap.get("atr") or entry * 0.03
    stop = round(entry - engine.ATR_STOP_MULT * atr, 2)
    target = round(max(snap.get("resistance") or 0, entry + engine.ATR_TARGET_MULT * atr), 2)
    return stop, target


def review_portfolio(df: pd.DataFrame | None = None) -> dict:
    """
    סוקרת את כל ההחזקות הניתנות לניתוח (יש להן טיקר yfinance שנפתר).
    מחזירה {"reviewed": [...], "unresolved": [...]}.
    """
    if df is None:
        df = load_holdings()
    resolved, unresolved = with_symbols(df)

    reviewed = []
    for _, row in resolved.iterrows():
        symbol = row["symbol"]
        entry = entry_price(row)
        snap = engine.snapshot(symbol)
        if snap is None:
            reviewed.append({
                "account": row.get("account"), "asset_name": row.get("asset_name"),
                "symbol": symbol, "action": "no_data", "reasons": ["אין נתוני שוק"],
            })
            continue
        sug_stop, sug_target = suggest_stop_target(snap, entry or snap["price"])
        result = engine.review_holding(symbol, entry_price=entry,
                                        stop=sug_stop, target=sug_target, snap=snap)
        result["account"] = row.get("account")
        result["asset_name"] = row.get("asset_name")
        result["quantity"] = row.get("quantity")
        result["entry_price"] = round(entry, 2) if entry else None
        result["suggested_stop"] = sug_stop
        result["suggested_target"] = sug_target
        reviewed.append(result)

    unresolved_list = [
        {"account": r.get("account"), "asset_name": r.get("asset_name"),
         "asset_id": r.get("asset_id"), "market_value": r.get("market_value")}
        for _, r in unresolved.iterrows()
    ] if not unresolved.empty else []

    return {"reviewed": reviewed, "unresolved": unresolved_list}


def run_buy_analysis(query: str) -> dict:
    """query יכול להיות שם עברי מהמיפוי (analysis/symbols.py) או טיקר ישירות."""
    symbol = resolve_symbol(query) or query.strip().upper()
    return engine.buy_analysis(symbol)


def run_allocate_deposit(amount: float, candidates: list[str]) -> dict:
    """
    candidates: שמות עבריים מהמיפוי או טיקרים. מועמדים שלא ניתן לפתור
    מוחזרים בנפרד תחת "unresolved" כדי שהמשתמש ידע למה הם לא נכללו.
    """
    resolved, unresolved = [], []
    for c in candidates:
        symbol = resolve_symbol(c) or (c.strip().upper() if _looks_like_ticker(c) else None)
        if symbol:
            resolved.append(symbol)
        else:
            unresolved.append(c)

    result = engine.allocate_deposit(amount, resolved)
    result["unresolved"] = unresolved
    return result
