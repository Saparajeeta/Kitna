#!/usr/bin/env python3
"""Validate the format of parser golden-case files (stdlib only).

Usage: python scripts/validate_cases.py [tests/golden/draft_cases.jsonl ...]
       python scripts/validate_cases.py --export-csv docs/review/phase1_cases_review.csv

Checks structure only. Whether an expected value is *linguistically right* is
the job of the native-speaker review (see docs/review/README.md).
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT = ROOT / "tests" / "golden" / "draft_cases.jsonl"

KINDS = {"number", "digits", "money", "time", "duration", "date"}
SCRIPTS = {"roman", "devanagari", "mixed", "none"}
STATUSES = {"draft", "validated", "rejected"}
REQUIRED = {"id", "text", "script", "kind", "expect", "tags", "status"}
OPTIONAL = {"relative_base", "note"}
EXPECT_KEYS = {"value", "ambiguous", "candidates", "approximate", "max_confidence", "none"}

DECIMAL = re.compile(r"^\d+\.\d+$")
INTSTR = re.compile(r"^\d+$")
AMOUNT = re.compile(r"^\d+(\.\d{2})?$")
HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
ISO_DUR = re.compile(r"^P(?=.)(\d+Y)?(\d+M)?(\d+W)?(\d+D)?(T(?=.)(\d+H)?(\d+M)?(\d+S)?)?$")
ID = re.compile(r"^[A-Z]{3}-\d{3}$")


def _is_date(v: object) -> bool:
    try:
        return isinstance(v, str) and date.fromisoformat(v).isoformat() == v
    except ValueError:
        return False


def _scalar_ok(kind: str, v: object) -> bool:
    """One concrete (non-range) value of the given kind."""
    if kind == "number":
        return (isinstance(v, int) and not isinstance(v, bool)) or (
            isinstance(v, str) and bool(DECIMAL.match(v))
        )
    if kind == "digits":
        return isinstance(v, str) and bool(INTSTR.match(v))
    if kind == "time":
        return isinstance(v, str) and bool(HHMM.match(v))
    if kind == "duration":
        return isinstance(v, str) and bool(ISO_DUR.match(v))
    if kind == "date":
        return _is_date(v)
    return False


def _value_ok(kind: str, v: object) -> bool:
    if kind == "money":
        if not isinstance(v, dict) or v.get("currency") != "INR":
            return False
        keys = set(v) - {"currency"}
        if keys == {"amount"}:
            return isinstance(v["amount"], str) and bool(AMOUNT.match(v["amount"]))
        return bool(keys) and keys <= {"min", "max"} and all(
            isinstance(v[k], str) and AMOUNT.match(v[k]) for k in keys
        )
    if kind == "number" and isinstance(v, dict):
        return set(v) == {"min", "max"} and all(_scalar_ok(kind, x) for x in v.values())
    return _scalar_ok(kind, v)


def check_case(c: dict) -> list[str]:
    errs: list[str] = []
    missing = REQUIRED - set(c)
    if missing:
        return [f"missing keys {sorted(missing)}"]
    extra = set(c) - REQUIRED - OPTIONAL
    if extra:
        errs.append(f"unknown keys {sorted(extra)}")
    if not ID.match(str(c["id"])):
        errs.append("bad id")
    if not isinstance(c["text"], str) or not c["text"].strip():
        errs.append("empty text")
    if c["script"] not in SCRIPTS:
        errs.append(f"bad script {c['script']!r}")
    if c["kind"] not in KINDS:
        return errs + [f"bad kind {c['kind']!r}"]
    if c["status"] not in STATUSES:
        errs.append(f"bad status {c['status']!r}")
    if not isinstance(c["tags"], list) or not all(isinstance(t, str) for t in c["tags"]):
        errs.append("tags must be a list of strings")
    if c["kind"] == "date" and not _is_date(c.get("relative_base")):
        errs.append("date cases need an ISO relative_base")

    e = c["expect"]
    if not isinstance(e, dict) or set(e) - EXPECT_KEYS:
        return errs + ["bad expect block"]
    if e.get("none") is True:
        if set(e) != {"none"}:
            errs.append("'none' cases take no other expect keys")
        return errs
    if "value" not in e:
        return errs + ["expect needs 'value' (or 'none': true)"]
    if e.get("ambiguous"):
        cands = e.get("candidates")
        if e["value"] is not None:
            errs.append("ambiguous cases must have value null (never pick silently)")
        if not isinstance(cands, list) or len(cands) < 2 or len(set(map(str, cands))) != len(cands):
            errs.append("ambiguous cases need >=2 distinct candidates")
        elif not all(_value_ok(c["kind"], x) for x in cands):
            errs.append("candidate has wrong canonical form")
        if "ambiguity" not in c["tags"]:
            errs.append("ambiguous cases must carry the 'ambiguity' tag")
    else:
        if "candidates" in e:
            errs.append("candidates only allowed when ambiguous")
        if not _value_ok(c["kind"], e["value"]):
            errs.append(f"value {e['value']!r} is not canonical for kind {c['kind']}")
    mc = e.get("max_confidence")
    if mc is not None and not (isinstance(mc, (int, float)) and 0 < mc < 1):
        errs.append("max_confidence must be in (0,1)")
    if "approximate" in e and not isinstance(e["approximate"], bool):
        errs.append("approximate must be boolean")
    return errs


def load(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def validate(paths: list[Path]) -> list[str]:
    problems: list[str] = []
    seen_ids: set[str] = set()
    seen_text: set[tuple[str, str]] = set()
    for p in paths:
        for i, c in enumerate(load(p), 1):
            where = f"{p.name}:{i} ({c.get('id', '?')})"
            problems += [f"{where}: {m}" for m in check_case(c)]
            if c.get("id") in seen_ids:
                problems.append(f"{where}: duplicate id")
            seen_ids.add(c.get("id", ""))
            key = (c.get("kind", ""), c.get("text", ""))
            if key in seen_text:
                problems.append(f"{where}: duplicate (kind, text)")
            seen_text.add(key)
    return problems


def export_csv(cases: list[dict], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "text", "kind", "relative_base", "expected", "tags", "author_note",
                    "verdict (ok / wrong / unnatural)", "corrected_value", "reviewer_comment"])
        for c in cases:
            w.writerow([c["id"], c["text"], c["kind"], c.get("relative_base", ""),
                        json.dumps(c["expect"], ensure_ascii=False), " ".join(c["tags"]),
                        c.get("note", ""), "", "", ""])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="*", type=Path, default=[DEFAULT])
    ap.add_argument("--export-csv", type=Path, help="also write a reviewer spreadsheet")
    a = ap.parse_args()
    problems = validate(a.paths)
    for m in problems:
        print("ERROR", m, file=sys.stderr)
    cases = [c for p in a.paths for c in load(p)]
    print(f"{len(cases)} cases, {len(problems)} problems")
    if a.export_csv and not problems:
        export_csv(cases, a.export_csv)
        print(f"wrote {a.export_csv}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
