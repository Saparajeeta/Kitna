"""Demo logic, the claims checker, and the rule that drafts carry no unbacked numbers."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def demo() -> ModuleType:
    return _load("kitna_demo_app", ROOT / "demo" / "app.py")


@pytest.fixture(scope="module")
def claims() -> ModuleType:
    return _load("kitna_check_claims", ROOT / "scripts" / "check_claims.py")


def test_demo_shows_value_confidence_and_every_candidate(demo: ModuleType) -> None:
    rows, status, raw = demo.explain("Ramesh ko kal 5 baje dhai lakh rupaye", "2026-11-12", "10:00")
    by_kind = {r[1]: r for r in rows}
    assert by_kind["money"][2] == "INR 250000" and by_kind["money"][3] == "1.00" and by_kind["money"][4] == "no"
    amb = by_kind["datetime"]
    assert amb[2] == "(not decided)" and amb[4] == "yes"
    assert amb[5].split(" | ") == ["2026-11-11T05:00", "2026-11-11T17:00", "2026-11-13T05:00", "2026-11-13T17:00"]
    assert "ambiguous" in status and len(raw) == 2 and raw[0]["schema_version"] == "1"
    assert len(demo.HEADERS) == len(rows[0])


def test_demo_edge_cases(demo: ModuleType) -> None:
    assert demo.explain("")[1] == "Type something above."
    assert demo.explain("mujhe paani de do", "2026-11-12", "10:00")[0] == []
    assert "must look like" in demo.explain("kal", "12/11/2026", "10:00")[1]
    rows, status, _ = demo.explain("kal jaunga")
    assert rows and "server's clock" in status
    rows, _, _ = demo.explain("tees hazzar", kind="number")
    assert rows[0][2] == "30000" and rows[0][3] == "0.85"
    for example in demo.EXAMPLES:
        demo.explain(*example)


def test_claims_checklist_is_consistent(claims: ModuleType) -> None:
    assert claims.check_checklist() == []


def test_drafts_and_dataset_card_have_no_bare_numbers(claims: ModuleType) -> None:
    assert claims.check_drafts() == []


def test_bare_number_detector(claims: ModuleType) -> None:
    text = ("---\nsize: 100\n---\nWe have [N items] and `250000` here.\n<!-- 99 -->\n```\n42\n```\n"
            "Licence CC BY 4.0.\nAccuracy was 93%.\nKappa [0.81] was fine.\n")
    assert [line for _, line in claims.bare_numbers(text)] == ["Accuracy was 93%."]


def test_checker_catches_a_broken_claim(claims: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "README.md").write_text("We got 5 of 5, see results/x.json\n", encoding="utf-8")
    (tmp_path / "results").mkdir()
    (tmp_path / "results" / "x.json").write_text('{"match": 4}', encoding="utf-8")
    listing = tmp_path / "claims.md"
    listing.write_text("## Claims made\n\n| ID | Claim | Stated in | Evidence | Evidence contains |\n"
                       "|---|---|---|---|---|\n"
                       '| C1 | `5 of 5` | `README.md` | `results/x.json` | `"match": 5` |\n'
                       "| C2 | `7 of 7` | `README.md` | `results/y.json` | `x` |\n", encoding="utf-8")
    monkeypatch.setattr(claims, "ROOT", tmp_path)
    monkeypatch.setattr(claims, "CHECKLIST", listing)
    problems = "\n".join(claims.check_checklist())
    assert "C1: results/x.json does not contain" in problems
    assert "C2: README.md no longer contains the claim text" in problems
    assert "C2: evidence file results/y.json does not exist" in problems


def test_public_drafts_keep_the_required_wording() -> None:
    card = (ROOT / "hf" / "README.md").read_text(encoding="utf-8")
    for needle in ("license: cc-by-4.0", "ai_drafted", "human_written", "Out-of-scope uses", "Limitations",
                   "Who wrote what", "[TBD"):
        assert needle in card, needle
    for name in ("linkedin_post.md", "devto_writeup.md", "resume_bullets.md"):
        text = (ROOT / "drafts" / name).read_text(encoding="utf-8")
        assert "[" in text and "not published" in text.lower() or "draft" in text.lower()
        for banned in ("first ever", "the first ", "state-of-the-art", "% coverage", "tests passed"):
            assert banned not in text.lower(), (name, banned)


def test_every_yaml_file_in_the_repository_parses() -> None:
    yaml = pytest.importorskip("yaml")
    files = [p for pattern in ("*.yml", "*.yaml", ".github/**/*.yml", "bench/*.yaml", "*.cff")
             for p in ROOT.glob(pattern)] + [ROOT / ".pre-commit-config.yaml"]
    assert len(files) >= 10
    for path in files:
        assert yaml.safe_load(path.read_text(encoding="utf-8")) is not None, path
