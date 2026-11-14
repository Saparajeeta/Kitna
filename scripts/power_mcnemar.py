#!/usr/bin/env python3
"""Planning aid for docs/analysis_plan.md: simulated power of the exact McNemar test.

Not a result about any model. Assumptions are inputs, written into the output file.
Usage: python scripts/power_mcnemar.py  ->  results/planning/mcnemar_power.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parent.parent
PAIRS = (100, 130)                 # paired call scenarios expected from 150-200 scenarios
ONLY_OTHER_RIGHT = (0.02, 0.05)    # share of pairs where only the Hindi variant is right
DIFFS = (0.05, 0.08, 0.10, 0.12, 0.15, 0.20)
REPS, SEED, ALPHA = 5000, 20261112, 0.05


def power(n: int, p01: float, diff: float, rng: np.random.Generator) -> float:
    p10 = p01 + diff
    counts = rng.multinomial(n, [p10, p01, 1 - p10 - p01], size=REPS)
    hits = 0
    cache: dict[tuple[int, int], bool] = {}
    for b10, b01, _ in counts:
        key = (int(b10), int(b01))
        if key not in cache:
            k = key[0] + key[1]
            cache[key] = k > 0 and binomtest(key[0], k, 0.5).pvalue < ALPHA
        hits += cache[key]
    return hits / REPS


def main() -> int:
    rng = np.random.default_rng(SEED)
    rows = [{"pairs": n, "only_hindi_variant_right": p01, "true_accuracy_difference": d,
             "power": round(power(n, p01, d, rng), 3)} for n in PAIRS for p01 in ONLY_OTHER_RIGHT for d in DIFFS]
    out = {"what_this_is": "Simulated power of a two-sided exact McNemar test at alpha 0.05, single test, no "
                           "multiplicity correction. A planning aid under stated assumptions; not a measurement.",
           "replications": REPS, "seed": SEED, "rows": rows}
    path = ROOT / "results" / "planning" / "mcnemar_power.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    for r in rows:
        print(r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
