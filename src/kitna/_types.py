"""Public value and result types."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

KINDS = ("number", "digits", "money", "time", "duration", "date", "datetime")


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
        lo = "" if self.min is None else str(self.min)
        hi = "" if self.max is None else str(self.max)
        return f"{lo}..{hi}"


@dataclass(frozen=True, slots=True)
class Result:
    """One parsed expression.

    ``confidence`` is an ordering, not a calibrated probability: 1.0 means every
    step was an exact table match; lower means a spelling repair, an unusual
    form or a weak cue was involved.

    When ``ambiguous`` is true, ``value`` is ``None`` and ``candidates`` holds
    every reading. Kitna never picks one silently.
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
