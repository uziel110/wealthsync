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


def with_symbols(
    df: pd.DataFrame, overrides: dict[str, str] | None = None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    מפצל את התיק לשתי טבלאות: ניירות שנפתרו לטיקר yfinance (resolved)
    וניירות שלא ניתן למפות (unresolved — בד"כ פנסיה/גמל/מספר נייר ת"א בלי
    מיפוי שם, סטטי או שנוסף מהאתר).
    """
    if df.empty:
        return df, df
    symbols = df.apply(
        lambda r: resolve_symbol(r.get("asset_name", ""), r.get("asset_id"), overrides=overrides),
        axis=1,
    )
    resolved = df.assign(symbol=symbols)
    return resolved[resolved["symbol"].notna()].copy(), resolved[resolved["symbol"].isna()].copy()


def _overrides_from_df(df: pd.DataFrame) -> dict[str, str]:
    """
    בונה מילון מיפויים מתוך טבלת symbol_overrides. כל מיפוי נכנס פעמיים —
    לפי שם מנורמל ולפי מספר נייר (asset_id), אם קיים — כך ש-resolve_symbol
    יוכל להתאים גם כששם הנייר משתנה מעט בין ברוקרים/ייצואים אבל מספר הנייר
    נשאר קבוע (ראו symbols.resolve_symbol). מופרד מ-load_symbol_overrides
    כדי שניתן לבדוק אותו בטסטים בלי תלות ב-sheets.gsheets/gspread.
    """
    if df.empty or "name" not in df.columns or "symbol" not in df.columns:
        return {}
    from .symbols import _normalize
    overrides: dict[str, str] = {}
    for _, r in df.iterrows():
        symbol = str(r.get("symbol", "")).strip().upper()
        if not symbol:
            continue
        name = str(r.get("name", "")).strip()
        if name:
            overrides[_normalize(name)] = symbol
        asset_id = str(r.get("asset_id", "")).strip()
        if asset_id:
            overrides[_normalize(asset_id)] = symbol
    return overrides


def load_symbol_overrides() -> dict[str, str]:
    """
    טוען מיפויים שהמשתמש הוסיף מהאתר (גיליון symbol_overrides) — בנוסף
    לטבלה הסטטית NAME_TO_SYMBOL. נכשל בשקט ומחזיר {} אם Sheets לא נגיש
    (למשל בטסטים/סקריפטים שרצים בלי streamlit/gspread).
    """
    try:
        from sheets.gsheets import read_symbol_overrides
        df = read_symbol_overrides()
    except Exception:
        return {}
    return _overrides_from_df(df)


def add_symbol_mapping(asset_name: str, symbol: str, asset_id: str = "") -> dict:
    """
    מאמתת טיקר מול yfinance (verify_symbol) ושומרת את המיפוי בגיליון
    symbol_overrides רק אם האימות הצליח — לא ניתן להוסיף טיקר לא מאומת
    מהאתר, אותו עיקרון שחל על NAME_TO_SYMBOL הסטטי (ראו analysis/symbols.py
    ופרשת NVMI.TA/NXSN.TA ב-CLAUDE.md). מחזירה את תוצאת verify_symbol כך
    שה-UI יציג למשתמש את שם החברה לאישור.
    """
    from .symbols import verify_symbol, _normalize
    check = verify_symbol(symbol)
    if check["ok"]:
        from sheets.gsheets import save_symbol_override
        save_symbol_override(_normalize(asset_name), symbol.strip().upper(), asset_id)
    return check


def list_unmapped_assets(df: pd.DataFrame | None = None) -> list[dict]:
    """
    רשימה ייחודית (לפי שם נייר) של נכסים בתיק שלא נפתרו לטיקר yfinance —
    לטאב "מיפוי טיקרים" באתר, כך שהמשתמש לא צריך לעבור על כל ההחזקות בנפרד.
    """
    if df is None:
        df = load_holdings()
    if df.empty:
        return []
    overrides = load_symbol_overrides()
    _, unresolved = with_symbols(df, overrides=overrides)
    if unresolved.empty:
        return []
    cols = [c for c in ("asset_name", "asset_id", "account", "market_value") if c in unresolved.columns]
    dedup = unresolved[cols].drop_duplicates(subset=["asset_name"]) if "asset_name" in cols else unresolved[cols]
    return dedup.to_dict("records")


def suggest_stop_target(snap: dict, entry: float) -> tuple[float, float]:
    """
    מציע סטופ/יעד לפי ATR — אין בסכימה הקיימת שדות stop/target מאוחסנים,
    אז הכלי מציע אותם בכל ריצה (באותה לוגיקה כמו buy_analysis).
    """
    atr = snap.get("atr") or entry * 0.03
    stop = round(entry - engine.ATR_STOP_MULT * atr, 2)
    target = round(max(snap.get("resistance") or 0, entry + engine.ATR_TARGET_MULT * atr), 2)
    return stop, target


def _num(x) -> float | None:
    """המרה בטוחה לסקלר float (מתעלמת מפסיקים/ריק/NaN)."""
    try:
        v = float(str(x).replace(",", ""))
    except (TypeError, ValueError):
        return None
    return None if pd.isna(v) else v


def proxy_levels(snap: dict, price: float) -> tuple[float, float]:
    """
    סטופ/יעד ביחידות של ``price`` עצמו (המטבע של ההחזקה האמיתית), כשהתנודתיות
    (ATR) ורמת ההתנגדות של הפרוקסי נלקחות כ**אחוזים** — כך שנייר שקלי שממופה
    לפרוקסי דולרי (GLD/SPY) מקבל סטופ/יעד הגיוניים בש"ח במקום לערבב יחידות
    (₪ מול $). אחוזים הם חסרי-מטבע, אז הסיגנל תקף בכל מקרה.
    """
    ref = snap.get("price") or price
    atr_pct = ((snap.get("atr") or ref * 0.03) / ref) if ref else 0.03
    res = snap.get("resistance")
    res_pct = max((res - ref) / ref, 0.0) if (res and ref) else 0.0
    stop = round(price * (1 - engine.ATR_STOP_MULT * atr_pct), 2)
    target = round(price * (1 + max(engine.ATR_TARGET_MULT * atr_pct, res_pct)), 2)
    return stop, target


def review_portfolio(df: pd.DataFrame | None = None) -> dict:
    """
    סוקרת את כל ההחזקות הניתנות לניתוח (יש להן טיקר yfinance שנפתר).
    מחזירה {"reviewed": [...], "unresolved": [...]}.
    """
    if df is None:
        df = load_holdings()
    overrides = load_symbol_overrides()
    resolved, unresolved = with_symbols(df, overrides=overrides)

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
        # רווח/הפסד והמחירים מחושבים מההחזקה האמיתית (במטבע שלה), בעוד הפרוקסי
        # מספק רק תנודתיות/רמות כאחוזים — כך נייר שקלי שממופה לפרוקסי דולרי
        # (GLD/SPY) מקבל מספרים שקליים נכונים במקום לערבב ₪ מול $.
        qty  = _num(row.get("quantity"))
        cost = _num(row.get("cost_basis"))
        mv   = _num(row.get("market_value"))
        real_price = (mv / qty) if (mv and qty) else (entry or snap["price"])
        pnl_pct = ((mv - cost) / cost * 100) if (mv is not None and cost) else None

        sug_stop, sug_target = proxy_levels(snap, real_price)
        # אי-התאמת יחידות/מטבע: מחיר הכניסה (יחידות אמיתיות) מול מחיר הפרוקסי
        is_proxy = bool(
            entry and snap.get("price")
            and max(entry, snap["price"]) / max(min(entry, snap["price"]), 1e-9) > 5
        )

        result = engine.review_holding(symbol, snap=snap, pnl_pct=pnl_pct)
        result["account"] = row.get("account")
        result["asset_name"] = row.get("asset_name")
        result["quantity"] = row.get("quantity")
        result["entry_price"] = round(entry, 2) if entry else None
        result["current_price"] = round(real_price, 2) if real_price else None
        result["suggested_stop"] = sug_stop
        result["suggested_target"] = sug_target
        result["is_proxy"] = is_proxy
        reviewed.append(result)

    unresolved_list = [
        {"account": r.get("account"), "asset_name": r.get("asset_name"),
         "asset_id": r.get("asset_id"), "market_value": r.get("market_value")}
        for _, r in unresolved.iterrows()
    ] if not unresolved.empty else []

    return {"reviewed": reviewed, "unresolved": unresolved_list}


def run_buy_analysis(query: str) -> dict:
    """query יכול להיות שם עברי מהמיפוי (סטטי או שנוסף מהאתר) או טיקר ישירות."""
    overrides = load_symbol_overrides()
    symbol = resolve_symbol(query, overrides=overrides) or query.strip().upper()
    return engine.buy_analysis(symbol)


def run_allocate_deposit(amount: float, candidates: list[str]) -> dict:
    """
    candidates: שמות עבריים מהמיפוי או טיקרים. מועמדים שלא ניתן לפתור
    מוחזרים בנפרד תחת "unresolved" כדי שהמשתמש ידע למה הם לא נכללו.
    """
    overrides = load_symbol_overrides()
    resolved, unresolved = [], []
    for c in candidates:
        symbol = resolve_symbol(c, overrides=overrides) or (c.strip().upper() if _looks_like_ticker(c) else None)
        if symbol:
            resolved.append(symbol)
        else:
            unresolved.append(c)

    result = engine.allocate_deposit(amount, resolved)
    result["unresolved"] = unresolved
    return result
