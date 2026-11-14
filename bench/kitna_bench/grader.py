"""Grading: tool-name match, then argument match after normalisation; error taxonomy."""
from __future__ import annotations

import datetime as dt
from typing import Any

from .items import Item, params_of
from .normalize import kitna_value, strict_value, text_key

ERROR_TYPES = ("wrong_tool", "wrong_scale", "wrong_date_direction", "am_pm", "fraction_idiom",
               "hallucinated_argument", "refusal", "other")
_SCALES = {10 ** k for k in range(1, 8)}
_QUESTION = ("?", "？", "؟")


def response_kind(tool_calls: list[dict[str, Any]], text: str) -> str:
    """call: a tool was called. clarify: no call and the text asks something. no_call: neither.

    The question test is a heuristic (a question mark); the manual-review export exists to check it.
    """
    if tool_calls:
        return "call"
    return "clarify" if any(q in text for q in _QUESTION) else "no_call"


def _gold_keys(item: Item, name: str, kind: str) -> set[str]:
    gold = item["gold"]
    values = [gold["arguments"][name], *gold.get("aliases", {}).get(name, [])]
    if kind in ("enum", "string", "id"):
        return {text_key(v) for v in values}
    return {gold["arguments"][name]}


def grade(item: Item, tool_calls: list[dict[str, Any]], text: str, error: str | None = None) -> dict[str, Any]:
    """Score one response. Returns flat fields; `correct` is the per-item verdict."""
    now = dt.datetime.fromisoformat(item["now"])
    expected, gold = item["expected_behavior"], item["gold"]
    kind = "error" if error else response_kind(tool_calls, text)
    out: dict[str, Any] = {
        "expected": expected, "response_kind": kind, "tool_match": None, "args": {}, "extra_args": [],
        "n_args": 0, "n_args_ok": 0, "n_args_ok_strict": 0, "correct": False, "correct_strict": False,
        "error_type": None, "error_detail": "",
    }
    if error:
        out["error_type"], out["error_detail"] = "other", "adapter_error"
        return out
    call = tool_calls[0] if tool_calls else None
    if expected == "abstain":
        out["correct"] = out["correct_strict"] = call is None
        if call is not None:
            out["error_type"], out["error_detail"] = "wrong_tool", "called_a_tool_on_a_negative_item"
        return out
    if expected == "clarify":
        out["correct"] = out["correct_strict"] = kind == "clarify"
        if kind == "call":
            guessed = [n for n in item["clarify_about"] if n in ((call or {}).get("arguments") or {})]
            out["error_type"] = "hallucinated_argument" if guessed else "other"
            out["error_detail"] = "guessed:" + ",".join(guessed) if guessed else "called_without_asking"
        elif kind == "no_call":
            out["error_type"], out["error_detail"] = "refusal", "neither_asked_nor_called"
        return out
    # expected == "call": every graded gold argument is scored, also when the call is missing or wrong.
    props = params_of(item, gold["tool"])
    right_tool = call is not None and call.get("name") == gold["tool"]
    given: dict[str, Any] = ((call or {}).get("arguments") or {}) if right_tool else {}
    for name, gold_value in gold["arguments"].items():
        p = props[name]
        if not p.get("x-graded", True):
            continue
        k = p["x-kitna-kind"]
        keys = _gold_keys(item, name, k)
        raw = given.get(name)
        strict = strict_value(raw, k) if name in given else None
        loose = kitna_value(raw, k, now) if name in given else None
        out["args"][name] = {"kind": k, "gold": gold_value, "given": raw, "normalized": loose,
                             "ok": loose in keys, "ok_strict": strict in keys, "present": name in given}
    out["n_args"] = len(out["args"])
    out["n_args_ok"] = sum(a["ok"] for a in out["args"].values())
    out["n_args_ok_strict"] = sum(a["ok_strict"] for a in out["args"].values())
    if call is None:
        out["error_type"] = "refusal" if kind == "no_call" else "other"
        out["error_detail"] = "no_tool_call" if kind == "no_call" else "unnecessary_clarification"
        return out
    out["tool_match"] = right_tool
    if not right_tool:
        out["error_type"], out["error_detail"] = "wrong_tool", str(call.get("name"))
        return out
    if call.get("arguments") is None:
        out["error_detail"] = "arguments_not_valid_json"
    out["extra_args"] = sorted(n for n in given if n not in gold["arguments"] and n in props
                               and props[n].get("x-graded", True) and given[n] not in (None, "")
                               ) + sorted(n for n in given if n not in props)
    out["correct"] = out["n_args_ok"] == out["n_args"] and not out["extra_args"]
    out["correct_strict"] = out["n_args_ok_strict"] == out["n_args"] and not out["extra_args"]
    if not out["correct"]:
        out["error_type"], out["error_detail"] = classify_error(item, out, now)
    return out


def classify_error(item: Item, graded: dict[str, Any], now: dt.datetime) -> tuple[str, str]:
    """First matching type, in a fixed order, for a call with the right tool and wrong arguments."""
    bad = {n: a for n, a in graded["args"].items() if not a["ok"]}
    for name, a in bad.items():
        if a["kind"] == "number" and a["normalized"] is not None:
            try:
                g, v = float(a["gold"]), float(a["normalized"])
            except ValueError:
                continue
            if g and v and (round(v / g, 9) in _SCALES or round(g / v, 9) in _SCALES):
                return "wrong_scale", name
    for name, a in bad.items():
        if a["kind"] in ("date", "datetime") and a["normalized"] is not None:
            gold_day = dt.date.fromisoformat(a["gold"][:10])
            given_day = dt.date.fromisoformat(a["normalized"][:10])
            dg, dv = (gold_day - now.date()).days, (given_day - now.date()).days
            if (dg < 0) != (dv < 0):
                return "wrong_date_direction", name
    for name, a in bad.items():
        if a["kind"] in ("time", "datetime") and a["normalized"] is not None:
            gt, vt = str(a["gold"]), str(a["normalized"])
            if gt[:-5] == vt[:-5] and gt[-2:] == vt[-2:] and abs(int(gt[-5:-3]) - int(vt[-5:-3])) == 12:
                return "am_pm", name
    if "fraction_idiom" in item["phenomena"]:
        for name, a in bad.items():
            if a["present"] and a["kind"] in ("number", "time", "datetime", "duration"):
                return "fraction_idiom", name
    if graded["extra_args"]:
        return "hallucinated_argument", ",".join(graded["extra_args"])
    missing = [n for n, a in bad.items() if not a["present"]]
    if missing:
        return "other", "missing_argument:" + ",".join(missing)
    return "other", "wrong_value:" + ",".join(bad)
