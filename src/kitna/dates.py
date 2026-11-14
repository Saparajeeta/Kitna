"""Dates: aaj / kal / parso / narso, weekdays, offsets, absolute dates, and the
tense cues that decide whether ``kal`` is yesterday or tomorrow.

Contested rules (bare weekday, ``agle``, dates with no year, weak cues) are read
from ``data/policy.tsv`` via :mod:`kitna.policy`; nothing here hard-codes them.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from ._types import Duration
from .normalize import Token, detect_script, lexicon, match_temporal
from .numerals import NumberRead, read_number
from .policy import policy
from .time import read_duration


@dataclass(frozen=True, slots=True)
class DatePiece:
    """A date expression before its direction (past / future) is decided."""

    end: int
    fixed: date | None = None
    past: date | None = None
    future: date | None = None
    #: what to do with no strong cue: "ambiguous" (weak cues and ``prefer`` may
    #: decide, else all candidates), "future" / "past", or "flag" (always candidates)
    default: str = "ambiguous"
    flag: tuple[date, ...] = ()
    relative_word: bool = False  # kal / parso / narso
    confidence: float = 1.0
    notes: tuple[str, ...] = field(default=())


@dataclass(frozen=True, slots=True)
class OffsetPiece:
    """``do ghante baad``: an offset that needs the time of day to resolve."""

    end: int
    duration: Duration
    sign: int
    confidence: float


@dataclass(frozen=True, slots=True)
class Cue:
    direction: str | None  # strong cue: "future" | "past" | None
    weak: tuple[str, float, str] | None  # (direction, confidence, note)


# --------------------------------------------------------------------------- calendar helpers


def _add_months(d: date, months: int) -> date:
    y, m = divmod(d.year * 12 + d.month - 1 + months, 12)
    return date(y, m + 1, min(d.day, calendar.monthrange(y, m + 1)[1]))


def shift(d: datetime, dur: Duration, sign: int) -> datetime:
    """Apply a duration to a date-time (calendar months, clamped to month end)."""
    out = d.replace(year=d.year, month=d.month)
    moved = _add_months(out.date(), sign * (dur.years * 12 + dur.months))
    out = datetime.combine(moved, out.time())
    return out + sign * timedelta(weeks=dur.weeks, days=dur.days, hours=dur.hours,
                                  minutes=dur.minutes, seconds=dur.seconds)


def _week_start(d: date) -> date:
    back = d.weekday() if policy().choice("week.start") == "monday" else (d.weekday() + 1) % 7
    return d - timedelta(days=back)


def _in_week(start: date, weekday: int) -> date:
    return next(start + timedelta(days=k) for k in range(7) if (start + timedelta(days=k)).weekday() == weekday)


def _safe(y: int, m: int, d: int) -> date | None:
    try:
        return date(y, m, d)
    except ValueError:
        return None


def _around(base: date, candidates: list[date | None]) -> tuple[date | None, date | None]:
    """(latest candidate before base, earliest candidate on or after base)."""
    ok = sorted(c for c in candidates if c is not None)
    before = [c for c in ok if c < base]
    after = [c for c in ok if c >= base]
    return (before[-1] if before else None), (after[0] if after else None)


def _undated(base: date, prev: date | None, nxt: date | None, policy_key: str, what: str) -> DatePiece | None:
    if nxt is None or prev is None:
        return None
    if nxt == base:
        return DatePiece(0, fixed=base)
    mode = policy().choice(policy_key)
    default = "ambiguous" if mode == "flag" else mode
    return DatePiece(0, past=prev, future=nxt, default=default, notes=(f"{what}: last or next occurrence",))


def _day_number(tokens: tuple[Token, ...], i: int) -> tuple[int, int, float] | None:
    num = read_number(tokens, i)
    if not isinstance(num, NumberRead) or num.value != num.value.to_integral_value():
        return None
    if not 1 <= num.value <= 31 or num.has_scale:
        return None
    return int(num.value), num.end, num.confidence


# --------------------------------------------------------------------------- readers


def _numeric_date(tok: Token) -> date | None:
    for sep in "-/":
        parts = tok.norm.split(sep)
        if len(parts) == 3 and all(p.isdigit() for p in parts):
            a, b, c = (int(p) for p in parts)
            if len(parts[0]) == 4:
                return _safe(a, b, c)
            year = c + 2000 if len(parts[2]) <= 2 else c
            day, month = (a, b) if policy().choice("date.numeric_order") == "dmy" else (b, a)
            return _safe(year, month, day)
    return None


def _weekday(tokens: tuple[Token, ...], i: int, base: date) -> DatePiece | None:
    j = i
    mod: str | None = None
    for role in ("next", "prev", "this"):
        m = match_temporal(tokens, j, role)
        if m:
            mod, j = role, m[1]
            break
    week = False
    if mod:
        u = match_temporal(tokens, j, "unit")
        if u and u[0] == "week":
            week, j = True, u[1]
    wd_m = match_temporal(tokens, j, "weekday")
    if wd_m is None:
        return None
    wd, end = int(wd_m[0]), wd_m[1]
    nxt = base + timedelta(days=(wd - base.weekday() - 1) % 7 + 1)  # strictly after base
    prv = base - timedelta(days=(base.weekday() - wd - 1) % 7 + 1)  # strictly before base
    this_week = _in_week(_week_start(base), wd)
    pol = policy()
    if week:
        start = _week_start(base) + timedelta(days={"next": 7, "prev": -7, "this": 0}[mod or "this"])
        return DatePiece(end, fixed=_in_week(start, wd))
    if mod == "prev":
        return DatePiece(end, fixed=prv)
    if mod == "next":
        rule = pol.choice("weekday.agle")
        next_week = _in_week(_week_start(base) + timedelta(days=7), wd)
        if rule == "next_occurrence" or nxt == next_week:
            return DatePiece(end, fixed=nxt)
        if rule == "next_week":
            return DatePiece(end, fixed=next_week)
        return DatePiece(end, default="flag", flag=(nxt, next_week), past=prv,
                         notes=("'agle <weekday>': the coming one or next week's",))
    if mod == "this":
        on_or_after = base if base.weekday() == wd else nxt
        return DatePiece(end, past=this_week if this_week < base else prv, future=on_or_after, default="future")
    if base.weekday() == wd:
        rule = pol.choice("weekday.same_day")
        if rule == "flag":
            return DatePiece(end, default="flag", flag=(base, nxt), past=prv,
                             notes=("today is that weekday: today or next week",))
        return DatePiece(end, past=prv, future=base if rule == "today" else nxt, default="future")
    return DatePiece(end, past=prv, future=nxt, default="future")


def _read_date(tokens: tuple[Token, ...], i: int, base: date) -> DatePiece | None:
    n = len(tokens)
    pol = policy()
    t = tokens[i]

    if t.type == "reserved":
        d = _numeric_date(t)
        return DatePiece(i + 1, fixed=d) if d else None

    # "aaj se paanch din baad"
    ft = match_temporal(tokens, i, "from_today")
    if ft:
        dur = read_duration(tokens, ft[1])
        if dur:
            after = match_temporal(tokens, dur[1], "after")
            if after and not (dur[0].hours or dur[0].minutes or dur[0].seconds):
                moved = shift(datetime.combine(base, datetime.min.time()), dur[0], 1).date()
                return DatePiece(after[1], fixed=moved, confidence=dur[2])

    rel = match_temporal(tokens, i, "rel")
    if rel:
        key, end = rel
        if key in ("0", "+1", "-1"):
            return DatePiece(end, fixed=base + timedelta(days=int(key)))
        days = {"kal": 1, "parso": 2, "narso": 3}[key]
        conf = pol.conf("narso") if key == "narso" else 1.0
        notes = ("narso / tarso is regional",) if key == "narso" else ()
        return DatePiece(end, past=base - timedelta(days=days), future=base + timedelta(days=days),
                         relative_word=True, confidence=conf, notes=notes)

    wd = _weekday(tokens, i, base)
    if wd:
        return wd

    # "agle mahine ki 5 tareekh"
    for role, step in (("next", 1), ("prev", -1), ("this", 0)):
        m = match_temporal(tokens, i, role)
        u = match_temporal(tokens, m[1], "unit") if m else None
        if u and u[0] == "month":
            j = u[1]
            of = match_temporal(tokens, j, "of")
            if of:
                j = of[1]
            dn = _day_number(tokens, j)
            if dn:
                first = _add_months(base.replace(day=1), step)
                d = _safe(first.year, first.month, dn[0])
                end = dn[1]
                tk = match_temporal(tokens, end, "tareekh")
                if tk:
                    end = tk[1]
                if d:
                    return DatePiece(end, fixed=d, confidence=dn[2])
            return None

    # month first: "August 15, 2027" (English order)
    mon = match_temporal(tokens, i, "month")
    dn = _day_number(tokens, mon[1]) if mon else _day_number(tokens, i)
    if mon is None and dn is not None:
        mon2 = match_temporal(tokens, dn[1], "month")
        if mon2:
            day, month, end, conf = dn[0], int(mon2[0]), mon2[1], dn[2]
        else:
            tk = match_temporal(tokens, dn[1], "tareekh")
            if tk is None:
                return None
            # "20 tareekh": no month
            months = [_add_months(base.replace(day=1), k) for k in range(-12, 13)]
            prev, nxt = _around(base, [_safe(m.year, m.month, dn[0]) for m in months])
            piece = _undated(base, prev, nxt, "date.no_month", "no month given")
            return piece and DatePiece(tk[1], piece.fixed, piece.past, piece.future, piece.default,
                                       confidence=dn[2], notes=piece.notes)
    elif mon is not None and dn is not None:
        day, month, end, conf = dn[0], int(mon[0]), dn[1], dn[2]
    else:
        return None
    if end < n and tokens[end].type == "punct" and tokens[end].text == "," and end + 1 < n:
        end_y = end + 1
    else:
        end_y = end
    if end_y < n and tokens[end_y].type == "num" and len(tokens[end_y].norm) == 4 and tokens[end_y].norm.isdigit():
        d = _safe(int(tokens[end_y].norm), month, day)
        return DatePiece(end_y + 1, fixed=d, confidence=conf) if d else None
    prev, nxt = _around(base, [_safe(y, month, day) for y in range(base.year - 8, base.year + 9)])
    piece = _undated(base, prev, nxt, "date.no_year", "no year given")
    return piece and DatePiece(end, piece.fixed, piece.past, piece.future, piece.default,
                               confidence=conf, notes=piece.notes)


def read_date(tokens: tuple[Token, ...], i: int, base: date) -> DatePiece | OffsetPiece | None:
    """Read one date expression (or a sub-day offset) starting at token ``i``."""
    piece = _read_date(tokens, i, base)
    if piece is not None:
        return piece
    # "3 din baad", "do hafte pehle", "do ghante baad"
    dur = read_duration(tokens, i)
    if dur:
        for role, sign in (("after", 1), ("before", -1)):
            m = match_temporal(tokens, dur[1], role)
            if m:
                if dur[0].hours or dur[0].minutes or dur[0].seconds:
                    return OffsetPiece(m[1], dur[0], sign, dur[2])
                moved = shift(datetime.combine(base, datetime.min.time()), dur[0], sign).date()
                return DatePiece(m[1], fixed=moved, confidence=dur[2])
    return None


# --------------------------------------------------------------------------- cues


def clause_bounds(tokens: tuple[Token, ...], i: int) -> tuple[int, int]:
    """Token range of the clause containing token ``i``."""
    def is_break(k: int) -> bool:
        return tokens[k].type == "punct" or match_temporal(tokens, k, "clause_break") is not None

    lo = i
    while lo > 0 and not is_break(lo - 1):
        lo -= 1
    hi = i
    while hi < len(tokens) and not is_break(hi):
        hi += 1
    return lo, hi


def find_cue(tokens: tuple[Token, ...], lo: int, hi: int) -> Cue:
    """Tense cue inside tokens[lo:hi]. Two opposite strong cues cancel out."""
    lex, pol = lexicon(), policy()
    suffixes = [p[0] for _, p in lex.temporal.get("cue_future_suffix", ())]
    blocked = {p[0] for _, p in lex.temporal.get("cue_not_future", ())}
    future = past = False
    for k in range(lo, hi):
        if tokens[k].type != "word":
            continue
        w = tokens[k].norm
        if match_temporal(tokens, k, "cue_future_word"):
            future = True
        elif match_temporal(tokens, k, "cue_past_word"):
            past = True
        elif w not in blocked and any(w.endswith(s) and len(w) > len(s) for s in suffixes):
            future = True
        elif k + 1 < hi and match_temporal(tokens, k + 1, "cue_future_na"):
            deva = detect_script(w) == "devanagari"
            if (deva and w.endswith("ना")) or (not deva and len(w) >= 4 and w.endswith("na")):
                future = True  # "jaana hai" = have to go
    if future != past:
        return Cue("future" if future else "past", None)
    if future and past:
        return Cue(None, None)
    words = [tokens[k].norm for k in range(lo, hi) if tokens[k].type == "word"]
    imperative = pol.words("cue.weak_imperative")
    final_only = {"do", "दो"}
    if any(w in imperative and (w not in final_only or idx == len(words) - 1) for idx, w in enumerate(words)):
        return Cue(None, ("future", pol.conf("weak_cue_imperative"), "imperative request read as a weak future cue"))
    if any(w in pol.words("cue.weak_present") for w in words):
        return Cue(None, ("future", pol.conf("weak_cue_present"), "present tense read as a weak future cue"))
    return Cue(None, None)


def resolve(
    piece: DatePiece, cue: Cue, prefer: str | None
) -> tuple[date | None, tuple[date, ...], float, tuple[str, ...]]:
    """Decide a :class:`DatePiece`: ``(value, candidates, confidence, notes)``.

    Order: a strong tense cue; the piece's own default; a weak cue; the caller's
    ``prefer``; otherwise every candidate, flagged.
    """
    if piece.fixed is not None:
        return piece.fixed, (), piece.confidence, piece.notes

    def pick(direction: str) -> date | None:
        return piece.future if direction == "future" else piece.past

    if cue.direction and pick(cue.direction) is not None:
        note = f"{cue.direction} tense cue"
        return pick(cue.direction), (), piece.confidence, (*piece.notes, note)
    if piece.default in ("future", "past") and pick(piece.default) is not None:
        return pick(piece.default), (), piece.confidence, piece.notes
    if piece.default == "flag":
        return None, tuple(sorted(piece.flag)), piece.confidence, piece.notes
    if cue.weak and pick(cue.weak[0]) is not None:
        return pick(cue.weak[0]), (), piece.confidence * cue.weak[1], (*piece.notes, cue.weak[2])
    allowed = not piece.relative_word or policy().choice("prefer.relative_words") == "yes"
    if prefer and allowed and pick(prefer) is not None:
        return pick(prefer), (), piece.confidence, (*piece.notes, f"resolved by prefer={prefer!r}")
    cands = tuple(sorted(c for c in (piece.past, piece.future) if c is not None))
    return None, cands, piece.confidence, (*piece.notes, "no tense cue: direction unknown")
