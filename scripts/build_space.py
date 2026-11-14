#!/usr/bin/env python3
"""Assemble the files of the Hugging Face Space into one folder (nothing is uploaded).

    python scripts/build_space.py            # writes space_build/
    python scripts/build_space.py --check    # only checks that every source file exists

The folder then holds exactly what the Space repository needs:
app.py, kitna_demo/, cases_review.csv (reviewer mode), requirements.txt, README.md (the Space card).
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = {
    "app.py": ROOT / "demo" / "app.py",
    "kitna_demo": ROOT / "demo" / "kitna_demo",
    "README.md": ROOT / "demo" / "space" / "README.md",
    "requirements.txt": ROOT / "demo" / "space" / "requirements.txt",
    "cases_review.csv": ROOT / "docs" / "review" / "phase1_cases_review.csv",
}


def build(out: Path) -> list[str]:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for name, src in SOURCES.items():
        if src.is_dir():
            shutil.copytree(src, out / name, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            shutil.copyfile(src, out / name)
    return sorted(str(p.relative_to(out)) for p in out.rglob("*") if p.is_file())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=ROOT / "space_build")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    missing = [str(p) for p in SOURCES.values() if not p.exists()]
    if missing:
        print("build_space.py: missing " + ", ".join(missing), file=sys.stderr)
        return 1
    if args.check:
        print("space sources: ok")
        return 0
    for f in build(args.out):
        print(f)
    print(f"\nwrote {args.out}. Nothing was uploaded; see demo/README.md for the deploy steps.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
