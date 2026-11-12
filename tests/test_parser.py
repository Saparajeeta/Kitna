"""Behaviour not covered by the golden file: API contract, look-alikes, data tables."""
from __future__ import annotations

from decimal import Decimal

import pytest

import kitna
from kitna.normalize import DataTableError, lexicon, lookup, tokenize, word_key


def vals(text: str, kind: str | None = None) -> list[str]:
    return [r.canonical for r in kitna.parse(text, kind=kind)]


def test_script_detection() -> None:
    assert kitna.detect_script("dhai lakh") == "roman"
    assert kitna.detect_script("ढाई लाख") == "devanagari"
    assert kitna.detect_script("५ lakh") == "mixed"
    assert kitna.detect_script("2,50,000") == "none"


def test_nukta_forms_share_a_key() -> None:
    assert word_key("ह\u095bार") == word_key("हज\u093cार") == word_key("हजार")
    assert word_key("पाँच") == word_key("पांच")


def test_spans_index_the_original_text() -> None:
    text = "Ramesh ko ढाई हज\u093cार रुपये bhejo"
    (r,) = kitna.parse(text)
    assert text[r.span[0]:r.span[1]] == r.text == "ढाई हज\u093cार रुपये"
    assert r.value == kitna.Money(Decimal(2500))


@pytest.mark.parametrize("text", [
    "do you have change", "uske saath jao", "ek saath chalo ", "mujhe ticket do",
    "rehne do", "ek baar", "there", "chappal", "saare log",
])
def test_lookalikes_give_nothing_or_no_wrong_number(text: str) -> None:
    got = vals(text)
    assert "2" not in got and "60" not in got and "1..60" not in got
    assert not any(c.startswith("3") or c.startswith("56") for c in got)


@pytest.mark.parametrize(("text", "expected"), [
    ("ek ya do", ["1", "2"]),
    ("500 rupaye do", ["INR 500"]),
    ("saath rupaye", ["INR 60"]),
    ("ek sau saath", ["160"]),
    ("two hundred and five", ["205"]),
    ("twenty-five thousand", ["25000"]),
    ("thirty five lakhs", ["3500000"]),
    ("do hazaar paanch sau pachpan rupaye", ["INR 2555"]),
    ("₹ 1.5 lakh se 2 lakh tak", ["INR 150000..INR 200000"]),
    ("kam se kam 5 lakh", ["500000.."]),
    ("100 se 2 hazaar", ["100..2000"]),
    ("5 se 3", ["5", "3"]),
    ("dedh do ghante", ["1.5..2"]),
])
def test_assorted(text: str, expected: list[str]) -> None:
    assert vals(text) == expected


def test_numeric_dates_and_clock_times_are_not_read_as_numbers() -> None:
    assert vals("2026-12-25") == []
    assert vals("12/11/2026 ko 5:30 baje") == []


def test_kind_is_hint_and_filter() -> None:
    assert vals("500 rupaye", kind="number") == ["500"]
    assert vals("5000", kind="money") == ["INR 5000"]
    assert vals("ek do", kind="digits") == ["12"]
    assert vals("2.5L", kind="number") == ["2.5"]
    assert kitna.parse_number("kuch nahi") is None
    r = kitna.parse_money("dhai lakh")
    assert r is not None and r.value == kitna.Money(Decimal(250000)) and r.notes


def test_spelling_repair_lowers_confidence() -> None:
    exact = kitna.parse_number("tees hazaar")
    squeezed = kitna.parse_number("tees hazzar")
    edited = kitna.parse_number("ninyaanwe hazaar")  # v/w swap: one edit from a listed spelling
    assert exact and squeezed and edited
    assert exact.confidence == 1.0 > squeezed.confidence > edited.confidence > 0
    assert squeezed.value == 30000 and edited.value == 99000
    assert lookup("thirsty") is None  # listed under no_fuzzy


def test_bad_arguments() -> None:
    with pytest.raises(kitna.KitnaError):
        kitna.parse("ek", kind="weight")
    with pytest.raises(kitna.KitnaError):
        kitna.parse("ek", prefer="maybe")
    with pytest.raises(kitna.KitnaError):
        kitna.parse(123)  # type: ignore[arg-type]
    with pytest.raises(NotImplementedError):
        kitna.parse("5 baje", kind="time")


def test_tables_are_versioned_and_unambiguous() -> None:
    lex = lexicon()  # raises DataTableError on a spelling listed under two values
    assert set(lex.versions) == {"numbers_hi.tsv", "numbers_en.tsv", "scales.tsv", "fractions.tsv",
                                 "markers.tsv", "context.tsv"}
    assert all(v for v in lex.versions.values())
    hindi = {int(e.value) for e in lex.words.values() if e.cat == "num" and not e.en}
    assert hindi == set(range(100))
    assert issubclass(DataTableError, RuntimeError)


def test_tokenizer_keeps_rs_dot_together() -> None:
    assert [t.norm for t in tokenize("Rs. 1,250")] == ["rs", "1250"]
