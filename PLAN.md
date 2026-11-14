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
2. Parser: **built** (numbers, fractions, money, time, durations, dates, ambiguity, CLI, clock warning,
   strict mode, versioned JSON output). Contested rules are provisional and live in
   `src/kitna/data/policy.tsv`; affected cases stay tagged `review`.
   **HUMAN CHECKPOINT:** native-speaker answers (`docs/open_questions.md`) and the held-out set
   (`docs/heldout_protocol.md`; `scripts/bench.py heldout freeze|check|score`).
3. Benchmark (`bench/`): schema, validator, 15 tools, 40-scenario AI seed set, 160 AI-drafted scenario
   drafts, authoring kit, annotation tools: **built**.
   **HUMAN CHECKPOINT:** native speakers write the Roman Hinglish lines; at least two other native speakers
   label independently; agreement is computed; disagreements are settled.
4. Harness: adapters, mock, runner (estimate, confirmation, cost cap, resume), grader, statistics, ablation,
   error types, reports, manifest, kill criterion: **built, run with the mock adapter only**.
   Analysis plan: `docs/analysis_plan.md`, tag `analysis-plan-v1`.
   **OWNER STEP:** fill `bench/models.yaml`, run `scripts/bench.py run` (needs network and keys).
5. Packaging: CI (3.10-3.14), release workflow, pre-commit, dependabot, release-notes template: **written,
   never run on GitHub**. **OWNER STEP:** checklist in `docs/releasing.md`. `0.1.0` only after native-speaker
   review and a frozen held-out set.
6. Public surfaces: dataset card, Gradio demo, leaderboard page, post drafts, claims checklist:
   **drafts with placeholders**; numbers are filled only from `results/`.

## Known blockers and risks
- **Network**: this environment reaches only GitHub and PyPI. Hugging Face,
  arXiv and model-provider docs are unreachable, so current model names for the
  eval config cannot be looked up here, and no model can be called. Phase 5
  needs either a wider network or you supplying the model list and running the
  harness yourself.
- **No native-speaker review yet.** All Hindi/Hinglish in this repo is
  AI-drafted; round 1 checked arithmetic only.
- **Kill criterion** applies as specified in the brief.
