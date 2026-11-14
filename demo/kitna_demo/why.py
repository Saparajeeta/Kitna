"""Why a value was read the way it was: the rule that fired, in English and Hindi.

The Hindi wording was drafted by an AI and has not been checked by a native speaker.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache
from importlib import resources

from kitna import Result
from kitna.normalize import match_temporal, tokenize, word_key
from kitna.policy import policy

from .say import indian


@dataclass(frozen=True)
class Why:
    en: str
    hi: str
    policy_key: str | None = None
    #: True when this line is the reason a value is ambiguous
    is_ambiguity: bool = False

    def text(self, lang: str) -> str:
        return self.hi if lang == "hi" else self.en

    def contested(self) -> str | None:
        """Open-question id when this rule is still awaiting native speakers."""
        if not self.policy_key:
            return None
        q = policy().questions.get(self.policy_key, "-")
        return None if q in ("-", "") else q


T: dict[str, tuple[str, str]] = {
    "add_half": ("‘{w}’ adds a half to the number after it.", "‘{w}’ अगली संख्या में आधा जोड़ता है।"),
    "add_quarter": ("‘{w}’ adds a quarter to the number after it.", "‘{w}’ अगली संख्या में चौथाई जोड़ता है।"),
    "sub_quarter": ("‘{w}’ takes a quarter off the number after it.", "‘{w}’ अगली संख्या में से चौथाई घटाता है।"),
    "fixed": ("‘{w}’ means {v}.", "‘{w}’ का मतलब {v} है।"),
    "scale": ("‘{w}’ is {v}.", "‘{w}’ यानी {v}।"),
    "currency": ("A rupee word or sign makes this an amount in rupees.",
                 "रुपये का शब्द या चिह्न होने से इसे रुपयों की रकम माना गया।"),
    "daypart": ("‘{w}’ decides whether this hour is AM or PM.", "‘{w}’ से तय हुआ कि यह समय AM है या PM।"),
    "kal": ("‘{w}’ can mean yesterday or tomorrow; the rest of the sentence has to decide.",
            "‘{w}’ का मतलब बीता हुआ कल भी हो सकता है और आने वाला कल भी; यह बाक़ी वाक्य से तय होता है।"),
    "parso": ("‘{w}’ can mean two days ago or two days from now; the rest of the sentence has to decide.",
              "‘{w}’ का मतलब दो दिन पहले भी हो सकता है और दो दिन बाद भी; यह बाक़ी वाक्य से तय होता है।"),
    "agle": ("‘{w}’ before a weekday is read as the next one coming, not the one in the following week.",
             "वार से पहले ‘{w}’ को सबसे पहले आने वाला वार माना गया, उसके अगले हफ़्ते वाला नहीं।"),
    "bare_hour": ("There is no morning, afternoon, evening or night word, so the hour could be AM or PM. "
                  "Kitna does not guess.",
                  "सुबह, दोपहर, शाम या रात जैसा कोई शब्द नहीं है, इसलिए समय AM भी हो सकता है और PM भी। "
                  "Kitna अंदाज़ा नहीं लगाता।"),
    "no_cue": ("Nothing in the sentence shows past or future, so both days are kept.",
               "वाक्य में बीते या आने वाले समय का कोई संकेत नहीं है, इसलिए दोनों दिन रखे गए।"),
    "future": ("The verb is in the future tense, so the coming day is meant.",
               "क्रिया भविष्य काल में है, इसलिए आने वाला दिन माना गया।"),
    "past": ("The verb is in the past tense, so the day that has passed is meant.",
             "क्रिया भूतकाल में है, इसलिए बीता हुआ दिन माना गया।"),
    "weak_imperative": ("The sentence is a request, which is read as pointing to the future. This is a weaker "
                        "signal, so the confidence is lower.",
                        "वाक्य एक अनुरोध है, जिसे आने वाले समय का संकेत माना गया। यह कमज़ोर संकेत है, इसलिए भरोसा कम रखा गया।"),
    "weak_present": ("Present tense (‘hai’) is read as a weak sign of the future, so the confidence is lower.",
                     "वर्तमान काल (‘है’) को आने वाले समय का कमज़ोर संकेत माना गया, इसलिए भरोसा कम रखा गया।"),
    "context_future": ("It is {now} now. {dropped} today has already passed and the sentence points to the future, "
                       "so the other reading is used.",
                       "अभी {now} बजे हैं। आज का {dropped} निकल चुका है और वाक्य आने वाले समय की बात करता है, "
                       "इसलिए दूसरा समय चुना गया।"),
    "context_past": ("It is {now} now. {dropped} today has not happened yet and the sentence is about the past, "
                     "so the other reading is used.",
                     "अभी {now} बजे हैं। आज का {dropped} अभी आया नहीं है और वाक्य बीते समय की बात करता है, "
                     "इसलिए दूसरा समय चुना गया।"),
    "regional": ("‘narso / tarso’ is regional, so the confidence is slightly lower.",
                 "‘नरसों / तरसों’ कुछ इलाक़ों में ही बोला जाता है, इसलिए भरोसा थोड़ा कम रखा गया।"),
    "odd_daypart": ("This hour is unusual for that part of the day, so the confidence is lower.",
                    "दिन के उस हिस्से के लिए यह घंटा असामान्य है, इसलिए भरोसा कम रखा गया।"),
    "agle_flag": ("‘agle’ before a weekday could be the coming one or the one in the following week.",
                  "वार से पहले ‘अगले’ का मतलब आने वाला वार भी हो सकता है और उसके अगले हफ़्ते वाला भी।"),
    "same_day": ("Today is that weekday, so it could mean today or next week.",
                 "आज वही वार है, इसलिए मतलब आज भी हो सकता है और अगले हफ़्ते भी।"),
    "no_year": ("No year was given, so the last and the next such date are both possible.",
                "साल नहीं बताया गया, इसलिए पिछली और अगली दोनों तारीख़ें संभव हैं।"),
    "no_month": ("No month was given, so the last and the next such date are both possible.",
                 "महीना नहीं बताया गया, इसलिए पिछली और अगली दोनों तारीख़ें संभव हैं।"),
    "last_next": ("It could be the last such day or the next one.", "यह पिछला ऐसा दिन भी हो सकता है और अगला भी।"),
    "loose": ("The spelling was matched loosely (a repeated, missing or changed letter), so the confidence is lower.",
              "वर्तनी थोड़ी अलग थी (कोई अक्षर दोहराया, छूटा या बदला हुआ), इसलिए भरोसा कम रखा गया।"),
    "approx": ("A word such as ‘lagbhag’ or ‘about’ marks this as approximate.",
               "‘लगभग’ जैसे शब्द की वजह से इसे अंदाज़न माना गया।"),
    "direct": ("Read directly from the words and digits; no contested rule was needed.",
               "शब्दों और अंकों से सीधे पढ़ा गया; किसी विवादित नियम की ज़रूरत नहीं पड़ी।"),
    "clock": ("No ‘now’ was given, so the device clock was used for this value.",
              "‘अभी’ का समय नहीं दिया गया था, इसलिए डिवाइस की घड़ी इस्तेमाल हुई।"),
}
_FRACTION_VALUE = {"1.5": "1½", "2.5": "2½", "0.75": "¾", "0.5": "½", "0.25": "¼"}
_NOTE_RULES: tuple[tuple[str, str, str | None, bool], ...] = (
    (r"^no day-part word", "bare_hour", "time.bare_hour", True),
    (r"^no tense cue", "no_cue", None, True),
    (r"^future tense cue", "future", None, False),
    (r"^past tense cue", "past", None, False),
    (r"^imperative request", "weak_imperative", "cue.weak_imperative", False),
    (r"^present tense read", "weak_present", "cue.weak_present", False),
    (r"^narso / tarso", "regional", "confidence.narso", False),
    (r"is unusual with hour", "odd_daypart", "confidence.odd_daypart", False),
    (r"^'agle <weekday>'", "agle_flag", "weekday.agle", True),
    (r"^today is that weekday", "same_day", "weekday.same_day", True),
    (r"^no year given", "no_year", "date.no_year", True),
    (r"^no month given", "no_month", "date.no_month", True),
    (r"last or next occurrence$", "last_next", None, True),
)
_CONTEXT = re.compile(r"^context: (.+?) today (has already passed|has not happened yet) at (\d\d:\d\d)")


def _line(key: str, policy_key: str | None = None, ambiguity: bool = False, **fmt: str) -> Why:
    en, hi = T[key]
    return Why(en.format(**fmt), hi.format(**fmt), policy_key, ambiguity)


@lru_cache(maxsize=1)
def _tables() -> tuple[dict[str, tuple[str, str]], dict[str, str]]:
    """word -> (fraction type, value) and word -> scale value, from the parser's own data tables."""
    data = resources.files("kitna").joinpath("data")
    fractions: dict[str, tuple[str, str]] = {}
    scales: dict[str, str] = {}
    for raw in data.joinpath("fractions.tsv").read_text(encoding="utf-8").splitlines():
        cols = raw.split("\t")
        if raw.startswith("#") or len(cols) < 4:
            continue
        for word in cols[3].split():
            fractions[word_key(word)] = (cols[1], cols[2])
    for raw in data.joinpath("scales.tsv").read_text(encoding="utf-8").splitlines():
        cols = raw.split("\t")
        if raw.startswith("#") or len(cols) < 3:
            continue
        for word in cols[2].split():
            scales[word_key(word)] = cols[0]
    return fractions, scales


