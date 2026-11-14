"""Canonical forms for gold and predicted argument values.

`strict_value` accepts only the canonical machine form (what the tool schema asks for).
`kitna_value` first tries that, then falls back to the kitna parser, so that
"2.5 lakh", "6 PM" or "kal" in a model's output can still be compared.
"""
from __future__ import annotations

import datetime as dt
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from typing import Any

import kitna

QUANTITY_KINDS = ("number", "date", "time", "datetime", "duration")
_DUR = re.compile(r"^P(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$")
_PUNCT = re.compile(r"[\s\-_.,;:!?'\"()।]+")


def _number(text: str) -> str | None:
    t = text.strip().replace(",", "").replace("₹", "").strip()
    try:
        d = Decimal(t)
    except InvalidOperation:
        return None
    if not d.is_finite():
        return None
    if d == d.to_integral_value():
        return str(int(d))
    return format(d.normalize(), "f")


def _duration(text: str) -> str | None:
    m = _DUR.match(text.strip().upper())
    if not m or text.strip().upper() in ("P", "PT"):
        return None
    w, d, h, mi, s = (int(x) if x else 0 for x in m.groups())
    total = ((w * 7 + d) * 24 + h) * 3600 + mi * 60 + s
    if total == 0:
        return None
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    out = "P" + (f"{days}D" if days else "")
    if hours or minutes or seconds:
        out += "T" + (f"{hours}H" if hours else "") + (f"{minutes}M" if minutes else "") + (
            f"{seconds}S" if seconds else "")
    return out


def text_key(value: str) -> str:
    """Comparison key for names, places, IDs: case, spacing and punctuation do not matter."""
    return _PUNCT.sub("", unicodedata.normalize("NFKC", value).casefold())


def strict_value(value: Any, kind: str) -> str | None:
    """Canonical string if `value` is already in machine form, else None."""
    if value is None or isinstance(value, (dict, list)):
        return None
    if isinstance(value, bool):
        return None
    if kind == "number":
        return _number(str(value))
    text = str(value).strip()
    try:
        if kind == "date":
            return dt.date.fromisoformat(text).isoformat() if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text) else None
        if kind == "time":
            if not re.fullmatch(r"\d{1,2}:\d{2}(:\d{2})?", text):
                return None
            return dt.time.fromisoformat(text.zfill(5) if len(text) == 4 else text).strftime("%H:%M")
        if kind == "datetime":
            m = re.fullmatch(r"(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?", text)
            if not m:
                return None
            # An explicit offset other than IST would change the wall-clock time; do not guess.
            if m.group(5) and m.group(5).replace(":", "") != "+0530":
                return None
            return dt.datetime.fromisoformat(f"{m.group(1)}T{m.group(2)}").strftime("%Y-%m-%dT%H:%M")
    except ValueError:
        return None
    if kind == "duration":
        return _duration(text)
    if kind in ("enum", "string", "id"):
        return text_key(text) or None
    raise ValueError(f"unknown kind {kind!r}")


def kitna_value(value: Any, kind: str, now: dt.datetime) -> str | None:
    """Canonical string via the strict form or, failing that, the kitna parser. None if unreadable or ambiguous."""
    strict = strict_value(value, kind)
    if strict is not None or kind not in QUANTITY_KINDS:
        return strict
    if value is None or isinstance(value, (dict, list, bool)):
        return None
    text = str(value)
    kinds = [kind] + (["money"] if kind == "number" else [])
    for k in kinds:
        try:
            results = kitna.parse(text, kind=k, relative_base=now)
        except kitna.KitnaError:
            continue
        results = [r for r in results if r.kind == k]
        if len(results) != 1 or results[0].ambiguous or results[0].approximate:
            continue
        canon = results[0].canonical
        if k == "money":
            canon = canon.split(" ", 1)[1] if canon.startswith("INR ") else ""
        if canon and ".." not in canon:
            return strict_value(canon, kind) or canon
    return None


def is_canonical(value: str, kind: str) -> bool:
    """Gold values must already be canonical (strings/ids/enums: any non-empty text)."""
    if kind in ("enum", "string", "id"):
        return bool(value.strip())
    return strict_value(value, kind) == value
