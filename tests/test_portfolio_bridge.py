import pandas as pd
import pytest

from analysis import engine, symbols
from analysis.portfolio_bridge import (
    entry_price, with_symbols, suggest_stop_target, proxy_levels,
    review_portfolio, run_buy_analysis, run_allocate_deposit,
    load_symbol_overrides, add_symbol_mapping, list_unmapped_assets,
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


def test_with_symbols_resolves_via_override():
    overrides = {"גמל להשקעה מסלול כללי": "ESG.TA"}
    resolved, unresolved = with_symbols(_holdings_df(), overrides=overrides)
    assert "ESG.TA" in set(resolved["symbol"])
    assert unresolved.empty


def test_load_symbol_overrides_returns_empty_dict_when_sheets_unavailable():
    # בסביבת הטסטים אין streamlit/gspread מותקנים — הפונקציה צריכה ליפול
    # בשקט ל-{} בלי לזרוק שגיאה, כדי שלא תקריס review_portfolio/run_buy_analysis.
    assert load_symbol_overrides() == {}


def test_add_symbol_mapping_skips_save_when_verification_fails(monkeypatch):
    monkeypatch.setattr(symbols, "verify_symbol",
                         lambda symbol: {"symbol": symbol, "ok": False, "company_name": None,
                                          "last_price": None, "error": "אין נתוני מסחר"})
    result = add_symbol_mapping("נייר לא קיים", "FAKE123")
    assert result["ok"] is False


def test_proxy_levels_scale_to_holding_units_not_proxy():
    # פרוקסי דולרי (price 388, atr 9) מול מחיר החזקה שקלי (1.8) — הסטופ/יעד
    # צריכים לצאת ביחידות של ההחזקה (~1.8), לא ביחידות הפרוקסי.
    snap = {"price": 388.6, "atr": 9.1, "resistance": 448.0}
    stop, target = proxy_levels(snap, price=1.8)
    assert 1.0 < stop < 1.8          # סטופ מעט מתחת למחיר ההחזקה
    assert 1.8 < target < 2.5        # יעד מעט מעל — לא 448 ולא שלילי


def test_review_pnl_from_real_holding_not_proxy_price(monkeypatch):
    # קרן שקלית (entry ~1.71) שממופה לפרוקסי דולרי GLD (price 388): רווח/הפסד
    # חייב לבוא מ-market_value/cost_basis (אמיתי), לא מהשוואת 388 מול 1.71.
    gld = {"price": 388.6, "rsi": 45, "rsi_prev": 47, "macd_hist": -0.5,
           "macd_hist_prev": -0.2, "bb_lower": 380, "bb_mid": 400, "bb_upper": 420,
           "atr": 9.1, "sma50": 400, "sma200": 360, "support": 378, "resistance": 448}
    monkeypatch.setattr(engine, "snapshot", lambda symbol: gld)

    df = pd.DataFrame([{
        "account": "מיטב", "asset_name": "זהב מיטב", "asset_id": "GLD",
        "quantity": 29155, "cost_basis": 50000.0, "market_value": 53000.0,
    }])
    r = review_portfolio(df)["reviewed"][0]
    assert r["pnl_pct"] == pytest.approx(6.0, abs=0.5)   # (53000-50000)/50000
    assert r["suggested_stop"] > 0                        # לא שלילי
    assert r["suggested_stop"] < r["current_price"] < r["suggested_target"]
    assert r["is_proxy"] is True


def test_list_unmapped_assets_dedupes_by_name():
    df = pd.concat([_holdings_df(), pd.DataFrame([
        {"account": "הראל", "asset_name": "גמל להשקעה מסלול כללי", "asset_id": "",
         "quantity": 1, "cost_basis": 10000.0, "market_value": 10500.0},
    ])], ignore_index=True)
    unmapped = list_unmapped_assets(df)
    assert len(unmapped) == 1
    assert unmapped[0]["asset_name"] == "גמל להשקעה מסלול כללי"
