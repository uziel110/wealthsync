from analysis.symbols import resolve_symbol, NAME_TO_SYMBOL


def test_resolve_known_hebrew_name():
    assert resolve_symbol("ישראכרט") == "ISCD.TA"


def test_resolve_strips_bidi_marks():
    # תווי RTL/LTR נסתרים שמודבקים בייצוא בנקים — חייבים להתעלם מהם
    wrapped = "‏ישראכרט‎"
    assert resolve_symbol(wrapped) == "ISCD.TA"


def test_resolve_falls_back_to_alpha_asset_id():
    assert resolve_symbol("מניות לא ממופות", asset_id="AAPL") == "AAPL"


def test_resolve_unknown_numeric_id_returns_none():
    assert resolve_symbol("נייר לא מוכר", asset_id="1081124") is None


def test_resolve_unknown_name_without_asset_id_returns_none():
    assert resolve_symbol("חברה שלא קיימת בטבלה") is None


def test_mapping_table_has_no_blank_entries():
    for name, symbol in NAME_TO_SYMBOL.items():
        assert name.strip() and symbol.strip()
