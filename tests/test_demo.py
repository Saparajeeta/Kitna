"""The demo's display logic (demo/kitna_demo). Pure functions: no Gradio needed for these."""
from __future__ import annotations

import csv
import datetime as dt
import io
import json
import re
from decimal import Decimal
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import pytest
from kitna_demo import NOTICE, STORY, action, compare, feedback, gallery, review, say, voice, why
from kitna_demo.read import MAX_TEXT, InputError, as_json, cards, highlighted, parse_base, read

import kitna
from kitna import Duration, Money, Range

ROOT = Path(__file__).resolve().parent.parent
NOW = dt.datetime(2026, 11, 12, 10, 0)
PAYMENT = "Ramesh ko kal 5 baje dhai lakh rupaye bhej dena"
INTERNAL = re.compile(r"\b(datetime|kind:|not decided|candidates|canonical|None|relative_base|\| )")


def visible(html: str) -> str:
    """Text a user can see: tags removed, the developer 'Details' table excluded."""
    html = re.sub(r"<details.*?</details>", "", html, flags=re.S)
    return re.sub(r"<[^>]+>", " ", html)


# ---------------------------------------------------------------- wording

@pytest.mark.parametrize("n, text", [(250000, "2,50,000"), (1000, "1,000"), (999, "999"), (12345678, "1,23,45,678"),
                                     (Decimal("1234.5"), "1,234.5"), (-150000, "-1,50,000"), (0, "0")])
def test_indian_grouping(n: Decimal | int, text: str) -> None:
    assert say.indian(n) == text


def test_plain_words_for_every_kind_of_value() -> None:
    assert say.plain(Money(Decimal("250000"))) == "₹2,50,000"
    assert say.plain(Money(Decimal("100.5"))) == "₹100.50"
    assert say.plain(dt.time(17, 0)) == "5:00 PM" and say.plain(dt.time(0, 5)) == "12:05 AM"
    assert say.plain(dt.date(2026, 11, 13), NOW) == "tomorrow, Fri 13 Nov 2026"
    assert say.plain(dt.date(2026, 11, 20), NOW) == "Fri 20 Nov 2026"
    assert say.plain(dt.datetime(2026, 11, 11, 7, 0), NOW) == "yesterday, Wed 11 Nov 2026, 7:00 AM"
    assert say.plain(dt.datetime(2026, 11, 13, 17, 0), NOW, short=True) == "tomorrow at 5:00 PM"
    assert say.plain(Duration(hours=2, minutes=30)) == "2 hours 30 minutes" and say.plain(Duration(days=1)) == "1 day"
    assert say.plain(Range(Decimal(2000), Decimal(3000))) == "2,000 to 3,000"
    assert say.plain(Range(None, dt.date(2026, 11, 14)), NOW) == "by day after tomorrow, Sat 14 Nov 2026"
    assert say.plain(Range(None, Decimal(5000))) == "up to 5,000" and say.plain(Range(Decimal(5), None)) == "at least 5"


def test_confidence_is_a_label_and_never_a_number_for_ambiguous_values() -> None:
    assert say.level(1.0, False, False)[0] == "High" and say.level(0.85, False, False)[0] == "Medium"
    assert say.level(0.6, False, False)[0] == "Low"
    assert say.level(1.0, True, False)[0] == "Ambiguous" and say.level(1.0, True, True)[0] == "Chosen by you"


# ---------------------------------------------------------------- read, highlight, cards

def test_message_is_highlighted_with_a_plain_reading_next_to_each_value() -> None:
    reading = read(PAYMENT, NOW)
    html = highlighted(reading)
    assert html.count("<mark") == 2
    assert "dhai lakh rupaye<span class=\"k-eq\"> = ₹2,50,000</span>" in html
    assert "kal 5 baje<span class=\"k-eq\"> = tomorrow, Fri 13 Nov 2026, 5:00 AM or 5:00 PM</span>" in html
    assert "k-amb" in html and "Ramesh ko " in html and html.rstrip().endswith("bhej dena</div>")


