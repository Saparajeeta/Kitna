"""Run the parser against the golden cases.

The cases are the author's own drafts. Passing them shows the parser does what
the draft says, not that it is accurate; see docs/heldout_protocol.md.
"""
from __future__ import annotations

from typing import Any

import pytest
from conftest import check_case, load_cases

CASES = load_cases()


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_golden(case: dict[str, Any]) -> None:
    assert check_case(case) is None
