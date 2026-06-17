"""
בדיקות ללוגיקת הניתוח (analysis/engine.py) עם snapshot סינתטי — בלי קריאות
רשת ל-yfinance. snapshot() עצמה (fetch + אינדיקטורים) היא מודול שהמשתמש
כתב וכבר בדק; כאן נבדקת רק לוגיקת ההחלטה (buy_analysis/review_holding/
allocate_deposit) שמקבלת snap מוכן.
"""
import pytest

from analysis import engine


def make_snap(**overrides):
    base = {
        "symbol": "TEST", "price": 100.0,
        "rsi": 50.0, "rsi_prev": 48.0,
        "macd_hist": 0.5, "macd_hist_prev": 0.2,
        "bb_lower": 90.0, "bb_mid": 100.0, "bb_upper": 110.0,
        "atr": 3.0, "sma50": 95.0, "sma200": 90.0,
        "support": 92.0, "resistance": 108.0,
    }
    base.update(overrides)
    return base


def test_buy_analysis_oversold_uptrend_is_a_buy():
    snap = make_snap(rsi=25, price=100, sma50=95, sma200=90, macd_hist=0.5, macd_hist_prev=0.1)
    result = engine.buy_analysis("TEST", snap=snap)
    assert result["verdict"] == "buy"
    assert result["score"] >= engine.BUY_SCORE_MIN


def test_buy_analysis_overbought_and_stretched_waits_for_pullback():
    snap = make_snap(rsi=78, price=111, bb_upper=110, sma50=95, sma200=90)
    result = engine.buy_analysis("TEST", snap=snap)
    assert result["verdict"] != "buy"
    assert "המתן" in result["timing"]


def test_buy_analysis_stop_below_entry_and_target_above():
    snap = make_snap()
    result = engine.buy_analysis("TEST", snap=snap)
    entry = result["entry_zone"][1]
    assert result["stop"] < entry < result["target"]


def test_review_holding_sells_on_broken_stop():
    snap = make_snap(price=80)
    result = engine.review_holding("TEST", entry_price=100, stop=85, target=130, snap=snap)
    assert result["action"] == "sell"


def test_review_holding_trims_on_target_hit():
    snap = make_snap(price=131)
    result = engine.review_holding("TEST", entry_price=100, stop=85, target=130, snap=snap)
    assert result["action"] == "trim"


def test_review_holding_adds_on_pullback_to_support_in_uptrend():
    snap = make_snap(price=93, sma50=90, support=92)
    result = engine.review_holding("TEST", entry_price=80, snap=snap)
    assert result["action"] == "add"


def test_review_holding_no_data_when_snapshot_missing(monkeypatch):
    monkeypatch.setattr(engine, "snapshot", lambda symbol: None)
    result = engine.review_holding("UNKNOWN")
    assert result["action"] == "no_data"


def test_allocate_deposit_skips_non_buy_candidates(monkeypatch):
    snaps = {
        "GOOD": make_snap(rsi=25, sma50=95, sma200=90),
        "BAD": make_snap(rsi=80, price=111, bb_upper=110),
    }
    monkeypatch.setattr(engine, "snapshot", lambda symbol: snaps.get(symbol))

    result = engine.allocate_deposit(10_000, ["GOOD", "BAD"])
    symbols_allocated = [a["symbol"] for a in result["allocations"]]
    assert "GOOD" in symbols_allocated
    assert "BAD" not in symbols_allocated


def test_allocate_deposit_respects_max_position_cap(monkeypatch):
    snap = make_snap(rsi=25, sma50=95, sma200=90)
    monkeypatch.setattr(engine, "snapshot", lambda symbol: snap)

    result = engine.allocate_deposit(10_000, ["ONLY_ONE"], max_pos_pct=0.25)
    assert result["allocations"][0]["amount"] <= 10_000 * 0.25 + 1e-6