def test_cards_use_plain_words_and_hide_raw_fields_behind_details() -> None:
    html = cards(read(PAYMENT, NOW))
    shown = visible(html)
    assert "Date and time" in shown and "Amount" in shown and "Ambiguous" in shown and "High" in shown
    assert not INTERNAL.search(shown), INTERNAL.search(shown)
    assert "1.00" not in shown and "1.0" not in shown
    assert html.count("<details") == 2 and "not shown: the value is ambiguous" in html
    assert "Exact value for software" in html


def test_ambiguity_is_a_question_and_choosing_updates_everything() -> None:
    reading = read(PAYMENT, NOW)
    item = reading.questions[0]
    assert item.question == "‘kal 5 baje’: did you mean 5:00 AM or 5:00 PM?"
    assert item.labels() == ["tomorrow, Fri 13 Nov 2026, 5:00 AM", "tomorrow, Fri 13 Nov 2026, 5:00 PM"]
    assert "could be AM or PM" in item.reason()
    assert not item.decided and reading.undecided == [item]
    chosen = read(PAYMENT, NOW, {0: 1})
    assert chosen.items[0].decided and chosen.items[0].reading == "tomorrow, Fri 13 Nov 2026, 5:00 PM"
    assert "Chosen by you" in cards(chosen) and "k-chosen" in highlighted(chosen)
    assert json.loads(as_json(chosen))[0]["chosen_by_user"] == "2026-11-13T17:00"
    assert read(PAYMENT, NOW, {0: 9}).items[0].chosen is None, "an out-of-range choice is ignored"


def test_yesterday_or_tomorrow_question_when_no_tense() -> None:
    item = read("kal subah 7 baje dawai", NOW).questions[0]
    assert item.question == "‘kal subah 7 baje’: did you mean yesterday or tomorrow?"
    assert item.reading == "yesterday or tomorrow, at 7:00 AM"
    four = read("kal 5 baje", NOW).questions[0]
    assert len(four.options) == 4 and four.question.endswith("which one did you mean?")
    assert four.reading.count(" or ") == 3


def test_every_parse_has_a_why_in_english_and_hindi_with_the_policy_row() -> None:
    reading = read(PAYMENT, NOW)
    money = reading.items[1].why
    assert [w.en for w in money] == ["‘dhai’ means 2½.", "‘lakh’ is 1,00,000.",
                                     "A rupee word or sign makes this an amount in rupees."]
    when = reading.items[0].why
    assert any(w.policy_key == "time.bare_hour" and w.contested() == "Q3" and w.is_ambiguity for w in when)
    assert any(w.policy_key == "cue.weak_imperative" and w.contested() == "Q4" for w in when)
    html = cards(reading)
    assert "Contested rule <code>time.bare_hour</code> (open question Q3" in html and "Why?" in html
    hindi = cards(reading, "hi")
    assert "क्यों?" in hindi and "का मतलब 2½ है" in hindi and "Kitna अंदाज़ा नहीं लगाता" in hindi


def test_context_resolver_is_explained() -> None:
    item = read("aaj 2 bje doctor ko call krungi", NOW).items[0]
    assert item.reading == "today, Thu 12 Nov 2026, 2:00 PM" and not item.ambiguous
    w = item.why[-1]
    assert w.en.startswith("It is 10:00 now. 02:00 today has already passed")
    assert w.policy_key == "context.today_future" and w.contested() == "Q13" and "अभी 10:00 बजे हैं" in w.hi
    assert say.level(item.result.confidence, False, False)[0] == "Medium"


def test_every_note_the_parser_can_emit_has_a_translation() -> None:
    texts = [PAYMENT, "kal 5 baje", "kal jaunga", "kal gaya tha", "narso aaunga", "shaam 11 baje", "agle somvaar",
             "20 tareekh", "20 November", "kal chhutti hai", "aaj 2 bje call krungi", "guruvaar", "tees hazzar",
             "lagbhag 50 hazaar", "sawa do baje", "paune teen sau", "saade paanch hazaar"]
    for text in texts:
        for item in read(text, NOW).items:
            assert item.why, text
            for w in item.why:
                assert re.search(r"[\u0900-\u097F]", w.hi), (text, w.en)
                assert w.en[0].isupper() or w.en[0] == "‘", (text, w.en)
    unknown = why.from_note("some brand new note")
    assert unknown.en == "Some brand new note." and unknown.policy_key is None


