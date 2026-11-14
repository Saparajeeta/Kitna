"""Kitna demo: read a Hinglish / Hindi message, show what was understood and what was not.

Run locally:  pip install -e ".[demo,compare]"  then  python demo/app.py   (open http://localhost:7860)
The display logic lives in ``kitna_demo`` and is unit-tested; this file only wires the page together.
Nothing typed here is stored by this app: no database, no log of your text, no analytics.
"""
from __future__ import annotations

import os
from typing import Any

import gradio as gr
from kitna_demo import NOTICE, REPO, STORY, action, compare, feedback, gallery, review, voice
from kitna_demo.read import (
    EMPTY_HTML,
    MAX_CHOICES,
    MAX_TEXT,
    InputError,
    Reading,
    as_json,
    cards,
    highlighted,
    parse_base,
    read,
)
from kitna_demo.style import CSS, HEAD, JS_LOCAL_NOW, JS_SHARE, JS_THEME

import kitna

LANGS = {"English": "en", "हिन्दी": "hi"}
N_OUT = 7  # outputs of show(): message, cards, action card, confirm button, call, json, confirm note

HEADER = f"""<div class="k-story">{STORY}</div>
<div class="k-banner" role="note"><strong>Honest status:</strong> {NOTICE}
<a href="{REPO}/blob/main/docs/limitations.md" target="_blank" rel="noopener">What it cannot do</a> ·
<a href="{REPO}/blob/main/docs/claims_checklist.md" target="_blank" rel="noopener">What has been
measured</a>
</div>"""
ABOUT = f"""<div class="k-about">

### What this page shows
Kitna is a small open-source library. It finds numbers, rupee amounts, dates, times and lengths of time in
messages written in Hinglish (Hindi in English letters), Hindi (Devanagari) or English, and returns exact values.
When a phrase has more than one meaning it says so and lists every reading instead of picking one.

### What has been measured, and what has not
- **Not measured: accuracy.** The rules and the test cases were written by the same AI, so their agreement
  proves nothing. A set written by native speakers does not exist yet.
- **Not measured: whether AI agents misread these phrases.** The benchmark for that is built but no model has
  been run. The first line of this page is the reason the project exists, not a result.
- **Measured:** how two general-purpose libraries did on the project's own draft cases
  ([results file]({REPO}/blob/main/results/phase1/baseline_probe_summary.json)). That is not a ranking.
- Everything else: [claims checklist]({REPO}/blob/main/docs/claims_checklist.md).

### What Kitna does not do
It does not understand whole sentences, pick tools, or know who is being paid. English fraction phrases
(“one and a half lakh”), recurring times (“har somvaar”) and several other forms are not read:
[known limits]({REPO}/blob/main/docs/limitations.md).

### Your data
This app has no database and writes no log of what you type. It sets no cookies and loads no fonts or scripts
from other sites. Reviewer mode keeps your answers in your own browser until you download them. Feedback leaves
your device only if you press the GitHub link or send the file yourself. The company hosting the page may keep
ordinary web-server logs.

### Help make it right
Native speakers can check cases in a few minutes: open <a href="review">Reviewer mode</a>.
Source code: [{REPO.split("//")[1]}]({REPO}) · Kitna {kitna.__version__}
</div>"""


def _error(message: str) -> str:
    return f'<div class="k-error" role="alert">{message}</div>'


def _reading(text: str, day: str, clock: str, picks: tuple[int | None, ...]) -> Reading:
    base = parse_base(day, clock)
    first = read(text, base)
    choices = {item.index: pick for item, pick in zip(first.questions, picks, strict=False) if pick is not None}
    return read(text, base, choices) if choices else first


def show(text: str, day: str, clock: str, lang: str, *picks: int | None) -> tuple[Any, ...]:
    """Everything below the input box, for the current text, 'now', language and choices."""
    try:
        reading = _reading(text, day, clock, picks)
    except (InputError, kitna.KitnaError) as ex:
        return (_error(str(ex)), "", "", gr.update(interactive=False), "", "", "")
    if not reading.text:
        return (EMPTY_HTML, "", "", gr.update(interactive=False), "", "", "")
    act = action.build(reading)
    return (highlighted(reading), cards(reading, LANGS.get(lang, "en")), action.card(act, reading),
            gr.update(interactive=bool(act.tool) and not act.blocked), act.call_text, as_json(reading), "")


