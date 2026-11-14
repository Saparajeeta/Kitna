---
title: "[Working title] What does 'kal dhai lakh bhej dena' mean to a tool-calling model?"
published: false
tags: python, nlp, llm, opensource
---

<!-- DRAFT, AI-written, not published. Fill every [bracket] from results/ and list it in docs/claims_checklist.md. -->

## The problem

A lot of people in India type Hindi in English letters and mix in English. Requests to an
assistant look like "Ramesh ko kal dhai lakh bhej dena" or "kal subah saade paanch baje cab
book kar do". To call a tool correctly, a model has to turn those into exact arguments: an
amount in rupees, a date, a time.

Three things make that harder than it looks:

- **Fraction idioms.** "dhai", "dedh", "saade teen", "paune do" combine with "sau",
  "hazaar", "lakh", "crore".
- **Words with two meanings.** "kal" is yesterday or tomorrow; "5 baje" is morning or
  evening. Sometimes the sentence settles it, sometimes it does not.
- **No standard spelling.** "hazaar", "hajar", "hzr".

## What I checked first

Before building anything I looked at what exists (details and caveats in
`docs/related_work.md`): a machine-translated Hindi version of a function-calling
benchmark, an ordering benchmark with Hinglish scenarios, and general number and date
parsers with Hindi support in Devanagari. I did not find a library for Romanized Hindi
quantities with fraction idioms and explicit ambiguity, or a speaker-written, three-script
tool-calling set. That is a statement about what I found, not a claim to be first.

## Part one: the parser

- Rule-based, no model, no dependencies.
- Spellings and every contested rule live in plain tables, so a native speaker can change a
  decision without touching code.
- Ambiguity is returned, not resolved: `value` is empty and every candidate is listed.

```python
import kitna
kitna.parse("dhai lakh")[0].value          # 250000
kitna.parse("5 baje")[0].candidates        # 05:00 and 17:00
```

How good is it? [Held-out result: accuracy with interval, number of items, who wrote them,
link to the results file. If the held-out set does not exist yet, say exactly that: the only
check so far is agreement with cases the same AI drafted, which is a self-consistency check,
not accuracy.]

## Part two: the benchmark

- [N scenarios] in five domains, each in Devanagari, Roman Hinglish and English.
- Roman Hinglish lines written by [N writers] native speakers from neutral briefs. Tool
  schemas, gold arguments and the other two variants were AI-drafted and are marked so.
- [N annotators] other speakers labelled the arguments independently; agreement was
  [kappa] ([link to agreement file]).
- Some items are deliberately ambiguous (the right move is to ask) and some need no tool.

## Results

[Table copied from results/bench/<run>/summary.md, with model version and run date per row.]

[One paragraph on the English-versus-Hinglish comparison, using the paired test from the
analysis plan. If every model is near the ceiling, say so plainly.]

[One paragraph on the ablation: did giving the model the parser's reading help, hurt, or
make no measurable difference?]

## What went wrong along the way

[Honest notes: rules that turned out wrong after native-speaker review, items that had to be
dropped, anything the analysis plan had to amend.]

## Limits

Small set, few writers, synthetic requests, AI-drafted English and Devanagari lines, a
grader that depends on the parser. Full list in the dataset card.

## Try it

[Install line, once a release exists.] Repository: [link]. If you speak Hindi, the open
questions page is where help matters most.