def test_empty_nothing_found_and_bad_input_states() -> None:
    assert "Type or paste a message" in highlighted(read("", NOW)) and cards(read("", NOW)) == ""
    nothing = highlighted(read("mujhe paani de do", NOW))
    assert "No number, amount, date or time found" in nothing and "Was this right?" in nothing
    assert "&lt;b&gt;" in highlighted(read("<b>dhai lakh</b>", NOW)), "user text is escaped"
    with pytest.raises(InputError, match="longer than"):
        read("x" * (MAX_TEXT + 1), NOW)
    assert parse_base("2026-11-12", "10:00") == NOW and parse_base("2026-11-12", "") == dt.datetime(2026, 11, 12)
    for day, clock, msg in (("", "10:00", "fill in today"), ("12/11/2026", "10:00", "not a date"),
                            ("2026-11-12", "25:00", "not a time"), ("2026-11-12", "ten", "not a time")):
        with pytest.raises(InputError, match=msg):
            parse_base(day, clock)


# ---------------------------------------------------------------- action card

def test_action_is_blocked_until_the_ambiguous_value_is_chosen() -> None:
    reading = read(PAYMENT, NOW)
    act = action.build(reading)
    assert act.tool == "transfer" and act.blocked and act.waiting_for == ["kal 5 baje"]
    assert act.call_text == 'transfer(to="Ramesh", amount=250000, currency="INR", when=<choose above>)'
    html = action.card(act, reading)
    assert "Confirm is locked" in html and "Preview only. Nothing is sent, saved or executed." in html
    assert "keyword rules written for this demo" in html

    chosen = read(PAYMENT, NOW, {0: 1})
    act = action.build(chosen)
    assert not act.blocked and act.sentence == "Send ₹2,50,000 to Ramesh tomorrow at 5:00 PM?"
    assert json.loads(act.call_json) == {"name": "transfer", "arguments": {
        "to": "Ramesh", "amount": 250000, "currency": "INR", "when": "2026-11-13T17:00"}}
    assert "You can confirm" in action.card(act, chosen)
    assert "nothing was sent" in action.CONFIRMED_HTML


def test_gallery_has_eight_synthetic_scenarios_and_each_reads_and_acts() -> None:
    assert len(gallery.EXAMPLES) == 8 and len({label for label, _ in gallery.EXAMPLES}) == 8
    expected = {"Payment request": "transfer", "Collections call": "record_promise_to_pay",
                "Reminder": "set_reminder", "Train booking": "book_ticket", "COD order": "place_order",
                "Salary": "record_income", "How long": "schedule_meeting", "देवनागरी": "transfer"}
    for label, text in gallery.EXAMPLES:
        reading = read(text, parse_base(*gallery.NOW))
        assert reading.items, label
        assert action.build(reading).tool == expected[label], label
        assert not re.search(r"\d{10}|@|\+91", text), "no phone numbers or addresses in examples"
    sentences = {label: action.build(read(text, NOW)).sentence for label, text in gallery.EXAMPLES}
    assert sentences["Reminder"] == "Set a reminder today at 2:00 PM?"
    assert sentences["Collections call"] == "Record a payment of ₹3,500 due by day after tomorrow?"
    assert sentences["Train booking"] == "Book 2 train tickets tomorrow?"
    assert sentences["COD order"] == "Place the order for ₹1,750, cash on delivery?"
    assert sentences["Salary"] == "Save income as ₹1,50,000 per month?"
    assert sentences["How long"] == "Block a meeting of 2 hours 30 minutes?"
    assert sentences["देवनागरी"] == "Send ₹2,500 to सुरेश tomorrow at 5:30 PM?"


def test_no_action_and_recipient_rules() -> None:
    reading = read("dhai lakh", NOW)
    assert action.build(reading).tool is None and "No action matched" in action.card(action.build(reading), reading)
    assert action.card(action.build(read("", NOW)), read("", NOW)) == ""
    assert action.build(read("mujhe kal ko 500 rupaye bhej do", NOW)).arguments.get("to") is None
    assert action.build(read("Sunita ko 500 rupaye", NOW)).tool == "transfer"
    assert action.build(read("das minute ruko", NOW)).tool == "set_timer"


