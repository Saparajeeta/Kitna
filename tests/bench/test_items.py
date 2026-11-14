from __future__ import annotations

import copy
import datetime as dt
import json
from collections import Counter
from pathlib import Path

import pytest
from kitna_bench import authoring, drafts
from kitna_bench.cli import DRAFTS_FILE, SEED_FILE, main
from kitna_bench.items import load_items, load_tools, summarize, validate_item, validate_items
from kitna_bench.normalize import is_canonical, kitna_value, strict_value
from kitna_bench.seed import build_seed

import kitna

NOW = dt.datetime(2026, 11, 12, 10, 0)


@pytest.fixture(scope="module")
def seed() -> list[dict]:
    return load_items(SEED_FILE)


def test_seed_file_is_current_and_valid(seed: list[dict]) -> None:
    assert seed == build_seed()
    assert validate_items(seed) == []
    assert main(["seed", "--check"]) == 0


def test_seed_is_exactly_40_ai_drafted_scenarios_in_three_variants(seed: list[dict]) -> None:
    s = summarize(seed)
    assert s["scenarios"] == 40 and s["rows"] == 120
    assert s["by_provenance"] == {"ai_drafted": 120}
    assert s["by_variant"] == {"devanagari": 40, "english": 40, "roman": 40}
    assert set(s["by_domain"].values()) == {8}
    assert s["by_expected_behavior"]["abstain"] == 15 and s["by_expected_behavior"]["clarify"] >= 27


def test_every_tool_has_a_domain_and_typed_params() -> None:
    tools = load_tools()
    assert len(tools) == 15
    assert Counter(t["domain"] for t in tools.values()) == Counter(
        {"payments": 3, "travel": 3, "reminders": 3, "shopping": 3, "support": 3})


@pytest.mark.parametrize(("mutate", "needle"), [
    (lambda i: i.update(id="seed-pay-001-en"), "id must be"),
    (lambda i: i.update(utterance="Ramesh ko dhai lakh भेज दो"), "contains Devanagari"),
    (lambda i: i["gold"].update(tool="fly_to_moon"), "not one of the item's tools"),
    (lambda i: i["gold"]["arguments"].update(amount_inr="2.5 lakh"), "not in canonical number form"),
    (lambda i: i["gold"]["arguments"].update(colour="red"), "not a parameter"),
    (lambda i: i["gold"]["arguments"].pop("amount_inr"), "has no gold value"),
    (lambda i: i.update(expected_behavior="clarify"), "ambiguous must be true"),
    (lambda i: i.update(provenance="human_written"), "need a writer id"),
    (lambda i: i.update(utterance="Ramesh ko 9876543210 par dhai lakh bhej do"), "mobile number"),
    (lambda i: i.update(utterance="ramesh@okbank ko dhai lakh bhej do"), "UPI ID"),
    (lambda i: i.update(extra_field=1), "schema:"),
    (lambda i: i.update(domain="astrology"), "schema:"),
])
def test_validator_rejects(seed: list[dict], mutate, needle: str) -> None:
    item = copy.deepcopy(next(i for i in seed if i["id"] == "seed-pay-001-roman"))
    assert validate_item(item) == []
    mutate(item)
    assert any(needle in p for p in validate_item(item)), validate_item(item)


def test_cross_row_rules(seed: list[dict]) -> None:
    rows = copy.deepcopy(seed)
    assert any("needs exactly one item per variant" in p for p in validate_items(rows[1:]))
    rows[0]["gold"]["arguments"]["amount_inr"] = "1"
    assert any("gold differs between variants" in p for p in validate_items(rows))
    assert any("duplicate id" in p for p in validate_items(seed + seed[:1]))


def test_canonical_forms() -> None:
    assert strict_value(250000, "number") == "250000"
    assert strict_value("2,50,000", "number") == "250000"
    assert strict_value(2.50, "number") == "2.5"
    assert strict_value("2.5 lakh", "number") is None
    assert kitna_value("2.5 lakh", "number", NOW) == "250000"
    assert kitna_value("₹1,500", "number", NOW) == "1500"
    assert strict_value("2026-11-13T18:00:00+05:30", "datetime") == "2026-11-13T18:00"
    assert strict_value("2026-11-13T12:30:00Z", "datetime") is None      # a different wall-clock time: not guessed
    assert strict_value("2026-11-13 18:00", "datetime") == "2026-11-13T18:00"
    assert strict_value("6:05", "time") == "06:05" and strict_value("18:00:00", "time") == "18:00"
    assert kitna_value("6 PM", "time", NOW) == "18:00"
    assert kitna_value("tomorrow", "date", NOW) == "2026-11-13"
    assert kitna_value("kal", "date", NOW) is None                       # ambiguous: no credit for a guess
    assert kitna_value("5 baje", "time", NOW) is None
    assert strict_value("PT90M", "duration") == "PT1H30M" and strict_value("P1DT0H", "duration") == "P1D"
    assert kitna_value("dedh ghante", "duration", NOW) == "PT1H30M"
    assert strict_value("  New-Delhi ", "string") == "newdelhi"
    assert strict_value(True, "number") is None and strict_value({"a": 1}, "date") is None
    assert is_canonical("250000", "number") and not is_canonical("250000.0", "number")
    assert is_canonical("PT1H30M", "duration") and not is_canonical("PT90M", "duration")


