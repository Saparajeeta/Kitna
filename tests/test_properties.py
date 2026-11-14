"""Property and fuzz tests (hypothesis)."""
from __future__ import annotations

from decimal import Decimal

from hypothesis import given, settings
from hypothesis import strategies as st

import kitna
from kitna.normalize import detect_script, lexicon, squeeze

LEX = lexicon()
_ROMAN: dict[int, str] = {}
_DEVA: dict[int, str] = {}
for _k, _e in LEX.words.items():
    if _e.cat == "num" and not _e.en:
        (_DEVA if detect_script(_k) == "devanagari" else _ROMAN).setdefault(int(_e.value), _k)
SCALES = {"roman": [(10**7, "crore"), (10**5, "lakh"), (10**3, "hazaar"), (100, "sau")],
          "devanagari": [(10**7, "करोड़"), (10**5, "लाख"), (10**3, "हज़ार"), (100, "सौ")]}


def to_words(n: int, script: str = "roman") -> str:
    """Independent reference: spell 0 <= n < 10^9 in Hindi."""
    names = _ROMAN if script == "roman" else _DEVA
    if n == 0:
        return names[0]
    parts = []
    for size, word in SCALES[script]:
        q, n = divmod(n, size)
        if q:
            parts += [names[q], word]
    if n:
        parts.append(names[n])
    return " ".join(parts)


def indian_grouping(n: int) -> str:
    s = str(n)
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    groups = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    return ",".join(([head] if head else []) + groups + [tail])


numbers = st.integers(min_value=0, max_value=10**9 - 1)


@given(numbers, st.sampled_from(["roman", "devanagari"]))
def test_round_trip_words(n: int, script: str) -> None:
    r = kitna.parse_number(to_words(n, script))
    assert r is not None and r.value == n and r.confidence == 1.0 and not r.ambiguous


@given(numbers)
def test_round_trip_indian_grouping(n: int) -> None:
    for text in (indian_grouping(n), indian_grouping(n).translate(str.maketrans("0123456789", "०१२३४५६७८९"))):
        r = kitna.parse_number(text)
        assert r is not None and r.value == n


@given(st.integers(1, 99), st.integers(1, 99))
def test_scales_are_monotonic(a: int, b: int) -> None:
    order = ["", "sau", "hazaar", "lakh", "crore"]
    got = []
    for w in order:
        r = kitna.parse_number(f"{_ROMAN[a]} {w}".strip())
        assert r is not None
        got.append(r.value)
    assert got == sorted(got) and len(set(got)) == len(got)
    if a < b:  # same scale: bigger mantissa, bigger value
        for w in order[1:]:
            ra, rb = kitna.parse_number(f"{_ROMAN[a]} {w}"), kitna.parse_number(f"{_ROMAN[b]} {w}")
            assert ra is not None and rb is not None and ra.value < rb.value


@given(st.integers(3, 99), st.sampled_from(["sawa", "saade", "paune"]),
       st.sampled_from([("", 1), ("sau", 100), ("hazaar", 1000), ("lakh", 10**5), ("crore", 10**7)]))
def test_fraction_idioms(n: int, word: str, scale: tuple[str, int]) -> None:
    delta = {"sawa": Decimal("0.25"), "saade": Decimal("0.5"), "paune": Decimal("-0.25")}[word]
    r = kitna.parse_number(f"{word} {_ROMAN[n]} {scale[0]}".strip())
    assert r is not None and r.value == (n + delta) * scale[1]


@given(st.text(max_size=80))
@settings(max_examples=400)
def test_never_crashes_on_arbitrary_unicode(text: str) -> None:
    for kind in (None, *kitna.KINDS):
        results = kitna.parse(text, kind=kind, relative_base=BASE)
        assert results == kitna.parse(text, kind=kind, relative_base=BASE)  # deterministic
        last = 0
        for r in results:
            assert 0 <= r.span[0] < r.span[1] <= len(text) and r.span[0] >= last
            assert text[r.span[0]:r.span[1]] == r.text
            assert 0.0 < r.confidence <= 1.0
            last = r.span[1]


BASE = __import__("datetime").datetime(2026, 11, 12, 10, 0)
TEMPORAL_VOCAB = sorted({" ".join(p) for entries in LEX.temporal.values() for _, p in entries})
VOCAB = sorted(LEX.words) + TEMPORAL_VOCAB + ["5:30", "12/11/2026", "2026", "31", "29", "12", "24", "0",
                                              "rupaye", "se", "tak", "ke", "aaspaas", "kam",
                             "point", "double", "-", "₹",
                             "paise", "lagbhag", "baje", "mujhe", "de", ",", "5", "2,50,000", "1.5", "L", "k"]


@given(st.lists(st.sampled_from(VOCAB), max_size=12), st.sampled_from([" ", "", "  ", "-"]))
@settings(max_examples=400)
def test_never_crashes_on_word_salad(words: list[str], joiner: str) -> None:
    """ASR-style noise: number vocabulary in any order, with spaces dropped."""
    text = joiner.join(words)
    for r in kitna.parse(text, relative_base=BASE):
        assert text[r.span[0]:r.span[1]] == r.text
        assert r.ambiguous == (r.value is None) == bool(r.candidates)


@given(st.dates(min_value=__import__("datetime").date(1990, 1, 1), max_value=__import__("datetime").date(2090, 1, 1)),
       st.sampled_from(sorted({" ".join(p) for role in ("rel", "weekday", "next", "prev", "this", "month",
                                                         "unit", "after", "before", "tareekh", "daypart", "baje")
                               for _, p in LEX.temporal[role]}) + ["29", "30", "31", "1", "do", "dedh"]).flatmap(
           lambda w: st.lists(st.just(w) | st.sampled_from(["31", "29", "agle", "mahine", "ki", "tareekh", "feb",
                                                            "pichhle", "hafte", "saal", "baad", "pehle", "100"]),
                              min_size=1, max_size=6)))
@settings(max_examples=400)
def test_dates_never_crash_on_any_base_date(base, words: list[str]) -> None:  # type: ignore[no-untyped-def]
    """Month ends, leap days and far years must not raise."""
    for r in kitna.parse(" ".join(words), relative_base=base):
        assert r.kind in kitna.KINDS


@given(st.integers(1, 12), st.sampled_from(["subah", "dopahar", "shaam", "raat"]))
def test_daypart_never_leaves_a_time_ambiguous(hour: int, daypart: str) -> None:
    r = kitna.parse_time(f"{daypart} {hour} baje")
    assert r is not None and not r.ambiguous and r.value.hour % 12 == hour % 12


@given(st.integers(1, 12))
def test_bare_hour_is_always_flagged_with_both_readings(hour: int) -> None:
    r = kitna.parse_time(f"{hour} baje")
    assert r is not None and r.ambiguous and [c.hour for c in r.candidates] == [hour % 12, hour % 12 + 12]


@given(st.sampled_from(sorted(k for k, e in LEX.words.items() if k.isascii() and len(k) >= 4)),
       st.data())
def test_doubled_letter_never_changes_the_value(word: str, data: st.DataObject) -> None:
    """Spelling noise may lose a word, but must never turn it into a different number."""
    i = data.draw(st.integers(0, len(word) - 1))
    noisy = word[:i] + word[i] + word[i:]
    truth, got = LEX.words[word], kitna.normalize.lookup(noisy)
    if noisy in LEX.words or got is None:
        return
    assert (got[0].cat, got[0].value) == (truth.cat, truth.value)
    assert got[1] < 1.0 and squeeze(noisy) == squeeze(word)
