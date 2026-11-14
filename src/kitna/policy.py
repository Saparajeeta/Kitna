"""Every contested parsing decision, loaded from ``data/policy.tsv``.

When a native-speaker answer changes a rule (day-part hours, how ``agle
shanivaar`` reads, what to do with a date that has no year, how much to trust a
weak tense cue), edit the ``value`` column of that file. No code changes.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from importlib import resources

_CHOICES = {
    "time.bare_hour": ("flag",),
    "weekday.bare": ("next",),
    "weekday.same_day": ("flag", "today", "next_week"),
    "weekday.agle": ("next_occurrence", "next_week", "flag"),
    "date.no_year": ("flag", "future", "past"),
    "date.no_month": ("flag", "future", "past"),
    "prefer.relative_words": ("yes", "no"),
    "number.ek_baar": ("nothing", "one"),
    "week.start": ("monday", "sunday"),
    "date.numeric_order": ("dmy", "mdy"),
}


class PolicyError(RuntimeError):
    """``data/policy.tsv`` is malformed or holds an unsupported value."""


@dataclass(frozen=True, slots=True)
class DayPart:
    am: frozenset[int]
    pm: frozenset[int]
    fallback: str  # "am" | "pm"


@dataclass(frozen=True)
class Policy:
    values: dict[str, str]
    questions: dict[str, str]  # key -> open-question id ("-" when settled)
    dayparts: dict[str, DayPart]
    version: str

    def choice(self, key: str) -> str:
        return self.values[key]

    def conf(self, name: str) -> float:
        return float(self.values[f"confidence.{name}"])

    def words(self, key: str) -> frozenset[str]:
        from .normalize import word_key  # local import: normalize imports this module

        return frozenset(word_key(w) for w in self.values[key].split())


def _hours(spec: str) -> frozenset[int]:
    out: set[int] = set()
    for part in filter(None, spec.split(",")):
        lo, _, hi = part.partition("-")
        out.update(range(int(lo), int(hi or lo) + 1))
    if not out <= set(range(1, 13)):
        raise PolicyError(f"day-part hours must be 1-12, got {spec!r}")
    return frozenset(out)


@lru_cache(maxsize=1)
def policy() -> Policy:
    text = resources.files("kitna").joinpath("data", "policy.tsv").read_text(encoding="utf-8")
    values: dict[str, str] = {}
    questions: dict[str, str] = {}
    version = ""
    for line in text.splitlines():
        if line.startswith("# version:"):
            version = line.split(":", 1)[1].strip()
        if not line.strip() or line.startswith("#"):
            continue
        cols = [c.strip() for c in line.split("\t")]
        if len(cols) < 3:
            raise PolicyError(f"policy.tsv: need key, value, question: {line!r}")
        values[cols[0]], questions[cols[0]] = cols[1], cols[2]
    for key, allowed in _CHOICES.items():
        if values.get(key) not in allowed:
            raise PolicyError(f"policy.tsv: {key} must be one of {allowed}, got {values.get(key)!r}")
    dayparts: dict[str, DayPart] = {}
    for key, val in values.items():
        if key.startswith("daypart."):
            f = dict(p.split("=", 1) for p in val.split())
            if f.get("fallback") not in ("am", "pm"):
                raise PolicyError(f"policy.tsv: {key} needs fallback=am|pm")
            dp = DayPart(_hours(f.get("am", "")), _hours(f.get("pm", "")), f["fallback"])
            if dp.am & dp.pm:
                raise PolicyError(f"policy.tsv: {key} lists an hour as both am and pm")
            dayparts[key.split(".", 1)[1]] = dp
    try:
        for key, val in values.items():
            if key.startswith("confidence.") and not 0 < float(val) <= 1:
                raise PolicyError(f"policy.tsv: {key} must be in (0, 1]")
        int(values["saade.min_n"])
    except (KeyError, ValueError) as ex:
        raise PolicyError(f"policy.tsv: {ex}") from ex
    return Policy(values, questions, dayparts, version)