def run(text: str, day: str, clock: str, lang: str) -> tuple[Any, ...]:
    """A fresh read: reset the questions, then show."""
    radios: list[Any] = [gr.update(visible=False, value=None, choices=[]) for _ in range(MAX_CHOICES)]
    try:
        reading = _reading(text, day, clock, ())
        for slot, item in enumerate(reading.questions):
            radios[slot] = gr.update(visible=True, value=None, choices=item.labels(), label=item.question,
                                     info=item.reason(LANGS.get(lang, "en")))
    except (InputError, kitna.KitnaError):
        pass
    return (*radios, *show(text, day, clock, lang))


def prefill(day: str, clock: str, request: gr.Request) -> tuple[str, str, str]:
    """Text and 'now' from a shared link (?text=...&d=...&t=...); 'now' otherwise comes from the visitor's clock."""
    q = request.query_params if request is not None else {}
    return str(q.get("text", ""))[:MAX_TEXT], str(q.get("d", "") or day), str(q.get("t", "") or clock)


def give_feedback(text: str, day: str, clock: str, verdict: str | None, expected: str) -> tuple[str, Any]:
    if not (text or "").strip():
        return _error("Read a message first, then tell us if it was right."), gr.update(visible=False)
    if verdict is None:
        return _error("Choose 👍 or 👎 first."), gr.update(visible=False)
    wrong = verdict.startswith("👎")
    if wrong and not (expected or "").strip():
        return _error("Please type what the correct value is, so the mistake can be fixed."), gr.update(visible=False)
    try:
        base = parse_base(day, clock)
        got = [f"{r.text!r} -> {r.canonical}" for r in kitna.parse(text, relative_base=base)]
    except (InputError, kitna.KitnaError) as ex:
        return _error(str(ex)), gr.update(visible=False)
    html, line = feedback.panel(feedback.record(text.strip(), base, "wrong" if wrong else "right", expected or "", got))
    return html, gr.update(visible=True, value=line)


def run_compare(text: str, day: str, clock: str) -> str:
    try:
        base = parse_base(day, clock)
    except InputError as ex:
        return _error(str(ex))
    text = (text or "").strip()[:MAX_TEXT]
    return compare.table(compare.run_all(text, base) if text else [], text)


def do_transcribe(path: str | None) -> tuple[str, str]:
    try:
        return voice.transcribe(path), ""
    except Exception as ex:  # noqa: BLE001 - any speech-model failure is shown, not raised
        return "", _error(str(ex))


# ---------------------------------------------------------------- reviewer mode

def _review_state(state: dict[str, Any] | None) -> dict[str, Any]:
    state = dict(state or {})
    state.setdefault("pos", 0)
    state.setdefault("answers", {})
    return state


def review_view(state: dict[str, Any] | None) -> tuple[str, str, str, str]:
    """(progress bar, card, corrected value, comment) for the current position."""
    state = _review_state(state)
    _, rows = review.load()
    pos = max(0, min(int(state["pos"]), len(rows)))
    done = sum(1 for r in rows if (state["answers"].get(r["id"]) or {}).get("verdict"))
    row = rows[pos] if pos < len(rows) else None
    prev = state["answers"].get(row["id"], {}) if row else {}
    return (review.progress(done, len(rows)), review.card(row, pos, len(rows), prev),
            prev.get("corrected", ""), prev.get("comment", ""))


def review_answer(verdict: str, state: dict[str, Any] | None, corrected: str, comment: str) -> tuple[Any, ...]:
    state = _review_state(state)
    _, rows = review.load()
    pos = int(state["pos"])
    if 0 <= pos < len(rows):
        answers = dict(state["answers"])
        answers[rows[pos]["id"]] = {"verdict": verdict, "corrected": (corrected or "").strip(),
                                    "comment": (comment or "").strip()}
        state = {"pos": pos + 1, "answers": answers}
    return (state, *review_view(state))


def review_move(step: int, state: dict[str, Any] | None) -> tuple[Any, ...]:
    state = _review_state(state)
    _, rows = review.load()
    state["pos"] = max(0, min(int(state["pos"]) + step, len(rows)))
    return (state, *review_view(state))


def review_export(state: dict[str, Any] | None) -> str:
    state = _review_state(state)
    header, rows = review.load()
    done = sum(1 for r in rows if (state["answers"].get(r["id"]) or {}).get("verdict"))
    if not done:
        return _error("No answers yet. Tap OK, Wrong or Unnatural on at least one card first.")
    return review.download_link(review.export_csv(header, rows, state["answers"]), done)


# ---------------------------------------------------------------- page

