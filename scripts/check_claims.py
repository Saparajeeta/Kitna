#!/usr/bin/env python3
"""No claim without a results file.

1. docs/claims_checklist.md: every row of the "Claims made" table must hold: the quoted
   text really appears in the file that states it, the evidence file exists, the evidence
   file contains the stated token, and the stating file links to the evidence file.
2. drafts/ and hf/: numbers may appear only inside [bracketed placeholders], code, quoted
   example utterances, HTML comments or a short allow-list of design facts (licence names, the target size...).
   A filled-in number must come with a row in the checklist.

Exit status 0 when clean. Run: python scripts/check_claims.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECKLIST = ROOT / "docs" / "claims_checklist.md"
DRAFT_FILES = ["drafts/linkedin_post.md", "drafts/demo_script.md", "drafts/devto_writeup.md",
               "drafts/resume_bullets.md", "hf/README.md"]
# Design facts that are not measurements. Anything else with a digit needs a placeholder or a checklist row.
ALLOWED = [
    r"CC BY 4\.0", r"cc-by-4\.0", r"Apache-2\.0", r"n<1K", r"150-200", r"40-scenario", r"Domains: 5",
    r"Thursday 12 November 2026, 10:00 IST", r"November 2026", r"ISO 8601", r"w01", r"w\.\.",
]


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _unquote(cell: str) -> str:
    return cell.strip().strip("`")


def check_checklist() -> list[str]:
    problems: list[str] = []
    text = CHECKLIST.read_text(encoding="utf-8")
    section = text.split("## Claims made", 1)[1].split("\n## ", 1)[0]
    rows = [_cells(ln) for ln in section.splitlines() if ln.startswith("|") and not ln.startswith("|---")][1:]
    if not rows:
        return ["claims checklist: the 'Claims made' table is empty"]
    for row in rows:
        if len(row) != 5:
            problems.append(f"claims checklist: row needs 5 cells: {row}")
            continue
        cid, quote, stated, evidence, token = (_unquote(c) for c in row)
        for name in [s.strip().strip("`") for s in stated.split(",")]:
            path = ROOT / name
            if not path.exists():
                problems.append(f"{cid}: stating file {name} does not exist")
                continue
            body = path.read_text(encoding="utf-8")
            if quote not in body:
                problems.append(f"{cid}: {name} no longer contains the claim text {quote!r}")
            if evidence not in body:
                problems.append(f"{cid}: {name} does not link to {evidence}")
        ev = ROOT / evidence
        if not ev.exists():
            problems.append(f"{cid}: evidence file {evidence} does not exist")
        elif token not in ev.read_text(encoding="utf-8"):
            problems.append(f"{cid}: {evidence} does not contain {token!r}; the claim is no longer backed")
    return problems


def bare_numbers(text: str) -> list[tuple[int, str]]:
    """(line number, line) for every line with a digit outside placeholders, code, comments, front matter."""
    text = re.sub(r"\A---\n.*?\n---\n", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    text = re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    text = re.sub(r"```.*?```", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        stripped = re.sub(r"^\s*\d+\.\s", "", line)          # ordered-list markers
        stripped = re.sub(r"`[^`]*`", "", stripped)
        stripped = re.sub(r'"[^"]*"', "", stripped)             # quoted example utterances
        stripped = re.sub(r"\[[^\]]*\]", "", stripped)
        stripped = re.sub(r"https?://\S+", "", stripped)
        for pat in ALLOWED:
            stripped = re.sub(pat, "", stripped)
        if re.search(r"\d", stripped):
            out.append((n, line.strip()))
    return out


def check_drafts() -> list[str]:
    problems = []
    for name in DRAFT_FILES:
        path = ROOT / name
        if not path.exists():
            problems.append(f"{name} is missing")
            continue
        for n, line in bare_numbers(path.read_text(encoding="utf-8")):
            problems.append(f"{name}:{n}: a number outside a [placeholder]: {line[:90]!r}. Put it in brackets, "
                            "or back it with a results file and a checklist row and add it to ALLOWED.")
    return problems


def main() -> int:
    problems = check_checklist() + check_drafts()
    for p in problems:
        print(f"PROBLEM {p}")
    print("claims check: " + ("FAILED" if problems else "ok"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
