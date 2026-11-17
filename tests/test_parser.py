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
    ("dedh do kilo", ["1.5..2"]),
])
def test_assorted(text: str, expected: list[str]) -> None:
    assert vals(text) == expected


def test_numeric_dates_and_clock_times_are_not_read_as_numbers() -> None:
    assert vals("2026-12-25", kind="number") == []
    assert vals("12/11/2026 ko 5:30 baje", kind="number") == []
    assert vals("2026-12-25") == ["2026-12-25"]
    assert vals("12/11/2026 ko 5:30 pm") == ["2026-11-12T17:30"]


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
    with pytest.raises(kitna.KitnaError):
        kitna.parse("kal", relative_base="2026-11-12")  # type: ignore[arg-type]


def test_tables_are_versioned_and_unambiguous() -> None:
    lex = lexicon()  # raises DataTableError on a spelling listed under two values
    assert set(lex.versions) == {"numbers_hi.tsv", "numbers_en.tsv", "scales.tsv", "fractions.tsv",
                                 "markers.tsv", "context.tsv", "time_words.tsv", "policy.tsv"}
    assert all(v for v in lex.versions.values())
    hindi = {int(e.value) for e in lex.words.values() if e.cat == "num" and not e.en}
    assert hindi == set(range(100))
    assert issubclass(DataTableError, RuntimeError)


def test_tokenizer_keeps_rs_dot_together() -> None:
    assert [t.norm for t in tokenize("Rs. 1,250")] == ["rs", "1250"]


# --------------------------------------------------------------------------- false positives first


@pytest.mark.parametrize("text", [
    "no one came", "one of them", "the one I want", "ten", "I have two options", "a hundred times",
    "May I come in", "march karo", "is baar", "challenge accepted",
])
def test_english_and_lookalike_words_do_not_fire_without_an_anchor(text: str) -> None:
    assert kitna.parse(text, relative_base=BASE) == []


@pytest.mark.parametrize(("text", "expected"), [
    ("ten rupaye", ["INR 10"]),
    ("two lakh", ["200000"]),
    ("two hundred", ["200"]),
    ("ten din", ["P10D"]),
    ("at five pm", ["17:00"]),
    ("पाँच two", ["5..2"]),
])
def test_english_number_words_count_when_anchored(text: str, expected: list[str]) -> None:
    got = [r.canonical for r in kitna.parse(text, relative_base=BASE)]
    assert got == expected or (text == "पाँच two" and got == ["5", "2"])


@pytest.mark.xfail(strict=True, reason="known limitation: 'saath' (60) needs a hyphen, scale or currency word "
                                       "beside it, because it usually means 'with'")
def test_known_limitation_pachaas_saath_without_hyphen() -> None:
    assert vals("pachaas saath") == ["50..60"]


def test_pachaas_saath_with_hyphen_or_scale_works() -> None:
    assert vals("pachaas-saath") == ["50..60"]
    assert vals("pachaas saath hazaar") == ["50000..60000"]


# --------------------------------------------------------------------------- time, dates, policy

BASE = __import__("datetime").datetime(2026, 11, 12, 10, 0)  # a Thursday


@pytest.mark.parametrize(("text", "expected"), [
    ("kal subah saade saat baje 2.5 lakh rupaye bhej dunga", ["2026-11-13T07:30", "INR 250000"]),
    ("do din pehle 2 ghante ka kaam tha", ["2026-11-10", "PT2H"]),
    ("15 august ko jaunga", ["2027-08-15"]),
    ("har somvaar", []),
    ("kal aaya tha, parso jaunga", ["2026-11-11", "2026-11-14"]),
    ("kal jaunga lekin gaya tha", ["2026-11-13"]),
    ("kal gaya tha jaunga", ["2026-11-11 | 2026-11-13"]),  # opposite cues in one clause cancel
    ("tomorrow 5 pm", ["2026-11-13T17:00"]),
    ("31 tareekh ko jaunga", ["2026-12-31"]),  # November has no 31st
])
def test_temporal_assorted(text: str, expected: list[str]) -> None:
    assert [r.canonical for r in kitna.parse(text, relative_base=BASE)] == expected


def test_sub_day_offset_needs_a_time_of_day() -> None:
    import datetime as dt

    (r,) = kitna.parse("do ghante baad", relative_base=dt.date(2026, 11, 12))
    assert r.kind == "duration" and r.canonical == "PT2H" and "relative_base" in r.notes[0]
    (r,) = kitna.parse("do ghante baad", relative_base=BASE)
    assert r.kind == "datetime" and r.canonical == "2026-11-12T12:00"