def test_seed_gold_quantities_are_found_by_kitna_in_the_hindi_variants(seed: list[dict]) -> None:
    """Self-consistency of the AI-drafted seed (not accuracy): the parser reads the same values the gold states.

    Listed exceptions are known parser behaviours, kept visible here.
    """
    known = {("seed-trv-003", "travel_date")}   # '20 November' with no year: the parser flags two candidates
    misses = []
    for item in seed:
        if item["variant"] == "english":
            continue
        props = {t["name"]: t for t in item["tools"]}.get(item["gold"]["tool"], {}).get(
            "parameters", {}).get("properties", {})
        found = []
        for r in kitna.parse(item["utterance"], relative_base=NOW):
            found.append(r.canonical.replace("INR ", ""))
            if r.kind == "datetime" and not r.ambiguous:
                found += r.canonical.split("T")
        for name, value in item["gold"]["arguments"].items():
            if props[name]["x-kitna-kind"] in ("number", "date", "time", "datetime", "duration"):
                if value not in found and (item["scenario_id"], name) not in known:
                    misses.append((item["id"], name, value, found))
    assert misses == []


# ---------------------------------------------------------------- drafts and authoring kit

def test_drafts_file_is_current_balanced_and_unique() -> None:
    rows = drafts.build_drafts()
    assert authoring.load_drafts(DRAFTS_FILE) == json.loads(json.dumps(rows))
    assert len(rows) == 160
    per = Counter((r["domain"], r["expected_behavior"]) for r in rows)
    assert set(per.values()) == {22, 6, 4}
    for key in ("english", "devanagari", "brief", "scenario_id"):
        dup = [k for k, v in Counter(r[key] for r in rows).items() if v > 1]
        assert dup == [], (key, dup)
    assert all("roman" not in r for r in rows)


def test_draft_phrase_tables_agree_with_the_parser() -> None:
    """Self-consistency (not accuracy) of the AI-drafted Devanagari phrases against the stated values."""
    for value, _, hi, _ in drafts.AMOUNTS:
        assert [r.canonical for r in kitna.parse(hi)] == [f"INR {value}"], hi
    for hhmm, _, hi in drafts.TIMES:
        assert [r.canonical for r in kitna.parse(hi)] == [hhmm], hi
    for iso, _, hi, _ in drafts.DURATIONS:
        assert [r.canonical for r in kitna.parse(hi)] == [iso], hi
    for off, _en, hi, _ in drafts.DAYS:
        want = (NOW + dt.timedelta(days=off)).date().isoformat()
        got = kitna.parse(hi + " jaunga", relative_base=NOW)[0]
        assert want in [c.isoformat() for c in got.candidates] or got.canonical == want, hi


def _fill(sheet: Path, text_for) -> None:
    import csv

    with sheet.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["roman_utterance"] = text_for(r)
    with sheet.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=authoring.SHEET_COLUMNS)
        w.writeheader()
        w.writerows(rows)


def test_writer_sheets_round_trip(tmp_path: Path) -> None:
    rows = drafts.build_drafts()
    counts = authoring.write_writer_sheets(rows, tmp_path, ["w01", "w02", "w03"])
    assert sum(counts.values()) == 160 and max(counts.values()) - min(counts.values()) <= 1
    sheet_text = (tmp_path / "writer_w01.csv").read_text(encoding="utf-8-sig")
    assert "english" not in sheet_text.splitlines()[0] and "रुपये" not in sheet_text   # writers never see AI lines
    sheets = sorted(tmp_path.glob("writer_*.csv"))
    res = authoring.import_sheets(rows, sheets)
    assert res["scenarios_written"] == 0 and len(res["scenarios_missing"]) == 160 and res["problems"] == []
    for s in sheets:
        _fill(s, lambda r: f"placeholder line for {r['scenario_id']} likha gaya")
    res = authoring.import_sheets(rows, sheets)
    assert res["problems"] == [] and len(res["items"]) == 480 and res["writers"] == ["w01", "w02", "w03"]
    roman = [i for i in res["items"] if i["variant"] == "roman"]
    assert {i["provenance"] for i in roman} == {"human_written"}
    assert {i["provenance"] for i in res["items"] if i["variant"] != "roman"} == {"ai_drafted"}
    kal = [i for i in res["items"] if "variant_specific_gold" in i["phenomena"]]
    assert {i["expected_behavior"] for i in kal if i["variant"] == "english"} == {"call"}
    assert {i["expected_behavior"] for i in kal if i["variant"] != "english"} == {"clarify"}


def test_import_reports_bad_rows(tmp_path: Path) -> None:
    rows = drafts.build_drafts()
    authoring.write_writer_sheets(rows, tmp_path, ["w01"])
    sheet = tmp_path / "writer_w01.csv"
    bad = {"v1-pay-001": "रमेश को पैसे भेज दो", "v1-pay-002": "call 9876543210 abhi", "v1-pay-003": "same line",
           "v1-pay-004": "same line"}
    _fill(sheet, lambda r: bad.get(r["scenario_id"], ""))
    res = authoring.import_sheets(rows, [sheet])
    text = "\n".join(res["problems"])
    assert "Devanagari letters" in text and "mobile number" in text and "same Roman line" in text
    assert main(["import", "--sheets", str(sheet), "--out", str(tmp_path / "x.jsonl")]) == 1
    assert not (tmp_path / "x.jsonl").exists()
