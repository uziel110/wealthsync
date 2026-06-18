# CLAUDE.md — WealthSync

הקשר לסשנים עתידיים: מודל הנתונים של WealthSync, וההחלטות שהתקבלו בבניית שכבת
"ניתוח השקעות" (analysis/) — שכבה חינמית (yfinance בלבד) שמתחברת לתיק האמיתי
בלי לשכתב את הכלי הקיים.

## מודל הנתונים (מקור: app.py + sheets/gsheets.py)

- **מקור האמת**: Google Sheets, דרך `sheets/gsheets.py` (gspread + service
  account ב-`st.secrets`/`.streamlit/secrets.toml`). אין DB מקומי.
- שני worksheets:
  - `holdings` — סנאפשוט נוכחי מלא, נכתב מחדש (overwrite) בכל שמירה.
    עמודות מרכזיות: `account`, `asset_name`, `asset_id`, `quantity`,
    `cost_basis`, `market_value` (יש גם עמודות תצוגה/סוג נכס שנוספות ב-`enrich()`
    באפליקציה, לא בגיליון עצמו).
  - `snapshots` — היסטוריה מצטברת (append-only), דדופ' לפי חשבון+יום.
- **אין שדות `entry_price`/`stop`/`target` בסכימה**. מחיר כניסה ממוצע מחושב
  כ-`cost_basis / quantity`. stop/target לא מאוחסנים בכלל — מוצעים בכל ריצה
  לפי ATR (החלטת המשתמש: "אני רוצה שהכלי יציע את המספר", לא לשמור בסכימה).
- **`asset_id` לא אחיד**: תלוי בברוקר/parser המקור — פעמים טיקר (`AAPL`),
  פעמים מספר נייר ת"א (`1081124`), פעמים טקסט חופשי/ריק (גמל/פנסיה).
  ראו `parsers/ibi_parser.py`, `leumi_parser.py`, `hapoalim_parser.py`,
  `gamel_pdf_parser.py`. זו הסיבה לטבלת המיפוי `analysis/symbols.py`.
- `utils/market.py:get_price()` — קוד מת, לא בשימוש באפליקציה. לא נוגעים בו.

## ארכיטקטורה של שכבת הניתוח

```
analysis/
  engine.py            לוגיקת האינדיקטורים/החלטות — מ-analysis.py שהמשתמש
                        ספק, בלי שינוי לוגי. RSI/MACD/Bollinger/ATR/SMA,
                        buy_analysis / review_holding / allocate_deposit.
  symbols.py            מיפוי שם עברי → טיקר yfinance (NAME_TO_SYMBOL dict),
                        resolve_symbol(), verify_symbol() (בדיקה אמיתית מול
                        yfinance — לא להוסיף טיקר בלי לאמת!).
  portfolio_bridge.py   שכבת חיבור: load_holdings() (קורא מ-sheets.gsheets,
                        import עצלן בתוך הפונקציה כדי שטסטים/CLI לא יזדקקו
                        ל-streamlit/gspread), entry_price(), with_symbols()
                        (resolved/unresolved), review_portfolio(),
                        run_buy_analysis(), run_allocate_deposit(),
                        load_symbol_overrides()/add_symbol_mapping()/
                        list_unmapped_assets() (מיפוי טיקרים שנוסף מהאתר,
                        ראו "מיפוי טיקרים מהאתר" למטה).
  report.py             generator ל-HTML כהה RTL (ל-CLI/דוחות עצמאיים).
tools/verify_symbols.py  סקריפט עצמאי שמריץ verify_symbol() על כל הטבלה.
cli.py                   buy SYMBOL / review / deposit AMOUNT --candidates...
                        כותב דוחות ל-reports/ (ב-gitignore — מידע פיננסי אישי).
tests/                   24 טסטים, ללא רשת (snapshot סינתטי / DataFrame מוזרק).
```

### החלטות עיצוב

- **לא לשכתב את app.py הקיים** — רק תוספות: אופציית ניווט חדשה
  `"🧭 ניתוח השקעות"`, פונקציית עמוד `page_invest_analysis()`, ו-`elif` אחד
  בניתוב. שום דף/פונקציה קיימת לא נערכה.
