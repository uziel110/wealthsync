import pandas as pd
import pytest

from analysis import engine
from analysis.portfolio_bridge import (
    entry_price, with_symbols, suggest_stop_target,
    review_portfolio, run_buy_analysis, run_allocate_deposit,
)


def _holdings_df():
    return pd.DataFrame([
        {"account": "פסגות", "asset_name": "ישראכרט", "asset_id": "1081124",
         "quantity": 10, "cost_basis": 9000.0, "market_value": 11940.0},
        {"account": "פסגות", "asset_name": "מניות אפל", "asset_id": "AAPL",
         "quantity": 5, "cost_basis": 4000.0, "market_value": 4500.0},
        {"account": "הראל", "asset_name": "גמל להשקעה מסלול כללי", "asset_id": "",
         "quantity": 1, "cost_basis": 50000.0, "market_value": 53000.0},
    ])


def test_entry_price_is_cost_over_quantity():
    row = pd.Series({"quantity": 10, "cost_basis": 9000.0})
    assert entry_price(row) == 900.0


def test_entry_price_none_when_quantity_zero():
    row = pd.Series({"quantity": 0, "cost_basis": 9000.0})
    assert entry_price(row) is None


def test_with_symbols_splits_resolved_and_unresolved():
    resolved, unresolved = with_symbols(_holdings_df())
    assert set(resolved["symbol"]) == {"ISCD.TA", "AAPL"}
    assert len(unresolved) == 1
    assert unresolved.iloc[0]["asset_name"] == "גמל להשקעה מסלול כללי"


def test_suggest_stop_target_uses_atr():
    snap = {"atr": 2.0, "resistance": 50.0}
    stop, target = suggest_stop_target(snap, entry=100.0)
    assert stop == 100.0 - engine.ATR_STOP_MULT * 2.0
    assert target == max(50.0, 100.0 + engine.ATR_TARGET_MULT * 2.0)


def test_review_portfolio_reports_unresolved_holdings(monkeypatch):
    fake_snap = {
        "price": 130.0, "rsi": 50, "rsi_prev": 48,
        "macd_hist": 0.1, "macd_hist_prev": 0.0,
        "bb_lower": 110, "bb_mid": 120, "bb_upper": 140,
        "atr": 3.0, "sma50": 125, "sma200": 110,
        "support": 118, "resistance": 138,
    }
    monkeypatch.setattr(engine, "snapshot", lambda symbol: fake_snap)

    review = review_portfolio(_holdings_df())
    assert len(review["reviewed"]) == 2
    assert len(review["unresolved"]) == 1
    assert review["unresolved"][0]["asset_name"] == "גמל להשקעה מסלול כללי"

    isracard = next(r for r in review["reviewed"] if r["symbol"] == "ISCD.TA")
    assert isracard["suggested_stop"] is not None
    assert isracard["suggested_target"] is not None


def test_review_portfolio_marks_no_data_when_snapshot_missing(monkeypatch):
    monkeypatch.setattr(engine, "snapshot", lambda symbol: None)
    review = review_portfolio(_holdings_df())
    assert all(r["action"] == "no_data" for r in review["reviewed"])


def test_run_buy_analysis_resolves_hebrew_name(monkeypatch):
    captured = {}

    def fake_buy_analysis(symbol, snap=None):
        captured["symbol"] = symbol
        return {"symbol": symbol, "verdict": "buy"}

    monkeypatch.setattr(engine, "buy_analysis", fake_buy_analysis)
    run_buy_analysis("ישראכרט")
    assert captured["symbol"] == "ISCD.TA"


def test_run_buy_analysis_passes_through_raw_ticker(monkeypatch):
    captured = {}
    monkeypatch.setattr(engine, "buy_analysis",
                         lambda symbol, snap=None: captured.setdefault("symbol", symbol) or {})
    run_buy_analysis("aapl")
    assert captured["symbol"] == "AAPL"


def test_run_allocate_deposit_reports_unresolved_candidates(monkeypatch):
    monkeypatch.setattr(engine, "allocate_deposit",
                         lambda amount, candidates, **kw: {"deposit": amount, "allocations": [], "waiting": []})
    result = run_allocate_deposit(5000, ["ישראכרט", "שם שלא קיים בכלל בלי אותיות בלבד 123"])
    assert "שם שלא קיים בכלל בלי אותיות בלבד 123" in result["unresolved"]
