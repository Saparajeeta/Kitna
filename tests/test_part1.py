"""Regression tests for the phase-2 fixes: clock handling, false positives, the
gap list from review round 1, script variants and the versioned output schema."""
from __future__ import annotations

import datetime as dt
import json
from importlib import resources
from typing import Any

import jsonschema
import pytest
from conftest import load_cases, run_case
from hypothesis import given, settings
from hypothesis import strategies as st

import kitna
from kitna.api import CLOCK_WARNING
from kitna.normalize import detect_script, lexicon

BASE = dt.datetime(2026, 11, 12, 10, 0)  # Thursday
FAKE_NOW = dt.datetime(2030, 1, 15, 9, 30, 42)
SCHEMA = json.loads(resources.files("kitna").joinpath("data", "result.schema.json").read_text(encoding="utf-8"))


def canon(text: str, **kw: Any) -> list[str]:
    kw.setdefault("relative_base", BASE)
    return [r.canonical for r in kitna.parse(text, **kw)]


# --------------------------------------------------------------------------- system clock


def test_missing_base_uses_injected_clock_and_warns() -> None:
    (r,) = kitna.parse("kal jaunga", now=lambda: FAKE_NOW)
    assert r.canonical == "2030-01-16" and r.warnings == (CLOCK_WARNING,)
    (r,) = kitna.parse("do ghante baad", now=lambda: FAKE_NOW)
    assert r.canonical == "2030-01-15T11:30" and r.warnings  # seconds are dropped


def test_explicit_base_never_warns_and_ignores_now() -> None:
    (r,) = kitna.parse("kal jaunga", relative_base=BASE, now=lambda: FAKE_NOW)
    assert r.canonical == "2026-11-13" and r.warnings == ()


@pytest.mark.parametrize("text", ["5 baje", "shaam 5 baje", "15 August 2027", "12/11/2026", "dhai ghante", "dhai lakh"])
def test_absolute_values_need_no_base_and_never_warn(text: str) -> None:
    def boom() -> dt.datetime:
        return FAKE_NOW

    for r in kitna.parse(text, now=boom, strict=True):
        assert r.warnings == ()


@pytest.mark.parametrize("text", ["kal", "somvaar ko", "3 din baad", "do ghante baad", "26 January", "20 tareekh ko",
                                  "kal subah 7 baje", "agle mahine ki 5 tareekh"])
def test_strict_mode_requires_base_for_relative_expressions(text: str) -> None:
    with pytest.raises(kitna.KitnaError, match="relative_base"):
        kitna.parse(text, strict=True)
    assert kitna.parse(text, strict=True, relative_base=BASE)


def test_strict_mode_is_scoped_to_the_requested_kind() -> None:
    # asking only for money must not fail because a relative date is also present
    (r,) = kitna.parse("kal 500 rupaye", kind="money", strict=True)
    assert r.canonical == "INR 500"


def test_now_must_return_a_datetime() -> None:
    with pytest.raises(kitna.KitnaError):
        kitna.parse("kal", now=lambda: dt.date(2030, 1, 1))  # type: ignore[arg-type,return-value]


# --------------------------------------------------------------------------- false positives


@pytest.mark.parametrize("text", [
    "I have two options", "no one came", "one of them", "ek baar", "mere saat chalo",
    "mujhe paise de do", "the one I want", "ten",
])
def test_no_quantity_is_reported(text: str) -> None:
    assert kitna.parse(text, relative_base=BASE) == []


def test_pehle_as_first_is_not_a_date_offset() -> None:
    assert canon("pehle teen din rukna") == ["P3D"]
    assert canon("pehle teen din rukna", kind="date") == []


# --------------------------------------------------------------------------- gap list from review round 1


@pytest.mark.parametrize(("text", "expected"), [
    ("9 se 11 baje", ["09:00..11:00 | 21:00..23:00"]),
    ("5 baje tak", ["..05:00 | ..17:00"]),
    ("shaam 5 baje tak", ["..17:00"]),
    ("do ghante baad", ["2026-11-12T12:00"]),
    ("das minute pehle", ["2026-11-12T09:50"]),
    ("kal subah 7 baje jaunga", ["2026-11-13T07:00"]),
    ("kal gaya tha aur parso jaunga", ["2026-11-11", "2026-11-14"]),
    ("kal tak", ["..2026-11-11 | ..2026-11-13"]),
    ("parso tak bhej dunga", ["..2026-11-14"]),
    ("shanivaar ko gaya tha", ["2026-11-07"]),
    ("2 lakhs", ["200000"]),
    ("5 crores", ["50000000"]),
    ("two lakh fifty thousand", ["250000"]),
    ("rupees fifty thousand only", ["INR 50000"]),
    ("५ lakh", ["500000"]),
    ("पाँच ह\u095bार", ["5000"]),
    ("पाँच हज\u093cार", ["5000"]),
    ("20 tareekh ko", ["2026-10-20 | 2026-11-20"]),
    ("teen-chaar hazaar", ["3000..4000"]),
    ("pachaas-saath", ["50..60"]),
    # Devanagari / Roman mixes
    ("kal शाम 5 baje जाऊँगा", ["2026-11-13T17:00"]),
    ("ढाई lakh रुपये", ["INR 250000"]),
    ("अगले somvaar को", ["2026-11-16"]),
    ("२ ghante बाद", ["2026-11-12T12:00"]),
    ("subah साढ़े 7 बजे", ["07:30"]),
])
def test_gap_cases(text: str, expected: list[str]) -> None:
    assert canon(text) == expected


# --------------------------------------------------------------------------- script variants

LEX = lexicon()


