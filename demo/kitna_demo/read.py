"""'Read my message': run Kitna, then turn the results into display-ready items and HTML."""
from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass, field
from html import escape
from typing import Any

import kitna
from kitna import Range, Result

from .say import KIND_LABEL, level, plain
from .why import Why, explain

MAX_TEXT = 2000
MAX_CHOICES = 4  # ambiguous values that get their own question; more are still listed on their cards
EMPTY_HTML = ('<div class="k-empty">Type or paste a message above, or tap an example. '
              'Try: <q>kal 5 baje dhai lakh rupaye bhej dena</q></div>')


class InputError(ValueError):
    """Something the user typed cannot be used; the message is safe to show."""


@dataclass
class Item:
    index: int
    result: Result
    options: list[Any]
    chosen: int | None
    why: list[Why]
    base: dt.datetime

    @property
    def ambiguous(self) -> bool:
        return self.result.ambiguous

    @property
    def value(self) -> Any:
        """The value in effect: the parser's, or the reading the user picked; ``None`` while undecided."""
        if not self.ambiguous:
            return self.result.value
        return None if self.chosen is None else self.options[self.chosen]

    @property
    def decided(self) -> bool:
        return self.value is not None

    def labels(self, *, short: bool = False) -> list[str]:
        return [plain(o, self.base, short=short) for o in self.options]

    @property
    def reading(self) -> str:
        if self.decided:
            text = plain(self.value, self.base)
        else:
            text = self._either()
        return ("about " if self.result.approximate else "") + text

    def _either(self) -> str:
        """Every reading, without repeating the part they share ('tomorrow, Fri 13 Nov 2026, 5:00 AM or 5:00 PM')."""
        opts = self.options
        if len(opts) > 1 and all(isinstance(o, dt.datetime) for o in opts):
            today = self.base.date()
            if len({o.date() for o in opts}) == 1:
                return f"{plain(opts[0].date(), self.base)}, " + " or ".join(plain(o.time()) for o in opts)
            if len({o.time() for o in opts}) == 1:
                days = " or ".join(plain(o.date(), self.base, short=(o.date() - today).days in range(-2, 3))
                                   for o in opts)
                return f"{days}, at {plain(opts[0].time())}"
            return " or ".join(self.labels(short=True))
        return " or ".join(self.labels())

    @property
    def question(self) -> str:
        """'Did you mean tomorrow or yesterday?' for a two-way choice."""
        opts = self.options
        if len(opts) == 2:
            a, b = self.labels(short=True)
            if all(isinstance(o, dt.datetime) for o in opts):
                if opts[0].date() == opts[1].date():
                    a, b = plain(opts[0].time()), plain(opts[1].time())
                elif opts[0].time() == opts[1].time():
                    a, b = plain(opts[0].date(), self.base, short=True), plain(opts[1].date(), self.base, short=True)
            return f"‘{self.result.text}’: did you mean {a} or {b}?"
        return f"‘{self.result.text}’: which one did you mean?"

    def reason(self, lang: str = "en") -> str:
        lines = [w.text(lang) for w in self.why if w.is_ambiguity]
        return " ".join(lines)


@dataclass
class Reading:
    text: str
    base: dt.datetime
    items: list[Item] = field(default_factory=list)

    @property
    def undecided(self) -> list[Item]:
        return [i for i in self.items if not i.decided]

    @property
    def questions(self) -> list[Item]:
        """Ambiguous items that get a question, in text order (at most MAX_CHOICES)."""
        return [i for i in self.items if i.ambiguous][:MAX_CHOICES]


def parse_base(day: str | None, clock: str | None) -> dt.datetime:
    """The user's 'now' from the two form fields; raises InputError with a plain message."""
    day, clock = (day or "").strip(), (clock or "").strip()
    if not day:
        raise InputError("Please fill in today's date (for example 2026-11-12).")
    try:
        d = dt.date.fromisoformat(day)
    except ValueError:
        raise InputError(f"‘{day}’ is not a date I can read. Use year-month-day, for example 2026-11-12.") from None
    try:
        hh, _, mm = (clock or "00:00").partition(":")
        t = dt.time(int(hh), int(mm or 0))
    except ValueError:
        raise InputError(f"‘{clock}’ is not a time I can read. Use 24-hour hours:minutes, for example 10:00.") from None
    return dt.datetime.combine(d, t)


