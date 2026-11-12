"""The public ``parse`` function and its convenience wrappers."""
from __future__ import annotations

from datetime import date, datetime

from ._types import KINDS, KitnaError, Result
from .money import Skip, read_quantity
from .normalize import tokenize
from .numerals import read_digits

_IMPLEMENTED = ("number", "digits", "money")


def parse(
    text: str,
    kind: str | None = None,
    relative_base: date | datetime | None = None,
    *,
    prefer: str | None = None,
) -> list[Result]:
    """Find quantities in ``text`` and return them in text order.

    ``kind`` is a hint and a filter. With ``kind="money"`` bare numbers are read
    as rupee amounts; with ``kind="digits"`` number words are read as a digit
    string; with ``kind="number"`` currency words are ignored. Only results of
    that kind are returned.

    ``relative_base`` and ``prefer`` are used by date and time parsing (not yet
    implemented in this version).

    Deterministic, no I/O beyond reading the bundled data tables once.
    """
    if not isinstance(text, str):
        raise KitnaError(f"text must be str, not {type(text).__name__}")
    if kind is not None and kind not in KINDS:
        raise KitnaError(f"unknown kind {kind!r}; expected one of {', '.join(KINDS)}")
    if prefer not in (None, "future", "past"):
        raise KitnaError(f"prefer must be 'future', 'past' or None, not {prefer!r}")
    if relative_base is not None and not isinstance(relative_base, date):
        raise KitnaError("relative_base must be a datetime.date or datetime.datetime")
    if kind is not None and kind not in _IMPLEMENTED:
        raise NotImplementedError(f"kind {kind!r} is specified but not implemented yet in this version")

    tokens = tokenize(text)
    out: list[Result] = []
    i = 0
    while i < len(tokens):
        if tokens[i].type == "punct":
            i += 1
            continue
        if kind in (None, "digits"):
            d = read_digits(tokens, i, forced=kind == "digits")
            if d is not None:
                digits, j, conf = d
                s, e = tokens[i].start, tokens[j - 1].end
                out.append(Result((s, e), text[s:e], "digits", digits, digits, round(conf, 4)))
                i = j
                continue
        if kind != "digits":
            q = read_quantity(text, tokens, i, kind=kind)
            if isinstance(q, Skip):
                i = q.end
                continue
            if q is not None:
                out.append(q[0])
                i = q[1]
                continue
        i += 1
    return [r for r in out if kind is None or r.kind == kind]


def _first(text: str, kind: str) -> Result | None:
    results = parse(text, kind=kind)
    return results[0] if results else None


def parse_number(text: str) -> Result | None:
    """First number in ``text`` (currency words ignored), or ``None``."""
    return _first(text, "number")


def parse_money(text: str) -> Result | None:
    """First amount in ``text``, read as rupees, or ``None``."""
    return _first(text, "money")
