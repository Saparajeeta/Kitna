from __future__ import annotations

import json
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Any

import kitna

ROOT = Path(__file__).resolve().parent.parent
CASES_FILE = ROOT / "tests" / "golden" / "draft_cases.jsonl"


def load_cases() -> list[dict[str, Any]]:
    return [json.loads(x) for x in CASES_FILE.read_text(encoding="utf-8").splitlines() if x.strip()]


def to_golden(v: Any) -> Any:
    """Convert a Result value to the JSON form used in the golden files."""
    if isinstance(v, kitna.Range):
        d: dict[str, Any] = {}
        for k in ("min", "max"):
            x = getattr(v, k)
            if isinstance(x, kitna.Money):
                d[k], d["currency"] = x.amount_str, x.currency
            elif x is not None:
                d[k] = to_golden(x)
        return d
    if isinstance(v, kitna.Money):
        return {"amount": v.amount_str, "currency": v.currency}
    if isinstance(v, (Decimal, kitna.Duration, datetime, date, time)):
        return kitna.canonical(v)
    return v


def run_case(case: dict[str, Any]) -> list[kitna.Result]:
    rb = case.get("relative_base")
    base = None if rb is None else datetime.fromisoformat(rb) if "T" in rb else date.fromisoformat(rb)
    if case.get("hint", True):
        return kitna.parse(case["text"], kind=case["kind"], relative_base=base, prefer=case.get("prefer"))
    # "hint": false -> no kind hint; keep only results of the case's kind
    found = kitna.parse(case["text"], relative_base=base, prefer=case.get("prefer"))
    return [r for r in found if r.kind == case["kind"]]


def check_case(case: dict[str, Any]) -> str | None:
    """Return None if the parser output matches the case, else a description of the mismatch."""
    results = run_case(case)
    e = case["expect"]
    if e.get("none"):
        return None if not results else f"expected nothing, got {[r.canonical for r in results]}"
    blocks = e["results"] if "results" in e else [e]
    if len(results) != len(blocks):
        return f"expected {len(blocks)} result(s), got {[r.canonical for r in results]}"
    for r, b in zip(results, blocks, strict=True):
        if case["text"][r.span[0]:r.span[1]] != r.text:
            return "span does not index the text"
        if b.get("ambiguous"):
            if not r.ambiguous or r.value is not None:
                return f"expected ambiguous, got {r.canonical}"
            if [to_golden(c) for c in r.candidates] != b["candidates"]:
                return f"candidates {[to_golden(c) for c in r.candidates]} != {b['candidates']}"
        elif r.ambiguous or to_golden(r.value) != b["value"]:
            return f"value {r.canonical!r} != {b['value']!r}"
        if r.approximate != b.get("approximate", False):
            return "approximate flag differs"
        if not 0.0 < r.confidence <= b.get("max_confidence", 1.0):
            return f"confidence {r.confidence} above {b.get('max_confidence', 1.0)}"
    return None
