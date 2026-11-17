"""Check the quantity arguments of a model's tool call against what the user actually wrote.

A model that reads ``dhai lakh`` may put ``25000`` in ``amount``; one that reads ``kal 5 baje`` may
pick 05:00 without asking. :func:`postprocess_tool_call` reads the user's message with Kitna and, for
every numeric, date, time, date-time or duration argument, either confirms it, corrects it (when the
message has exactly one clear value of that kind), or flags it (when the message is ambiguous or the
value cannot be traced to the message). It never guesses between readings.

Limits: it compares values, it does not understand roles. If a message holds two amounts and the
call's amount matches neither, the argument is reported as unverified rather than corrected. Units
are not converted (an ``amount_in_paise`` argument will look wrong). Text arguments are left alone.
"""
from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
from typing import Any

from ._types import Duration, KitnaError, Money, Range, Result, canonical
from .api import parse

ARGUMENT_KINDS = ("number", "money", "date", "time", "datetime", "duration", "skip")
_FORMAT_KIND = {"date": "date", "time": "time", "date-time": "datetime", "duration": "duration"}
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_TIME = re.compile(r"(\d{1,2}):(\d{2})(:\d{2}(\.\d+)?)?")
_DATETIME = re.compile(r"(\d{4}-\d{2}-\d{2})([T ])(\d{1,2}:\d{2})(:\d{2}(?:\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?")
_DURATION = re.compile(r"P(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?", re.IGNORECASE)


@dataclass(frozen=True)
class ArgumentReview:
    """What happened to one argument.

    ``status``: ``confirmed`` (matches the message), ``corrected`` (replaced; see ``before`` /
    ``after``), ``ambiguous`` (the message has more than one reading; ``candidates`` lists them and
    the value was left alone), ``unverified`` (nothing in the message to check it against, or it
    could not be matched to one value), ``skipped`` (not a quantity).
    """

    name: str
    status: str
    kind: str
    before: Any
    after: Any
    reason: str
    candidates: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "status": self.status, "kind": self.kind, "before": self.before,
                "after": self.after, "reason": self.reason, "candidates": list(self.candidates)}


@dataclass(frozen=True)
class ToolCallReview:
    """Result of :func:`postprocess_tool_call`. ``call`` has the same shape as the call passed in."""

    call: Any
    name: str
    arguments: dict[str, Any]
    reviews: tuple[ArgumentReview, ...] = field(default_factory=tuple)

    @property
    def changed(self) -> bool:
        return any(r.status == "corrected" for r in self.reviews)

    @property
    def needs_confirmation(self) -> bool:
        """True when a value is ambiguous in the message: ask the user before acting."""
        return any(r.status == "ambiguous" for r in self.reviews)

    @property
    def unverified(self) -> tuple[str, ...]:
        return tuple(r.name for r in self.reviews if r.status == "unverified")

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "arguments": self.arguments, "call": self.call, "changed": self.changed,
                "needs_confirmation": self.needs_confirmation, "unverified": list(self.unverified),
                "reviews": [r.to_dict() for r in self.reviews]}


@dataclass
class _Reading:
    text: str
    options: tuple[Any, ...]
    confidence: float = 1.0
    used: bool = False


def _unpack(call: Any) -> tuple[str, dict[str, Any], str]:
    """``(tool name, arguments, shape)`` for the common tool-call layouts."""
    if not isinstance(call, dict):
        raise KitnaError("tool call must be a dict (OpenAI or Anthropic layout, or {'name', 'arguments'})")
    if isinstance(call.get("function"), dict):
        inner, shape, key = call["function"], "openai_chat", "arguments"
    elif "input" in call and "arguments" not in call:
        inner, shape, key = call, "anthropic", "input"
    else:
        inner, shape, key = call, "flat", "arguments"
    name = inner.get("name")
    raw = inner.get(key, {})
    if not isinstance(name, str) or not name:
        raise KitnaError("tool call has no 'name'")
    if isinstance(raw, str):
        try:
            args = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError as ex:
            raise KitnaError(f"tool call arguments are not valid JSON: {ex}") from ex
        shape += "_str"
    else:
        args = raw
    if not isinstance(args, dict):
        raise KitnaError("tool call arguments must be a JSON object")
    return name, dict(args), shape


