# Benchmark methodology

!!! note "The benchmark does not exist yet, and no model has been run"
    Built and tested offline: item schema and validator, an AI-drafted seed set, the
    authoring kit, annotation tools, the harness, grader, statistics and reports.
    **Not done:** the human-written Roman Hinglish lines, the independent labels, and
    every model run. There are no results.

## Question

How often do LLMs fill tool-call arguments correctly when the user writes in Romanized
Hinglish or Devanagari Hindi, compared with the same request in English?

## Items

- Target 150-200 scenarios in five domains: payments and bills, travel booking, reminders
  and calendar, shopping and orders, customer support. 160 scenario drafts exist.
- Each scenario has three variants: Devanagari, Romanized Hinglish, English (the control).
- Three tools are offered per item, with Indian-context parameters (rupee amounts, IST
  times, Indian cities). The same tool schemas are used for all three variants, so that the
  comparison isolates the language of the request.
- Includes negative items (no tool should be called) and ambiguity items (the right
  behaviour is to ask). Both are scored separately from ordinary items.
- Everything is synthetic. Nothing is copied or translated from BFCL, BFCL-Hi or any other
  dataset. The validator rejects anything that looks like a phone number, UPI ID or URL.

Format, fields and commands: `bench/README.md` in the repository.

## Who writes what

| Part | Author | Recorded as |
|---|---|---|
| Roman Hinglish utterances | native speakers, from neutral briefs, in their own typing style | `provenance: human_written` |
| Tool schemas, gold arguments, Devanagari and English variants, briefs | AI-drafted | `provenance: ai_drafted` |
| Independent labels of tool and arguments | at least two further native speakers | `labels` |

Writers see only a brief ("Payee: Ramesh. Amount: ₹2,50,000."), never the AI's English or
Devanagari line. The 40-scenario seed set is AI-drafted in all variants, exists to test the
pipeline, and is never reported.

## Labels and agreement

Annotators get sheets without gold values. Agreement is reported as Cohen's kappa and
percent agreement for the behaviour (call / ask / no tool), the tool, and argument values
per argument type and overall, after normalising values (so `2.5 lakh` and `250000` are the
same label). Disagreements are listed for adjudication. Annotator count: `[TBD]`. Kappa:
`[TBD]`.

## Running models

One command, run by the project owner: `python scripts/bench.py run --models
bench/models.yaml --items bench/items/dev_v1.jsonl --max-cost-usd N`. Any
OpenAI-compatible endpoint works (hosted APIs, Ollama, vLLM). Model names are never
hardcoded. The harness prints the call count and a cost estimate, requires a typed
confirmation, stops at the cost cap, retries with backoff, saves raw responses and resumes.

## Grading, statistics, ablation, kill criterion

Fixed in advance in the [analysis plan](analysis_plan.md).

## Known threats to validity

- The grader uses the parser under development; a parser bug can mis-grade. A strict
  grader column and a manual-review sample are produced for every run.
- AI-drafted, templated English and Devanagari lines are more regular than human text, so
  "language" is partly confounded with "who wrote it".
- Scenarios come from tables of names, amounts and times; some combinations are unrealistic.
- Few writers from few regions: `[TBD: writer count and regions]`.
- "Asked a question" is detected by a question mark.