# ---------------------------------------------------------------- live comparison

def test_comparison_reports_missing_libraries_and_never_hardcodes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(compare, "_version", lambda dist: None)
    outcomes = compare.run_all(PAYMENT, NOW)
    assert [o.library for o in outcomes] == ["kitna", "number-parser", "dateparser"]
    assert outcomes[1].version is None and outcomes[1].rows == [] and outcomes[2].rows == []
    html = compare.table(outcomes, PAYMENT)
    assert html.count("not installed") >= 2 and 'pip install "kitna[compare]"' in html.replace("&quot;", '"')
    assert "Live comparison" in html and "not a measurement" in html
    assert "Type a message" in compare.table([], "  ")
    source = (ROOT / "demo" / "kitna_demo" / "compare.py").read_text(encoding="utf-8")
    assert not re.search(r"\d+ of \d+|\d+\s*%", source), "no pre-computed scores in the comparison module"


def test_comparison_runs_the_real_libraries_when_installed() -> None:
    pytest.importorskip("number_parser")
    pytest.importorskip("dateparser")
    kitna_row, numbers, dates = compare.run_all("paanch hazaar", NOW)
    assert kitna_row.version == kitna.__version__ and "5000" in kitna_row.rows[0][1]
    assert numbers.version and len(numbers.rows) == 4 and all("language=" in call for call, _ in numbers.rows)
    assert dates.version and len(dates.rows) == 2 and "RELATIVE_BASE" in dates.rows[0][0]
    html = compare.table([kitna_row, numbers, dates], "paanch hazaar")
    assert f"version {numbers.version}" in html and f"version {dates.version}" in html


# ---------------------------------------------------------------- feedback

def test_feedback_is_a_json_line_a_download_and_a_prefilled_issue() -> None:
    rec = feedback.record(PAYMENT, NOW, "wrong", " kal means yesterday here ", ["'kal 5 baje' -> x"])
    assert rec["provenance"] == "user_feedback_unverified" and rec["expected"] == "kal means yesterday here"
    html, line = feedback.panel(rec)
    assert json.loads(line) == rec and "Nothing has been sent or saved" in html
    url = urlparse(feedback.issue_url(rec))
    q = parse_qs(url.query)
    assert url.netloc == "github.com" and url.path == "/Saparajeeta/Kitna/issues/new"
    assert q["template"] == ["wrong_parse.yml"] and q["text"] == [PAYMENT]
    assert q["expected"] == ["kal means yesterday here"] and q["version"] == [kitna.__version__]
    template = (ROOT / ".github" / "ISSUE_TEMPLATE" / "wrong_parse.yml").read_text(encoding="utf-8")
    for field in ("text", "call", "got", "expected", "version"):
        assert f"id: {field}" in template, "the link must use the issue form's field ids"
    data = re.search(r'download="kitna_feedback.jsonl" href="(data:[^"]+)"', html)
    assert data and json.loads(unquote(data.group(1).split(",", 1)[1])) == rec
    assert "this was right" in feedback.panel(feedback.record(PAYMENT, NOW, "right", "", []))[0]


# ---------------------------------------------------------------- reviewer mode

def test_reviewer_cases_come_from_the_review_sheet_with_undecided_rules_first() -> None:
    header, rows = review.load()
    source = ROOT / "docs" / "review" / "phase1_cases_review.csv"
    assert review.cases_path() == source
    with source.open(encoding="utf-8-sig", newline="") as fh:
        original = list(csv.DictReader(fh))
    assert list(header) == list(original[0].keys()) and len(rows) == len(original)
    flagged = ["review" in r["tags"].split() for r in rows]
    n = sum(flagged)
    assert n > 0 and all(flagged[:n]) and not any(flagged[n:])
    golden = [json.loads(x) for x in (ROOT / "tests" / "golden" / "draft_cases.jsonl").read_text("utf-8").splitlines()]
    assert {r["id"] for r in rows} == {c["id"] for c in golden}, "the sheet and the case file must stay in step"