def _repack(call: dict[str, Any], args: dict[str, Any], shape: str) -> dict[str, Any]:
    out = copy.deepcopy(call)
    value: Any = json.dumps(args, ensure_ascii=False) if shape.endswith("_str") else args
    if shape.startswith("openai_chat"):
        out["function"]["arguments"] = value
    elif shape.startswith("anthropic"):
        out["input"] = value
    else:
        out["arguments"] = value
    return out


def _properties(schema: Any) -> dict[str, Any]:
    """The ``properties`` of a parameter schema, or of a whole OpenAI / Anthropic tool definition."""
    if not isinstance(schema, dict):
        return {}
    for path in (("function", "parameters"), ("parameters",), ("input_schema",)):
        node: Any = schema
        for key in path:
            node = node.get(key) if isinstance(node, dict) else None
        if isinstance(node, dict):
            schema = node
            break
    props = schema.get("properties")
    return props if isinstance(props, dict) else {}


def _kind_of(name: str, value: Any, kinds: dict[str, str], props: dict[str, Any]) -> str:
    if name in kinds:
        if kinds[name] not in ARGUMENT_KINDS:
            raise KitnaError(f"kinds[{name!r}] must be one of {', '.join(ARGUMENT_KINDS)}")
        return kinds[name]
    spec = props.get(name)
    if isinstance(spec, dict):
        if spec.get("x-kitna-kind") in ARGUMENT_KINDS:
            return str(spec["x-kitna-kind"])
        if spec.get("format") in _FORMAT_KIND:
            return _FORMAT_KIND[spec["format"]]
        if spec.get("type") in ("number", "integer"):
            return "number"
        if spec.get("type") == "string" and not isinstance(value, str):
            return "skip"
    if isinstance(value, bool) or value is None:
        return "skip"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        v = value.strip()
        if _DATETIME.fullmatch(v):
            return "datetime"
        if _DATE.fullmatch(v):
            return "date"
        if _TIME.fullmatch(v):
            return "time"
        if len(v) > 1 and v[0] in "Pp" and _DURATION.fullmatch(v):
            return "duration"
    return "skip"


def _seconds(d: Duration) -> int | None:
    if d.years or d.months:
        return None
    return ((d.weeks * 7 + d.days) * 24 + d.hours) * 3600 + d.minutes * 60 + d.seconds


def _normalise(value: Any, kind: str) -> Any:
    """The comparable form of an argument value, or ``None`` when it cannot be read as ``kind``."""
    try:
        if kind in ("number", "money"):
            if isinstance(value, bool):
                return None
            if isinstance(value, (int, float)):
                return Decimal(str(value))
            return Decimal(str(value).replace(",", "").strip())
        text = str(value).strip()
        if kind == "date":
            return date.fromisoformat(text) if _DATE.fullmatch(text) else None
        if kind == "time":
            m = _TIME.fullmatch(text)
            return time(int(m.group(1)), int(m.group(2))) if m else None
        if kind == "datetime":
            m = _DATETIME.fullmatch(text)
            if not m:
                return None
            hh, mm = m.group(3).split(":")
            return datetime.combine(date.fromisoformat(m.group(1)), time(int(hh), int(mm)))
        if kind == "duration":
            m = _DURATION.fullmatch(text)
            if not m or len(text) < 2:
                return None
            w, d, h, mi, s = (int(g or 0) for g in m.groups())
            return ((w * 7 + d) * 24 + h) * 3600 + mi * 60 + s
    except (InvalidOperation, ValueError):
        return None
    return None


def _iso_duration(seconds: int) -> str:
    days, rest = divmod(seconds, 86400)
    hours, rest = divmod(rest, 3600)
    minutes, secs = divmod(rest, 60)
    return str(Duration(days=days, hours=hours, minutes=minutes, seconds=secs))


def _show(option: Any, kind: str) -> str:
    if kind == "duration":
        return _iso_duration(option)
    if isinstance(option, Decimal):
        return format(option.normalize(), "f")
    return canonical(option)