- **שני סטיילים נפרדים, לא בסתירה**: דף ה-Streamlit האינטראקטיבי
  (`page_invest_analysis`) משתמש בדיזיין הקיים של האפליקציה (`ws-card`,
  `badge()`, `section_header()`) לעקביות חזותית. דוחות ה-CLI
  (`analysis/report.py`) הם HTML כהה/RTL עצמאי (כמו "StockPulse"), כי הם
  קבצים שנוצרים מחוץ להקשר Streamlit בכל מקרה — אין סתירה בין שתי הדרישות
  בבריף.
- **caching**: `@st.cache_data(ttl=900, show_spinner=False)` על שלוש קריאות
  הניתוח בעמוד, תואם את הקונבנציה הקיימת ב-`utils/market.py`.
- **טבלת מיפוי כ-dict בקוד** (לא worksheet נוסף ב-Sheets) — נבחר כי קל
  לעקוב היסטוריה ב-git, לבדוק בטסטים, ולהריץ אימות סטטי
  (`tools/verify_symbols.py`) בלי תלות ברשת Sheets. ניתן להרחיב בעתיד
  ל-worksheet אם המיפוי יגדל מאוד.
- **כל טיקר חדש חייב אימות מול yfinance לפני הוספה** — מקרה מתועד:
  `NVMI.TA` עבר אימות טכני (יש נתונים) אבל `longName` היה "Nova Ltd.",
  לא NextVision. הטיקר הנכון הוא `NXSN.TA`. בלי האימות הזה הניתוח היה
  מתבסס בשקט על חברה שגויה.
- **לא נוגעים ב-`page_ai()`** (תכונת "🤖 המלצות AI" הקיימת, מבוססת Gemini) —
  שכבה נפרדת ולא קשורה.
- **מיפוי טיקרים מהאתר (טאב "🔗 מיפוי טיקרים")**: בנוסף ל-`NAME_TO_SYMBOL`
  הסטטי (נשמר ב-git, מאומת ב-`tools/verify_symbols.py`), המשתמש יכול להוסיף
  מיפוי שם→טיקר בזמן ריצה מעמוד ה-Streamlit, לניירות שמופיעים ב"לא נותחו".
  המיפויים האלה נשמרים בגיליון Sheets חדש, `symbol_overrides`
  (`name, symbol, asset_id, added_at`), דרך `sheets.gsheets.save_symbol_override`
  (upsert לפי name). **לא שינינו** את ה-dict הסטטי בקוד — overrides נטענים
  בזמן ריצה (`portfolio_bridge.load_symbol_overrides()`, עם fallback שקט ל-`{}`
  אם Sheets לא נגיש) ומוזרקים ל-`resolve_symbol(..., overrides=...)` שבודק
  אותם *לפני* הטבלה הסטטית. נבחר worksheet (ולא קובץ JSON מקומי) כי זה
  תואם את העיקרון "אין DB מקומי" ועובד גם בפריסת Streamlit Cloud (filesystem
  לא persistent בין ריסטארטים). העקרון "כל טיקר חדש חייב אימות מול yfinance
  לפני הוספה" נשמר: ה-UI מריץ `verify_symbol` ומציג שם חברה+מחיר למשתמש,
  ושומר בפועל (`add_symbol_mapping`) רק אם האימות הצליח — אבל בדיקת
  "זו אכן החברה הנכונה" (כמו NVMI.TA/NXSN.TA) היא עדיין על המשתמש, לא אוטומטית.

## איך להריץ

```bash
python3 -m pytest tests/ -q                 # 24 טסטים, בלי רשת
python3 tools/verify_symbols.py             # מאמת את כל NAME_TO_SYMBOL מול yfinance
python3 cli.py buy ISCD.TA                  # דוח HTML + סיכום בטרמינל
python3 cli.py review                       # סוקר את כל התיק (סקירה שבועית — חמישי בערב)
python3 cli.py deposit 2000 --candidates "ישראכרט,AAPL"
```

## פתוח / מה חסר

- `requirements-dev.txt` מכיל `pytest` (לא ב-`requirements.txt` הראשי, כי
  לא נדרש בפרודקשן).
- `NAME_TO_SYMBOL` מכיל כרגע כיסוי בסיסי (8 שמות) — להרחיב לפי הצורך, ולהריץ
  `tools/verify_symbols.py` אחרי כל הוספה.
- אין תזמון אוטומטי (cron/scheduler) ל"סקירה שבועית בחמישי בערב" — כרגע
  הרצה ידנית via `cli.py review`. אם נדרש תזמון אמיתי, להוסיף לפי הסביבה
  (cron / GitHub Actions / Streamlit-side job) — לא הוחלט עדיין.
