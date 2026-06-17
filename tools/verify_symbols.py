"""
מאמת את כל הטיקרים ב-analysis/symbols.py מול yfinance: שולף שם חברה
ומחיר אחרון לכל ערך, כדי שתוכל לעבור עין ולוודא שהטיקר תואם לשם בתיק
*לפני* שמסתמכים עליו לניתוח.

שימוש:
    python tools/verify_symbols.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis.symbols import NAME_TO_SYMBOL, verify_symbol


def main() -> int:
    seen = set()
    failures = 0
    for name, symbol in NAME_TO_SYMBOL.items():
        if symbol in seen:
            continue
        seen.add(symbol)
        result = verify_symbol(symbol)
        if result["ok"]:
            print(f"  ✓ {symbol:12s} {result['company_name'] or '?':40s} "
                  f"מחיר אחרון: {result['last_price']:.2f}  (מופיע בתיק כ: {name})")
        else:
            failures += 1
            print(f"  ✗ {symbol:12s} שגיאה: {result['error']}  (מופיע בתיק כ: {name})")

    print()
    if failures:
        print(f"נמצאו {failures} טיקרים שלא ניתן לאמת. בדוק/תקן ב-analysis/symbols.py.")
        return 1
    print(f"כל {len(seen)} הטיקרים אומתו בהצלחה מול yfinance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
