"""'Was this right?': opt-in feedback. Nothing is stored or sent by this app.

The user gets a JSON line to download or copy, and a link that opens a pre-filled GitHub issue.
Clicking the link (and then "Submit" on GitHub) is the only way anything leaves the browser.
"""
from __future__ import annotations

import datetime as dt
import json
from html import escape
from urllib.parse import quote, urlencode

import kitna

ISSUES = "https://github.com/Saparajeeta/Kitna/issues/new"
MAX_URL_FIELD = 1500


def record(text: str, base: dt.datetime, verdict: str, expected: str, got: list[str]) -> dict[str, object]:
    return {
        "text": text, "relative_base": base.strftime("%Y-%m-%dT%H:%M"), "verdict": verdict,
        "expected": expected.strip(), "kitna_returned": got, "kitna_version": kitna.__version__,
        "provenance": "user_feedback_unverified",
    }


def issue_url(rec: dict[str, object]) -> str:
    text = str(rec["text"])[:MAX_URL_FIELD]
    returned = rec["kitna_returned"]
    got = "\n".join(str(g) for g in returned) if isinstance(returned, list) and returned else "(nothing)"
    params = {
        "template": "wrong_parse.yml",
        "title": f"Wrong parse: {text[:60]}",
        "text": text,
        "call": f'kitna parse "..." --base {rec["relative_base"]}',
        "got": got[:MAX_URL_FIELD],
        "expected": str(rec["expected"])[:MAX_URL_FIELD],
        "version": str(rec["kitna_version"]),
    }
    return f"{ISSUES}?{urlencode(params, quote_via=quote)}"


def panel(rec: dict[str, object]) -> tuple[str, str]:
    """(HTML with the download link and the issue link, the JSON line)."""
    line = json.dumps(rec, ensure_ascii=False)
    data_uri = "data:application/json;charset=utf-8," + quote(line + "\n")
    if rec["verdict"] == "right":
        lead = "Thank you. A “this was right” note helps too."
    else:
        lead = "Thank you. Your correction is below."
    html = (f'<div class="k-fb" role="status"><p><strong>{lead}</strong> Nothing has been sent or saved. '
            'Choose how to share it:</p><ul>'
            f'<li><a href="{escape(issue_url(rec))}" target="_blank" rel="noopener">Open a pre-filled GitHub issue</a>'
            ' (you review it and press Submit there; needs a GitHub account)</li>'
            f'<li><a download="kitna_feedback.jsonl" href="{data_uri}">Download as a JSON line</a>'
            ' and send it to the project owner any way you like</li>'
            '<li>or copy the line from the box below</li></ul></div>')
    return html, line
