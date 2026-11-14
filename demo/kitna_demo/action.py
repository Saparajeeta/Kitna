"""'Make it an action': the tool call an agent could send, shown as a confirmation card.

A PREVIEW ONLY. Nothing is executed. The action is picked by simple keyword rules written for this
demo; in a real agent the language model picks the tool and Kitna supplies or checks the values.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from dataclasses import dataclass, field
from html import escape
from typing import Any

import kitna
from kitna import Duration, Money, Range
from kitna.normalize import tokenize

from .read import Item, Reading
from .say import plain, rupees

PENDING = "<choose above>"
HOW = ("How this card is made: simple keyword rules written for this demo pick the action. In a real agent "
       "the language model picks the tool, and Kitna supplies or checks the numbers, dates and times.")
_INTENTS: tuple[tuple[str, frozenset[str]], ...] = (
    ("set_reminder", frozenset("yaad remind reminder alarm याद रिमाइंडर".split())),
    ("book_ticket", frozenset("ticket tickets train flight bus book booking टिकट ट्रेन बुक".split())),
    ("record_promise_to_pay", frozenset("emi kist kisht kisht bakaya due overdue jama किस्त बकाया जमा".split())),
    ("place_order", frozenset("order cod delivery deliver parcel ऑर्डर डिलीवरी".split())),
    ("record_income", frozenset("salary tankhwah tankha vetan ctc income सैलरी तनख्वाह वेतन".split())),
    ("transfer", frozenset("bhej bhejo bhejna bhejdo transfer send pay payment bhijwa भेज भेजो भेजना ट्रांसफर".split())),
)
_NOT_A_NAME = frozenset("mujh mujhe mujhko usko unko isko inko aap aapko tum tumko hum humko kis kisi sab kal aaj "
                        "parso shaam subah raat dopahar sir madam ji bhai मुझे उसको आपको".split())


@dataclass
class Action:
    tool: str | None
    arguments: dict[str, Any] = field(default_factory=dict)
    sentence: str = ""
    blocked: bool = False
    waiting_for: list[str] = field(default_factory=list)

    @property
    def call_text(self) -> str:
        if not self.tool:
            return ""
        parts = []
        for k, v in self.arguments.items():
            parts.append(f"{k}={PENDING}" if v == PENDING else f"{k}={json.dumps(v, ensure_ascii=False)}")
        return f"{self.tool}({', '.join(parts)})"

    @property
    def call_json(self) -> str:
        if not self.tool:
            return ""
        return json.dumps({"name": self.tool, "arguments": self.arguments}, ensure_ascii=False, indent=2)


def _recipient(reading: Reading) -> str | None:
    """The word before 'ko' when it is not part of a value and not a pronoun or time word."""
    spans = [i.result.span for i in reading.items]
    for m in re.finditer(r"(\S+)\s+(?:ko|को)(?=\s|$|[,.!?।])", reading.text):
        word = m.group(1).strip(",.!?।\"'()")
        if not word or any(ch.isdigit() for ch in word):
            continue
        inside = any(s <= m.start(1) < e for s, e in spans)
        if not inside and word.lower() not in _NOT_A_NAME:
            return word
    return None


def _first(reading: Reading, kinds: tuple[str, ...]) -> Item | None:
    return next((i for i in reading.items if i.result.kind in kinds), None)


def _arg(item: Item | None, action: Action) -> tuple[Any, Any]:
    """(machine value, the value itself) for one item; marks the action blocked while it is undecided."""
    if item is None:
        return None, None
    if not item.decided:
        action.blocked = True
        action.waiting_for.append(item.result.text)
        return PENDING, None
    value = item.value
    if isinstance(value, Range):
        value = value.max if value.max is not None else value.min
    if isinstance(value, Money):
        return (int(value.amount) if value.amount == value.amount.to_integral_value() else float(value.amount)), value
    if isinstance(value, Duration):
        return kitna.canonical(value), value
    if isinstance(value, (dt.date, dt.time)):
        return kitna.canonical(value), value
    try:
        return (int(value) if value == int(value) else float(value)), value
    except (TypeError, ValueError):
        return str(value), value


def _when_words(value: Any, base: dt.datetime) -> str:
    if value is None:
        return ""
    if isinstance(value, dt.datetime):
        return " " + plain(value, base, short=True)
    if isinstance(value, dt.date):
        text = plain(value, base, short=True)
        return f" {text}" if text[:1].islower() else f" on {text}"
    return " at " + plain(value, base)


def build(reading: Reading) -> Action:
    """Pick an action by keyword and fill it from the values in effect."""
    words = {t.norm for t in tokenize(reading.text) if t.type == "word"}
    tool = next((name for name, keys in _INTENTS if words & keys), None)
    amount_item = _first(reading, ("money",)) or _first(reading, ("number",))
    when_item = _first(reading, ("datetime", "date", "time"))
    length_item = _first(reading, ("duration",))
    if tool is None and length_item is not None:
        tool = "schedule_meeting" if words & {"meeting", "call", "मीटिंग"} else "set_timer"
    if tool is None and amount_item is not None and amount_item.result.kind == "money" and _recipient(reading):
        tool = "transfer"
    action = Action(tool)
    if tool is None:
        return action
    base = reading.base
    pending = "…"
    if tool == "transfer":
        to = _recipient(reading)
        amount, money = _arg(amount_item, action)
        when, when_v = _arg(when_item, action)
        action.arguments = {k: v for k, v in (("to", to), ("amount", amount), ("currency", "INR"), ("when", when))
                            if v is not None}
        shown = rupees(money.amount) if isinstance(money, Money) else (plain(money) if money is not None else pending)
        if amount is None:
            shown = "(no amount found)"
        action.sentence = (f"Send {shown} to {to or '(no recipient found)'}"
                           f"{_when_words(when_v, base) if when != PENDING else ' ' + pending}?")
    elif tool == "set_reminder":
        when, when_v = _arg(when_item, action)
        note = re.sub(r"\s+", " ", _without_values(reading)).strip(" ,.-")
        action.arguments = {k: v for k, v in (("when", when), ("note", note[:80] or None)) if v is not None}
        action.sentence = f"Set a reminder{_when_words(when_v, base) if when != PENDING else ' ' + pending}?"
    elif tool == "book_ticket":
        count_item = _first(reading, ("number",))
        when, when_v = _arg(when_item, action)
        count, _ = _arg(count_item, action)
        mode = next((m for m in ("train", "flight", "bus") if m in words), None)
        action.arguments = {k: v for k, v in (("mode", mode), ("passengers", count), ("travel_date", when))
                            if v is not None}
        n = count if isinstance(count, int) else None
        action.sentence = (f"Book {n if n else 'a'} {mode or 'travel'} ticket{'s' if n and n > 1 else ''}"
                           f"{_when_words(when_v, base) if when != PENDING else ' ' + pending}?")
    elif tool == "record_promise_to_pay":
        amount, money = _arg(amount_item, action)
        when, when_v = _arg(when_item, action)
        action.arguments = {k: v for k, v in (("amount", amount), ("currency", "INR"), ("due_by", when))
                            if v is not None}
        shown = rupees(money.amount) if isinstance(money, Money) else (plain(money) if money is not None else pending)
        due = f" due by{_when_words(when_v, base)}" if when_v is not None else (" due " + pending if when else "")
        action.sentence = f"Record a payment of {shown}{due}?"
    elif tool == "place_order":
        amount, money = _arg(amount_item, action)
        when, when_v = _arg(when_item, action)
        pay = "cash_on_delivery" if words & {"cod", "cash"} else None
        action.arguments = {k: v for k, v in (("amount", amount), ("currency", "INR"), ("payment", pay),
                                              ("deliver_by", when)) if v is not None}
        shown = rupees(money.amount) if isinstance(money, Money) else (plain(money) if money is not None else pending)
        action.sentence = (f"Place the order for {shown}{', cash on delivery' if pay else ''}"
                           f"{_when_words(when_v, base) if when_v is not None else ''}?")
    elif tool == "record_income":
        amount, money = _arg(amount_item, action)
        period = "month" if words & {"mahina", "mahine", "month", "monthly", "महीना", "महीने"} else \
            "year" if words & {"saal", "salana", "year", "yearly", "annual", "साल"} else None
        action.arguments = {k: v for k, v in (("amount", amount), ("currency", "INR"), ("per", period))
                            if v is not None}
        shown = rupees(money.amount) if isinstance(money, Money) else (plain(money) if money is not None else pending)
        action.sentence = f"Save income as {shown}{' per ' + period if period else ''}?"
    else:  # schedule_meeting / set_timer
        length, length_v = _arg(length_item, action)
        when, when_v = _arg(when_item, action)
        minutes = None
        if isinstance(length_v, Duration) and not (length_v.years or length_v.months):
            minutes = ((length_v.weeks * 7 + length_v.days) * 24 + length_v.hours) * 60 + length_v.minutes
        action.arguments = {k: v for k, v in (("duration", length), ("duration_minutes", minutes), ("start", when))
                            if v is not None}
        what = "Block a meeting of" if tool == "schedule_meeting" else "Start a timer for"
        action.sentence = f"{what} {plain(length_v) if length_v is not None else pending}{_when_words(when_v, base)}?"
    return action


def _without_values(reading: Reading) -> str:
    out, pos = [], 0
    for item in reading.items:
        out.append(reading.text[pos:item.result.span[0]])
        pos = item.result.span[1]
    out.append(reading.text[pos:])
    return " ".join(out)


def card(action: Action, reading: Reading) -> str:
    if not reading.text:
        return ""
    if action.tool is None:
        return ('<div class="k-act k-act-none"><strong>No action matched this message.</strong> '
                'The values above are what an agent would receive.'
                f'<p class="k-how">{escape(HOW)}</p></div>')
    if action.blocked:
        waiting = ", ".join(f"‘{escape(w)}’" for w in action.waiting_for)
        state = (f'<p class="k-block" role="alert">Confirm is locked: {waiting} has more than one meaning. '
                 'Choose the reading above first.</p>')
    else:
        state = '<p class="k-ready">Every value is decided. You can confirm.</p>'
    return (f'<div class="k-act"><div class="k-acth">An agent would ask you:</div>'
            f'<div class="k-sentence">{escape(action.sentence)}</div>{state}'
            f'<p class="k-preview">Preview only. Nothing is sent, saved or executed.</p>'
            f'<p class="k-how">{escape(HOW)}</p></div>')


CONFIRMED_HTML = ('<div class="k-done" role="status"><strong>Confirmed (preview).</strong> In a real app the tool '
                  'call below would now be sent. Here nothing was sent, saved or executed.</div>')
