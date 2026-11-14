"""Clock times: baje / bajke / bajne mein, day-parts, am/pm, time ranges, durations.

The contested parts (which hours each day-part word covers, what a bare hour
means) come from ``data/policy.tsv`` via :mod:`kitna.policy`.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from decimal import Decimal

from ._types import Duration, Range
from .normalize import Token, match_temporal
from .numerals import NumberRead, read_number
from .policy import policy

_DAY_MIN = 24 * 60


@dataclass(frozen=True, slots=True)
class _Point:
    minutes: int  # as said: hour * 60 + minutes (hour may be 0-24)
    meridiem: str | None  # explicit "am" / "pm"
    daypart: str | None
    end: int
    confidence: float
    marked: bool  # had baje / bajke / am / pm / a clock string


@dataclass(frozen=True, slots=True)
class TimeRead:
    end: int
    value: time | Range | None
    candidates: tuple[time | Range, ...]
    confidence: float
    notes: tuple[str, ...]


def _number(tokens: tuple[Token, ...], i: int) -> NumberRead | None:
    r = read_number(tokens, i, unit_follows=True)
    return r if isinstance(r, NumberRead) else None


def _point(tokens: tuple[Token, ...], i: int) -> _Point | None:
    n, j = len(tokens), i
    daypart: str | None = None
    dp = match_temporal(tokens, j, "daypart")
    if dp:
        daypart, j = dp
        part = match_temporal(tokens, j, "particle")
        if part:
            j = part[1]
    if j >= n:
        return None
    conf, marked = 1.0, False
    if tokens[j].type == "reserved" and ":" in tokens[j].text:
        h, m = (int(x) for x in tokens[j].norm.split(":"))
        if h > 24 or m > 59:
            return None
        minutes, marked, j = h * 60 + m, True, j + 1
    else:
        num = _number(tokens, j)
        if num is None or not 0 < num.value <= 24:
            return None
        mins = num.value * 60
        if mins != mins.to_integral_value():
            return None
        minutes, conf, j = int(mins), num.confidence, num.end
        whole_hour = num.value == num.value.to_integral_value()
        bk, bn = match_temporal(tokens, j, "bajke"), match_temporal(tokens, j, "bajne")
        if (bk or bn) and whole_hour:
            extra = _number(tokens, (bk or bn)[1])  # type: ignore[index]
            if extra is None or extra.value != extra.value.to_integral_value() or not 0 < extra.value < 60:
                return None
            minutes += int(extra.value) if bk else -int(extra.value)
            conf, j, marked = min(conf, extra.confidence), extra.end, True
            unit = match_temporal(tokens, j, "unit")
            if unit and unit[0] == "minute":
                j = unit[1]
        else:
            bj = match_temporal(tokens, j, "baje")
            if bj:
                j, marked = bj[1], True
    meridiem: str | None = None
    ap = match_temporal(tokens, j, "ampm")
    if ap:
        meridiem, j, marked = ap[0], ap[1], True
    if daypart is None and marked:  # "5 baje shaam ko"
        dp = match_temporal(tokens, j, "daypart")
        if dp:
            daypart, j = dp
    return _Point(minutes, meridiem, daypart, j, conf, marked)


def _resolve(p: _Point) -> tuple[list[time], float, list[str]]:
    """All 24-hour readings of a point, with confidence and notes."""
    minutes = p.minutes % _DAY_MIN
    h, m = divmod(minutes, 60)
    h12 = h % 12
    if p.meridiem:
        return [time(h12 + (12 if p.meridiem == "pm" else 0), m)], p.confidence, []
    if h >= 13 or (h == 0 and p.daypart is None and p.minutes % 60 == 0 and p.minutes == 0):
        return [time(h, m)], p.confidence, []
    if p.daypart:
        rule = policy().dayparts[p.daypart]
        said = h12 or 12
        if said in rule.am:
            return [time(h12, m)], p.confidence, []
        if said in rule.pm:
            return [time(h12 + 12, m)], p.confidence, []
        hh = h12 + (12 if rule.fallback == "pm" else 0)
        note = f"'{p.daypart}' is unusual with hour {said}; read as {rule.fallback.upper()}"
        return [time(hh, m)], p.confidence * policy().conf("odd_daypart"), [note]
    return [time(h12, m), time(h12 + 12, m)], p.confidence, ["no day-part word: AM or PM unknown"]


def read_time(tokens: tuple[Token, ...], i: int) -> TimeRead | None:
    """Read a clock time or a time range starting at token ``i``."""
    p1 = _point(tokens, i)
    if p1 is None:
        return None
    sep = match_temporal(tokens, p1.end, "range_sep")
    p2 = _point(tokens, sep[1]) if sep else None
    if p2 is not None and p2.marked:
        if p2.daypart is None and p2.meridiem is None and p1.daypart:
            p2 = _Point(p2.minutes, None, p1.daypart, p2.end, p2.confidence, True)
        c1, f1, n1 = _resolve(p1)
        c2, f2, n2 = _resolve(p2)
        if len(c1) == 2 and len(c2) == 2:
            pairs = [(c1[0], c2[0]), (c1[1], c2[1])]  # both AM or both PM
        else:
            pairs = [(a, b) for a in c1 for b in c2 if a < b] or [(a, b) for a in c1 for b in c2]
        end = p2.end
        until = match_temporal(tokens, end, "until")
        if until:
            end = until[1]
        ranges = tuple(Range(a, b) for a, b in pairs)
        rnotes = tuple(dict.fromkeys(n1 + n2))
        if len(ranges) == 1:
            return TimeRead(end, ranges[0], (), min(f1, f2), rnotes)
        return TimeRead(end, None, ranges, min(f1, f2), rnotes)
    if not p1.marked:
        return None
    cands, conf, notes = _resolve(p1)
    end = p1.end
    until = match_temporal(tokens, end, "until")
    if until:
        end = until[1]
        wrapped: list[time | Range] = [Range(None, c) for c in cands]
    else:
        wrapped = list(cands)
    if len(wrapped) == 1:
        return TimeRead(end, wrapped[0], (), conf, tuple(notes))
    return TimeRead(end, None, tuple(wrapped), conf, tuple(notes))


# --------------------------------------------------------------------------- durations

_ORDER = ("year", "month", "week", "day", "hour", "minute", "second")
#: a fractional amount of a unit becomes this many of the next smaller one
_SPLIT = {"year": ("month", 12), "month": ("day", 30), "week": ("day", 7), "day": ("hour", 24),
          "hour": ("minute", 60), "minute": ("second", 60)}


def read_duration(tokens: tuple[Token, ...], i: int) -> tuple[Duration, int, float] | None:
    """Read ``dhai ghante``, ``2 ghante 30 minute``, ``dedh saal`` ... at token ``i``.

    A fractional amount is carried into the next smaller unit (``dedh saal`` =
    1 year 6 months). A month is counted as 30 days for that purpose only.
    """
    parts: dict[str, int] = {}
    conf, j, last_rank = 1.0, i, -1
    while True:
        num = _number(tokens, j)
        if num is None:
            break
        unit = match_temporal(tokens, num.end, "unit")
        if unit is None or _ORDER.index(unit[0]) <= last_rank:
            break
        name, value = unit[0], num.value
        whole = int(value)
        frac = value - whole
        add = {name: whole} if whole else {}
        if frac:
            if name not in _SPLIT:
                break
            small, per = _SPLIT[name]
            sub = frac * per
            if sub != sub.to_integral_value():
                break
            add[small] = int(sub)
        if value <= 0 or value > Decimal(10000):
            break
        for k, v in add.items():
            parts[k] = parts.get(k, 0) + v
        conf, j, last_rank = min(conf, num.confidence), unit[1], _ORDER.index(name)
    if not parts:
        return None
    return Duration(**{k + "s": v for k, v in parts.items()}), j, conf
