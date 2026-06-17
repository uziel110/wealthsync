# -*- coding: utf-8 -*-
"""
analysis/engine.py — מודול ניתוח עצמאי (חינמי, ללא תלות בתשלום).
תלויות: yfinance, pandas, numpy בלבד.

שלוש פונקציות עיקריות:
  buy_analysis(symbol)                 -> האם לקנות, באיזה מחיר, מתי
  review_holding(symbol, entry, ...)   -> מה לעשות עם אחזקה קיימת (שבועי)
  allocate_deposit(amount, candidates) -> חלוקת הפקדה חדשה

הערה קריטית: מניות .TA מצוטטות באגורות — המחיר מחולק ב-100 אוטומטית.

מקור: כתיבה עצמאית שצורפה לפרויקט (ראו BRIEF). הלוגיקה כאן נשארת
ללא שינוי — שכבת החיבור לתיק נמצאת ב-analysis/portfolio_bridge.py.
"""
import math
import pandas as pd
import numpy as np

# ----- פרמטרים (אפשר לכוונן) -----
RSI_PERIOD = 14
MACD_FAST, MACD_SLOW, MACD_SIGNAL = 12, 26, 9
BB_PERIOD, BB_STD = 20, 2.0
ATR_PERIOD = 14
SMA_SHORT, SMA_LONG = 50, 200
SR_LOOKBACK = 60
ATR_STOP_MULT, ATR_TARGET_MULT = 2.0, 3.0
RSI_OVERBOUGHT, RSI_OVERSOLD = 70, 30
BUY_SCORE_MIN = 50          # סף ל"כדאי לקנות עכשיו"
MAX_POSITION_PCT = 0.25     # מקסימום 25% מהפקדה למניה אחת


# ===========================================================================
# נתוני שוק
# ===========================================================================
def is_tase(symbol: str) -> bool:
    return symbol.upper().endswith(".TA")


def fetch(symbol: str, period="1y"):
    import yfinance as yf
    try:
        df = yf.download(symbol, period=period, interval="1d",
                         auto_adjust=True, progress=False)
    except Exception:
        return None
    if df is None or df.empty:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns=str.title)
    if is_tase(symbol):                      # אגורות -> שקלים
        for c in ["Open", "High", "Low", "Close"]:
            if c in df:
                df[c] = df[c] / 100.0
    return df.dropna()


# ===========================================================================
# אינדיקטורים
# ===========================================================================
def _rsi(close, p=RSI_PERIOD):
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1/p, min_periods=p, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1/p, min_periods=p, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return 100 - 100/(1+rs)


def _macd(close):
    f = close.ewm(span=MACD_FAST, adjust=False).mean()
    s = close.ewm(span=MACD_SLOW, adjust=False).mean()
    line = f - s
    sig = line.ewm(span=MACD_SIGNAL, adjust=False).mean()
    return line, sig, line - sig


def _bollinger(close, p=BB_PERIOD, n=BB_STD):
    m = close.rolling(p).mean()
    sd = close.rolling(p).std()
    return m - n*sd, m, m + n*sd


