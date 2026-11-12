"""Run the parser against the golden cases (still drafts; see docs/review/)."""
from __future__ import annotations

from typing import Any

import pytest
from conftest import load_cases, to_golden

import kitna

IMPLEMENTED = {"number", "digits", "money"}
CASES = load_cases()


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_golden(case: dict[str, Any]) -> None:
    if case["kind"] not in IMPLEMENTED:
        pytest.skip(f"kind {case['kind']!r} not implemented yet")
    results = kitna.parse(case["text"], kind=case["kind"])
    e = case["expect"]
    if e.get("none"):
        assert results == []
        return
    assert len(results) == 1, [r.canonical for r in results]
    r = results[0]
    assert to_golden(r.value) == e["value"]
    assert r.approximate == e.get("approximate", False)
    assert r.confidence <= e.get("max_confidence", 1.0)
    assert 0.0 < r.confidence <= 1.0
    assert case["text"][r.span[0]:r.span[1]] == r.text
