# -*- coding: utf-8 -*-
"""
analysis/symbols.py — מיפוי שם נייר (כפי שמופיע בתיק) → טיקר yfinance.

asset_id בתיק *אינו* טיקר אמין: בפסגות/הפועלים/לאומי הוא לרוב מספר נייר
ת"א (מספר מסחר), לא סימבול. כדי להפעיל ניתוח yfinance על מניה ישראלית
חייבים למפות את השם לטיקר (לרוב <SYMBOL>.TA).

איך מוסיפים נייר חדש:
    1. הוסף שורה ל-NAME_TO_SYMBOL: "שם כפי שמופיע בתיק": "TICKER.TA"
    2. הרץ `python tools/verify_symbols.py` — זה מאחזר מ-yfinance את שם
       החברה (longName) בפועל ומציג אותו לצידך, כדי שתאשר שהטיקר נכון
       *לפני* שמסתמכים עליו (לדוגמה: NVMI.TA הוא Nova Ltd, לא נקסט ויזן —
       הטיקר הנכון לנקסט ויזן הוא NXSN.TA. אומת ב-2026-06-17).

מפתחות מנורמלים (ללא תווי RTL/LTR נסתרים, strip, ללא רישיות — הנירמול
קורה בזמן ריצה ב-resolve_symbol, לא צריך לנרמל כשמוסיפים שורה).
"""
from __future__ import annotations

import re

# שם → טיקר yfinance. מוּמת מול yfinance.Ticker(...).info["longName"] (ראו הערה למעלה).
NAME_TO_SYMBOL: dict[str, str] = {
    "ישראכרט": "ISCD.TA",
    "נקסט ויזן": "NXSN.TA",
    "נקסט ויזן סטביליזד סיסטמס": "NXSN.TA",
    "בנק הפועלים": "POLI.TA",
    "הפועלים": "POLI.TA",
    "בנק לאומי": "LUMI.TA",
    "לאומי": "LUMI.TA",
    "מזרחי טפחות": "MZTF.TA",
    "בנק מזרחי טפחות": "MZTF.TA",
    "בזק": "BEZQ.TA",
    "טבע": "TEVA",
    "נייס": "NICE",
}

# תווי RTL/LTR נסתרים שמודבקים בייצוא של בנקים ישראליים (אותו regex כמו enrich() ב-app.py)
_BIDI_CHARS = re.compile(r"[‎‏‪-‮⁦-⁩]")


def _normalize(name: str) -> str:
    return _BIDI_CHARS.sub("", str(name)).strip()


def resolve_symbol(
    asset_name: str, asset_id: str | None = None, overrides: dict[str, str] | None = None
) -> str | None:
    """
    מנסה לפתור שם/מספר נייר מהתיק לטיקר yfinance.

    סדר עדיפות:
      1. overrides — מיפויים שהמשתמש הוסיף מהאתר (ראו
         portfolio_bridge.load_symbol_overrides/add_symbol_mapping), כדי
         שיוכל לתקן מיפוי קיים בלי לחכות לדיפלוי קוד חדש
      2. התאמה מדויקת של asset_name (מנורמל) בטבלת NAME_TO_SYMBOL הסטטית
      3. אם asset_id מורכב מאותיות בלבד (כמו "AAPL", "TEVA") — מניחים
         שזה כבר טיקר yfinance תקני ומחזירים אותו כפי שהוא
      4. None — לא ניתן לפתור (למשל מספר נייר ת"א בלי מיפוי שם)
    """
    name = _normalize(asset_name)
    if overrides and name in overrides:
        return overrides[name]
    if name in NAME_TO_SYMBOL:
        return NAME_TO_SYMBOL[name]

    aid = _normalize(asset_id or "")
    if aid and aid.replace(".", "").isalpha() and len(aid) <= 10:
        return aid.upper()

    return None


def verify_symbol(symbol: str) -> dict:
    """
    מאמת טיקר מול yfinance בזמן ריצה: שולף שם חברה ומחיר אחרון.
    שימוש: tools/verify_symbols.py, או לפני הוספת מיפוי חדש לקבוע.
    מחזיר dict: {"symbol", "ok", "company_name", "last_price", "error"}.
    """
    try:
        import yfinance as yf
        t = yf.Ticker(symbol)
        hist = t.history(period="5d")
        if hist.empty:
            return {"symbol": symbol, "ok": False, "company_name": None,
                     "last_price": None, "error": "אין נתוני מסחר"}
        price = float(hist["Close"].iloc[-1])
        try:
            info = t.info
            company_name = info.get("longName") or info.get("shortName")
        except Exception:
            company_name = None
        return {"symbol": symbol, "ok": True, "company_name": company_name,
                 "last_price": price, "error": None}
    except Exception as exc:
        return {"symbol": symbol, "ok": False, "company_name": None,
                 "last_price": None, "error": str(exc)}
