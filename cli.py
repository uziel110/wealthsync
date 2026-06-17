"""
ממשק שורת פקודה לשכבת הניתוח (analysis/). חינמי לחלוטין — yfinance בלבד.
נתוני התיק נטענים מ-Google Sheets (אותו מקור אמת כמו ב-Streamlit app).

שימוש:
    python cli.py buy ישראכרט
    python cli.py buy AAPL
    python cli.py review
    python cli.py deposit 5000 --candidates ישראכרט "נקסט ויזן" AAPL

כל פקודה כותבת דוח HTML (RTL, כהה) לתיקיית reports/ ומדפיסה סיכום קצר.
מיועד גם להרצה מתוזמנת (קרון/Task Scheduler) בימי חמישי בערב לסקירה שבועית.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from analysis.portfolio_bridge import run_buy_analysis, run_allocate_deposit, review_portfolio
from analysis.report import render_buy_report, render_review_report, render_deposit_report

REPORTS_DIR = Path(__file__).resolve().parent / "reports"

_VERDICT_HE = {"buy": "קנייה", "wait": "המתנה", "skip": "דילוג", "no_data": "אין נתונים"}
_ACTION_HE = {"hold": "להחזיק", "add": "להוסיף", "trim": "לקצץ חלקית",
              "sell": "למכור", "no_data": "אין נתונים"}


def _write_report(name: str, html: str) -> Path:
    REPORTS_DIR.mkdir(exist_ok=True)
    from datetime import datetime
    path = REPORTS_DIR / f"{name}_{datetime.now():%Y-%m-%d_%H%M}.html"
    path.write_text(html, encoding="utf-8")
    return path


def cmd_buy(args: argparse.Namespace) -> int:
    result = run_buy_analysis(args.symbol)
    verdict = result.get("verdict", "no_data")
    if verdict == "no_data":
        print(f"{args.symbol}: אין נתוני שוק.")
        return 1
    print(f"{result['symbol']}: {_VERDICT_HE[verdict]} | מחיר {result['price']} | "
          f"ניקוד {result['score']}/100 | {result['timing']}")
    path = _write_report(f"buy_{result['symbol']}", render_buy_report(result))
    print(f"דוח: {path}")
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    review = review_portfolio()
    if not review["reviewed"] and not review["unresolved"]:
        print("התיק ריק — אין מה לסקור.")
        return 1
    for r in review["reviewed"]:
        action = r.get("action", "no_data")
        print(f"  {r.get('asset_name', r.get('symbol')):20s} -> {_ACTION_HE.get(action, action)}")
    if review["unresolved"]:
        print(f"\n{len(review['unresolved'])} ניירות לא נותחו (אין מיפוי טיקר) — ראו הדוח.")
    path = _write_report("review", render_review_report(review))
    print(f"\nדוח: {path}")
    return 0


def cmd_deposit(args: argparse.Namespace) -> int:
    allocation = run_allocate_deposit(args.amount, args.candidates)
    if allocation["allocations"]:
        for a in allocation["allocations"]:
            print(f"  {a['symbol']:10s} ₪{a['amount']:>10,.0f} ({a['shares']} מניות)")
        print(f"  נשאר במזומן: ₪{allocation['cash_left']:,.0f}")
    else:
        print(allocation.get("note", "אין מועמדות אטרקטיביות כרגע."))
    if allocation.get("unresolved"):
        print(f"לא נפתרו לטיקר: {', '.join(allocation['unresolved'])}")
    path = _write_report("deposit", render_deposit_report(allocation))
    print(f"דוח: {path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="WealthSync — שכבת ניתוח חינמית")
    sub = parser.add_subparsers(dest="command", required=True)

    p_buy = sub.add_parser("buy", help="ניתוח קנייה לסימבול/שם נייר בודד")
    p_buy.add_argument("symbol", help="טיקר yfinance או שם נייר ממופה (ראו analysis/symbols.py)")
    p_buy.set_defaults(func=cmd_buy)

    p_review = sub.add_parser("review", help="סקירה שבועית לכל התיק")
    p_review.set_defaults(func=cmd_review)

    p_deposit = sub.add_parser("deposit", help="הקצאת הפקדה חדשה בין מועמדים")
    p_deposit.add_argument("amount", type=float, help="סכום ההפקדה בש\"ח")
    p_deposit.add_argument("--candidates", nargs="+", required=True,
                            help="רשימת שמות/טיקרים מועמדים")
    p_deposit.set_defaults(func=cmd_deposit)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
