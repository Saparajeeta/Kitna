---
# DRAFT dataset card. Not published. Every [TBD] must be replaced from a file in results/ before upload.
license: cc-by-4.0
language:
  - hi
  - en
pretty_name: Kitna tool-calling benchmark (Devanagari, Romanized Hinglish, English)
task_categories:
  - text-generation
tags:
  - function-calling
  - tool-use
  - hinglish
  - code-mixed
  - romanized-hindi
size_categories:
  - n<1K
---

# Kitna tool-calling benchmark

> **Draft card.** The dataset is not finished and is not published. Counts marked `[TBD]`
> do not exist yet.

## Summary

Short user requests to an assistant with tools, in Indian everyday contexts (payments,
travel, reminders, shopping, customer support). Each scenario is written three ways:
Devanagari Hindi, Romanized Hinglish and English. Each has a gold tool call with canonical
argument values, or is marked as needing a clarifying question, or as needing no tool.

It is meant to measure whether a model fills tool arguments (amounts such as "dhai lakh",
times such as "saade paanch baje", days such as "kal") as well from Hinglish as from English.

- Scenarios: `[TBD]` (target 150-200), three variants each
- Domains: 5
- Licence: CC BY 4.0
- Repository and code: https://github.com/Saparajeeta/Kitna

## Who wrote what

| Part | Written by | Marked in the data as |
|---|---|---|
| Roman Hinglish utterances | `[TBD: number]` native Hindi/Hinglish speakers, from neutral briefs, without AI tools | `provenance: human_written`, `author_id: w..` |
| Tool schemas | an AI model | file `tools.json` |
| Gold tool and arguments | drafted by an AI model, then checked against independent human labels | `gold` |
| English utterances | an AI model | `provenance: ai_drafted` |
| Devanagari utterances | an AI model | `provenance: ai_drafted` |
| Writer briefs | an AI model | not part of the items |

The AI-drafted parts were produced by an AI coding agent (Arena.ai Agent Mode) in
November 2026 and were not written by a native speaker.

A separate 40-scenario **seed** split is AI-drafted in all three variants. It exists to test
software and must not be used to report results.

## Annotation

- Annotators: `[TBD: number]` native speakers, none of whom wrote the utterance they labelled
  or saw the gold values.
- Share of items double-labelled: `[TBD]`
- Agreement (Cohen's kappa and percent agreement), per argument type and overall: `[TBD]`,
  source `results/annotation/agreement.json`
- Items changed or dropped after adjudication: `[TBD]`

## Format

JSON Lines, one object per language variant. Fields: `id`, `scenario_id`, `split`, `domain`,
`variant`, `utterance`, `now`, `tools`, `gold` (`tool`, `arguments`, `aliases`), `phenomena`,
`ambiguous`, `expected_behavior` (`call`, `clarify`, `abstain`), `clarify_about`,
`provenance`, `author_id`, `labels`. The JSON Schema is `bench/schema/item.schema.json` in
the repository.

## Intended uses

- Evaluating tool-calling (function-calling) models on code-mixed Hindi-English input.
- Comparing the three variants of the same scenario.
- Testing whether a system asks when a request is ambiguous.

## Out-of-scope uses

- Training or fine-tuning: the set is small and is an evaluation set.
- Claims about Hinglish or Hindi in general, about speech, or about other Indian languages.
- Claims about real banking, travel or support systems: tools and data are synthetic.
- Using the seed split, or any AI-drafted variant alone, as evidence of how people write.

## Limitations

- Small: `[TBD]` scenarios.
- Few writers (`[TBD]`), from `[TBD: regions]`; spelling and word choice reflect them.
- English and Devanagari lines are AI-drafted from templates and are more regular than human
  text. Differences between variants mix "language" with "who wrote it".
- Scenarios were generated from tables of names, amounts and times, so they are less varied
  than real requests, and some combinations are unrealistic.
- "Ambiguous" is a judgement. Items where annotators disagreed are documented, not hidden.
- Gold values assume one fixed "now" (Thursday 12 November 2026, 10:00 IST).
- The reference grader normalises values with the Kitna parser, which is itself pre-alpha.

## Personal and sensitive information

All names, amounts, order IDs and places are made up. The validator rejects anything that
looks like a phone number, UPI ID, e-mail address or URL. Writers are identified only by
codes.

## Results

None yet. `[TBD]`: link to a run directory under `results/bench/`.

## Citation

See `CITATION.cff` in the repository.
