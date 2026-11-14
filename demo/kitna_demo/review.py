"""Reviewer mode: the draft parser cases, one card at a time, exported as the review CSV.

The source is the review spreadsheet itself (``docs/review/phase1_cases_review.csv``), so the export
has exactly its columns and rows, with the three reviewer columns filled in.
"""
from __future__ import annotations

import csv
import datetime as dt
import io
import json
import os
from functools import lru_cache
from html import escape
from pathlib import Path
from typing import Any
from urllib.parse import quote

import kitna

from .say import KIND_LABEL, plain

VERDICTS = ("ok", "wrong", "unnatural")
VERDICT_COLUMN = "verdict (ok / wrong / unnatural)"
_HERE = Path(__file__).resolve().parent
_PLACES = (_HERE.parent / "cases_review.csv",  # next to app.py in a Space
           _HERE.parent.parent / "docs" / "review" / "phase1_cases_review.csv")  # in the repository
DEFAULT_BASE = dt.datetime(2026, 11, 12, 10, 0)


def cases_path() -> Path | None:
    env = os.environ.get("KITNA_REVIEW_CSV")
    for p in ((Path(env),) if env else ()) + _PLACES:
        if p.is_file():
            return p
    return None


@lru_cache(maxsize=2)
def _load(path: str) -> tuple[tuple[str, ...], tuple[dict[str, str], ...]]:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        header = tuple(reader.fieldnames or ())
        rows = tuple(dict(r) for r in reader)
    if VERDICT_COLUMN not in header or "id" not in header:
        raise ValueError(f"{path} does not look like the review spreadsheet")
    return header, rows


def load(path: Path | None = None) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    """(header, rows) with the cases that rest on undecided rules (tag 'review') first."""
    path = path or cases_path()
    if path is None:
        return (), []
    header, rows = _load(str(path))
    ordered = sorted(rows, key=lambda r: "review" not in r.get("tags", "").split())
    return header, ordered


def _base(row: dict[str, str]) -> tuple[dt.date | dt.datetime | None, dt.datetime]:
    raw = row.get("relative_base", "").strip()
    if not raw:
        return None, DEFAULT_BASE
    if "T" in raw:
        when = dt.datetime.fromisoformat(raw)
        return when, when
    day = dt.date.fromisoformat(raw)
    return day, dt.datetime.combine(day, dt.time(10, 0))


def draft_answer(row: dict[str, str]) -> str:
    """What the parser currently returns for this case, in plain words."""
    base, shown_base = _base(row)
    kind = row.get("kind") or None
    try:
        results = kitna.parse(row["text"], kind=kind if kind in kitna.KINDS else None, relative_base=base,
                              prefer=row.get("prefer") or None)
    except kitna.KitnaError as ex:
        return f"(could not be read: {ex})"
    if not results:
        return "nothing: no number, amount, date or time here"
    parts = []
    for r in results:
        with_time = shown_base if base is not None else None
        if r.ambiguous:
            text = "either " + " or ".join(plain(c, with_time) for c in r.candidates) + " (not decided: both kept)"
        else:
            text = plain(r.value, with_time)
        parts.append(("about " if r.approximate else "") + text)
    return "; ".join(parts)


def progress(done: int, total: int) -> str:
    pct = 0 if not total else round(100 * done / total)
    return (f'<div class="k-prog" role="progressbar" aria-valuemin="0" aria-valuemax="{total}" '
            f'aria-valuenow="{done}" aria-label="Cases reviewed"><div class="k-bar" style="width:{pct}%"></div>'
            f'</div><div class="k-progt">{done} of {total} checked</div>')


def card(row: dict[str, str] | None, position: int, total: int, answer: dict[str, str] | None = None) -> str:
    if row is None:
        if total == 0:
            return ('<div class="k-empty">The case list was not found. Reviewer mode needs '
                    '<code>cases_review.csv</code> next to the app.</div>')
        return ('<div class="k-rcard"><h3>That was the last one. Thank you!</h3>'
                '<p>Press “Get my CSV” below and send the file to the person who asked you.</p></div>')
    base, _ = _base(row)
    tags = row.get("tags", "")
    today = ""
    if base is not None:
        stamp = f"{base:%A} {base.day} {base:%B %Y}" + (f", {base:%H:%M}" if isinstance(base, dt.datetime) else "")
        today = f'<p class="k-rtoday">Imagine today is <strong>{escape(stamp)}</strong>.</p>'
    flag = ('<span class="k-chip k-chip-amb">rule not settled yet</span>' if "review" in tags.split() else "")
    prev = ""
    if answer and answer.get("verdict"):
        prev = f'<p class="k-rprev">You already answered: <strong>{escape(answer["verdict"])}</strong></p>'
    note = f'<p class="k-rnote">Author’s note: {escape(row["author_note"])}</p>' if row.get("author_note") else ""
    kind = KIND_LABEL.get(row.get("kind", ""), row.get("kind", ""))
    return (f'<div class="k-rcard"><div class="k-top"><span class="k-kind">Case {position + 1} of {total} · '
            f'{escape(row["id"])} · {escape(kind)}</span>{flag}</div>'
            f'<p class="k-rlabel">Someone types:</p><div class="k-rtext">{escape(row["text"])}</div>{today}'
            f'<p class="k-rlabel">Kitna’s draft answer:</p><div class="k-read">{escape(draft_answer(row))}</div>'
            f'{note}{prev}<details class="k-det"><summary>Details</summary><table>'
            f'<tr><th scope="row">Stored answer</th><td><code>{escape(row.get("expected", ""))}</code></td></tr>'
            f'<tr><th scope="row">Topics</th><td>{escape(tags or "-")}</td></tr></table></details>'
            '<p class="k-rhelp"><strong>OK</strong>: that is what it means. <strong>Wrong</strong>: it means '
            'something else (type what, if you can). <strong>Unnatural</strong>: nobody would write this.</p></div>')


def export_csv(header: tuple[str, ...], rows: list[dict[str, str]], answers: dict[str, Any]) -> str:
    """The review spreadsheet (original row order, BOM, CRLF) with the reviewer's columns filled in."""
    if not header:
        return ""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(header), lineterminator="\r\n")
    writer.writeheader()
    for row in sorted(rows, key=lambda r: _original_order(header, r)):
        out = dict(row)
        a = answers.get(row["id"]) or {}
        if a.get("verdict") in VERDICTS:
            out[VERDICT_COLUMN] = a["verdict"]
            out["corrected_value"] = (a.get("corrected") or "").strip()
            out["reviewer_comment"] = (a.get("comment") or "").strip()
        writer.writerow(out)
    return "\ufeff" + buf.getvalue()


def _original_order(header: tuple[str, ...], row: dict[str, str]) -> int:
    path = cases_path()
    if path is None:
        return 0
    ids = _ids(str(path))
    return ids.get(row["id"], len(ids))


@lru_cache(maxsize=2)
def _ids(path: str) -> dict[str, int]:
    return {r["id"]: n for n, r in enumerate(_load(path)[1])}


def download_link(csv_text: str, done: int) -> str:
    if not csv_text:
        return ""
    uri = "data:text/csv;charset=utf-8," + quote(csv_text)
    return (f'<div class="k-fb"><a class="k-dl" download="kitna_review.csv" href="{uri}">Download kitna_review.csv</a>'
            f'<p>{done} answers inside. The file is made in your browser from your answers; nothing was uploaded. '
            'Send it by WhatsApp, e-mail or however you like.</p></div>')


def state_json(answers: dict[str, Any]) -> str:
    return json.dumps(answers, ensure_ascii=False)
