#!/usr/bin/env python3
"""Entry point for the benchmark tooling: python scripts/bench.py --help

Needs the bench extra:  pip install -e ".[bench]"
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bench"))

from kitna_bench.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
