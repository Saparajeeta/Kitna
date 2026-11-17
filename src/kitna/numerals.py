"""Number words, digit strings, scales and spoken digit sequences."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from . import fractions
from .normalize import Entry, Token, lexicon, lookup
from .policy import policy

_HUNDRED = Decimal(100)


@dataclass(frozen=True, slots=True)
class NumberRead:
    value: Decimal
    end: int  # index of the first token not consumed
    confidence: float
    has_scale: bool
    #: every word was an English number word and there was no digit string or scale
    #: word; such a run needs an anchor before it counts (see money.read_quantity)
    english_only: bool
    #: when the number is "mantissa x scales" with nothing after (teen hazaar),
    #: the mantissa and the multiplier; used to spread a scale over a range
    mantissa: Decimal | None
    multiplier: Decimal | None
    notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Rejected:
    end: int
    reason: str


def match_marker(tokens: tuple[Token, ...], i: int, roles: tuple[str, ...]) -> tuple[str, int] | None:
    """Longest marker phrase with one of ``roles`` starting at token ``i``."""
    for role, phrase in lexicon().markers:
        if role in roles and i + len(phrase) <= len(tokens):
            window = tokens[i:i + len(phrase)]
            if all(t.norm == p and t.type != "num" for t, p in zip(window, phrase, strict=True)):
                return role, i + len(phrase)
    return None


def _raw(tokens: tuple[Token, ...], i: int) -> tuple[Entry, float] | None:
    if 0 <= i < len(tokens) and tokens[i].type == "word":
        return lookup(tokens[i].norm)
    return None


def _numeric_neighbour(tokens: tuple[Token, ...], i: int) -> bool:
    """True if token ``i`` sits next to a digit string, a scale or fraction word, a
    currency word, or is hyphen-joined to a number word (``pachaas-saath``)."""
    for step in (-1, 1):
        j = i + step
        hyphen = 0 <= j < len(tokens) and tokens[j].type == "sym" and tokens[j].norm in "-–"
        if hyphen:
            j += step
        if not 0 <= j < len(tokens):
            continue
        hit = _raw(tokens, j)
        if tokens[j].type == "num" or (hit is not None and (hyphen or hit[0].cat != "num")):
            return True
        if match_marker(tokens, j, ("currency_before", "currency_after", "paise")) is not None:
            return True
    return False


def classify(tokens: tuple[Token, ...], i: int) -> tuple[Entry, float] | None:
    """Number/scale/fraction entry for token ``i``, or None.

    Applies the look-alike rules from ``data/context.tsv`` (``de do``,
    ``ek baar``, ``mere saath`` ...).
    """
    hit = _raw(tokens, i)
    if hit is None:
        return None
    w = tokens[i].norm
    rules = lexicon().rules
    prev = tokens[i - 1] if i > 0 else None
    nxt = tokens[i + 1] if i + 1 < len(tokens) else None
    for words, ctx in rules.get("not_number_if_prev", ()):
        if w in words and prev is not None and prev.norm in ctx:
            return None
    for words, ctx in rules.get("not_number_if_next", ()):
        if w in words and nxt is not None and nxt.norm in ctx:
            return None
    for words, _ in rules.get("needs_numeric_neighbour", ()):
        if w in words and not _numeric_neighbour(tokens, i):
            if sum(t.type == "word" for t in tokens) > 1:
                return None
    for words, _ in rules.get("verb_if_clause_final", ()):
        if w in words and (nxt is None or nxt.type == "punct") and prev is not None and prev.type == "word":
            connectors = {c for _, ctx in rules.get("connectors", ()) for c in ctx}
            plain = _raw(tokens, i - 1) is None and prev.norm not in connectors
            if plain and match_marker(tokens, i - 1, ("point", "double", "triple")) is None:
                return None
    return hit


def _literal(tok: Token) -> Decimal:
    return Decimal(tok.norm)


def _digit_at(tokens: tuple[Token, ...], i: int) -> tuple[str, float] | None:
    """A single spoken or written digit at ``i``."""
    if i >= len(tokens):
        return None
    t = tokens[i]
    if t.type == "num":
        return (t.norm, 1.0) if t.norm.isdigit() and len(t.norm) == 1 else None
    hit = classify(tokens, i)
    if hit and hit[0].cat == "num" and hit[0].value < 10:
        return str(int(hit[0].value)), hit[1]
    return None


def read_digits(tokens: tuple[Token, ...], i: int, *, forced: bool) -> tuple[str, int, float] | None:
    """Read a spoken digit sequence (``nau aath saat``, ``double nine``).

    Without ``forced`` (no ``kind="digits"`` hint) a sequence is recognised only
    when it has three or more digits, or uses double/triple, and is not followed
    by a scale word.
    """
    out, conf, j, special = "", 1.0, i, False
    while j < len(tokens):
        rep = match_marker(tokens, j, ("double", "triple"))
        if rep is not None:
            d = _digit_at(tokens, rep[1])
            if d is None:
                break
            out += d[0] * (2 if rep[0] == "double" else 3)
            conf, j, special = min(conf, d[1]), rep[1] + 1, True
            continue
        d = _digit_at(tokens, j)
        if d is None:
            break
        out, conf, j = out + d[0], min(conf, d[1]), j + 1
    if not out:
        return None
    if not forced:
        nxt = classify(tokens, j)
        if nxt is not None or (j < len(tokens) and tokens[j].type == "num"):
            return None
        if len(out) < 3 and not special:
            return None
    return out, j, conf


def read_number(
    tokens: tuple[Token, ...], i: int, *, kind: str | None = None, unit_follows: bool = False
) -> NumberRead | Rejected | None:
    """Read one cardinal number starting at token ``i``.

    Grammar (Indian system): Hindi 0-99 are atomic words; ``sau`` multiplies what
    is in front of it (``pachees sau`` = 2500); larger scales must descend
    (crore > lakh > hazaar). Fraction idioms are handled by :mod:`kitna.fractions`.
    """
    n = len(tokens)
    total = Decimal(0)
    cur: Decimal | None = None
    unit_used = hundred_used = has_scale = False
    last_big: Decimal | None = None
    mantissa: Decimal | None = None
    conf = 1.0
    notes: list[str] = []
    j = i
    english_only = True

    def note_scale() -> None:
        nonlocal mantissa, has_scale
        if not has_scale:
            mantissa = cur
        has_scale = True

    while j < n:
        t = tokens[j]
        if t.type == "num":
            v = _literal(t)
            english_only = False
            if unit_used or (cur is not None and v >= _HUNDRED) or (last_big is not None and v >= last_big):
                break
            cur = (cur or Decimal(0)) + v
            unit_used = True
            j += 1
            # glued abbreviations: 5k, 2.5L
            if j < n and tokens[j].glued and tokens[j].type == "word":
                ab = tokens[j].norm
                if ab == "k":
                    note_scale()
                    cur *= 1000
                    j += 1
                elif ab == "l" and kind == "money":
                    after = j + 1
                    ok = after >= n or tokens[after].type == "punct" or match_marker(
                        tokens, after,
                        ("currency_after", "approx_after", "max_after", "range_sep", "currency_tail"),
                    ) is not None
                    if not ok:
                        return Rejected(j + 1, "'L' followed by a noun reads as litres, not lakh")
                    note_scale()
                    cur *= 100000
                    notes.append("'L' read as lakh because kind='money'")
                    j += 1
            continue
        if t.type != "word":
            break
        whole = cur is not None and cur == cur.to_integral_value()
        if match_marker(tokens, j, ("point",)) and unit_used and whole and cur is not None:
            digits, k = "", j + 1
            while (d := _digit_at(tokens, k)) is not None:
                digits, conf, k = digits + d[0], min(conf, d[1]), k + 1
            if k < n and tokens[k].type == "num" and not digits:
                digits, k = tokens[k].norm, k + 1
            if not digits.isdigit():
                break
            cur += Decimal("0." + digits)
            j = k
            continue
        if match_marker(tokens, j, ("and",)) and (cur is not None or total) and j + 1 < n:
            nxt = classify(tokens, j + 1)
            if nxt and nxt[0].en and nxt[0].cat == "num" and not unit_used:
                j += 1
                continue
            break
        hit = classify(tokens, j)
        if hit is None:
            break
        e, c = hit
        if e.cat == "frac":
            english_only = False
            if cur is not None or unit_used:
                break
            nxt = classify(tokens, j + 1)
            nxt_lit = j + 1 < n and tokens[j + 1].type == "num"
            try:
                if e.ftype == "add" and (nxt_lit or (nxt and nxt[0].cat == "num")):
                    base = _literal(tokens[j + 1]) if nxt_lit else nxt[0].value  # type: ignore[index]
                    if base != base.to_integral_value() or base >= _HUNDRED:
                        break
                    cur = fractions.with_number(e, base)
                    conf = min(conf, c, 1.0 if nxt_lit else nxt[1])  # type: ignore[index]
                    if e.name == "saade" and base == 1:
                        conf = min(conf, policy().conf("saade_ek"))
                        notes.append("Nonstandard saade ek interpreted as 1.5; standard wording is dedh (Q9)")
                    j += 2
                elif nxt and nxt[0].cat == "scale":
                    cur = fractions.before_scale(e)
                    conf = min(conf, c)
                    j += 1
                else:
                    cur, factor = fractions.alone(e, unit_follows=unit_follows)
                    conf = min(conf, c) * factor
                    if factor < 1:
                        notes.append(f"bare '{e.name}' is unusual")
                    j += 1
            except fractions.RejectedFraction as ex:
                end = j + 2 if (nxt_lit or (nxt and nxt[0].cat == "num")) else j + 1
                return Rejected(end, str(ex))
            unit_used = True
            continue
        if e.cat == "num":
            if unit_used:
                break
            english_only = english_only and e.en
            v = e.value
            j += 1
            if e.en and v >= 20 and v % 10 == 0:  # English "twenty five" / "twenty-five"
                k = j + 1 if j < n and tokens[j].type == "sym" and tokens[j].norm == "-" else j
                unit = classify(tokens, k)
                if unit and unit[0].en and unit[0].cat == "num" and 0 < unit[0].value < 10:
                    v, c, j = v + unit[0].value, min(c, unit[1]), k + 1
            cur = (cur or Decimal(0)) + v
            conf = min(conf, c)
            unit_used = True
            continue
        # scale word
        if hundred_used and e.value == _HUNDRED:
            break
        english_only = english_only and e.en and (cur is None)  # "two hundred" is anchored by its scale
        s = e.value
        if s == _HUNDRED:
            if hundred_used or (cur is not None and not unit_used):
                break
            if cur is None:
                cur = Decimal(1)
            note_scale()
            cur *= _HUNDRED
            hundred_used, unit_used = True, False
        else:
            if last_big is not None and s >= last_big:
                break
            if cur is None:
                if total:
                    break
                cur = Decimal(1)
            note_scale()
            total += cur * s
            cur, unit_used, hundred_used, last_big = None, False, False, s
        conf = min(conf, c)
        j += 1

    if j == i or (cur is None and not total):
        return None
    value = total + (cur or Decimal(0))
    mult: Decimal | None = None
    if has_scale and mantissa:
        # a power-of-ten ratio means nothing was added after the scale (teen hazaar, dhai lakh)
        probe = value / mantissa
        if probe in _PURE_MULTIPLIERS:
            mult = probe
    return NumberRead(value, j, conf, has_scale, english_only, mantissa, mult, tuple(notes))


_PURE_MULTIPLIERS = frozenset(Decimal(10) ** p for p in range(2, 13))
