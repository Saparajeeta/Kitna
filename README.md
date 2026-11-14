# Kitna

> **Status: pre-alpha (0.1.0.dev0), not on PyPI yet.** The parser handles numbers,
> money, times, durations and dates. **There is no accuracy figure**: no native
> speaker has reviewed the rules or the test cases, and the held-out set that
> will give one does not exist yet. The benchmark is not started. See [PLAN.md](PLAN.md).

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
  In our phase-1 probe, number-parser parsed 2 of 82 Roman-script number cases
  and dateparser 3 of 91 Roman-script date/time cases, all five being plain
  English inputs. The cases are our own unreviewed drafts, built to target
  this gap. Source: `results/phase1/baseline_probe_summary.json`.

Details, caveats and what these projects do well: [docs/related_work.md](docs/related_work.md).

## What works today

```console
$ kitna parse "kal subah saade saat baje 2.5 lakh rupaye bhej dunga" --base 2026-11-12
datetime	2026-11-13T07:30	confidence=1.0	'kal subah saade saat baje'
money	INR 250000	confidence=1.0	'2.5 lakh rupaye'
$ kitna parse "kal shaam sawa paanch baje" --base 2026-11-12
datetime	2026-11-11T17:15 | 2026-11-13T17:15	confidence=1.0  [ambiguous]	'kal shaam sawa paanch baje'
```

```python
import kitna
kitna.parse("paune do lakh rupaye")[0].canonical        # 'INR 175000'
kitna.parse("do se teen hazaar rupaye")[0].canonical    # 'INR 2000..INR 3000'
kitna.parse("5 baje")[0].candidates                     # 05:00 and 17:00, ambiguous=True
kitna.parse("mujhe paani de do")                        # []  ("do" is the verb)
kitna.parse("no one came")                              # []  (English "one" needs an anchor)
kitna.parse_date("26 January", date(2026, 11, 12), prefer="future").canonical   # '2027-01-26'
```

`kal` with no tense cue is returned as both yesterday and tomorrow; nothing is
picked silently. Confidence is an ordering, not a probability.

### What has been checked, and what has not

| Check | Result | Source |
|---|---|---|
| Parser vs. its author's own draft cases, settled rules | 322 of 322 match | `results/phase2/golden_summary.json` |
| Same, cases resting on rules still awaiting a native speaker (reported separately) | 36 of 36 match | same file |
| Test suite | 435 passed, 1 expected failure (a pinned known limitation) | `results/phase2/test_run.txt` |
| Native-speaker review of rules, spellings or cases | **not done** | `docs/review/` |
| Accuracy on a held-out set written by native speakers | **not measured; set does not exist** | `docs/heldout_protocol.md` |

The first two rows are a self-consistency check. They are not accuracy.

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
| `docs/limitations.md` | Behaviours that may surprise you; what the numbers do not mean |
| `docs/heldout_protocol.md` | How the first real accuracy number will be produced |
| `src/kitna/data/policy.tsv` | Every contested rule, editable without touching code |
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
