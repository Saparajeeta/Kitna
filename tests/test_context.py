"""Context resolvers: 'today' + a bare hour, decided by the current time and the verb's tense."""
from __future__ import annotations

import dataclasses
import datetime as dt

import pytest

import kitna
from kitna import api
from kitna.policy import policy

TEN = dt.datetime(2026, 11, 12, 10, 0)


def one(text: str, base: dt.date | dt.datetime = TEN) -> kitna.Result:
    results = [r for r in kitna.parse(text, relative_base=base) if r.kind == "datetime"]
    assert len(results) == 1, results
    return results[0]


def test_future_verb_drops_the_hour_that_has_already_passed() -> None:
    r = one("aaj 2 bje call krungi")
    assert r.canonical == "2026-11-12T14:00" and not r.ambiguous
    assert r.confidence == pytest.approx(policy().conf("context_time"))
    assert any(n.startswith("context: 02:00 today has already passed at 10:00") for n in r.notes)
    assert "context.today_future" in r.notes[-1]
    assert not any("AM or PM unknown" in n for n in r.notes)


def test_devanagari_and_a_request_also_resolve_with_lower_confidence() -> None:
    assert one("आज 2 बजे फोन करूंगी").canonical == "2026-11-12T14:00"
    weak = one("aaj 2 baje call karo")
    assert weak.canonical == "2026-11-12T14:00"
    assert weak.confidence < one("aaj 2 bje call krungi").confidence


@pytest.mark.parametrize("text, base", [
    ("aaj 11 baje aaunga", TEN),                              # 11:00 and 23:00 are both still to come
    ("aaj 5 baje aaunga", dt.datetime(2026, 11, 12, 18, 0)),  # both have passed: contradiction, keep both
    ("aaj 2 baje", TEN),                                      # no verb, no direction
    ("aaj 2 baje call krungi", dt.date(2026, 11, 12)),        # base has no clock time
])
def test_it_stays_ambiguous_when_the_context_does_not_leave_exactly_one(text: str, base: dt.date) -> None:
    r = one(text, base)
    assert r.ambiguous and len(r.candidates) == 2


def test_other_days_are_not_touched() -> None:
    r = one("parso 2 baje call karungi")
    assert r.ambiguous and r.canonical == "2026-11-14T02:00 | 2026-11-14T14:00"


def test_past_rule_is_off_by_default_and_both_rules_are_policy_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    real = policy()
    assert real.choice("context.today_future") == "resolve" and real.choice("context.today_past") == "flag"
    assert real.questions["context.today_future"] == real.questions["context.today_past"] == "Q13"
    assert one("aaj 5 baje pahuncha tha").ambiguous

    on = dataclasses.replace(real, values={**real.values, "context.today_past": "resolve"})
    monkeypatch.setattr(api, "policy", lambda: on)
    r = one("aaj 5 baje pahuncha tha")
    assert r.canonical == "2026-11-12T05:00" and "has not happened yet" in r.notes[-1]

    off = dataclasses.replace(real, values={**real.values, "context.today_future": "flag"})
    monkeypatch.setattr(api, "policy", lambda: off)
    assert one("aaj 2 bje call krungi").ambiguous


def test_without_a_base_the_clock_is_used_and_flagged() -> None:
    results = kitna.parse("aaj 2 bje call krungi", now=lambda: TEN)
    assert results[0].canonical == "2026-11-12T14:00" and results[0].warnings == (api.CLOCK_WARNING,)
