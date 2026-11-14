# Related work

Checked on 2026-11-12. This sandbox could reach only github.com and pypi.org, so
anything hosted elsewhere (Hugging Face, arXiv) was verified second-hand and is
marked as such. Nothing here is quoted from memory.

## Summary

| Project | Exists / last activity | What it covers | What it does not cover (relevant to Kitna) |
|---|---|---|---|
| **BFCL-Hi** (NVIDIA) | Dataset card read from the unmodified copy in `ananjaygoel/bfcl-hi-audit` (commit `7db0c0a`, 2026-10-25). Not checked directly on Hugging Face. | Hindi function-calling eval. The card calls it "the GCP-translated version of the English BFCL dataset", 2251 samples, CC-BY-4.0, labeling method "Not Applicable". | Devanagari only. Machine-translated, not authored in Hindi. Tasks are not Indian-context. No Romanized Hinglish. |
| **bfcl-hi-audit** | GitHub, last push 2026-10-25. | Audits translation damage in BFCL-Hi and builds a *Romanized Hinglish condition of BFCL* by rule-based romanisation plus restoring English spans. | Hinglish is derived mechanically from translated text, not written by speakers. Same US/global tasks, English schemas, exact-match English answer key. |
| **IndicOrderBench** | GitHub `Lingikaushikreddy/indicorderbench`, v0.1.1, last push 2026-10-19, Apache-2.0. | Multi-turn voice-ordering agents in Indian English **and Romanized Hinglish**; scores the committed order state. 42 scenario files in the starter pack. | One domain (food ordering). Quantities are small counts (`ek`, `do`, `teen`...). Its own review file says the Hinglish scenarios were written by a non-native author and are `unreviewed`. No Devanagari. No money/date/time normalisation. |
| **number-parser** (Zyte/Scrapinghub) | PyPI 0.3.2; GitHub last push 2026-10-03, BSD-3. | Number words to integers; Hindi supported in **Devanagari** (`language='hi'`). | No Romanized Hindi. No fraction idioms (ढाई, डेढ़, साढ़े...). No ambiguity or confidence output. |
| **dateparser** (Zyte/Scrapinghub) | PyPI 1.5.0; GitHub last push 2026-11-05, BSD-3. | Dates in 200+ locales incl. Hindi in **Devanagari** (months, weekdays, आज/कल/परसों, some relative forms). | No Romanized Hindi. कल and परसों are each mapped to one fixed direction. No बजे / सुबह-शाम time handling. |

## What Kitna can and cannot claim

Romanized Hinglish **is** covered by existing work: IndicOrderBench evaluates
agents on Romanized Hinglish, and bfcl-hi-audit publishes a Hinglish condition
of BFCL. (An early version of the project brief said otherwise; the project
owner withdrew that wording.) The claim Kitna can defend is narrower:

- no existing *tool-calling* benchmark we found has speaker-authored items in
  all three of Devanagari, Romanized Hinglish and English, with Indian-context
  schemas and gold arguments that depend on quantity/money/time/date
  normalisation;
- no existing *library* we found parses Romanized Hindi quantities, fraction
  idioms and kal/parso ambiguity into canonical values.

"We found" means a GitHub repository search plus PyPI on the date above. It is
not a literature review; Hugging Face and arXiv were not searchable from here.
`[TBD: repeat the search on Hugging Face Hub and arXiv before any public claim]`

## What the two parsers actually do on our input space

We ran both libraries on the Kitna draft cases (`scripts/probe_baselines.py`,
raw output in `results/phase1/`). Read this with care: the cases were written
to target the gap, they are **unreviewed drafts**, and both libraries were run
with near-default settings. This is a coverage check, not a quality ranking.

| Library (version) | Cases in scope | Correct | No parse | Other |
|---|---|---|---|---|
| number-parser 0.3.2 | 105 exact-integer number cases | 14 | 91 | - |
| ...Roman script | 82 | 2 (`fifty thousand`, `ten`: English) | 80 | - |
| ...Devanagari | 18 | 12 | 6 | - |
| ...mixed script | 1 (`५ lakh`) | 0 | 1 | - |
| ...digits only | 4 | 0 | 4 | - |
| dateparser 1.5.0 | 116 date, time and date-time cases | 10 | 102 | 3 single answers on cases we label ambiguous, 1 wrong |
| ...Roman script | 91 | 3 (all English-only inputs) | 87 | 1 single answer (`26 January`) |
| ...Devanagari | 21 | 3 | 15 | 2 single answers (कल, परसों), 1 wrong |
| ...digits only | 4 | 4 | 0 | - |

Out of scope for the probe, and so not counted: negatives, ranges, multi-result
cases, and cases that use Kitna's `prefer` option or run without a kind hint.
The case file has 358 cases; 221 were in scope.

Notes that keep this fair:

- number-parser's Devanagari misses were the fraction idioms (ढाई लाख, डेढ़ सौ,
  साढ़े सात हज़ार), one spelling (निन्यानवे) and one digit+word mix (5 लाख).
  Grouped digit strings are outside what `parse_number` is meant for.
- dateparser's one "wrong" (शुक्रवार को gave the previous Friday) is its default
  `PREFER_DATES_FROM` behaviour and can be changed by a setting. Its answers for
  कल (tomorrow) and परसों (two days ago) come from fixed entries in its Hindi
  data file; a caller has no signal that the other reading exists.
- Only `dateparser.parse` was tested, not `dateparser.search`.

## Optional pretrained components (not used in the core)

- **AI4Bharat IndicXlit** (transliteration): repo README states "The IndicXlit
  code (and models) are released under the MIT License"; PyPI package
  `ai4bharat-transliteration` 1.1.3, MIT. Last repo push 2023-10-13, so it is
  the most recent AI4Bharat transliteration *repository* we found on GitHub, but
  we could not check Hugging Face for a newer model. `[TBD: confirm]`
- **Whisper-family ASR**: not looked up yet. `[TBD in phase 5]`

## How Kitna differs, in one paragraph

Kitna's library is a deterministic parser for the Romanized and Devanagari
quantity expressions the two parsers above do not handle, and it reports
ambiguity instead of choosing. Kitna's benchmark uses that parser as the grader
for original, speaker-reviewed tool-calling items in three scripts. Neither
part replaces the projects above: BFCL-Hi is far larger, IndicOrderBench tests
live multi-turn agents, and dateparser covers many more languages and formats.
