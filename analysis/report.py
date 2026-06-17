# -*- coding: utf-8 -*-
"""
analysis/report.py — דוחות HTML בעברית (RTL, עיצוב כהה) לשלוש היכולות.
מיועד לפלט עצמאי (CLI / סקירה מתוזמנת), לא לתצוגה בתוך Streamlit.
"""
from __future__ import annotations

from datetime import datetime

_DISCLAIMER = "למחקר אישי בלבד, לא ייעוץ השקעות מוסמך."

_VERDICT_HE = {"buy": "קנייה", "wait": "המתנה", "skip": "דילוג", "no_data": "אין נתונים"}
_ACTION_HE = {"hold": "להחזיק", "add": "להוסיף", "trim": "לקצץ חלקית",
              "sell": "למכור", "no_data": "אין נתונים"}

_STYLE = """
<style>
  body { background:#0F172A; color:#E2E8F0; font-family:Heebo,Arial,sans-serif;
         direction:rtl; padding:2rem; max-width:900px; margin:0 auto; }
  h1 { font-size:1.5rem; color:#F8FAFC; }
  h2 { font-size:1.1rem; color:#94A3B8; text-transform:uppercase; letter-spacing:.04em;
       border-right:3px solid #2563EB; padding-right:.6rem; margin-top:2rem; }
  .card { background:#1E293B; border-radius:12px; padding:1.25rem 1.5rem;
          margin-bottom:1rem; border:1px solid #334155; }
  .row { display:flex; justify-content:space-between; padding:.3rem 0;
         border-bottom:1px solid #334155; font-size:.92rem; }
  .row:last-child { border-bottom:none; }
  .label { color:#94A3B8; }
  .val { font-weight:700; color:#F8FAFC; }
  .buy, .add { color:#34D399; }
  .skip, .sell { color:#F87171; }
  .wait, .trim, .hold { color:#FBBF24; }
  .reasons { font-size:.85rem; color:#CBD5E1; margin-top:.5rem; line-height:1.7; }
  .disclaimer { margin-top:2rem; font-size:.78rem; color:#64748B;
                border-top:1px solid #334155; padding-top:1rem; }
  table { width:100%; border-collapse:collapse; font-size:.88rem; }
  th, td { padding:.5rem .6rem; text-align:right; border-bottom:1px solid #334155; }
  th { color:#94A3B8; font-weight:600; }
</style>
"""


def _head(title: str) -> str:
    return f"<html><head><meta charset='utf-8'>{_STYLE}</head><body><h1>{title}</h1>"


def _foot() -> str:
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    return f"<div class='disclaimer'>נוצר ב-{now} · {_DISCLAIMER}</div></body></html>"


def render_buy_report(result: dict) -> str:
    verdict = result.get("verdict", "no_data")
    if verdict == "no_data":
        html = _head(f"ניתוח קנייה — {result['symbol']}")
        html += "<div class='card'>אין נתוני שוק עבור הסימבול הזה.</div>"
        return html + _foot()

    lo, hi = result["entry_zone"]
    reasons = "".join(f"<li>{r}</li>" for r in result["reasons"])
    html = _head(f"ניתוח קנייה — {result['symbol']}")
    html += f"""
    <div class="card">
      <div class="row"><span class="label">החלטה</span>
        <span class="val {verdict}">{_VERDICT_HE.get(verdict, verdict)}</span></div>
      <div class="row"><span class="label">מחיר נוכחי</span><span class="val">{result['price']}</span></div>
      <div class="row"><span class="label">ניקוד</span><span class="val">{result['score']}/100</span></div>
      <div class="row"><span class="label">תזמון</span><span class="val">{result['timing']}</span></div>
      <div class="row"><span class="label">אזור כניסה</span><span class="val">{lo} – {hi}</span></div>
      <div class="row"><span class="label">סטופ מוצע</span><span class="val">{result['stop']}</span></div>
      <div class="row"><span class="label">יעד מוצע</span><span class="val">{result['target']}</span></div>
      <div class="reasons"><ul>{reasons}</ul></div>
    </div>"""
    return html + _foot()


def render_review_report(review: dict) -> str:
    reviewed, unresolved = review["reviewed"], review["unresolved"]
    html = _head("סקירה שבועית — התיק")

    html += "<h2>החזקות שנותחו</h2>"
    for r in reviewed:
        action = r.get("action", "no_data")
        reasons = "".join(f"<li>{x}</li>" for x in r.get("reasons", []))
        pnl = f"{r['pnl_pct']:+.1f}%" if r.get("pnl_pct") is not None else "—"
        html += f"""
        <div class="card">
          <div class="row"><span class="label">נייר</span>
            <span class="val">{r.get('asset_name', r.get('symbol'))} ({r.get('symbol', '')})</span></div>
          <div class="row"><span class="label">פעולה מומלצת</span>
            <span class="val {action}">{_ACTION_HE.get(action, action)}</span></div>
          <div class="row"><span class="label">מחיר נוכחי</span><span class="val">{r.get('price', '—')}</span></div>
          <div class="row"><span class="label">רווח/הפסד</span><span class="val">{pnl}</span></div>
          <div class="row"><span class="label">סטופ מוצע</span><span class="val">{r.get('suggested_stop', '—')}</span></div>
          <div class="row"><span class="label">יעד מוצע</span><span class="val">{r.get('suggested_target', '—')}</span></div>
          <div class="reasons"><ul>{reasons}</ul></div>
        </div>"""

    if unresolved:
        html += "<h2>החזקות שלא נותחו (אין מיפוי טיקר)</h2><div class='card'><table><tr><th>נייר</th><th>חשבון</th><th>שווי</th></tr>"
        for u in unresolved:
            html += f"<tr><td>{u.get('asset_name')}</td><td>{u.get('account')}</td><td>₪{u.get('market_value', 0):,.0f}</td></tr>"
        html += "</table><div class='reasons'>הוסף מיפוי שם → טיקר ב-analysis/symbols.py כדי לכלול אותן.</div></div>"

    return html + _foot()


def render_deposit_report(allocation: dict) -> str:
    html = _head(f"הקצאת הפקדה — ₪{allocation['deposit']:,.0f}")

    if allocation.get("allocations"):
        html += "<h2>חלוקה מומלצת</h2><div class='card'><table><tr><th>נייר</th><th>סכום</th><th>מניות</th><th>אזור כניסה</th><th>סטופ</th><th>יעד</th></tr>"
        for a in allocation["allocations"]:
            lo, hi = a["entry_zone"]
            html += (f"<tr><td>{a['symbol']}</td><td>₪{a['amount']:,.0f}</td><td>{a['shares']}</td>"
                      f"<td>{lo}–{hi}</td><td>{a['stop']}</td><td>{a['target']}</td></tr>")
        html += "</table></div>"
        html += f"<div class='card row'><span class='label'>נשאר במזומן</span><span class='val'>₪{allocation.get('cash_left', 0):,.0f}</span></div>"
    else:
        html += f"<div class='card'>{allocation.get('note', 'אין מועמדות אטרקטיביות כרגע.')}</div>"

    if allocation.get("waiting"):
        html += "<h2>בהמתנה (לא אטרקטיבי לכניסה עכשיו)</h2><div class='card'><ul>"
        html += "".join(f"<li>{sym} — {timing}</li>" for sym, timing in allocation["waiting"])
        html += "</ul></div>"

    if allocation.get("unresolved"):
        html += "<h2>מועמדים שלא נפתרו לטיקר</h2><div class='card'>" + ", ".join(allocation["unresolved"]) + "</div>"

    return html + _foot()
