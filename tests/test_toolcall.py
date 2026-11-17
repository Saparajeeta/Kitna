"""postprocess_tool_call: confirm, correct or flag the quantity arguments of a model's tool call."""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

import kitna
from kitna import postprocess_tool_call as check

NOW = dt.datetime(2026, 11, 12, 10, 0)
ROOT = Path(__file__).resolve().parent.parent


def status(review: kitna.ToolCallReview) -> dict[str, str]:
    return {r.name: r.status for r in review.reviews}


def test_openai_layout_scale_slip_is_corrected_and_shape_is_kept() -> None:
    call = {"id": "c1", "type": "function",
            "function": {"name": "transfer", "arguments": json.dumps({"to": "Ramesh", "amount": 25000})}}
    r = check(call, "Ramesh ko dhai lakh rupaye bhej do", relative_base=NOW)
    assert r.changed and not r.needs_confirmation and r.name == "transfer"
    assert status(r) == {"to": "skipped", "amount": "corrected"}
    assert json.loads(r.call["function"]["arguments"]) == {"to": "Ramesh", "amount": 250000}
    assert r.call["id"] == "c1" and isinstance(r.call["function"]["arguments"], str)
    amount = r.reviews[1]
    assert (amount.before, amount.after) == (25000, 250000) and "factor of 10" in amount.reason
    assert json.loads(call["function"]["arguments"])["amount"] == 25000, "the input call must not be mutated"
    json.dumps(r.to_dict())


def test_anthropic_layout_and_silent_am_pick_is_flagged_not_changed() -> None:
    call = {"type": "tool_use", "id": "t1", "name": "remind", "input": {"when": "2026-11-13T05:00:00+05:30"}}
    r = check(call, "kal 5 baje yaad dilana, main jaunga", relative_base=NOW)
    assert r.needs_confirmation and not r.changed
    w = r.reviews[0]
    assert w.status == "ambiguous" and "2026-11-13T17:00" in w.candidates and "without asking" in w.reason
    assert r.call["input"]["when"] == "2026-11-13T05:00:00+05:30"


def test_values_matching_the_message_are_confirmed() -> None:
    r = check({"name": "pay", "arguments": {"amount": 3500.0, "date": "2026-11-14"}},
              "saade teen hazaar rupaye parso bhej dunga", relative_base=NOW)
    assert status(r) == {"amount": "confirmed", "date": "confirmed"} and not r.changed


def test_styles_survive_correction() -> None:
    args = {"at": "02:00:00", "when": "2026-11-12 02:00:00Z", "d": "PT2H"}
    text = "aaj 2 bje call krungi, dhai ghante lagenge"
    # the time here comes from a context resolver (a contested rule, confidence 0.9): reported, not applied
    careful = check({"name": "x", "arguments": args}, text, relative_base=NOW, kinds={"at": "time"})
    assert careful.arguments == {**args, "d": "PT2H30M"} and careful.unverified == ("at", "when")
    r = check({"name": "x", "arguments": args}, text, relative_base=NOW, kinds={"at": "time"}, min_confidence=0.9)
    assert r.arguments == {"at": "14:00:00", "when": "2026-11-12 14:00:00Z", "d": "PT2H30M"}
    assert check({"name": "x", "arguments": {"n": 2.0}}, "dhai lakh", kinds={"n": "number"}).arguments == {"n": 250000}
    assert check({"name": "x", "arguments": {"n": "2"}}, "dhai", kinds={"n": "number"}).arguments == {"n": "2.5"}


def test_nothing_in_the_message_or_several_candidates_means_unverified() -> None:
    r = check({"name": "pay", "arguments": {"amount": 500, "tip": 20}}, "paise bhej do", relative_base=NOW)
    assert status(r) == {"amount": "unverified", "tip": "unverified"} and r.unverified == ("amount", "tip")
    r = check({"name": "pay", "arguments": {"fee": 50}}, "saade teen hazaar bhejo aur paanch sau alag rakho")
    assert status(r) == {"fee": "unverified"} and r.arguments == {"fee": 50}
    assert "more than one candidate" in r.reviews[0].reason


