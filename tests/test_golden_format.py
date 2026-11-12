"""Structural checks on the golden-case files. No parser needed."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("validate_cases", ROOT / "scripts" / "validate_cases.py")
assert _spec and _spec.loader
vc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vc)

CASES = ROOT / "tests" / "golden" / "draft_cases.jsonl"


def test_draft_cases_are_well_formed() -> None:
    assert vc.validate([CASES]) == []


def test_draft_cases_not_marked_validated_without_reviewers() -> None:
    # Phase-1 rule: nothing is "validated" until native-speaker review is recorded.
    review_log = ROOT / "docs" / "review" / "REVIEW_LOG.md"
    if not review_log.exists():
        assert all(c["status"] == "draft" for c in vc.load(CASES))


def test_validator_rejects_silent_pick() -> None:
    bad = {"id": "DAT-999", "text": "kal", "script": "roman", "kind": "date",
           "relative_base": "2026-11-12", "tags": ["ambiguity"], "status": "draft",
           "expect": {"value": "2026-11-13", "ambiguous": True,
                      "candidates": ["2026-11-11", "2026-11-13"]}}
    assert any("never pick silently" in m for m in vc.check_case(bad))