def _atr(df, p=ATR_PERIOD):
    h, l, c = df["High"], df["Low"], df["Close"]
    pc = c.shift(1)
    tr = pd.concat([h-l, (h-pc).abs(), (l-pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/p, min_periods=p, adjust=False).mean()


def snapshot(symbol, df=None):
    """מצב טכני נוכחי של מניה. מחזיר dict או None."""
    if df is None:
        df = fetch(symbol)
    if df is None or len(df) < 30:
        return None
    c = df["Close"]
    r = _rsi(c); ml, ms, mh = _macd(c); bl, bm, bu = _bollinger(c); a = _atr(df)
    s50 = c.rolling(SMA_SHORT).mean(); s200 = c.rolling(SMA_LONG).mean()
    win = df.tail(SR_LOOKBACK)
    last = lambda x: float(x.dropna().iloc[-1]) if len(x.dropna()) else None
    prev = lambda x: float(x.dropna().iloc[-2]) if len(x.dropna()) > 1 else None
    return {
        "symbol": symbol, "price": last(c),
        "rsi": last(r), "rsi_prev": prev(r),
        "macd_hist": last(mh), "macd_hist_prev": prev(mh),
        "bb_lower": last(bl), "bb_mid": last(bm), "bb_upper": last(bu),
        "atr": last(a), "sma50": last(s50), "sma200": last(s200),
        "support": float(win["Low"].min()), "resistance": float(win["High"].max()),
    }


# ===========================================================================
# 1. ניתוח קנייה — האם / באיזה מחיר / מתי
# ===========================================================================
def buy_analysis(symbol, snap=None):
    snap = snap or snapshot(symbol)
    if not snap:
        return {"symbol": symbol, "verdict": "no_data", "reasons": ["אין נתוני שוק"]}

    p, rsi, atr = snap["price"], snap["rsi"], snap["atr"] or snap["price"]*0.03
    score, reasons = 0, []

    # RSI
    if rsi is not None:
        if rsi <= RSI_OVERSOLD:
            score += 30; reasons.append(f"RSI בקניית חסר ({rsi:.0f}) — הזדמנות")
        elif rsi < 60:
            score += 20; reasons.append(f"RSI מאוזן ({rsi:.0f})")
        elif rsi >= RSI_OVERBOUGHT:
            score -= 15; reasons.append(f"RSI בקניית יתר ({rsi:.0f}) — מתוח")
    # מגמה
    if snap["sma50"] and p > snap["sma50"]:
        score += 20; reasons.append("מעל ממוצע 50 (מגמה חיובית)")
    elif snap["sma50"]:
        score -= 5; reasons.append("מתחת לממוצע 50")
    if snap["sma200"] and p > snap["sma200"]:
        score += 10; reasons.append("מעל ממוצע 200 (מגמה ארוכה חיובית)")
    # MACD
    if snap["macd_hist"] is not None and snap["macd_hist_prev"] is not None:
        if snap["macd_hist"] > 0:
            score += 15; reasons.append("MACD חיובי")
        elif snap["macd_hist"] > snap["macd_hist_prev"]:
            score += 8; reasons.append("MACD מתהפך כלפי מעלה")
    # מתיחות (עונש יחיד מאוחד — קניית יתר וצמידות לבולינגר מתואמות)
    stretched = bool(snap["bb_upper"] and p >= snap["bb_upper"])
    if stretched and not (rsi and rsi >= RSI_OVERBOUGHT):
        score -= 12; reasons.append("צמוד לבולינגר העליון — אל תרדוף")

    score = max(0, min(100, score))

    # אזור כניסה ותזמון
    sup, s50, bb_mid = snap["support"], snap["sma50"], snap["bb_mid"]
    if stretched or (rsi and rsi >= RSI_OVERBOUGHT):
        timing = "המתן לתיקון — אל תיכנס במחיר הנוכחי"
        lo = max(x for x in [sup, s50, bb_mid] if x) if any([sup, s50, bb_mid]) else p*0.95
        entry_zone = (round(lo, 2), round(p*0.98, 2))
    elif score >= BUY_SCORE_MIN:
        timing = "כניסה עכשיו / צבירה הדרגתית"
        entry_zone = (round(max(sup or p*0.97, p*0.97), 2), round(p, 2))
    else:
        timing = "לא אטרקטיבי כרגע — להמתין/לדלג"
        entry_zone = (round(sup or p*0.95, 2), round(p*0.98, 2))

    entry = entry_zone[1]
    stop = round(entry - ATR_STOP_MULT*atr, 2)
    target = round(max(snap["resistance"] or 0, entry + ATR_TARGET_MULT*atr), 2)

    verdict = "buy" if score >= BUY_SCORE_MIN and not stretched else \
              ("wait" if score >= 35 else "skip")
    return {"symbol": symbol, "price": round(p, 2), "score": score,
            "verdict": verdict, "timing": timing, "entry_zone": entry_zone,
            "stop": stop, "target": target, "reasons": reasons, "snap": snap}


# ===========================================================================
# 2. סקירת אחזקה קיימת (שבועי) — מה לעשות
# ===========================================================================
def review_holding(symbol, entry_price=None, stop=None, target=None, snap=None):
    snap = snap or snapshot(symbol)
    if not snap:
        return {"symbol": symbol, "action": "no_data", "reasons": ["אין נתוני שוק"]}
    p = snap["price"]
    pnl = ((p - entry_price)/entry_price*100) if entry_price else None
    reasons, action = [], "hold"

    broke_stop = stop and p <= stop
    hit_target = target and p >= target
    below_50 = snap["sma50"] and p < snap["sma50"]
    macd_neg = snap["macd_hist"] is not None and snap["macd_hist"] < 0
    overbought = snap["rsi"] and snap["rsi"] >= RSI_OVERBOUGHT
    near_support = snap["support"] and 0 <= (p - snap["support"])/p < 0.04
    uptrend = snap["sma50"] and p > snap["sma50"]

    if broke_stop:
        action = "sell"; reasons.append(f"נשבר הסטופ ({stop})")
    elif below_50 and macd_neg:
        action = "sell"; reasons.append("מתחת לממוצע 50 + MACD שלילי (שבירת מגמה)")
    elif hit_target:
        action = "trim"; reasons.append(f"הגיע ליעד ({target}) — מימוש חלקי")
    elif overbought and pnl and pnl > 15:
        action = "trim"; reasons.append(f"RSI בקניית יתר + רווח {pnl:.0f}% — קצץ חלקית")
    elif uptrend and near_support:
        action = "add"; reasons.append("מגמת עלייה + תיקון לתמיכה — הזדמנות להוספה")
    else:
        reasons.append("יציב — אין שינוי")

    return {"symbol": symbol, "price": round(p, 2),
            "pnl_pct": round(pnl, 1) if pnl is not None else None,
            "action": action, "reasons": reasons, "snap": snap}


# ===========================================================================
# 3. הקצאת הפקדה חדשה — לאן / כמה / מתי
# ===========================================================================
def allocate_deposit(amount, candidates, max_pos_pct=MAX_POSITION_PCT):
    """candidates: רשימת סימבולים. מחזיר חלוקה מומלצת לסכום שהופקד."""
    analyses = [buy_analysis(s) for s in candidates]
    buyable = [a for a in analyses if a.get("verdict") == "buy"]
    waiting = [a for a in analyses if a.get("verdict") == "wait"]

    if not buyable:
        return {"deposit": amount, "allocations": [],
                "waiting": [(a["symbol"], a.get("timing")) for a in waiting],
                "note": "אין מועמדות אטרקטיביות לכניסה עכשיו — שווה להמתין/להשאיר במזומן."}

    total_score = sum(a["score"] for a in buyable)
    cap = amount * max_pos_pct
    allocations = []
    for a in sorted(buyable, key=lambda x: x["score"], reverse=True):
        raw = amount * (a["score"]/total_score)
        alloc = min(raw, cap)
        entry = a["entry_zone"][1]
        shares = math.floor(alloc/entry) if entry else 0
        if shares <= 0:
            continue
        allocations.append({
            "symbol": a["symbol"], "score": a["score"],
            "amount": round(shares*entry, 2), "shares": shares,
            "entry_zone": a["entry_zone"], "stop": a["stop"], "target": a["target"],
            "timing": a["timing"],
        })
    used = sum(x["amount"] for x in allocations)
    return {"deposit": amount, "allocations": allocations,
            "cash_left": round(amount - used, 2),
            "waiting": [(a["symbol"], a.get("timing")) for a in waiting]}
