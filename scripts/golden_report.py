#!/usr/bin/env python3
"""Summarise how the parser does on the DRAFT golden cases.

This is a self-consistency check, not an accuracy measurement: the cases were
drafted by the same author as the parser and no native speaker has reviewed
them. Cases tagged ``review`` depend on rules that are still contested
(docs/taxonomy.md section 5) and are reported separately, never in the headline.

Usage: python scripts/golden_report.py --out results/phase2
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))

import conftest  # noqa: E402

import kitna  # noqa: E402
from kitna.policy import policy  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "phase2")
    a = ap.parse_args()
    cases = conftest.load_cases()
    groups: dict[str, Counter[str]] = {"settled": Counter(), "review": Counter()}
    by_kind: dict[str, Counter[str]] = {}
    failures = []
    for c in cases:
        group = "review" if "review" in c["tags"] else "settled"
        problem = conftest.check_case(c)
        outcome = "match" if problem is None else "mismatch"
        groups[group][outcome] += 1
        groups[group]["n"] += 1
        if group == "settled":
            by_kind.setdefault(c["kind"], Counter())[outcome] += 1
            by_kind[c["kind"]]["n"] += 1
        if problem:
            failures.append({"id": c["id"], "text": c["text"], "group": group, "problem": problem})
    report = {
        "what_this_is": "agreement between the parser and its author's own draft expectations; "
                        "NOT an accuracy figure. No native-speaker review has happened and there is "
                        "no held-out set yet (docs/heldout_protocol.md).",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "kitna": kitna.__version__,
        "python": platform.python_version(),
        "policy_version": policy().version,
        "cases_total": len(cases),
        "cases_status": dict(Counter(c["status"] for c in cases)),
        "headline_excludes_review_tagged": True,
        "settled": dict(groups["settled"]),
        "settled_by_kind": {k: dict(v) for k, v in sorted(by_kind.items())},
        "review_tagged_reported_separately": dict(groups["review"]),
        "mismatches": failures,
    }
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "golden_summary.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                                               encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("cases_total", "settled", "review_tagged_reported_separately")}))


if __name__ == "__main__":
    main()
