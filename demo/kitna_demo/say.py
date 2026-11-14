"""Plain-language wording for parsed values. No internal terms reach the user from here."""
from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

from kitna import Duration, Money, Range

KIND_LABEL = {
    "number": "Number", "money": "Amount", "digits": "Digits (phone, PIN or ID)", "time": "Time",
    "date": "Date", "datetime": "Date and time", "duration": "Length of time",
}
_REL = {0: "today", 1: "tomorrow", -1: "yesterday", 2: "day after tomorrow", -2: "day before yesterday"}


def indian(n: Decimal | int) -> str:
    """1234567.5 -> '12,34,567.5' (Indian digit grouping)."""
    d = Decimal(str(n))
    sign, d = ("-" if d < 0 else ""), abs(d)
    whole, _, frac = format(d.normalize(), "f").partition(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        parts: list[str] = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        whole = ",".join([*parts, tail])
    return sign + whole + ("." + frac if frac else "")


def rupees(amount: Decimal, currency: str = "INR") -> str:
    text = indian(amount)
    if "." in text and len(text.split(".")[1]) == 1:
        text += "0"
    return f"₹{text}" if currency == "INR" else f"{currency} {text}"


def clock(t: time) -> str:
    hour = t.hour % 12 or 12
    return f"{hour}:{t.minute:02d} {'AM' if t.hour < 12 else 'PM'}"


def day(d: date, base: date | None = None, *, short: bool = False) -> str:
    """'tomorrow, Fri 13 Nov 2026' when a base is known; the date alone otherwise."""
    stamp = f"{d:%a} {d.day} {d:%b %Y}"
    rel = _REL.get((d - base).days) if base is not None else None
    if rel and short:
        return rel
    return f"{rel}, {stamp}" if rel else stamp


def length(d: Duration) -> str:
    parts = []
    for value, unit in ((d.years, "year"), (d.months, "month"), (d.weeks, "week"), (d.days, "day"),
                        (d.hours, "hour"), (d.minutes, "minute"), (d.seconds, "second")):
        if value:
            parts.append(f"{value} {unit}{'' if value == 1 else 's'}")
    return " ".join(parts) or "no time"


def plain(value: Any, base: datetime | None = None, *, short: bool = False) -> str:
    """One value in everyday words: '₹2,50,000', 'tomorrow, Fri 13 Nov 2026, 5:00 PM', '2 hours 30 minutes'."""
    today = base.date() if base is not None else None
    if isinstance(value, Range):
        lo = None if value.min is None else plain(value.min, base, short=short)
        hi = None if value.max is None else plain(value.max, base, short=short)
        if lo and hi:
            return f"{lo} to {hi}"
        if hi:
            return f"{'by' if isinstance(value.max, (date, datetime)) else 'up to'} {hi}"
        return f"{'from' if isinstance(value.min, (date, datetime)) else 'at least'} {lo}"
    if isinstance(value, Money):
        return rupees(value.amount, value.currency)
    if isinstance(value, datetime):
        return f"{day(value.date(), today, short=short)}{' at ' if short else ', '}{clock(value.time())}"
    if isinstance(value, date):
        return day(value, today, short=short)
    if isinstance(value, time):
        return clock(value)
    if isinstance(value, Duration):
        return length(value)
    if isinstance(value, (Decimal, int)) and not isinstance(value, bool):
        return indian(value)
    return str(value)


def level(confidence: float, ambiguous: bool, chosen: bool) -> tuple[str, str]:
    """(label, css key). An ambiguous value never shows a number-like confidence."""
    if ambiguous:
        return ("Chosen by you", "chosen") if chosen else ("Ambiguous", "amb")
    if confidence >= 0.95:
        return "High", "high"
    if confidence >= 0.8:
        return "Medium", "med"
    return "Low", "low"