def from_note(note: str) -> Why:
    m = _CONTEXT.match(note)
    if m:
        direction = "future" if m.group(2) == "has already passed" else "past"
        return _line(f"context_{direction}", f"context.today_{direction}", dropped=m.group(1), now=m.group(3))
    for pattern, key, policy_key, ambiguity in _NOTE_RULES:
        if re.search(pattern, note):
            return _line(key, policy_key, ambiguity)
    return Why(note[:1].upper() + note[1:] + ".", note, None)  # a note this table does not know: shown as written


def explain(result: Result) -> list[Why]:
    """Every rule that shaped ``result``, most specific first."""
    fractions, scales = _tables()
    out: list[Why] = []
    tokens = tokenize(result.text)
    numeric = result.kind in ("number", "money", "duration", "time", "datetime")
    for i, tok in enumerate(tokens):
        word = tok.text
        if numeric and tok.norm in fractions:
            kind, value = fractions[tok.norm]
            if kind == "fixed":
                out.append(_line("fixed", w=word, v=_FRACTION_VALUE.get(value, value)))
            else:
                out.append(_line({"0.5": "add_half", "0.25": "add_quarter"}.get(value, "sub_quarter"), w=word))
        elif result.kind in ("number", "money") and tok.norm in scales:
            out.append(_line("scale", w=word, v=indian(Decimal(scales[tok.norm]))))
        part = match_temporal(tokens, i, "daypart")
        if part and result.kind in ("time", "datetime"):
            out.append(_line("daypart", f"daypart.{part[0]}", w=word))
        rel = match_temporal(tokens, i, "rel")
        if rel and rel[0] in ("kal", "parso", "narso"):
            out.append(_line("kal" if rel[0] == "kal" else "parso", w=word))
        if match_temporal(tokens, i, "next") and i + 1 < len(tokens) and match_temporal(tokens, i + 1, "weekday") \
                and not result.ambiguous:
            out.append(_line("agle", "weekday.agle", w=word))
    if result.kind == "money":
        out.append(_line("currency"))
    if result.approximate:
        out.append(_line("approx"))
    out.extend(from_note(n) for n in result.notes)
    if result.warnings:
        out.append(_line("clock"))
    if result.confidence < 1 and not any(w.policy_key or "confidence" in w.en for w in out):
        out.append(_line("loose", "confidence.squeezed"))
    return out or [_line("direct")]