def _restyle(option: Any, kind: str, before: Any) -> Any:
    """Write a corrected value in the style the call used (int stays int, seconds stay, zone suffix stays)."""
    if kind in ("number", "money"):
        if isinstance(before, str):
            return format(option.normalize(), "f")
        if option == option.to_integral_value() and not isinstance(before, float):
            return int(option)
        return float(option)
    if kind == "date":
        return canonical(option)
    if kind == "time":
        m = _TIME.fullmatch(str(before).strip())
        return option.strftime("%H:%M") + (":00" if m and m.group(3) else "")
    if kind == "datetime":
        m = _DATETIME.fullmatch(str(before).strip())
        sep, secs, zone = (m.group(2), m.group(4), m.group(5)) if m else ("T", None, None)
        return option.strftime(f"%Y-%m-%d{sep}%H:%M") + (":00" if secs else "") + (zone or "")
    return _iso_duration(option)


def _options(r: Result) -> tuple[Any, ...]:
    values = (r.value,) if r.value is not None else r.candidates
    return tuple(v for v in values if not isinstance(v, Range))


def _readings(results: list[Result]) -> dict[str, list[_Reading]]:
    pool: dict[str, list[_Reading]] = {k: [] for k in ("number", "date", "time", "datetime", "duration")}
    for r in results:
        opts = _options(r)
        if not opts:
            continue
        if r.kind in ("number", "money"):
            amounts = tuple(Decimal(str(o.amount)) if isinstance(o, Money) else Decimal(str(o)) for o in opts)
            pool["number"].append(_Reading(r.text, amounts, r.confidence))
        elif r.kind == "duration":
            secs = tuple(s for s in (_seconds(o) for o in opts) if s is not None)
            if secs:
                pool["duration"].append(_Reading(r.text, secs, r.confidence))
        elif r.kind == "datetime":
            pool["datetime"].append(_Reading(r.text, opts, r.confidence))
            pool["date"].append(_Reading(r.text, tuple(dict.fromkeys(o.date() for o in opts)), r.confidence))
            pool["time"].append(_Reading(r.text, tuple(dict.fromkeys(o.time() for o in opts)), r.confidence))
        elif r.kind in ("date", "time"):
            pool[r.kind].append(_Reading(r.text, opts, r.confidence))
    if not pool["datetime"] and len(pool["date"]) == 1 and len(pool["time"]) == 1:
        d, t = pool["date"][0], pool["time"][0]
        pool["datetime"].append(_Reading(f"{d.text} … {t.text}",
                                         tuple(datetime.combine(x, y) for x in d.options for y in t.options),
                                         min(d.confidence, t.confidence)))
    return pool


def _scale_hint(before: Decimal, after: Decimal) -> str:
    if before > 0 and after > 0:
        big, small = max(before, after), min(before, after)
        ratio = big / small
        if ratio in (Decimal(10), Decimal(100), Decimal(1000)):
            return f" (off by a factor of {ratio.normalize():f}: a scale slip)"
    return ""


