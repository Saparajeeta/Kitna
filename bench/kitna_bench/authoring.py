"""Authoring kit: writer sheets out, validated items in.

Flow:  drafts (AI: tools, gold, English, Devanagari, brief)
       -> writer sheets (brief only; the writer types the Roman Hinglish line)
       -> import: merge sheets with drafts, validate every row, write items JSONL.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from .drafts import Draft, build_drafts
from .items import Item, load_tools, privacy_problems, tool_for_item, validate_items

SHEET_COLUMNS = ["scenario_id", "domain", "brief", "roman_utterance", "writer_id", "comment"]
_DEVA = re.compile(r"[\u0900-\u097F]")
_WRITER = re.compile(r"^w[0-9]{2,3}$")


def write_drafts(path: Path) -> list[Draft]:
    rows = build_drafts()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    return rows


def load_drafts(path: Path) -> list[Draft]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_writer_sheets(drafts: list[Draft], out_dir: Path, writers: list[str]) -> dict[str, int]:
    """Deal the scenarios round-robin (within each domain) to the writers; one CSV each.

    The sheet shows only the brief. It never shows the AI's English or Devanagari line or the gold values'
    wording, so the writer's phrasing is their own.
    """
    for w in writers:
        if not _WRITER.match(w):
            raise ValueError(f"writer id {w!r} must look like w01")
    if len(set(writers)) != len(writers) or not writers:
        raise ValueError("give at least one writer id, each once")
    out_dir.mkdir(parents=True, exist_ok=True)
    piles: dict[str, list[Draft]] = {w: [] for w in writers}
    for n, d in enumerate(sorted(drafts, key=lambda r: (r["domain"], r["scenario_id"]))):
        piles[writers[n % len(writers)]].append(d)
    for w, pile in piles.items():
        with (out_dir / f"writer_{w}.csv").open("w", encoding="utf-8-sig", newline="") as fh:
            out = csv.writer(fh)
            out.writerow(SHEET_COLUMNS)
            for d in pile:
                out.writerow([d["scenario_id"], d["domain"], d["brief"], "", w, ""])
    return {w: len(p) for w, p in piles.items()}


def read_writer_sheet(path: Path) -> tuple[dict[str, dict[str, str]], list[str]]:
    """scenario_id -> {roman_utterance, writer_id}; plus row-level problems (file:line: message)."""
    rows: dict[str, dict[str, str]] = {}
    problems: list[str] = []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in SHEET_COLUMNS[:5] if c not in (reader.fieldnames or [])]
        if missing:
            return {}, [f"{path.name}: missing column(s) {missing}"]
        for n, row in enumerate(reader, 2):
            sid = (row["scenario_id"] or "").strip()
            text = " ".join((row["roman_utterance"] or "").split())
            writer = (row["writer_id"] or "").strip()
            where = f"{path.name}:{n} ({sid or 'no scenario_id'})"
            if not sid:
                problems.append(f"{where}: scenario_id is empty")
                continue
            if not text:
                continue    # not written yet; reported by the importer as 'missing'
            if not _WRITER.match(writer):
                problems.append(f"{where}: writer_id must look like w01")
            if _DEVA.search(text):
                problems.append(f"{where}: the Roman line contains Devanagari letters; type it in English letters")
            if len(text) < 3 or len(text) > 400:
                problems.append(f"{where}: utterance must be 3-400 characters")
            problems += [f"{where}: utterance {p}" for p in privacy_problems(text)]
            if sid in rows:
                problems.append(f"{where}: scenario appears twice in this sheet")
            rows[sid] = {"roman_utterance": text, "writer_id": writer}
    return rows, problems


def _items_for(d: Draft, roman: dict[str, str], catalog: dict[str, dict[str, Any]], split: str) -> list[Item]:
    out = []
    for variant, suffix in (("english", "en"), ("roman", "roman"), ("devanagari", "deva")):
        gold_args, clarify, behavior = d["gold_arguments"], d["clarify_about"], d["expected_behavior"]
        if variant == "english" and d.get("english_gold"):
            gold_args = d["english_gold"]["gold_arguments"]
            clarify = d["english_gold"]["clarify_about"]
            behavior = d["english_gold"]["expected_behavior"]
        gold: dict[str, Any] = {"tool": d["gold_tool"], "arguments": dict(gold_args)}
        aliases = {k: v for k, v in d.get("aliases", {}).items() if k in gold_args}
        if aliases:
            gold["aliases"] = aliases
        human = variant == "roman"
        out.append({
            "schema_version": "1", "id": f"{d['scenario_id']}-{suffix}", "scenario_id": d["scenario_id"],
            "split": split, "domain": d["domain"], "variant": variant,
            "utterance": roman["roman_utterance"] if human else d[variant], "now": d["now"],
            "tools": [tool_for_item(t, catalog) for t in d["tools"]], "gold": gold, "phenomena": d["phenomena"],
            "ambiguous": behavior == "clarify", "expected_behavior": behavior, "clarify_about": list(clarify),
            "provenance": "human_written" if human else "ai_drafted",
            "author_id": roman["writer_id"] if human else d["author_id"], "labels": [],
        })
    return out


def import_sheets(drafts: list[Draft], sheets: list[Path], *, split: str = "dev") -> dict[str, Any]:
    """Merge writer sheets with the drafts. Returns items plus a report; nothing is written here.

    A scenario becomes three items only when its Roman line is present and its rows validate.
    """
    by_id = {d["scenario_id"]: d for d in drafts}
    problems: list[str] = []
    written: dict[str, dict[str, str]] = {}
    for path in sheets:
        rows, probs = read_writer_sheet(path)
        problems += probs
        for sid, row in rows.items():
            if sid not in by_id:
                problems.append(f"{path.name} ({sid}): unknown scenario_id")
            elif sid in written:
                problems.append(f"{path.name} ({sid}): already written in another sheet by {written[sid]['writer_id']}")
            else:
                written[sid] = row
    catalog = load_tools()
    items: list[Item] = []
    for sid in sorted(written):
        items += _items_for(by_id[sid], written[sid], catalog, split)
    seen: dict[str, str] = {}
    for sid, row in written.items():
        key = row["roman_utterance"].casefold()
        if key in seen:
            problems.append(f"{sid}: same Roman line as {seen[key]}")
        seen[key] = sid
    problems += validate_items(items)
    return {"items": items, "problems": problems, "scenarios_written": len(written),
            "scenarios_missing": sorted(set(by_id) - set(written)),
            "writers": sorted({r["writer_id"] for r in written.values()})}
