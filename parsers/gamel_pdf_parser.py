"""
Parser for Harel קופת גמל להשקעה PDF statements.

pdfplumber extracts RTL Hebrew PDFs with each word's characters reversed
AND word order reversed per line.  Numbers remain in normal order.
We correct for this before matching.
"""
from __future__ import annotations
import re
import io
import pandas as pd


def _unreverse(s: str) -> str:
    """Restore a reversed-Hebrew token to its original form.

    pdfplumber reverses both character order within each word and the
    left-to-right order of words.  Reverse each word's chars then flip
    the word list to recover the original string.
    """
    words = s.strip().split()
    return " ".join(w[::-1] for w in reversed(words))


def _num(s: str) -> float:
    return float(s.replace(",", "").strip())


def parse_gamel_pdf(file_bytes: io.BytesIO, account_name: str = "גמל") -> pd.DataFrame:
    """Return a DataFrame with one row per investment track found in the PDF."""
    import pdfplumber

    lines: list[str] = []
    with pdfplumber.open(file_bytes) as pdf:
        for page in pdf.pages:
            lines.extend((page.extract_text() or "").splitlines())

    # ── Investment tracks ─────────────────────────────────────────────────────
    # Header line (reversed): "... הריבצ העקשה לולסמ"
    # Track data line (reversed):  "0.82%  109,581.82  ריחס תוינמ"
    #   → percent  accumulation  reversed_name
    tracks: list[tuple[str, float]] = []
    in_tracks = False
    for line in lines:
        if "העקשה לולסמ" in line or "הריבצ העקשה" in line:
            in_tracks = True
            continue
        if in_tracks and ("תונורחא תועונת" in line or "תומושר" in line):
            break
        if in_tracks:
            m = re.match(r"^([\d.]+%)\s+([\d,]+\.?\d*)\s+([֐-׿ ]+)$", line.strip())
            if m:
                acc = _num(m.group(2))
                name = _unreverse(m.group(3))
                if acc > 0 and name:
                    tracks.append((name, acc))

    # ── Cost basis from summary section ──────────────────────────────────────
    # In the extracted text the numeric value appears on the line BEFORE its label.
    # Reversed labels:
    #   "ןובשחל תרבעהש םיפסכ"  ← כספים שהעברת לחשבון  (transfers in)
    #   "ןובשחל ודקפוהש םיפסכ" ← כספים שהופקדו לחשבון  (direct deposits)
    cost_transferred = 0.0
    cost_deposited   = 0.0
    for i, line in enumerate(lines):
        s = line.strip()
        # reversed "כספים שהעברת לחשבון" — note ןובשחל (to) not ןובשחהמ (from)
        if "ןובשחל תרבעהש םיפסכ" in s and i > 0:
            m = re.search(r"[\d,]+", lines[i - 1])
            if m:
                cost_transferred = _num(m.group())
        # reversed "כספים שהופקדו לחשבון השנה"
        if "ודקפוהש םיפסכ" in s and i > 0:
            m = re.search(r"[\d,]+", lines[i - 1])
            if m:
                cost_deposited = _num(m.group())

    total_cost = cost_transferred + cost_deposited

    # ── Fallback: use total accumulation if no tracks parsed ─────────────────
    if not tracks:
        for i, line in enumerate(lines):
            # reversed "צבירת הכספים" = "םיפסכה תריבצ"
            if "םיפסכה תריבצ" in line.strip() and i > 0:
                m = re.search(r"[\d,]+", lines[i - 1])
                if m:
                    tracks = [("גמל להשקעה", _num(m.group()))]
                break

    if not tracks:
        tracks = [("גמל להשקעה", 0.0)]

    total_market = sum(v for _, v in tracks) or 1.0
    rows = []
    for track_name, acc in tracks:
        ratio = acc / total_market
        rows.append({
            "account":      account_name,
            "asset_name":   f"גמל להשקעה — {track_name}",
            "asset_id":     "",
            "asset_type":   "gamel",
            "quantity":     1.0,
            "market_value": acc,
            "cost_basis":   round(total_cost * ratio, 2),
            "source":       "גמל PDF",
        })

    return pd.DataFrame(rows)
