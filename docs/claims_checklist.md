# Claims checklist

Every statement with a number, in the README, docs, dataset card or any post, must appear
here with the file in `results/` that backs it. `scripts/check_claims.py` (run in CI and in
the test suite) checks that the claim text is still where it is said to be, that the
evidence file exists and still contains the value, and that the stating file links to it. It
also checks that the drafts in `drafts/` and `hf/` contain no number outside a bracketed
placeholder.

## Claims made

| ID | Claim (exact text) | Stated in | Evidence file | Evidence contains |
|---|---|---|---|---|
| C1 | `322 of 322 match` | `README.md` | `results/phase2/golden_summary.json` | `"match": 322` |
| C2 | `36 of 36 match` | `README.md` | `results/phase2/golden_summary.json` | `"match": 36` |
| C3 | `573 passed, 1 expected failure` | `README.md` | `results/phase2/test_run.txt` | `573 passed, 1 xfailed` |
| C4 | `number-parser parsed 2 of 82 Roman-script number cases` | `README.md` | `results/phase1/baseline_probe_summary.json` | `"number_parser": "0.3.2"` |
| C5 | `dateparser 3 of 91 Roman-script date/time cases` | `README.md` | `results/phase1/baseline_probe_summary.json` | `"dateparser": "1.5.0"` |
| C6 | `roughly 12 to 15 points` | `docs/analysis_plan.md` | `results/planning/mcnemar_power.json` | `"pairs": 100` |

What each one is, and what it is not:

- **C1, C2**: the parser agrees with cases drafted by the same AI. A self-consistency
  check, **not accuracy**. C2 covers cases that rest on rules still awaiting a native
  speaker; it is always reported separately.
- **C3**: the test suite passes. Not a quality measure; not for headlines or resumes.
- **C4, C5**: coverage of two existing libraries on our own unreviewed, Roman-heavy draft
  cases. Not a ranking of those libraries.
- **C6**: a simulation under stated assumptions, used for planning.

## Claims that cannot be made yet

| Claim | Needs | Will be backed by |
|---|---|---|
| Parser accuracy | held-out set written by native speakers, frozen | `results/heldout/v1_kitna-<version>.json` |
| Number of benchmark scenarios, writers, annotators | the human-written benchmark | `bench/items/dev_v1.jsonl` summary, `results/annotation/agreement.json` |
| Inter-annotator agreement (kappa) | two independent label sets | `results/annotation/agreement.json` |
| Any model score, any English-vs-Hinglish gap, any ablation effect | a real run | `results/bench/<run>/summary.csv`, `paired_tests.csv`, `ablation_tests.csv` |
| "Models are at ceiling" or "models struggle" | a real run and the kill-criterion section | `results/bench/<run>/summary.md` |
| Works on Python 3.10-3.14 | a green CI run on GitHub | link to the CI run |
| Installs from PyPI | a published development release | PyPI page, release notes |
| Downloads, users, stars | never, unless copied from the platform with a date | - |

## Never to be cited

- Anything under `results/pipeline_check_mock/`: a mock "model" that reads the gold answers.
- Any run on the AI-drafted seed set (`seed_v0.jsonl`).
- Coverage percentages, property-test or fuzzing counts, as evidence of correctness.

## Adding a claim

1. Produce the number with a script that writes into `results/`.
2. State it with a link to that file.
3. Add a row above. Run `python scripts/check_claims.py`.

## Updating the test-count evidence (C3)

The claims check is itself a test, and C3 points at the saved test output. When the
number of tests changes: edit the count in `README.md` and in the C3 row first, then save
the output to a temporary file and move it into place, twice (the first pass still sees
the old file and records one failure):

```bash
python -m pytest -q --cov --cov-report=term > /tmp/t.txt; mv /tmp/t.txt results/phase2/test_run.txt
```
