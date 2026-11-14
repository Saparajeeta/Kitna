"""The Gradio wiring in demo/app.py (needs the `demo` extra)."""
from __future__ import annotations

import pytest

pytest.importorskip("gradio")

import app  # noqa: E402  (demo/ is on the test path)
from kitna_demo.read import MAX_CHOICES  # noqa: E402

DAY, CLOCK = "2026-11-12", "10:00"
PAYMENT = "Ramesh ko kal 5 baje dhai lakh rupaye bhej dena"


def test_run_shows_one_question_and_locks_confirm() -> None:
    out = app.run(PAYMENT, DAY, CLOCK, "English")
    radios, rest = out[:MAX_CHOICES], out[MAX_CHOICES:]
    assert len(rest) == app.N_OUT
    assert radios[0]["visible"] and radios[0]["value"] is None and len(radios[0]["choices"]) == 2
    assert radios[0]["label"].endswith("did you mean 5:00 AM or 5:00 PM?") and "AM or PM" in radios[0]["info"]
    assert all(not r["visible"] for r in radios[1:])
    message, cards, card, confirm, call, raw, note = rest
    assert "<mark" in message and "Ambiguous" in cards and "Confirm is locked" in card
    assert confirm["interactive"] is False and "when=<choose above>" in call and '"schema_version": "1"' in raw
    assert note == ""


def test_choosing_unlocks_confirm_and_hindi_toggle_keeps_the_choice() -> None:
    message, cards, card, confirm, call, _, _ = app.show(PAYMENT, DAY, CLOCK, "English", 1, None, None, None)
    assert confirm["interactive"] is True and 'when="2026-11-13T17:00"' in call
    assert "Send ₹2,50,000 to Ramesh tomorrow at 5:00 PM?" in card and "Chosen by you" in cards
    hindi = app.show(PAYMENT, DAY, CLOCK, "हिन्दी", 1, None, None, None)
    assert "क्यों?" in hindi[1] and hindi[3]["interactive"] is True


def test_empty_error_and_no_action_states() -> None:
    empty = app.run("", DAY, CLOCK, "English")[MAX_CHOICES:]
    assert "Type or paste a message" in empty[0] and empty[3]["interactive"] is False
    bad = app.run("kal", "12-11-2026", CLOCK, "English")[MAX_CHOICES:]
    assert 'role="alert"' in bad[0] and "not a date" in bad[0]
    plain = app.show("dhai lakh", DAY, CLOCK, "English")
    assert "No action matched" in plain[2] and plain[3]["interactive"] is False


def test_feedback_needs_a_verdict_and_a_correction() -> None:
    assert "Read a message first" in app.give_feedback("", DAY, CLOCK, None, "")[0]
    assert "Choose" in app.give_feedback(PAYMENT, DAY, CLOCK, None, "")[0]
    wrong = "👎 No, something is wrong"
    assert "type what the correct value is" in app.give_feedback(PAYMENT, DAY, CLOCK, wrong, " ")[0]
    html, box = app.give_feedback(PAYMENT, DAY, CLOCK, "👎 No, something is wrong", "kal = yesterday")
    assert "github.com/Saparajeeta/Kitna/issues/new" in html and box["visible"] and '"verdict": "wrong"' in box["value"]
    html, box = app.give_feedback(PAYMENT, DAY, CLOCK, "👍 Yes, all correct", "")
    assert '"verdict": "right"' in box["value"]


def test_shared_link_prefills_text_and_now() -> None:
    class Req:
        query_params = {"text": "dhai lakh", "d": "2026-01-02", "t": "09:30"}

    assert app.prefill("2026-11-12", "10:00", Req()) == ("dhai lakh", "2026-01-02", "09:30")  # type: ignore[arg-type]
    Req.query_params = {}
    assert app.prefill("2026-11-12", "10:00", Req()) == ("", "2026-11-12", "10:00")  # type: ignore[arg-type]


def test_compare_handler_and_transcribe_handler() -> None:
    assert "not a date" in app.run_compare("kal", "x", CLOCK)
    assert "Type a message" in app.run_compare("", DAY, CLOCK)
    assert "Live comparison" in app.run_compare("paanch hazaar", DAY, CLOCK)
    text, err = app.do_transcribe(None)
    assert text == "" and "Record or upload" in err


def test_reviewer_flow_records_answers_moves_and_exports() -> None:
    progress, card, fix, comment = app.review_view(None)
    assert "0 of 362 checked" in progress and "Case 1 of 362" in card and (fix, comment) == ("", "")
    state, progress, card, *_ = app.review_answer("wrong", None, " 4,000 ", "")
    first = next(iter(state["answers"]))
    assert state["pos"] == 1 and state["answers"][first] == {"verdict": "wrong", "corrected": "4,000", "comment": ""}
    assert "1 of 362 checked" in progress and "Case 2 of 362" in card
    back, _, card, fix, _ = app.review_move(-1, state)
    assert back["pos"] == 0 and "You already answered" in card and fix == "4,000"
    assert app.review_move(-5, state)[0]["pos"] == 0 and app.review_move(999, state)[0]["pos"] == 362
    assert "last one" in app.review_view({"pos": 362, "answers": {}})[1]
    assert "No answers yet" in app.review_export(None)
    link = app.review_export(state)
    assert 'download="kitna_review.csv"' in link and "1 answers inside" in link


def test_page_builds_with_story_banner_two_pages_and_private_launch_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    assert "Indian agents can misread" in app.HEADER and "Pre-alpha" in app.HEADER
    assert "Not measured: accuracy" in app.ABOUT and "no model has" in app.ABOUT
    demo = app.build_ui()
    config = demo.get_config_file()
    assert config["analytics_enabled"] is False
    assert [p[0] for p in config["pages"]] == ["", "review"]
    for var in ("HOST", "GRADIO_SERVER_NAME", "PORT"):
        monkeypatch.delenv(var, raising=False)
    options = app.launch_options()
    assert options["server_name"] == "127.0.0.1" and options["server_port"] == 7860 and options["ssr_mode"] is False
    assert "fonts.googleapis" not in str(options["theme"].to_dict()), "no third-party font requests"
    monkeypatch.setenv("KITNA_VOICE", "1")
    assert app.build_ui() is not None, "the page also builds with the voice tab switched on"