def test_review_card_is_plain_and_complete() -> None:
    _, rows = review.load()
    for row in rows:
        answer = review.draft_answer(row)
        assert answer and "could not be read" not in answer, row["id"]
    by_id = {r["id"]: r for r in rows}
    html = review.card(by_id["DAT-001"], 0, len(rows))
    assert "Imagine today is <strong>Thursday 12 November 2026</strong>" in html and "today, Thu 12 Nov 2026" in html
    assert "Case 1 of 362" in html and "Someone types:" in html
    shown = visible(html)
    assert not INTERNAL.search(shown), INTERNAL.search(shown)
    assert "last one" in review.card(None, 5, 5) and "not found" in review.card(None, 0, 0)
    assert "You already answered" in review.card(by_id["DAT-001"], 0, 5, {"verdict": "ok"})
    bar = review.progress(3, 12)
    assert 'aria-valuenow="3"' in bar and "width:25%" in bar and "3 of 12 checked" in bar


def test_review_export_is_the_same_sheet_with_three_columns_filled() -> None:
    header, rows = review.load()
    source = (ROOT / "docs" / "review" / "phase1_cases_review.csv").read_bytes().decode("utf-8")
    assert review.export_csv(header, rows, {}) == source, "no answers: byte-for-byte the original sheet"
    answers = {"NUM-002": {"verdict": "wrong", "corrected": " 5,000 ", "comment": 'he said "paanch"'},
               "DAT-001": {"verdict": "ok"}, "NUM-003": {"verdict": "maybe"}}
    text = review.export_csv(header, rows, answers)
    assert text.startswith("\ufeff") and text.count("\r\n") == source.count("\r\n")
    out = {r["id"]: r for r in csv.DictReader(io.StringIO(text.lstrip("\ufeff")))}
    assert out["NUM-002"][review.VERDICT_COLUMN] == "wrong" and out["NUM-002"]["corrected_value"] == "5,000"
    assert out["NUM-002"]["reviewer_comment"] == 'he said "paanch"' and out["DAT-001"][review.VERDICT_COLUMN] == "ok"
    assert out["NUM-003"][review.VERDICT_COLUMN] == "", "an unknown verdict is not written"
    assert list(out) == [r["id"] for r in csv.DictReader(io.StringIO(source.lstrip("\ufeff")))], "original order"
    link = review.download_link(text, 2)
    assert 'download="kitna_review.csv"' in link and "nothing was uploaded" in link
    assert unquote(link.split('href="data:text/csv;charset=utf-8,')[1].split('"')[0]) == text


# ---------------------------------------------------------------- voice (stretch, off by default)

def test_voice_is_off_by_default_and_never_claims_accuracy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KITNA_VOICE", raising=False)
    assert not voice.enabled()
    monkeypatch.setenv("KITNA_VOICE", "1")
    assert voice.enabled()
    assert "can be wrong" in voice.NOTICE and "No speech accuracy has been measured" in voice.NOTICE
    assert voice.transcribe("clip.wav", engine=lambda path: "  kal 5 baje  ") == "kal 5 baje"
    with pytest.raises(ValueError, match="Record or upload"):
        voice.transcribe(None)
    if not voice.installed():
        with pytest.raises(RuntimeError, match=r"kitna\[voice\]"):
            voice.transcribe("clip.wav")


def test_story_line_and_honesty_banner() -> None:
    assert STORY.startswith("Indian agents can misread ‘dhai lakh’, ‘parso’, ‘saade teen baje’.")
    assert STORY.endswith("Kitna reads them exactly, or tells you it’s unsure.")
    assert "Pre-alpha" in NOTICE and "No accuracy has been measured" in NOTICE and "native Hindi speakers" in NOTICE
    # the three phrases in the story line do what the line says (self-consistency, not accuracy)
    assert kitna.parse("dhai lakh")[0].canonical == "250000"
    assert kitna.parse("parso", relative_base=NOW)[0].ambiguous
    assert kitna.parse("saade teen baje")[0].canonical == "03:30 | 15:30"