def build_ui() -> gr.Blocks:
    with gr.Blocks(title="Kitna: reads amounts, dates and times in Hinglish", analytics_enabled=False) as demo:
        gr.HTML(HEADER)
        with gr.Tabs():
            with gr.Tab("Read"):
                text = gr.Textbox(
                    label="Your message (Hinglish, Hindi or English)", lines=3, max_length=MAX_TEXT, autofocus=True,
                    placeholder="For example: Ramesh ko kal 5 baje dhai lakh rupaye bhej dena",
                    info="Press Ctrl+Enter (or Shift+Enter) to read it. Nothing you type is stored.", elem_id="k-text")
                with gr.Row():
                    go = gr.Button("Read it", variant="primary", elem_id="k-read-btn", scale=3)
                    clear = gr.Button("Clear", scale=1)
                gr.Markdown("**Or tap an example** (all made up; they use Thursday 12 November 2026, 10:00 as “now”)")
                with gr.Row(elem_classes="k-gallery"):
                    example_buttons = [gr.Button(label, size="sm") for label, _ in gallery.EXAMPLES]
                with gr.Accordion("When is “now”? (used for kal, aaj, parso and bare hours)", open=False):
                    with gr.Row():
                        day = gr.Textbox(label="Today’s date (year-month-day)", placeholder="2026-11-12", max_length=10)
                        clock = gr.Textbox(label="Time now (24-hour)", placeholder="10:00", max_length=5)
                    gr.Markdown("Filled from your device’s clock. Change it to see how the same words read on "
                                "another day.")
                message = gr.HTML(EMPTY_HTML, label="What Kitna found")
                radios = [gr.Radio(choices=[], label="Which did you mean?", visible=False, type="index",
                                   elem_classes="k-choice") for _ in range(MAX_CHOICES)]
                lang = gr.Radio(list(LANGS), value="English", label="Explain in / समझाएँ")
                cards_html = gr.HTML()
                gr.Markdown("### Make it an action")
                action_html = gr.HTML()
                with gr.Row():
                    confirm = gr.Button("Confirm", variant="primary", interactive=False)
                    edit = gr.Button("Edit the call")
                confirm_note = gr.HTML()
                call = gr.Textbox(label="The tool call an agent would send", buttons=["copy"], interactive=False,
                                  lines=2)
                call_edit = gr.Textbox(label="Edit the call (your edits are not checked by Kitna)", visible=False,
                                       lines=3, buttons=["copy"])
                with gr.Accordion("For developers: the full result as JSON", open=False):
                    json_out = gr.Code(language="json", label="kitna.parse(...) output", buttons=["copy"],
                                       interactive=False)
                with gr.Accordion("Share this message as a link", open=False):
                    share = gr.Button("Make a link")
                    share_link = gr.Textbox(label="Link (opens this page with the message filled in; no account)",
                                            buttons=["copy"], interactive=False)
                    gr.Markdown("The message is part of the link itself, so anyone with the link can read it.")
                with gr.Accordion("Was this right? (helps native speakers validate Kitna)", open=False):
                    verdict = gr.Radio(["👍 Yes, all correct", "👎 No, something is wrong"], label="Was this right?")
                    expected = gr.Textbox(label="If it was wrong: what should it be?", lines=2, max_length=500,
                                          placeholder="For example: “kal” here means yesterday; the amount is 2,50,000")
                    send = gr.Button("Prepare my feedback")
                    fb_html = gr.HTML()
                    fb_line = gr.Textbox(label="Your feedback as one JSON line", buttons=["copy"], visible=False,
                                         interactive=False, lines=3)
            with gr.Tab("Compare"):
                gr.Markdown("### Kitna vs others\nRuns the message from the first tab through two general-purpose "
                            "libraries **live** and "
                            "shows exactly what each returned. Nothing here is pre-written.")
                cmp_go = gr.Button("Run the live comparison", variant="primary")
                cmp_html = gr.HTML('<div class="k-empty">Read a message in the first tab, then press the button.</div>')
            if voice.enabled():
                with gr.Tab("Speak"):
                    gr.HTML(f'<div class="k-banner" role="note">{voice.NOTICE}</div>')
                    audio = gr.Audio(sources=["microphone", "upload"], type="filepath", label="Record or upload")
                    transcribe = gr.Button("Write down what was said")
                    voice_err = gr.HTML()
                    transcript = gr.Textbox(label="Transcript (please correct it before reading)", lines=3)
                    use = gr.Button("Read this transcript", variant="primary")
                    transcribe.click(do_transcribe, [audio], [transcript, voice_err], api_visibility="private")
            with gr.Tab("About"):
                gr.Markdown(ABOUT)
        theme = gr.Button("Switch light / dark", size="sm")

        outs = [message, cards_html, action_html, confirm, call, json_out, confirm_note]
        run_in, run_out = [text, day, clock, lang], [*radios, *outs]
        go.click(run, run_in, run_out, api_name="read")
        text.submit(run, run_in, run_out, api_visibility="private")
        for radio in radios:
            radio.input(show, [text, day, clock, lang, *radios], outs, api_visibility="private")
        lang.input(show, [text, day, clock, lang, *radios], outs, api_visibility="private")
        for button, (_, sample) in zip(example_buttons, gallery.EXAMPLES, strict=True):
            button.click(lambda s=sample: (s, *gallery.NOW), None, [text, day, clock], api_visibility="private").then(
                run, run_in, run_out, api_visibility="private")
        clear.click(lambda: ("", *run("", "2026-01-01", "00:00", "English")), None,
                    [text, *radios, *outs], api_visibility="private")
        confirm.click(lambda: action.CONFIRMED_HTML, None, confirm_note, api_visibility="private")
        edit.click(lambda c: gr.update(visible=True, value=c), call, call_edit, api_visibility="private")
        share.click(None, [text, day, clock], share_link, js=JS_SHARE)
        send.click(give_feedback, [text, day, clock, verdict, expected], [fb_html, fb_line], api_visibility="private")
        cmp_go.click(run_compare, [text, day, clock], cmp_html, api_name="compare")
        theme.click(None, None, None, js=JS_THEME)
        if voice.enabled():
            use.click(lambda t: t, transcript, text, api_visibility="private").then(
                run, run_in, run_out, api_visibility="private")
        demo.load(prefill, [day, clock], [text, day, clock], js=JS_LOCAL_NOW, api_visibility="private").then(
            run, run_in, run_out, api_visibility="private")

    with demo.route("Reviewer mode", "/review"):
        gr.HTML("""<div class="k-story">Help check Kitna: is this what the words mean?</div>
<div class="k-banner" role="note">You will see short phrases with the answer Kitna’s draft rules give.
Tap <strong>OK</strong>, <strong>Wrong</strong> or <strong>Unnatural</strong>. There are no trick questions and no
right score: your honest reading is the point. Your answers stay in this browser until you download them.</div>""")
        saved = gr.BrowserState({"pos": 0, "answers": {}}, storage_key="kitna-review-v1", secret="kitna-review-v1")
        r_prog = gr.HTML()
        r_card = gr.HTML()
        with gr.Row(elem_classes="k-verdicts"):
            r_ok = gr.Button("✓ OK", variant="primary")
            r_wrong = gr.Button("✗ Wrong", variant="stop")
            r_odd = gr.Button("Unnatural")
        r_fix = gr.Textbox(label="If wrong: what does it mean? (optional)", max_length=200,
                           placeholder="For example: 3,500 or “day after tomorrow”")
        r_comment = gr.Textbox(label="Comment (optional)", max_length=300)
        with gr.Row():
            r_back = gr.Button("← Back", size="sm")
            r_skip = gr.Button("Skip →", size="sm")
        r_export = gr.Button("Get my CSV")
        r_file = gr.HTML()
        r_theme = gr.Button("Switch light / dark", size="sm")
        view = [r_prog, r_card, r_fix, r_comment]
        for button, name in ((r_ok, "ok"), (r_wrong, "wrong"), (r_odd, "unnatural")):
            button.click(lambda s, c, m, v=name: review_answer(v, s, c, m), [saved, r_fix, r_comment],
                         [saved, *view], api_visibility="private")
        r_back.click(lambda s: review_move(-1, s), saved, [saved, *view], api_visibility="private")
        r_skip.click(lambda s: review_move(1, s), saved, [saved, *view], api_visibility="private")
        r_export.click(review_export, saved, r_file, api_visibility="private")
        r_theme.click(None, None, None, js=JS_THEME)
        demo.load(review_view, saved, view, api_visibility="private")
    built: gr.Blocks = demo
    return built


def launch_options() -> dict[str, Any]:
    # 127.0.0.1 by default so the printed address opens in a browser on every system.
    # Hosted environments (containers, Spaces) set HOST or GRADIO_SERVER_NAME to 0.0.0.0.
    host = os.environ.get("HOST") or os.environ.get("GRADIO_SERVER_NAME") or "127.0.0.1"
    system = ["system-ui", "Noto Sans", "Noto Sans Devanagari", "sans-serif"]
    return dict(server_name=host, server_port=int(os.environ.get("PORT", "7860")), css=CSS, head=HEAD,
                theme=gr.themes.Soft(font=system, font_mono=["ui-monospace", "monospace"]),
                ssr_mode=False, show_error=True)


if __name__ == "__main__":
    build_ui().launch(**launch_options())
