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


def test_resolve_uses_override_for_unmapped_name():
    assert resolve_symbol("גמל להשקעה מסלול כללי", overrides={"גמל להשקעה מסלול כללי": "ESG.TA"}) == "ESG.TA"


def test_resolve_override_takes_priority_over_static_table():
    assert resolve_symbol("ישראכרט", overrides={"ישראכרט": "OVERRIDE.TA"}) == "OVERRIDE.TA"


def test_resolve_ignores_override_for_other_names():
    assert resolve_symbol("ישראכרט", overrides={"שם אחר": "X.TA"}) == "ISCD.TA"


def test_resolve_uses_override_by_asset_id_when_name_differs():
    # שם הקרן בייצוא הזה שונה מהשם שהמשתמש מיפה בעבר, אבל מספר הנייר קבוע
    assert resolve_symbol(
        "מנוטרלת מט\"ח - 500 P&S י(A4) הראל מחקה", asset_id="5127527",
        overrides={"5127527": "SPY"},
    ) == "SPY"


def test_resolve_name_override_takes_priority_over_asset_id_override():
    assert resolve_symbol(
        "ישראכרט", asset_id="1081124",
        overrides={"ישראכרט": "BY_NAME.TA", "1081124": "BY_ID.TA"},
    ) == "BY_NAME.TA"
