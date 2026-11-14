# Resume bullets (draft, AI-written)

<!-- Use a bullet only after every [bracket] is replaced from a file in results/ and the claim is in
     docs/claims_checklist.md. Drop any bullet you cannot back. Do not add test counts, coverage,
     property-test or fuzzing figures: they are not results. -->

- Built Kitna, an open-source Python library that converts Hinglish and Devanagari amounts,
  times and dates into exact values and reports ambiguity instead of guessing; measured
  [accuracy, with interval] on a held-out set of [N items] written by [N writers] native
  speakers.
- Designed and released a tool-calling benchmark of [N scenarios] in Devanagari, Romanized
  Hinglish and English across five domains, with Hinglish utterances written by [N writers]
  native speakers and independently labelled by [N annotators] (Cohen's kappa [kappa]).
- Evaluated [N models] tool-calling models with a pre-registered analysis plan (paired exact
  tests, multiple-comparison correction); found [finding, with effect size and interval, or
  "no measurable gap"].
- Wrote a resumable evaluation harness for any OpenAI-compatible endpoint with cost caps,
  saved raw outputs and a run manifest, so every reported figure traces to a results file.
- Ran a native-speaker review process for contested language rules, kept in a single data
  table so that [N decisions] were changed without code changes.
