# Benchmark methodology (planned)

!!! note "Nothing on this page has been run"
    The benchmark, the harness and the analysis do not exist yet. This page
    states the plan so it can be criticised before any model is evaluated.
    There are no results; every figure is `[TBD]`.

## Question

How often do LLMs fill tool-call arguments correctly when the user writes in
Romanized Hinglish or Devanagari Hindi, compared with the same request in
English?

## Items

- 150-200 items in five domains: money transfer and bill pay, travel booking,
  reminders and calendar, shopping and orders, customer support.
- Each item exists in three variants: Devanagari, Romanized Hinglish, English
  (the control).
- 1-3 tools per item with Indian-context parameters (rupee amounts, IST times,
  PIN codes, Indian cities).
- Includes negative items (no tool should be called) and ambiguous items (the
  right behaviour is to ask).
- All names, numbers and IDs are synthetic. Nothing is copied or translated from
  BFCL, BFCL-Hi or any other dataset.

## Who writes what

| Part | Author | Recorded as |
|---|---|---|
| Roman Hinglish utterances | native speakers, in their own typing style | `provenance: human_written` |
| Tool schemas, gold arguments, Devanagari and English variants | AI-drafted, then human-checked | `provenance: ai_drafted` |
| Gold-argument labels | at least two further native speakers, independently | `labels` |

A 40-item AI-drafted seed set exists only to test the pipeline and is never
reported as benchmark results.

## Labels and agreement

Double labelling of a subset; Cohen's kappa per argument type and overall, with
percent agreement; disagreements adjudicated and listed. Annotator count:
`[TBD]`. Kappa: `[TBD]`.

## Grading

Tool-name match, then argument match after normalising both the gold value and
the model's value with Kitna. Per-argument and per-item accuracy. Ambiguous
items are scored separately (did the model ask or guess?), as is abstention on
negative items.

## Statistics

Wilson intervals per condition; paired McNemar (or paired bootstrap) on
identical items for English vs. Hinglish; Holm correction across models; using
scipy/statsmodels. The analysis plan will be committed and tagged
(`docs/analysis_plan.md`) before any real run.

## Ablation

Raw utterance vs. utterance plus Kitna-parsed values passed to the model.
Whichever direction the effect goes is reported.

## Kill criterion

If every frontier model is near ceiling on the Hinglish variant, the report will
say so plainly and the project will be reframed as a deterministic parser and
grader.

## Known threats to validity

- The grader is the parser under development: a parser bug can mis-grade. Grader
  disagreements will be sampled for manual review.
- AI-drafted Devanagari and English variants may be more regular than human
  text.
- A few writers from a few regions: `[TBD: writer count and regions]`.