def test_two_amounts_one_already_matched_then_the_other_is_corrected() -> None:
    r = check({"name": "pay", "arguments": {"amount": 3500, "fee": 50}},
              "saade teen hazaar bhejo aur paanch sau alag rakho")
    assert status(r) == {"amount": "confirmed", "fee": "corrected"} and r.arguments["fee"] == 500


def test_kinds_schema_and_shape_decide_what_is_checked() -> None:
    schema = {"type": "function", "function": {"name": "f", "parameters": {"type": "object", "properties": {
        "pin": {"type": "string"}, "amount": {"type": "string", "x-kitna-kind": "money"},
        "day": {"type": "string", "format": "date"}}}}}
    r = check({"name": "f", "arguments": {"pin": "560001", "amount": "25000", "day": "2026-11-20"}},
              "dhai lakh rupaye 15 August 2027 ko", schema=schema, relative_base=NOW)
    assert status(r) == {"pin": "skipped", "amount": "corrected", "day": "corrected"}
    assert r.arguments == {"pin": "560001", "amount": "250000", "day": "2027-08-15"}
    anthropic = {"name": "f", "input_schema": {"type": "object", "properties": {"n": {"type": "integer"}}}}
    assert status(check({"name": "f", "input": {"n": 3}}, "do ticket", schema=anthropic)) == {"n": "corrected"}
    skipped = check({"name": "f", "arguments": {"amount": 25000}}, "dhai lakh", kinds={"amount": "skip"})
    assert status(skipped) == {"amount": "skipped"}
    assert status(check({"name": "f", "arguments": {"flag": True, "note": None, "s": "hello"}}, "dhai lakh")) == {
        "flag": "skipped", "note": "skipped", "s": "skipped"}


def test_correct_false_reports_but_does_not_change() -> None:
    r = check({"name": "pay", "arguments": {"amount": 25000}}, "dhai lakh rupaye", correct=False)
    assert r.arguments == {"amount": 25000} and r.reviews[0].status == "corrected" and r.reviews[0].after == 250000


def test_a_loosely_spelled_reading_is_not_used_to_overwrite() -> None:
    r = check({"name": "pay", "arguments": {"amount": 3000}}, "tees hazzar bhej do")
    assert status(r) == {"amount": "unverified"} and r.arguments == {"amount": 3000}
    assert "nothing was changed" in r.reviews[0].reason
    forced = check({"name": "pay", "arguments": {"amount": 3000}}, "tees hazzar bhej do", min_confidence=0.5)
    assert forced.arguments == {"amount": 30000}


def test_ambiguous_reading_that_the_call_does_not_match() -> None:
    r = check({"name": "x", "arguments": {"t": "09:00"}}, "5 baje milo", kinds={"t": "time"})
    assert r.reviews[0].status == "ambiguous" and r.reviews[0].candidates == ("05:00", "17:00")
    assert "none of them" in r.reviews[0].reason and r.arguments == {"t": "09:00"}


@pytest.mark.parametrize("bad", [
    "not a dict", {"arguments": {}}, {"name": "f", "arguments": "{not json"}, {"name": "f", "arguments": "[1]"},
])
def test_malformed_calls_raise_kitna_error(bad: Any) -> None:
    with pytest.raises(kitna.KitnaError):
        check(bad, "dhai lakh")


def test_unknown_kind_and_unreadable_value() -> None:
    with pytest.raises(kitna.KitnaError):
        check({"name": "f", "arguments": {"a": 1}}, "do", kinds={"a": "weight"})
    r = check({"name": "f", "arguments": {"d": "next week"}}, "kal jaunga", kinds={"d": "date"}, relative_base=NOW)
    assert r.reviews[0].status == "unverified" and "could not read" in r.reviews[0].reason
    assert check({"name": "f", "arguments": ""}, "do").arguments == {}


def test_example_script_runs_offline(capsys: pytest.CaptureFixture[str]) -> None:
    spec = importlib.util.spec_from_file_location("tool_call_guard", ROOT / "examples" / "tool_call_guard.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["tool_call_guard"] = module
    spec.loader.exec_module(module)
    reviews = module.main()
    out = capsys.readouterr().out
    assert [r.changed for r in reviews] == [True, False, True]
    assert reviews[1].needs_confirmation and "ASK THE USER" in out and '"amount": 250000' in out
    assert "NOT outputs of any real model" in (module.__doc__ or "")
