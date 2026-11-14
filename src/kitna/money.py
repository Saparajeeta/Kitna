"""Quantities with their modifiers: currency, ranges, bounds, approximation.

``read_quantity`` reads one expression of the shape::

    [about | at least | at most | Rs]*  NUMBER  [se|-|to NUMBER | NUMBER]
        [rupaye [NUMBER paise] | paise | only | ke aaspaas | tak]*
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ._types import Money, Range, Result, canonical, clean_number
from .normalize import Token, detect_script, lexicon, match_temporal
from .numerals import NumberRead, Rejected, match_marker, read_number
from .policy import policy

_PAISE_PER_RUPEE = Decimal(100)


@dataclass(frozen=True, slots=True)
class Skip:
    """Tokens that were examined and deliberately produce no result."""

    end: int
    reason: str


def _num(tokens: tuple[Token, ...], i: int, kind: str | None) -> NumberRead | Rejected | None:
    return read_number(tokens, i, kind=kind)


def read_quantity(
    text: str, tokens: tuple[Token, ...], i: int, *, kind: str | None
) -> tuple[Result, int] | Skip | None:
    """Read a number or money expression starting at token ``i``."""
    j = i
    approx = currency = False
    bound: str | None = None
    notes: list[str] = []
    conf = 1.0

    while (m := match_marker(tokens, j, ("approx_before", "min_before", "max_before", "currency_before"))):
        role, j = m
        if role == "approx_before":
            approx = True
        elif role == "currency_before":
            currency = True
        else:
            bound = "min" if role == "min_before" else "max"

    a = _num(tokens, j, kind)
    if a is None:
        return None
    if isinstance(a, Rejected):
        return Skip(a.end, a.reason)
    j, conf, notes = a.end, a.confidence, list(a.notes)
    lo: Decimal = a.value
    hi: Decimal | None = None

    # ---- range: "A se B", "A-B", "A to B", or two adjacent values "A B"
    k = j
    cur_mid = match_marker(tokens, k, ("currency_after",))
    if cur_mid:
        k = cur_mid[1]
    sep = match_marker(tokens, k, ("range_sep",))
    b = _num(tokens, sep[1], kind) if sep else (_num(tokens, j, kind) if not cur_mid else None)
    if isinstance(b, NumberRead):
        lo2 = lo
        if not a.has_scale and b.multiplier is not None and b.mantissa is not None and lo < b.mantissa:
            lo2 = lo * b.multiplier  # "do se teen hazaar": the scale covers both ends
        if lo2 < b.value:
            if lo2 != lo:
                notes.append("scale word applied to both ends of the range")
            lo, hi, j, conf = lo2, b.value, b.end, min(conf, b.confidence)
            currency = currency or bool(cur_mid)
            hyphen_words = (
                sep is not None and tokens[sep[1] - 1].type == "sym"
                and tokens[sep[1] - 2].type == "word" and tokens[sep[1]].type == "word"
            )
            if hyphen_words:
                # "teen-chaar hazaar": hyphenated number words are the same idiom as "teen chaar"
                approx = True
                notes.append("hyphenated number words read as an approximate range")
            if not sep:
                approx = True
                notes.append("adjacent values read as an approximate range")
                if a.value == 2 and b.value == 4:
                    conf *= policy().conf("do_chaar")
                    notes.append("'do chaar' is an idiom for 'a few'")

    # ---- trailing markers
    paise_only = False
    while True:
        m = match_marker(tokens, j, ("currency_after", "paise", "currency_tail", "approx_after", "max_after"))
        if not m:
            break
        role, nj = m
        if role == "currency_after":
            currency = True
            # "sau rupaye pachaas paise"
            if hi is None:
                c = _num(tokens, nj, kind)
                if isinstance(c, NumberRead) and c.value < _PAISE_PER_RUPEE:
                    p = match_marker(tokens, c.end, ("paise",))
                    if p:
                        lo += c.value / _PAISE_PER_RUPEE
                        conf, nj = min(conf, c.confidence), p[1]
        elif role == "paise":
            if currency or hi is not None:
                break
            currency = paise_only = True
            lo = lo / _PAISE_PER_RUPEE
        elif role == "currency_tail":
            if not currency:
                break
        elif role == "approx_after":
            approx = True
        elif role == "max_after":
            if hi is None:
                if bound == "min":
                    break
                bound = "max"
        j = nj
    if paise_only:
        notes.append("amount given in paise")

    # ---- a lone English number word ("no one", "the one I want", "ten") needs an anchor
    if kind is None and not currency and a.english_only and (not isinstance(b, NumberRead) or b.english_only):
        if not _anchored(tokens, i, j):
            return Skip(j, "English number word without a scale, currency, unit or Hindi neighbour")

    is_money = kind != "number" and (currency or kind == "money")
    if kind == "money" and not currency:
        notes.append("no currency word; treated as money because kind='money'")

    def wrap(d: Decimal) -> object:
        return Money(d) if is_money else clean_number(d)

    value: object
    if hi is not None:
        value = Range(wrap(lo), wrap(hi))
    elif bound == "min":
        value = Range(wrap(lo), None)
    elif bound == "max":
        value = Range(None, wrap(lo))
    else:
        value = wrap(lo)
    start, end = tokens[i].start, tokens[j - 1].end
    res = Result(
        span=(start, end), text=text[start:end], kind="money" if is_money else "number",
        value=value, canonical=canonical(value), confidence=round(conf, 4),
        approximate=approx, notes=tuple(notes),
    )
    return res, j


def _anchored(tokens: tuple[Token, ...], i: int, j: int) -> bool:
    """Is the English-only number at tokens[i:j] next to something that makes it a quantity?"""
    neighbours = {w for _, ctx in lexicon().rules.get("hindi_neighbours", ()) for w in ctx}
    for k in (i - 1, j):
        if 0 <= k < len(tokens) and tokens[k].type == "word":
            w = tokens[k].norm
            if w in neighbours or detect_script(w) == "devanagari" or match_temporal(tokens, k, "unit"):
                return True
    return False
