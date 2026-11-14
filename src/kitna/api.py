"""The public ``parse`` function and its convenience wrappers."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import date, datetime, time
from typing import Any

from ._types import KINDS, KitnaError, Range, Result, canonical
from .dates import DatePiece, OffsetPiece, clause_bounds, find_cue, read_date, resolve, shift
from .money import Skip, read_quantity
from .normalize import Token, match_temporal, tokenize
from .numerals import read_digits
from .time import read_duration, read_time

_TEMPORAL = ("time", "duration", "date", "datetime")


def _result(text: str, tokens: tuple[Token, ...], i: int, j: int, kind: str, value: Any,
            candidates: tuple[Any, ...], conf: float, notes: tuple[str, ...]) -> Result:
    s, e = tokens[i].start, tokens[j - 1].end
    canon = canonical(value) if not candidates else " | ".join(canonical(c) for c in candidates)
    return Result((s, e), text[s:e], kind, value, canon, round(conf, 4), candidates,
                  ambiguous=bool(candidates), notes=tuple(dict.fromkeys(notes)))


CLOCK_WARNING = ("relative_base was not given: resolved against the system clock, so the result depends on "
                 "when parse() was called")


def _temporal(text: str, tokens: tuple[Token, ...], base: datetime, base_has_time: bool,
              prefer: str | None, kind: str | None, base_given: bool, strict: bool) -> list[tuple[int, int, Result]]:
    out: list[tuple[int, int, Result]] = []
    n, i = len(tokens), 0
    merge = kind in (None, "datetime")

    def relative(i: int, j: int, res: Result) -> Result:
        """Mark (or, in strict mode, refuse) a result that needed 'today' / 'now'."""
        if base_given:
            return res
        if strict and (kind is None or kind == res.kind):
            raise KitnaError(f"{res.text!r} is relative to today/now: pass relative_base (strict mode)")
        return replace(res, warnings=(*res.warnings, CLOCK_WARNING))

    while i < n:
        if tokens[i].type == "punct":
            i += 1
            continue
        tr = read_time(tokens, i)
        if tr is not None:
            out.append((i, tr.end, _result(text, tokens, i, tr.end, "time", tr.value, tr.candidates,
                                           tr.confidence, tr.notes)))
            i = tr.end
            continue
        if match_temporal(tokens, i, "recurring"):
            # "har somvaar" (every Monday) is out of scope: skip it and the word after it
            i += 2
            continue
        piece = read_date(tokens, i, base.date())
        if isinstance(piece, OffsetPiece):
            if base_has_time:
                when = shift(base, piece.duration, piece.sign)
                res = _result(text, tokens, i, piece.end, "datetime", when, (), piece.confidence, ())
            else:
                res = _result(text, tokens, i, piece.end, "duration", piece.duration, (), piece.confidence,
                              ("offset from now (" + ("after" if piece.sign > 0 else "before")
                               + "): pass a datetime relative_base to resolve it",))
            out.append((i, piece.end, relative(i, piece.end, res)))
            i = piece.end
            continue
        if isinstance(piece, DatePiece):
            mark = relative if piece.uses_base else (lambda i, j, res: res)
            end = piece.end
            cue = find_cue(tokens, *clause_bounds(tokens, i))
            value, cands, conf, notes = resolve(piece, cue, prefer)
            # date + time said together -> one datetime
            k = end
            part = match_temporal(tokens, k, "particle")
            if part:
                k = part[1]
            tr = read_time(tokens, k) if merge and k < n else None
            if tr is not None and not isinstance(tr.value, Range) and not any(
                    isinstance(c, Range) for c in tr.candidates):
                days = (value,) if value is not None else cands
                times = (tr.value,) if tr.value is not None else tr.candidates
                combos = tuple(datetime.combine(d, t) for d in days for t in times if isinstance(t, time))
                single = combos[0] if len(combos) == 1 else None
                out.append((i, tr.end, mark(i, tr.end, _result(
                    text, tokens, i, tr.end, "datetime", single, () if single else combos,
                    min(conf, tr.confidence), notes + tr.notes))))
                i = tr.end
                continue
            until = match_temporal(tokens, end, "until")
            if until:
                end = until[1]
                rv: Any = Range(None, value) if value is not None else None
                rc: tuple[Any, ...] = tuple(Range(None, c) for c in cands)
                out.append((i, end, mark(i, end, _result(text, tokens, i, end, "date", rv, rc, conf, notes))))
            else:
                out.append((i, end, mark(i, end, _result(text, tokens, i, end, "date", value, cands, conf, notes))))
            i = end
            continue
        dur = read_duration(tokens, i)
        if dur is not None:
            out.append((i, dur[1], _result(text, tokens, i, dur[1], "duration", dur[0], (), dur[2], ())))
            i = dur[1]
            continue
        i += 1
    return out


def _quantities(text: str, tokens: tuple[Token, ...], kind: str | None) -> list[Result]:
    out: list[Result] = []
    i = 0
    while i < len(tokens):
        if tokens[i].type in ("punct", "reserved"):
            i += 1
            continue
        if kind in (None, "digits"):
            d = read_digits(tokens, i, forced=kind == "digits")
            if d is not None:
                digits, j, conf = d
                out.append(_result(text, tokens, i, j, "digits", digits, (), conf, ()))
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
    return out


def parse(
    text: str,
    kind: str | None = None,
    relative_base: date | datetime | None = None,
    *,
    prefer: str | None = None,
    strict: bool = False,
    now: Callable[[], datetime] | None = None,
) -> list[Result]:
    """Find quantities, money, times and dates in ``text``; results are in text order.

    ``kind`` is a hint and a filter: only results of that kind are returned, and
    it changes how bare numbers are read (``"money"``: rupee amounts;
    ``"digits"``: a digit string; ``"number"``: currency and time words ignored).

    ``relative_base`` is "today" (a ``date``) or "now" (a ``datetime``) for
    relative expressions (``kal``, ``somvaar``, ``3 din baad``, ``do ghante baad``).
    If it is omitted, the system clock is used and every result that needed it
    carries a ``warnings`` entry, because the output then depends on when you
    call. With ``strict=True`` such an expression raises :class:`KitnaError`
    instead. Absolute values (``5 baje``, ``15 August 2027``) never need a base.

    ``now`` replaces the system clock (a zero-argument callable returning a naive
    ``datetime``); it exists for tests and is used only when ``relative_base`` is
    omitted.

    ``prefer`` (``"future"`` or ``"past"``) resolves dates that are ambiguous only
    because a year, month or direction is missing. Off by default: ambiguous
    expressions come back with ``ambiguous=True`` and every candidate.

    No network, no I/O beyond reading the bundled data tables once.
    """
    if not isinstance(text, str):
        raise KitnaError(f"text must be str, not {type(text).__name__}")
    if kind is not None and kind not in KINDS:
        raise KitnaError(f"unknown kind {kind!r}; expected one of {', '.join(KINDS)}")
    if prefer not in (None, "future", "past"):
        raise KitnaError(f"prefer must be 'future', 'past' or None, not {prefer!r}")
    if relative_base is not None and not isinstance(relative_base, date):
        raise KitnaError("relative_base must be a datetime.date or datetime.datetime")

    tokens = tokenize(text)
    results: list[Result] = []
    claimed = [False] * len(tokens)
    if kind is None or kind in _TEMPORAL:
        if isinstance(relative_base, datetime):
            base, has_time = relative_base.replace(tzinfo=None), True
        elif relative_base is not None:
            base, has_time = datetime.combine(relative_base, time(0, 0)), False
        else:
            clock = (now or datetime.now)()
            if not isinstance(clock, datetime):
                raise KitnaError("now() must return a datetime.datetime")
            base, has_time = clock.replace(tzinfo=None, second=0, microsecond=0), True
        for i, j, r in _temporal(text, tokens, base, has_time, prefer, kind, relative_base is not None, strict):
            results.append(r)
            claimed[i:j] = [True] * (j - i)
    if kind is None or kind not in _TEMPORAL:
        # numbers are read only from tokens no date/time expression has claimed
        start = 0
        while start < len(tokens):
            if claimed[start]:
                start += 1
                continue
            end = start
            while end < len(tokens) and not claimed[end]:
                end += 1
            results.extend(_quantities(text, tokens[start:end], kind))
            start = end
    results.sort(key=lambda r: r.span)
    return [r for r in results if kind is None or r.kind == kind]


def _first(
    text: str, kind: str, base: date | datetime | None = None, prefer: str | None = None, strict: bool = False
) -> Result | None:
    results = parse(text, kind=kind, relative_base=base, prefer=prefer, strict=strict)
    return results[0] if results else None


def parse_number(text: str) -> Result | None:
    """First number in ``text`` (currency words ignored), or ``None``."""
    return _first(text, "number")


def parse_money(text: str) -> Result | None:
    """First amount in ``text``, read as rupees, or ``None``."""
    return _first(text, "money")


def parse_time(text: str) -> Result | None:
    """First clock time or time range in ``text``, or ``None``."""
    return _first(text, "time")


def parse_date(
    text: str, relative_base: date | datetime | None = None, *, prefer: str | None = None, strict: bool = False
) -> Result | None:
    """First date in ``text``, or ``None``. See :func:`parse` for the arguments."""
    return _first(text, "date", relative_base, prefer, strict)
