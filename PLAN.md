# Kitna build plan

## Name
`kitna` returned 404 from `https://pypi.org/pypi/kitna/json` and
`https://pypi.org/simple/kitna/` on 2026-11-12, i.e. unregistered. The name is
not reserved until a first upload. Fallback if it is taken by then: `kitna-nlp`
(also 404 on the same date).

## Phase 1: gap check (this commit)
| Step | Output | State |
|---|---|---|
| Confirm PyPI name | above | done |
| Read BFCL-Hi card, IndicOrderBench, number-parser, dateparser | `docs/related_work.md` | done, with gaps marked `[TBD]` |
| Probe the two parsers on our inputs | `scripts/probe_baselines.py`, `results/phase1/` | done |
| Phenomena, canonical forms, open questions | `docs/taxonomy.md` | draft |
| Labeled parser cases | `tests/golden/draft_cases.jsonl` (292), format validator + tests | draft |
| **HUMAN CHECKPOINT** | review per `docs/review/README.md` | **waiting** |

## Later phases (unchanged from the brief)
2. Parser: normalize, numerals, fractions, money, time, dates, ambiguity; tests at each step.
3. Packaging, mkdocs, CI (3.10-3.14), 0.1.0rc.
4. Benchmark items + schema. **HUMAN CHECKPOINT**: 3 native speakers label 100 items, Cohen's kappa, freeze v1.
5. Harness, analysis plan committed before runs, cost estimate + confirmation, runs, stats, ablation, errors.
6. Report, dataset card, leaderboard, README with sourced numbers only.

## Known blockers and risks
- **Network**: this environment reaches only GitHub and PyPI. Hugging Face,
  arXiv and model-provider docs are unreachable, so current model names for the
  eval config cannot be looked up here, and no model can be called. Phase 5
  needs either a wider network or you supplying the model list and running the
  harness yourself.
- **Author is not a native speaker.** All Hindi/Hinglish in this repo so far is
  AI-drafted. The brief asks for a human-written benchmark; phase-4 items I
  draft would be AI-written and human-reviewed unless speakers write them.
  That must be stated in the dataset card either way.
- **Kill criterion** applies as specified in the brief.