def test_default_base_is_the_system_clock() -> None:
    import datetime as dt

    r = kitna.parse_date("aaj")
    assert r is not None and abs((r.value - dt.date.today()).days) <= 1


def test_ambiguous_results_never_carry_a_value() -> None:
    for text in ("kal", "5 baje", "26 January", "20 tareekh ko", "guruvaar", "kal shaam 5 baje", "9 se 11 baje"):
        (r,) = kitna.parse(text, relative_base=BASE)
        assert r.ambiguous and r.value is None and len(r.candidates) >= 2 and " | " in r.canonical


def test_convenience_functions() -> None:
    t = kitna.parse_time("shaam sawa paanch baje")
    d = kitna.parse_date("26 January", BASE, prefer="future")
    assert t is not None and t.canonical == "17:15"
    assert d is not None and d.canonical == "2027-01-26"


def test_policy_file_is_the_single_place_for_contested_rules() -> None:
    from kitna.policy import policy

    pol = policy()
    # every open question that changes parser behaviour has a row
    asked = {q for q in pol.questions.values() if q != "-"}
    assert {"Q2", "Q3", "Q3b", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9", "Q9b", "Q11", "Q12", "Q13"} <= asked
    r = kitna.parse_number("saade ek")
    assert r is not None and r.canonical == "1.5" and r.confidence == 0.8
    assert r.warnings and "Nonstandard" in r.warnings[0]
    assert pol.choice("weekday.agle") == "flag"
    assert 2 in pol.dayparts["raat"].am and 4 in pol.dayparts["shaam"].pm


def test_changing_policy_changes_behaviour_without_code(monkeypatch: pytest.MonkeyPatch) -> None:
    """Q7 flipped by data alone: 'agle shanivaar' becomes next week's Saturday."""
    import dataclasses

    from kitna import dates
    from kitna.policy import policy

    real = policy()
    flipped = dataclasses.replace(real, values={**real.values, "weekday.agle": "next_week",
                                                "date.no_year": "future"})
    monkeypatch.setattr(dates, "policy", lambda: flipped)
    assert kitna.parse_date("agle shanivaar", BASE).canonical == "2026-11-21"  # type: ignore[union-attr]
    assert kitna.parse_date("26 January", BASE).canonical == "2027-01-26"  # type: ignore[union-attr]
    monkeypatch.undo()
    assert kitna.parse_date("agle shanivaar", BASE).canonical == "2026-11-14 | 2026-11-21"  # type: ignore[union-attr]


def test_cli(capsys: pytest.CaptureFixture[str]) -> None:
    from kitna.cli import main

    assert main(["parse", "dhai lakh"]) == 0
    assert "250000" in capsys.readouterr().out
    assert main(["parse", "5 baje", "--json"]) == 0
    assert '"ambiguous": true' in capsys.readouterr().out
    assert main(["parse", "kuch nahi"]) == 1
    assert main(["parse", "kal", "--base", "2026-11-12", "--prefer", "future", "--kind", "date"]) == 0
    assert "2026-11-13" in capsys.readouterr().out


def test_ek_baar_is_a_policy_row(monkeypatch: pytest.MonkeyPatch) -> None:
    """Q12 flipped by data alone."""
    import dataclasses

    from kitna import normalize
    from kitna.policy import policy

    assert vals("ek baar") == []
    real = policy()
    flipped = dataclasses.replace(real, values={**real.values, "number.ek_baar": "one"})
    monkeypatch.setattr(normalize, "policy", lambda: flipped)
    normalize.lexicon.cache_clear()
    try:
        assert vals("ek baar") == ["1"]
    finally:
        monkeypatch.undo()
        normalize.lexicon.cache_clear()
    assert vals("ek baar") == []


def test_english_day_after_tomorrow_is_not_read_as_tomorrow() -> None:
    import datetime as dt

    import kitna

    base = dt.datetime(2026, 11, 12, 10, 0)
    got = kitna.parse("book it for the day after tomorrow", relative_base=base)
    assert [r.canonical for r in got] == ["2026-11-14"]
    assert [r.canonical for r in kitna.parse("the day before yesterday", relative_base=base)] == ["2026-11-10"]
    assert [r.canonical for r in kitna.parse("tomorrow", relative_base=base)] == ["2026-11-13"]