def postprocess_tool_call(
    call: dict[str, Any],
    utterance: str,
    *,
    kinds: dict[str, str] | None = None,
    schema: dict[str, Any] | None = None,
    relative_base: date | datetime | None = None,
    prefer: str | None = None,
    correct: bool = True,
    min_confidence: float = 0.95,
) -> ToolCallReview:
    """Confirm, correct or flag the quantity arguments of ``call`` against ``utterance``.

    ``call`` may be an OpenAI tool call (``{"function": {"name", "arguments": "<json>"}}``), an
    Anthropic ``tool_use`` block (``{"name", "input": {...}}``) or ``{"name", "arguments"}``.

    Which arguments are quantities is taken, in order, from ``kinds`` (``{"amount": "money",
    "when": "datetime", "note": "skip"}``), from ``schema`` (the tool's parameter schema or whole tool
    definition: ``x-kitna-kind``, ``format`` or a numeric ``type``), and otherwise from the value's
    shape (a number, ``YYYY-MM-DD``, ``HH:MM``, an ISO date-time, an ISO duration).

    ``relative_base`` is the user's "now", as for :func:`kitna.parse`. With ``correct=False`` nothing
    is changed; arguments that would have been corrected are reported with ``after`` set and the
    call left as it was. A value is only overwritten when Kitna's own reading has a confidence of at
    least ``min_confidence``; a reading that came from a repaired spelling or a weak tense cue is
    reported, not applied.

    A correction applies Kitna's rules, which are AI-drafted and not yet reviewed by native speakers.
    Log ``reviews`` and keep a human confirmation step for anything that moves money.
    """
    name, args, shape = _unpack(call)
    props = _properties(schema)
    pool = _readings(parse(utterance, relative_base=relative_base, prefer=prefer))
    plan: list[tuple[str, str, Any]] = []
    for arg, value in args.items():
        kind = _kind_of(arg, value, kinds or {}, props)
        plan.append((arg, kind, None if kind == "skip" else _normalise(value, kind)))

    reviews: dict[str, ArgumentReview] = {}
    # pass 1: arguments whose value is one of the readings in the message
    for arg, kind, norm in plan:
        value = args[arg]
        if kind == "skip":
            reviews[arg] = ArgumentReview(arg, "skipped", kind, value, value, "not a number, date or time")
            continue
        readings = pool["number" if kind == "money" else kind]
        if norm is None:
            reviews[arg] = ArgumentReview(arg, "unverified", kind, value, value,
                                          f"could not read {value!r} as a {kind}")
            continue
        hit = next((r for r in readings if norm in r.options and not r.used), None) or next(
            (r for r in readings if norm in r.options), None)
        if hit is None:
            continue
        hit.used = True
        if len(hit.options) == 1:
            reviews[arg] = ArgumentReview(arg, "confirmed", kind, value, value, f"matches '{hit.text}' in the message")
        else:
            cands = tuple(_show(o, kind) for o in hit.options)
            reviews[arg] = ArgumentReview(
                arg, "ambiguous", kind, value, value,
                f"'{hit.text}' can mean {' or '.join(cands)}; the call picked one without asking", cands)
    # pass 2: everything else is compared with the readings no argument has claimed
    for arg, kind, norm in plan:
        if arg in reviews:
            continue
        value = args[arg]
        label = "number" if kind == "money" else kind
        free = [r for r in pool[label] if not r.used]
        if not pool[label]:
            reviews[arg] = ArgumentReview(arg, "unverified", kind, value, value,
                                          f"the message contains no {label} to check this against")
        elif len(free) == 1 and len(free[0].options) == 1 and free[0].confidence < min_confidence:
            reviews[arg] = ArgumentReview(
                arg, "unverified", kind, value, value,
                f"differs from '{free[0].text}' = {_show(free[0].options[0], kind)}, but Kitna's own reading rests "
                "on a loose spelling match or a weak cue, so nothing was changed")
        elif len(free) == 1 and len(free[0].options) == 1:
            free[0].used = True
            option = free[0].options[0]
            after = _restyle(option, kind, value)
            hint = _scale_hint(norm, option) if isinstance(norm, Decimal) else ""
            reason = (f"the message says '{free[0].text}' = {_show(option, kind)}; "
                      f"the call had {_show(norm, kind)}{hint}")
            reviews[arg] = ArgumentReview(arg, "corrected", kind, value, after, reason)
        elif len(free) == 1:
            free[0].used = True
            cands = tuple(_show(o, kind) for o in free[0].options)
            reviews[arg] = ArgumentReview(
                arg, "ambiguous", kind, value, value,
                f"'{free[0].text}' can mean {' or '.join(cands)}; the call's value is none of them", cands)
        else:
            seen = ", ".join(f"'{r.text}'" for r in (free or pool[label]))
            why = "every value in the message is already used by another argument" if not free else \
                "the message has more than one candidate"
            reviews[arg] = ArgumentReview(arg, "unverified", kind, value, value,
                                          f"does not match the message ({seen}); {why}, so nothing was changed")

    ordered = tuple(reviews[arg] for arg, _, _ in plan)
    fixed = {r.name: (r.after if correct else r.before) for r in ordered}
    return ToolCallReview(_repack(call, fixed, shape), name, fixed, ordered)
