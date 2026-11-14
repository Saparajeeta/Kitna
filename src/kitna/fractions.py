"""Fraction idioms: sawa, saade, dedh, dhai, paune, paun, aadha, paav.

The words and amounts come from ``data/fractions.tsv``. Two types:

* ``add``  (sawa +1/4, saade +1/2, paune -1/4): binds to the number after it,
  ``sawa teen`` = 3.25, ``paune paanch`` = 4.75. Directly before a scale word it
  means (1 + amount) x scale: ``sawa sau`` = 125, ``paune sau`` = 75.
* ``fixed`` (dedh 1.5, dhai 2.5, paun 0.75, aadha 0.5, paav 0.25): a value on its
  own that can multiply a scale, ``dhai lakh`` = 250000.
"""
from __future__ import annotations

from decimal import Decimal

from .normalize import Entry
from .policy import policy


class RejectedFraction(Exception):
    """The fraction word is used in a way speakers do not use it."""


def with_number(frac: Entry, n: Decimal) -> Decimal:
    """``add``-type fraction followed by the whole number ``n``."""
    if frac.name == "saade" and n < int(policy().choice("saade.min_n")):
        raise RejectedFraction(f"'saade' is not used with {n}; speakers say dedh / dhai")
    return n + frac.value


def before_scale(frac: Entry) -> Decimal:
    """Multiplier when the fraction word sits directly before a scale word."""
    if frac.name == "saade":
        raise RejectedFraction("'saade' needs a number after it")
    return frac.value if frac.ftype == "fixed" else Decimal(1) + frac.value


def alone(frac: Entry, *, unit_follows: bool = False) -> tuple[Decimal, float]:
    """Value and confidence factor of a fraction word standing by itself.

    A bare ``paune`` is unusual (speakers say ``paun``) unless a unit follows it
    (``paune ghante`` = 45 minutes).
    """
    if frac.name == "saade":
        raise RejectedFraction("'saade' needs a number after it")
    if frac.ftype == "fixed":
        return frac.value, 1.0
    factor = policy().conf("bare_paune") if frac.name == "paune" and not unit_follows else 1.0
    return Decimal(1) + frac.value, factor
