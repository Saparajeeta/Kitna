# Kitna

> **Status: phase 2 of 6, in progress.** Numbers, fraction idioms and money parse.
> Times, dates and the benchmark do not exist yet. Not on PyPI. See [PLAN.md](PLAN.md).

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

## What works today

```python
>>> import kitna
>>> [(r.kind, r.canonical, r.confidence) for r in kitna.parse("dhai lakh")]
[('number', '250000', 1.0)]
>>> kitna.parse("paune do lakh rupaye")[0].canonical
'INR 175000'
>>> kitna.parse("do se teen hazaar rupaye")[0].canonical
'INR 2000..INR 3000'
>>> kitna.parse("tees hazzar")[0].confidence      # misspelling repaired, confidence lowered
0.85
>>> kitna.parse("mujhe paani de do")              # "do" is the verb here
[]
>>> kitna.parse("zero nau ek", kind="digits")[0].value
'091'
```

Test status (source: `results/phase2/test_run.txt`): all 198 number, digit-sequence
and money cases in the draft golden file pass; the 147 time, duration and date
cases are skipped because those parsers are not written. Branch coverage of
`src/kitna` in that run was 97%. The golden cases are drafts that no native
speaker has reviewed, so "pass" means "matches the draft expectation".

Install from a checkout: `pip install -e ".[dev]"`, then `pytest`.

## Repository

| Path | What |
|---|---|
| `src/kitna/` | The library (zero runtime dependencies, typed) |
| `src/kitna/data/` | Spelling tables as plain TSV; see `data/README.md` to contribute |
| `tests/` | Golden cases, unit tests, hypothesis property and fuzz tests |
| `docs/related_work.md` | What BFCL-Hi, IndicOrderBench, number-parser, dateparser cover |
| `docs/taxonomy.md` | Phenomena, canonical forms, decisions, open questions (draft 2) |
| `docs/review/` | Reviewer instructions, spreadsheet, round-1 decisions |
| `scripts/`, `results/` | Case validator, baseline probe, raw outputs behind every number here |

## Limitations (current)

- All Hindi/Hinglish text so far was drafted by an AI agent. One non-native
  reviewer checked the arithmetic; no native speaker has reviewed it.
- The spelling tables are AI-drafted too. Unlisted spellings fall back to a
  repair step that can miss, and ordinary words that look like number words
  (`do`, `saath`, `ek`) are handled by a small rule list that will have gaps.
- Related-work checks were limited to GitHub and PyPI on 2026-11-12.

## License

Code: Apache-2.0. Benchmark data (planned): CC BY 4.0.
