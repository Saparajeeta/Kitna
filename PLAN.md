# Kitna build plan

## Name
`kitna` returned 404 from `https://pypi.org/pypi/kitna/json` and
`https://pypi.org/simple/kitna/` on 2026-11-12, i.e. unregistered. The name is
not reserved until a first upload. Fallback if it is taken by then: `kitna-nlp`
(also 404 on the same date).

## Phase 1: gap check
| Step | Output | State |
|---|---|---|
| Confirm PyPI name | above | done |
| Read BFCL-Hi card, IndicOrderBench, number-parser, dateparser | `docs/related_work.md` | done, gaps marked `[TBD]` |
| Probe the two parsers on our inputs | `scripts/probe_baselines.py`, `results/phase1/` | done (re-run on draft 2) |
| Phenomena, canonical forms | `docs/taxonomy.md` | draft 2, round-1 decisions applied |
| Labeled parser cases | `tests/golden/draft_cases.jsonl` (358), validator + tests | draft 2 |
| Review round 1 (arithmetic, non-native) | `docs/review/round1_decisions.md` | done |
| **HUMAN CHECKPOINT**: native-speaker review | `docs/review/README.md` | **waiting** (taxonomy section 5) |

## Later phases
2. Parser: **built** (numbers, fractions, money, time, durations, dates, ambiguity, CLI).
   Contested rules are provisional and live in `src/kitna/data/policy.tsv`; affected cases stay tagged `review`.
   **Open:** native-speaker answers (taxonomy section 5) and the held-out set (`docs/heldout_protocol.md`).
3. Packaging: CI (3.10-3.14) and trusted-publishing release workflow **written, not yet run on GitHub**;
   wheel builds and installs in a clean venv locally. **Owner action:** add the PyPI pending publisher, then tag
   `v0.1.0.dev0`. Still to do: mkdocs site, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT.
4. Benchmark, target **150-200 items**. Authorship split agreed in round 1:
   - Roman Hinglish utterances: written by the project owner and two other speakers (50-100 each, own style);
   - tool schemas, gold arguments, Devanagari and English variants: drafted by the AI agent;
   - gold arguments labeled independently by different people; Cohen's kappa; freeze v1;
   - the dataset card states which parts were AI-drafted.
5. Harness, analysis plan committed before runs, cost estimate + confirmation, runs, stats, ablation, errors.
6. Report, dataset card, leaderboard, README with sourced numbers only.

## Known blockers and risks
- **Network**: this environment reaches only GitHub and PyPI. Hugging Face,
  arXiv and model-provider docs are unreachable, so current model names for the
  eval config cannot be looked up here, and no model can be called. Phase 5
  needs either a wider network or you supplying the model list and running the
  harness yourself.
- **No native-speaker review yet.** All Hindi/Hinglish in this repo is
  AI-drafted; round 1 checked arithmetic only.
- **Kill criterion** applies as specified in the brief.
