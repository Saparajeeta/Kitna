# Analysis plan (version 1)

Written before any model was run on the benchmark. The commit that adds this
file is tagged `analysis-plan-v1`; every run manifest records the newest
`analysis-plan-v*` tag it could see. Changes after the first real run are
appended to section 10 with a date and a reason, and the plan gets a new tag.
Nothing here has been run; there are no results.

## 1. Questions

1. **Primary.** For each model, is per-item accuracy lower on the Romanized
   Hinglish variant than on the English variant of the same scenarios?
2. Same question for the Devanagari variant.
3. On ambiguity items, how often does a model ask instead of guessing?
4. On negative items, how often does a model call no tool?
5. **Ablation.** Does adding the Kitna parser's reading of the utterance to the
   prompt change per-item accuracy?

## 2. Data

- The benchmark file is `bench/items/dev_v1.jsonl` (name fixed once it exists):
  150-200 scenarios, three variants each. Roman lines written by native
  speakers; everything else AI-drafted and then label-checked by at least two
  further native speakers (`bench/README.md`).
- The 40-scenario seed set (`seed_v0.jsonl`) is AI-drafted end to end. Runs on it
  test the pipeline and are **never** reported as benchmark results.
- A scenario enters the cross-language comparison only if all three variants
  expect the same tool call. Scenarios tagged `variant_specific_gold` (Hindi
  `kal` with no English equivalent) are reported descriptively only.
- Items on which the two annotators disagree and adjudication fails are dropped
  before any model is run; the number dropped is reported.

## 3. Models and settings

- Chosen by the project owner in `bench/models.yaml` before the run; the list,
  model ids and version strings are copied into the manifest. No model is added
  or removed after seeing results without saying so in the report.
- One system prompt for all models and variants (`PROMPT_VERSION` in the
  manifest). Tools are passed through the provider's function-calling interface.
- Baseline: temperature 0, one sample (sample 0). All headline numbers use
  sample 0. Optional: three samples (sample 0 at temperature 0, samples 1-2 at
  0.7) to report run-to-run consistency as a secondary table.
- Seed `20261112` is sent where the endpoint accepts one and is used for the
  bootstrap and the review sample.

## 4. Scoring

- **Call items.** Correct means: the first tool call names the gold tool, every
  graded gold argument matches after normalisation, and no extra graded
  argument is supplied. Free-text arguments (titles) are not graded.
- **Normalisation.** A value in the machine format the schema asks for is
  compared directly. Otherwise it is passed through the Kitna parser with the
  item's "now"; an ambiguous or approximate parse earns no credit. A second
  column ("strict grader") shows accuracy without the Kitna fallback.
- **Per-argument accuracy**: matched graded gold arguments divided by all
  graded gold arguments on call items; arguments of a missing or wrong call
  count as wrong. Also split by argument kind.
- **Ambiguity items** (expected: ask). Scored separately. "Asked" = no tool call
  and the reply contains a question mark; "guessed" = any tool call.
- **Negative items** (expected: no tool). Scored separately. Correct = no tool
  call.
- The question-mark rule and the error-type classifier are heuristics. A seeded
  sample of 60 responses per run (`manual_review_sample.csv`) is re-judged by a
  person; the agreement rate is reported next to the automatic numbers.
- Failed requests (after retries) are re-run; any that still fail count as
  wrong and are listed.

## 5. Statistics

All with scipy / statsmodels / numpy (`bench/kitna_bench/stats.py`).

- Every proportion: 95% Wilson score interval.
- English vs. Roman and English vs. Devanagari, per model: exact (binomial)
  McNemar test on scenario pairs, two-sided, plus the accuracy difference with
  a 95% percentile bootstrap interval over scenarios (10,000 resamples).
- Multiple comparisons: Holm correction over the family "all models x {Roman,
  Devanagari}" at alpha = 0.05. The ablation family "all models x three
  variants" is corrected separately.
- No test is run on ambiguity or negative items (too few); rates and intervals
  only.
- Sample size. The drafted scenarios give about 110 paired call scenarios. In a
  simulation of a single, uncorrected test with 100 pairs, power reached 80%
  only at true differences of roughly 12 to 15 points, depending on how often
  only the Hindi variant is right
  ([results/planning/mcnemar_power.json](https://github.com/Saparajeeta/Kitna/blob/main/results/planning/mcnemar_power.json),
  made by `scripts/power_mcnemar.py`; assumptions are listed in the file). Holm
  correction lowers power further. Smaller differences will likely not reach
  significance; intervals are reported either way, and a non-significant result
  is not described as "no difference".

## 6. Ablation

Two conditions on identical items: `raw` (utterance only) and `kitna_hints`
(the system prompt also lists what the parser found, with every candidate when
it could not decide). Compared per model and variant with the paired tests of
section 5. The result is reported whichever way it goes. Known caveat, stated
with the result: the parser is weak on fully English sentences, so hints may
hurt the English variant.

## 7. Error analysis

Wrong call items get one type, first match in this order: wrong tool, wrong
scale (off by a power of ten), wrong date direction (past vs. future), AM/PM
(off by exactly 12 hours), fraction idiom (wrong number or time on an item
tagged with a fraction value), hallucinated argument, refusal, other. Counts per
model and variant; no significance tests.

## 8. Kill criterion

The ceiling is reached if, on the human-written benchmark, **every** evaluated
model has Roman-variant per-item accuracy of at least 95% on call items **and**
no English-vs-Roman difference is significant after Holm correction. If so, the
report says plainly that current models handle these tasks, and the project is
presented as a parser and grading tool rather than as evidence of a model
weakness. The report prints this section's verdict for every run.

## 9. What will not be claimed

- No ranking claim between two models unless their paired difference is
  significant after correction.
- No claim about Hinglish in general: a few writers, five domains, synthetic
  requests.
- Nothing from mock-adapter runs or from the seed set.
- Grader caveat: the grader uses the parser under development. Disagreements
  between the strict and the Kitna-normalised grader are listed for review.

## 10. Amendments

None.
