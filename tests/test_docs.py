"""Docs stay true: quickstart examples run, generated tables are current."""
from __future__ import annotations

import doctest
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_quickstart_examples_run() -> None:
    result = doctest.testfile(str(ROOT / "docs" / "quickstart.md"), module_relative=False,
                              optionflags=doctest.NORMALIZE_WHITESPACE)
    assert result.attempted >= 20 and result.failed == 0


def test_generated_policy_docs_are_current() -> None:
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "gen_policy_docs.py"), "--check"],
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr


def test_every_policy_question_has_a_row_in_the_docs() -> None:
    from kitna.policy import policy

    table = (ROOT / "docs" / "_generated" / "open_questions_table.md").read_text(encoding="utf-8")
    for q in {q for q in policy().questions.values() if q != "-"}:
        assert f"| {q} |" in table
