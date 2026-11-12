#!/usr/bin/env python3
"""Phase-1 gap check: run number-parser and dateparser on Kitna's draft cases.

Dev-only script (needs `pip install number-parser dateparser`). It is NOT a
general quality comparison: the cases were written to target Hinglish
phenomena, and they are still unreviewed drafts. It answers one question:
"do the existing libraries already cover this input space?"

Usage: python scripts/probe_baselines.py --out results/phase1
"""
from __future__ import annotations

import argparse
import json
import platform
import warnings
from collections import defaultdict
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "tests" / "golden" / "draft_cases.jsonl"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "phase1")
    a = ap.parse_args()

    import dateparser
    from number_parser import parse_number

    warnings.simplefilter("ignore")
    cases = [json.loads(x) for x in CASES.read_text(encoding="utf-8").splitlines() if x.strip()]
    rows = []
    for c in cases:
        e, kind = c["expect"], c["kind"]
        # out of scope for this probe: negatives, multi-result cases, ranges, caller options
        if e.get("none") or "results" in e or "prefer" in c:
            continue
        if isinstance(e["value"], dict) or any(isinstance(x, dict) for x in e.get("candidates", [])):
            continue
        row = {"id": c["id"], "text": c["text"], "script": c["script"], "kind": kind}
        if kind == "number" and isinstance(e["value"], int):
            # exact integers only: number-parser returns int | None
            for lang in ("hi", "en"):
                try:
                    got = parse_number(c["text"], language=lang)
                except Exception as ex:  # noqa: BLE001 - record, don't hide
                    got = f"EXC {type(ex).__name__}"
                row[f"got_{lang}"] = got
            row.update(tool="number-parser", expected=e["value"],
                       outcome="correct" if e["value"] in (row["got_hi"], row["got_en"]) else
                       "no_parse" if row["got_hi"] is None and row["got_en"] is None else "wrong")
        elif kind in ("date", "time", "datetime"):
            rb = c.get("relative_base", "2026-11-12")
            base = datetime.fromisoformat(rb if "T" in rb else rb + "T10:00")
            try:
                dt = dateparser.parse(c["text"], languages=["hi", "en"],
                                      settings={"RELATIVE_BASE": base, "DATE_ORDER": "DMY"})
            except Exception as ex:  # noqa: BLE001
                dt = None
                row["exception"] = type(ex).__name__
            fmt = {"date": "%Y-%m-%d", "time": "%H:%M", "datetime": "%Y-%m-%dT%H:%M"}[kind]
            got = None if dt is None else dt.strftime(fmt)
            row.update(tool="dateparser", got=got)
            if e.get("ambiguous"):
                row["expected"] = e["candidates"]
                # a single silent answer is the behaviour Kitna is designed to avoid
                row["outcome"] = "no_parse" if got is None else (
                    "silent_pick_of_candidate" if got in e["candidates"] else "wrong")
            else:
                row["expected"] = e["value"]
                row["outcome"] = "no_parse" if got is None else "correct" if got == e["value"] else "wrong"
        else:
            continue
        rows.append(row)

    summary: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for r in rows:
        for key in ("all", r["script"]):
            summary[r["tool"]][key][r["outcome"]] += 1
            summary[r["tool"]][key]["n"] += 1
    meta = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "python": platform.python_version(),
        "number_parser": version("number-parser"),
        "dateparser": version("dateparser"),
        "cases_file": str(CASES.relative_to(ROOT)),
        "cases_total": len(cases),
        "cases_status": "draft, not yet reviewed by native speakers",
        "scope": {
            "number-parser": "kind=number cases whose expected value is one exact integer (no ranges); "
                             "counted correct if language='hi' OR language='en' returns it",
            "dateparser": "kind=date, time and datetime cases with a single-value expectation; "
                          "languages=['hi','en'], DATE_ORDER=DMY, "
                          "RELATIVE_BASE=<case base> 10:00",
        },
        "summary": summary,
    }
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "baseline_probe_summary.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with (a.out / "baseline_probe_rows.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
