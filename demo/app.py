"""Gradio demo for the Kitna parser: the result, its confidence, and every candidate.

Run locally:   pip install -e ".[demo]" && python demo/app.py
The parsing logic is in `explain()`, which has no Gradio dependency and is unit-tested.
"""
from __future__ import annotations

import datetime as dt
import os
from typing import Any

import kitna

NOTICE = (
    "**Pre-alpha.** Rules and spellings were drafted by an AI and have not been reviewed by a native "
    "speaker. There is no accuracy figure yet. Confidence is an ordering, not a probability. "
    "Nothing you type is stored by this demo."
)
EXAMPLES = [
    ["Ramesh ko kal shaam 6 baje dhai lakh rupaye bhejna hai", "2026-11-12", "10:00", "any"],
    ["kal 5 baje", "2026-11-12", "10:00", "any"],
    ["paune do lakh", "2026-11-12", "10:00", "any"],
    ["कल सुबह साढ़े सात बजे", "2026-11-12", "10:00", "any"],
    ["do se teen hazaar rupaye", "2026-11-12", "10:00", "any"],
    ["mujhe paani de do", "2026-11-12", "10:00", "any"],
]
HEADERS = ["text found", "kind", "value", "confidence", "ambiguous", "every candidate", "approximate", "notes"]


def explain(text: str, base_date: str = "", base_time: str = "", kind: str = "any"
            ) -> tuple[list[list[str]], str, list[dict[str, Any]]]:
    """Parse `text`. Returns (table rows, a status line in Markdown, the JSON form of every result)."""
    text = (text or "").strip()
    if not text:
        return [], "Type something above.", []
    base: dt.datetime | None = None
    if (base_date or "").strip():
        try:
            base = dt.datetime.fromisoformat(f"{base_date.strip()}T{(base_time or '00:00').strip()}")
        except ValueError:
            return [], "The date must look like 2026-11-12 and the time like 10:00.", []
    try:
        results = kitna.parse(text[:500], kind=None if kind in ("", "any") else kind, relative_base=base)
    except kitna.KitnaError as exc:
        return [], f"Could not parse: {exc}", []
    rows = []
    for r in results:
        candidates = " | ".join(kitna.canonical(c) for c in r.candidates) if r.ambiguous else ""
        rows.append([r.text, r.kind, "(not decided)" if r.ambiguous else r.canonical, f"{r.confidence:.2f}",
                     "yes" if r.ambiguous else "no", candidates, "yes" if r.approximate else "no",
                     "; ".join((*r.notes, *r.warnings))])
    if not results:
        status = "Nothing found: no number, amount, time or date was recognised."
    else:
        n_amb = sum(r.ambiguous for r in results)
        status = f"{len(results)} value(s) found" + (
            f", {n_amb} ambiguous: every candidate is listed, none was picked." if n_amb else ".")
        if base is None and any(r.warnings for r in results):
            status += " No 'today' was given, so the server's clock was used."
    return rows, status, [r.to_dict() for r in results]


def build_ui() -> Any:
    import gradio as gr

    with gr.Blocks(title="Kitna: Hinglish quantities, money, times, dates") as ui:
        gr.Markdown("# Kitna\nHinglish and Devanagari quantities, money, times and dates to exact values.\n\n"
                    + NOTICE)
        with gr.Row():
            text = gr.Textbox(label="Text (Hinglish, Devanagari or mixed)", lines=2, scale=3,
                              placeholder="kal subah saade saat baje 2.5 lakh rupaye bhej dunga")
            kind = gr.Dropdown(["any", *kitna.KINDS], value="any", label="Look only for", scale=1)
        with gr.Row():
            date = gr.Textbox(label="Today (YYYY-MM-DD), for kal / parso / weekdays", value="2026-11-12")
            time = gr.Textbox(label="Time now (HH:MM)", value="10:00")
            go = gr.Button("Parse", variant="primary")
        status = gr.Markdown()
        table = gr.Dataframe(headers=HEADERS, label="Results (one row per value found)", wrap=True)
        with gr.Accordion("JSON output (Result.to_dict(), schema version 1)", open=False):
            raw = gr.JSON()
        gr.Examples(EXAMPLES, inputs=[text, date, time, kind])
        for trigger in (go.click, text.submit):
            trigger(explain, inputs=[text, date, time, kind], outputs=[table, status, raw])
    return ui


if __name__ == "__main__":
    # 127.0.0.1 by default so the printed address opens in a browser on every system.
    # Hosted environments (containers, Spaces) set HOST or GRADIO_SERVER_NAME to 0.0.0.0.
    host = os.environ.get("HOST") or os.environ.get("GRADIO_SERVER_NAME") or "127.0.0.1"
    build_ui().launch(server_name=host, server_port=int(os.environ.get("PORT", "7860")))
