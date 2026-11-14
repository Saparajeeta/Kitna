"""The claims checker and the rule that drafts carry no unbacked numbers. (Demo tests: test_demo.py.)"""
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
def claims() -> ModuleType:
    return _load("kitna_check_claims", ROOT / "scripts" / "check_claims.py")


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


def test_space_folder_is_complete_and_card_keeps_the_notice(tmp_path: Path) -> None:
    space = _load("kitna_build_space", ROOT / "scripts" / "build_space.py")
    assert space.main(["--check"]) == 0
    files = space.build(tmp_path / "space")
    assert {"app.py", "README.md", "requirements.txt", "cases_review.csv", "kitna_demo/review.py"} <= set(files)
    card = (tmp_path / "space" / "README.md").read_text(encoding="utf-8")
    assert card.startswith("---\n") and "sdk: gradio" in card and "app_file: app.py" in card
    assert "Pre-alpha" in card and "No accuracy has been measured" in card
    requirements = (tmp_path / "space" / "requirements.txt").read_text(encoding="utf-8")
    assert "kitna @ git+https://github.com/Saparajeeta/Kitna" in requirements


def test_dockerfile_serves_as_non_root_and_readme_keeps_story_and_status() -> None:
    docker = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert 'CMD ["kitna", "serve", "--host", "0.0.0.0", "--port", "8000"]' in docker and "USER kitna" in docker
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Kitna reads them exactly, or tells you it's unsure." in readme.split("\n", 4)[2]
    assert "has no accuracy figure" in readme and "## Quickstart in 60 seconds" in readme
    for shot in ("demo_ambiguity.png", "demo_context.png", "demo_action.png"):
        assert f"docs/assets/{shot}" in readme and (ROOT / "docs" / "assets" / shot).exists()
    for name in ("linkedin_post.md", "demo_script.md"):
        text = (ROOT / "drafts" / name).read_text(encoding="utf-8")
        assert "[TBD" in text and "not published" in text.lower() or "not recorded" in text.lower()
