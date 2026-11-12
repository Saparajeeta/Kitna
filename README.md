# Kitna

> **Status: phase 1 of 6 (gap check). There is no parser and no benchmark yet.**
> Nothing here is installable. See [PLAN.md](PLAN.md).

Kitna ("how much") is planned as two things:

- **A Python library** that converts Hinglish (Romanized Hindi mixed with
  English) and Devanagari quantities, money, times and dates into exact
  canonical values, with explicit ambiguity flags instead of silent guesses.
- **A benchmark** of tool-calling tasks in Indian contexts, in Devanagari,
  Romanized Hinglish and English, that measures how well LLMs fill tool
  arguments. Grading uses the library.

## Why

- The Hindi function-calling benchmark we examined (BFCL-Hi) is machine
  translated from English and keeps English function schemas.
- Romanized Hinglish is covered only thinly: one ordering benchmark with
  not-yet-reviewed Hinglish scenarios, and one mechanically romanised version
  of BFCL.
- The Hindi number and date parsers we examined handle Devanagari, not Roman
  script, and have no fraction idioms (dhai, dedh, saade) or ambiguity output.
  In our phase-1 probe, number-parser parsed 1 of 79 Roman-script number cases
  and dateparser 3 of 91 Roman-script date/time cases, all four being plain
  English inputs. The cases are our own unreviewed drafts, built to target
  this gap. Source: `results/phase1/baseline_probe_summary.json`.

Details, caveats and what these projects do well: [docs/related_work.md](docs/related_work.md).

## What exists today

| Path | What |
|---|---|
| `docs/related_work.md` | What BFCL-Hi, IndicOrderBench, number-parser, dateparser cover |
| `docs/taxonomy.md` | Phenomena, canonical forms, decisions, open questions (draft 2) |
| `tests/golden/draft_cases.jsonl` | 345 draft parser cases (arithmetic checked; no native-speaker review) |
| `docs/review/` | Reviewer instructions, spreadsheet, round-1 decisions |
| `scripts/`, `results/phase1/` | Case validator, baseline probe and its raw output |

```bash
python scripts/validate_cases.py     # stdlib only
pip install pytest && pytest -q
```

## Limitations (current)

- All Hindi/Hinglish text so far was drafted by an AI agent. One non-native
  reviewer checked the arithmetic; no native speaker has reviewed it.
- Related-work checks were limited to GitHub and PyPI on 2026-11-12.

## License

Code: Apache-2.0. Benchmark data (planned): CC BY 4.0.
