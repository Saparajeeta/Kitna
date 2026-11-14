"""Public value and result types."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

KINDS = ("number", "digits", "money", "time", "duration", "date", "datetime")
#: version of the dict produced by ``Result.to_dict()``
RESULT_SCHEMA_VERSION = "1"


class KitnaError(ValueError):
    """Raised for invalid arguments (unknown kind, bad relative_base, ...)."""


def clean_number(d: Decimal) -> int | Decimal:
    """Exact value as ``int`` when integral, else a normalised ``Decimal``."""
    if d == d.to_integral_value():
        return int(d)
    return d.normalize()


@dataclass(frozen=True, slots=True)
class Money:
    """An exact amount. ``amount`` is in whole currency units (rupees)."""

    amount: Decimal
    currency: str = "INR"

    @property
    def amount_str(self) -> str:
        """``"500"`` for whole rupees, two decimals otherwise (``"100.50"``)."""
        if self.amount == self.amount.to_integral_value():
            return str(int(self.amount))
        return str(self.amount.quantize(Decimal("0.01")))

    def __str__(self) -> str:
        return f"{self.currency} {self.amount_str}"


@dataclass(frozen=True, slots=True)
class Range:
    """A closed range. Either end may be ``None`` (``tak`` gives only ``max``)."""

    min: Any | None
    max: Any | None

    def __str__(self) -> str:
        return canonical(self)


@dataclass(frozen=True, slots=True)
class Duration:
    """A calendar duration. ``str()`` gives ISO 8601 (``PT2H30M``, ``P1Y6M``, ``P1W``)."""

    years: int = 0
    months: int = 0
    weeks: int = 0
    days: int = 0
    hours: int = 0
    minutes: int = 0
    seconds: int = 0

    def __str__(self) -> str:
        d = "".join(f"{v}{u}" for v, u in ((self.years, "Y"), (self.months, "M"), (self.weeks, "W"),
                                             (self.days, "D")) if v)
        t = "".join(f"{v}{u}" for v, u in ((self.hours, "H"), (self.minutes, "M"), (self.seconds, "S")) if v)
        return "P" + d + ("T" + t if t else "") if (d or t) else "PT0S"


def canonical(value: Any) -> str:
    """Canonical string for any result value.

    ``250000``, ``3.25``, ``INR 100.50``, ``INR 2000..INR 3000``, ``..5000``,
    ``17:15``, ``2026-11-13``, ``2026-11-13T07:00``, ``PT2H30M``.
    """
    if isinstance(value, Range):
        lo = "" if value.min is None else canonical(value.min)
        hi = "" if value.max is None else canonical(value.max)
        return f"{lo}..{hi}"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%dT%H:%M")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.strftime("%H:%M")
    if value is None:
        return ""
    return str(value)


def to_json(value: Any) -> Any:
    """JSON form of a result value.

    number: JSON integer, or a decimal string (``"3.25"``) so no precision is lost;
    digits: string; money: ``{"amount": "100.50", "currency": "INR"}``;
    time / date / datetime / duration: their canonical strings;
    range: ``{"min": ..., "max": ...}`` with either end possibly ``null``.
    """
    if isinstance(value, Range):
        return {"min": None if value.min is None else to_json(value.min),
                "max": None if value.max is None else to_json(value.max)}
    if isinstance(value, Money):
        return {"amount": value.amount_str, "currency": value.currency}
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, str)):
        return value
    return canonical(value)


@dataclass(frozen=True, slots=True)
class Result:
    """One parsed expression.

    ``confidence`` is an ordering, not a calibrated probability: 1.0 means every
    step was an exact table match; lower means a spelling repair, an unusual
    form or a weak cue was involved.

    When ``ambiguous`` is true, ``value`` is ``None``, ``candidates`` holds
    every reading and ``canonical`` joins them with ``" | "``. Kitna never picks
    one silently.
    """

    span: tuple[int, int]
    text: str
    kind: str
    value: Any
    canonical: str
    confidence: float
    candidates: tuple[Any, ...] = ()
    ambiguous: bool = False
    approximate: bool = False
    notes: tuple[str, ...] = ()
    #: things the caller should act on, e.g. a relative date resolved against the
    #: system clock because no ``relative_base`` was passed
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """JSON-serialisable form, described by ``kitna/data/result.schema.json``.

        Values are canonical strings (or ``{"min", "max"}`` objects for ranges);
        ``schema_version`` changes only when a field is removed or changes meaning.
        """
        return {
            "schema_version": RESULT_SCHEMA_VERSION,
            "span": list(self.span),
            "text": self.text,
            "kind": self.kind,
            "value": None if self.value is None else to_json(self.value),
            "canonical": self.canonical,
            "confidence": self.confidence,
            "ambiguous": self.ambiguous,
            "candidates": [to_json(c) for c in self.candidates],
            "approximate": self.approximate,
            "notes": list(self.notes),
            "warnings": list(self.warnings),
        }