def _pair(spellings: list[str]) -> tuple[str, str] | None:
    roman = next((s for s in spellings if detect_script(s) == "roman"), None)
    deva = next((s for s in spellings if detect_script(s) == "devanagari"), None)
    return (roman, deva) if roman and deva else None


def _temporal_pairs(role: str) -> list[tuple[str, str]]:
    by_key: dict[str, list[str]] = {}
    for key, phrase in LEX.temporal[role]:
        by_key.setdefault(key, []).append(" ".join(phrase))
    return [p for p in (_pair(v) for _, v in sorted(by_key.items())) if p]


def _number_pairs() -> dict[int, tuple[str, str]]:
    by_val: dict[int, list[str]] = {}
    for k, e in LEX.words.items():
        if e.cat == "num" and not e.en:
            by_val.setdefault(int(e.value), []).append(k)
    return {v: p for v, p in ((v, _pair(s)) for v, s in by_val.items()) if p}


NUM = _number_pairs()
P = {role: _temporal_pairs(role) for role in ("daypart", "rel", "weekday", "next", "prev", "after", "before")}
W = {"baje": ("baje", "बजे"), "din": ("din", "दिन"), "rupaye": ("rupaye", "रुपये"), "lakh": ("lakh", "लाख"),
     "hazaar": ("hazaar", "हज़ार"), "saade": ("saade", "साढ़े"), "sawa": ("sawa", "सवा"), "paune": ("paune", "पौने"),
     "dhai": ("dhai", "ढाई"), "tha": ("gaya tha", "गया था"), "ga": ("jaunga", "जाऊँगा"), "ko": ("ko", "को"),
     "tak": ("tak", "तक"), "se": ("se", "से")}

hour = st.integers(1, 12).map(NUM.__getitem__)
small = st.integers(3, 30).map(NUM.__getitem__)
frac = st.sampled_from([W["saade"], W["sawa"], W["paune"]])
pick = lambda role: st.sampled_from(P[role])  # noqa: E731
templates = st.one_of(
    st.tuples(pick("daypart"), frac, hour, st.just(W["baje"])),
    st.tuples(pick("daypart"), hour, st.just(W["baje"]), st.just(W["tak"])),
    st.tuples(hour, st.just(W["se"]), hour, st.just(W["baje"])),
    st.tuples(pick("rel"), st.sampled_from([W["tha"], W["ga"]])),
    st.tuples(pick("rel"), pick("daypart"), hour, st.just(W["baje"]), st.just(W["ga"])),
    st.tuples(st.one_of(pick("next"), pick("prev")), pick("weekday"), st.just(W["ko"])),
    st.tuples(pick("weekday"), st.just(W["ko"]), st.just(W["tha"])),
    st.tuples(small, st.just(W["din"]), st.one_of(pick("after"), pick("before"))),
    st.tuples(frac, small, st.sampled_from([W["lakh"], W["hazaar"]]), st.just(W["rupaye"])),
    st.tuples(st.just(W["dhai"]), st.just(W["lakh"]), st.just(W["rupaye"]), st.just(W["tak"])),
    st.tuples(small, st.just(W["se"]), small, st.just(W["hazaar"]), st.just(W["rupaye"])),
)


@given(templates, st.data())
@settings(max_examples=500)
def test_same_expression_in_any_script_mix_gives_the_same_result(template: tuple[tuple[str, str], ...],
                                                                 data: st.DataObject) -> None:
    """Roman, Devanagari, and any per-word mix of the two must parse to identical values."""
    roman = " ".join(w[0] for w in template)
    deva = " ".join(w[1] for w in template)
    mask = data.draw(st.lists(st.booleans(), min_size=len(template), max_size=len(template)))
    mixed = " ".join(w[int(m)] for w, m in zip(template, mask, strict=True))
    want = [(r.kind, r.canonical, r.ambiguous, r.approximate, r.confidence)
            for r in kitna.parse(roman, relative_base=BASE)]
    assert want, roman
    for variant in (deva, mixed):
        got = [(r.kind, r.canonical, r.ambiguous, r.approximate, r.confidence)
               for r in kitna.parse(variant, relative_base=BASE)]
        assert got == want, (roman, variant)


# --------------------------------------------------------------------------- versioned output schema


def test_schema_file_is_valid_and_versioned() -> None:
    jsonschema.Draft202012Validator.check_schema(SCHEMA)
    assert SCHEMA["properties"]["schema_version"]["const"] == kitna.RESULT_SCHEMA_VERSION == "1"
    assert set(SCHEMA["properties"]["kind"]["enum"]) == set(kitna.KINDS)


def test_every_golden_case_output_matches_the_schema() -> None:
    validator = jsonschema.Draft202012Validator(SCHEMA)
    seen = 0
    for case in load_cases():
        for r in run_case(case):
            d = r.to_dict()
            validator.validate(d)
            assert json.loads(json.dumps(d, ensure_ascii=False)) == d
            seen += 1
    assert seen > 300


def test_to_dict_field_set_is_frozen() -> None:
    """Changing this list is a schema change: bump RESULT_SCHEMA_VERSION and add a changelog entry."""
    (r,) = kitna.parse("dhai lakh rupaye tak")
    assert list(r.to_dict()) == ["schema_version", "span", "text", "kind", "value", "canonical", "confidence",
                                 "ambiguous", "candidates", "approximate", "notes", "warnings"]
    assert r.to_dict()["value"] == {"min": None, "max": {"amount": "250000", "currency": "INR"}}


@given(st.text(max_size=60))
@settings(max_examples=300)
def test_any_output_matches_the_schema(text: str) -> None:
    validator = jsonschema.Draft202012Validator(SCHEMA)
    for r in kitna.parse(text, relative_base=BASE):
        validator.validate(r.to_dict())
