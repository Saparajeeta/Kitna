"""End to end, offline: a (mock) model makes a tool call, Kitna checks its numbers and dates.

Run:  python examples/tool_call_guard.py

The "model" below is a stand-in that returns fixed tool calls containing mistakes written by hand
for this example: a dropped zero, a silent AM pick, a lost half hour. They are illustrations of the kinds
of error the helper is built to catch. They are NOT outputs of any real model and say nothing about
how often real models make such mistakes.
"""
from __future__ import annotations

import datetime as dt
import json
from typing import Any

import kitna

NOW = dt.datetime(2026, 11, 12, 10, 0)  # Thursday; the user's "now"

TOOLS = [{
    "type": "function",
    "function": {
        "name": "transfer_money",
        "parameters": {"type": "object", "properties": {
            "to": {"type": "string"},
            "amount": {"type": "number", "x-kitna-kind": "money"},
            "when": {"type": "string", "format": "date-time"}}},
    },
}, {
    "type": "function",
    "function": {
        "name": "block_calendar",
        "parameters": {"type": "object", "properties": {"duration": {"type": "string", "format": "duration"}}},
    },
}]

#: what the stand-in model "answers" for each message (OpenAI chat-completions tool-call layout)
SCRIPTED = {
    "Ramesh ko dhai lakh rupaye bhej do": (
        "transfer_money", {"to": "Ramesh", "amount": 25000}),                       # a zero was dropped
    "Ramesh ko kal 5 baje dhai lakh rupaye bhej dena": (
        "transfer_money", {"to": "Ramesh", "amount": 250000, "when": "2026-11-13T05:00:00"}),  # AM chosen silently
    "meeting dhai ghante ki rakh do": (
        "block_calendar", {"duration": "PT2H"}),                                    # the half hour was lost
}


def mock_model(message: str) -> dict[str, Any]:
    """Stands in for a chat-completion call. Returns one tool call in the OpenAI layout."""
    name, arguments = SCRIPTED[message]
    return {"id": "call_0", "type": "function",
            "function": {"name": name, "arguments": json.dumps(arguments, ensure_ascii=False)}}


def schema_for(name: str) -> dict[str, Any]:
    return next(t for t in TOOLS if t["function"]["name"] == name)


def main() -> list[kitna.ToolCallReview]:
    reviews = []
    for message in SCRIPTED:
        call = mock_model(message)
        review = kitna.postprocess_tool_call(call, message, schema=schema_for(call["function"]["name"]),
                                             relative_base=NOW)
        reviews.append(review)
        print(f"\nUser:        {message}")
        print(f"Model call:  {call['function']['name']}({call['function']['arguments']})")
        for arg in review.reviews:
            if arg.status != "skipped":
                print(f"  {arg.name:12} {arg.status:10} {arg.reason}")
        if review.needs_confirmation:
            print("Decision:    ASK THE USER before running this call")
        else:
            print(f"Decision:    run {review.name}({json.dumps(review.arguments, ensure_ascii=False)})")
    return reviews


if __name__ == "__main__":
    main()