def read(text: str, base: dt.datetime, choices: dict[int, int] | None = None) -> Reading:
    """Parse ``text``. ``choices`` maps an item index to the reading the user picked."""
    text = (text or "").strip()
    if len(text) > MAX_TEXT:
        raise InputError(f"That message is longer than {MAX_TEXT} characters. Please paste a shorter part.")
    reading = Reading(text, base)
    for index, result in enumerate(kitna.parse(text, relative_base=base)):
        options = list(result.candidates)
        chosen = (choices or {}).get(index)
        if chosen is not None and not 0 <= chosen < len(options):
            chosen = None
        reading.items.append(Item(index, result, options, chosen, explain(result), base))
    return reading


# ---------------------------------------------------------------- HTML

def highlighted(reading: Reading) -> str:
    """The message with each found value marked and its plain reading right next to it."""
    if not reading.text:
        return EMPTY_HTML
    if not reading.items:
        return ('<div class="k-empty"><strong>No number, amount, date or time found in this message.</strong><br>'
                'If there is one, Kitna missed it. Please tell us in “Was this right?” below.</div>')
    out, pos = [], 0
    for item in reading.items:
        start, end = item.result.span
        out.append(escape(reading.text[pos:start]))
        _, css = level(item.result.confidence, item.ambiguous, item.chosen is not None)
        kind = KIND_LABEL.get(item.result.kind, "Value")
        out.append(f'<mark class="k-hl k-{css}" title="{escape(kind)}">{escape(reading.text[start:end])}'
                   f'<span class="k-eq"> = {escape(item.reading)}</span></mark>')
        pos = end
    out.append(escape(reading.text[pos:]))
    return f'<div class="k-msg" role="status" aria-live="polite">{"".join(out)}</div>'


def _details(item: Item) -> str:
    r = item.result
    rows = [("Words read", r.text), ("Type of value", KIND_LABEL.get(r.kind, r.kind)),
            ("Exact value for software", r.canonical if not item.ambiguous else " or ".join(r.canonical.split(" | "))),
            ("Position in the message", f"characters {r.span[0] + 1} to {r.span[1]}"),
            ("Confidence score (an ordering, not a probability)",
             "not shown: the value is ambiguous" if item.ambiguous else f"{r.confidence:.2f}")]
    if isinstance(r.value, Range) or any(isinstance(o, Range) for o in item.options):
        rows.append(("Shape", "a range (from … to …)"))
    body = "".join(f"<tr><th scope='row'>{escape(k)}</th><td>{escape(str(v))}</td></tr>" for k, v in rows)
    return f'<details class="k-det"><summary>Details</summary><table>{body}</table></details>'


def cards(reading: Reading, lang: str = "en") -> str:
    """One summary card per value."""
    if not reading.items:
        return ""
    out = []
    for item in reading.items:
        label, css = level(item.result.confidence, item.ambiguous, item.chosen is not None)
        whys = []
        for w in item.why:
            q = w.contested()
            tag = ""
            if q:
                tag = (f' <span class="k-rule">Contested rule <code>{escape(w.policy_key or "")}</code> '
                       f'(open question {escape(q)}, waiting for native speakers)</span>')
            whys.append(f"<li>{escape(w.text(lang))}{tag}</li>")
        ask = ""
        if item.ambiguous and not item.decided:
            ask = '<p class="k-ask">Kitna is not sure. Pick the reading you meant in the question above.</p>'
        out.append(
            f'<section class="k-card k-{css}" aria-label="{escape(KIND_LABEL.get(item.result.kind, "Value"))}">'
            f'<div class="k-top"><span class="k-kind">{escape(KIND_LABEL.get(item.result.kind, "Value"))}</span>'
            f'<span class="k-chip k-chip-{css}">{escape(label)}</span></div>'
            f'<div class="k-said">“{escape(item.result.text)}”</div>'
            f'<div class="k-read">{escape(item.reading)}</div>{ask}'
            f'<div class="k-why"><span class="k-whyh">{"क्यों?" if lang == "hi" else "Why?"}</span>'
            f'<ul>{"".join(whys)}</ul></div>{_details(item)}</section>')
    return f'<div class="k-cards">{"".join(out)}</div>'


def as_json(reading: Reading) -> str:
    """What a program receives: one object per value (kitna's documented result format)."""
    rows = []
    for item in reading.items:
        row = item.result.to_dict()
        if item.ambiguous and item.chosen is not None:
            row["chosen_by_user"] = kitna.canonical(item.value)
        rows.append(row)
    return json.dumps(rows, ensure_ascii=False, indent=2)
