# Kitna benchmark (in construction)

Tool-calling requests in Indian contexts, each written three ways: Devanagari
Hindi, Romanized Hinglish and English. The question it is built to answer: do
models fill tool arguments as well from Hinglish as from English?

**State today.** The tooling works end to end on a mock model. There is no
benchmark yet: the Roman Hinglish lines must be written by native speakers and
the labels checked by others. No model has been run. See "What exists" below.

Licence: benchmark data CC BY 4.0 (`LICENSE-DATA.md`); code Apache-2.0.

## What exists

| File | What | Who wrote it |
|---|---|---|
| `schema/item.schema.json` | JSON Schema for one item | - |
| `tools.json` | 15 tool definitions, 3 per domain | AI-drafted |
| `items/seed_v0.jsonl` | 40 scenarios x 3 variants, for testing the pipeline only | AI-drafted, all three variants, `provenance: ai_drafted` |
| `authoring/scenarios_v1_draft.jsonl` | 160 scenario drafts for the real benchmark: tools, gold call, English line, Devanagari line, writer brief. **No Roman line.** | AI-drafted |
| `authoring/guideline.md`, `template.csv`, `worked_examples.md` | Kit for the human writers | AI-drafted instructions |
| `items/dev_v1.jsonl` | The benchmark | **does not exist yet** |
| `models.example.yaml`, `models.mock.yaml` | Model list template; offline mock list | - |
| `kitna_bench/` | Validator, authoring import, annotation tools, harness, grader, statistics, reports | - |

The seed set is never reported as benchmark results. It was written by the same
AI that wrote the parser, so agreement between them shows nothing.

## Item format

One JSON object per line; one line per language variant. A scenario is three
lines sharing a `scenario_id`.

| Field | Meaning |
|---|---|
| `id`, `scenario_id` | `<scenario_id>-<deva|roman|en>` |
| `split` | `seed` (AI-drafted pipeline test), `dev`, `test` |
| `domain` | `payments`, `travel`, `reminders`, `shopping`, `support` |
| `variant` | `devanagari`, `roman`, `english` |
| `utterance` | What the user says |
| `now` | The date and time the model is told it is (IST) |
| `tools` | 1-3 tool schemas. Each parameter has `x-kitna-kind` (how it is graded) and optionally `x-graded: false` (free text, not scored). The `x-` fields are not sent to the model. |
| `gold.tool` | Tool to call; `null` on negative items |
| `gold.arguments` | Canonical values, as strings, for every argument the utterance fixes |
| `gold.aliases` | Other accepted spellings of names and places |
| `phenomena` | Tags such as `fraction_value`, `kal`, `bare_hour`, `negative` |
| `ambiguous`, `expected_behavior`, `clarify_about` | `call`, `clarify` (ask, do not guess; lists which arguments) or `abstain` (no tool) |
| `provenance`, `author_id` | `ai_drafted` + `ai:<name>`, or `human_written` + writer id `w01` |
| `labels` | Independent labels from annotators (`a01`, ...) who did not see the gold |

Canonical values: numbers and rupee amounts as plain digits (`250000`), dates
`YYYY-MM-DD`, times `HH:MM`, date-times `YYYY-MM-DDTHH:MM`, durations ISO 8601
(`PT1H30M`), names in English letters.

The validator also enforces: all three variants per scenario with the same gold
(unless tagged `variant_specific_gold`), gold arguments exist in the tool and
are canonical, no Devanagari in Roman lines, nothing that looks like a real
phone number, UPI ID or URL, seed split is AI-only, at most 200 non-seed
scenarios.

## Commands

Install once: `pip install -e ".[dev,bench]"`.

```bash
python scripts/bench.py validate bench/items/seed_v0.jsonl     # schema + cross-row rules
python scripts/bench.py writer-sheets --writers w01 w02 w03    # one CSV per writer
python scripts/bench.py import --sheets bench/authoring/sheets/writer_*.csv
python scripts/bench.py label-sheets --items bench/items/dev_v1.jsonl --annotators a01 a02
python scripts/bench.py agreement --items bench/items/dev_v1.jsonl \
    --a bench/annotation/labels_a01.csv --b bench/annotation/labels_a02.csv
python scripts/bench.py run --models bench/models.mock.yaml    # offline pipeline check
python scripts/bench.py plan --models bench/models.yaml --items bench/items/dev_v1.jsonl
python scripts/bench.py run  --models bench/models.yaml --items bench/items/dev_v1.jsonl --max-cost-usd 5
python scripts/bench.py leaderboard
```

`run` prints the call count and a cost estimate, asks for a typed `yes` before
contacting any real endpoint, stops at the cost cap, saves every raw response,
and continues where it stopped when run again with the same `--out`.

## Human steps, in order

1. **Writers** (you and friends, native speakers): fill the `roman_utterance`
   column of your sheet. Read `authoring/guideline.md` first. Then
   `bench.py import`.
2. **Annotators** (at least two *other* native speakers, who have not seen the
   gold values): read `authoring/annotation_guideline.md`, fill
   `labels_a01.csv` / `labels_a02.csv`. Then
   `bench.py agreement`, and settle `disagreements.csv` together.
3. Fix or drop scenarios where the gold was wrong or people could not agree.
4. Only then: `bench.py run` with real models.

Separate from this benchmark: the parser's held-out accuracy set
(`docs/heldout_protocol.md`, `bench.py heldout freeze|check|score`).
