# Limitations and behaviours that may surprise you

Everything here is true of version 0.1.0.dev0. Nothing in this project is an
accuracy claim yet: see [heldout_protocol.md](heldout_protocol.md).

## What the test numbers do and do not mean

- The golden cases in `tests/golden/draft_cases.jsonl` were drafted by the same
  AI agent that wrote the parser. The parser matching them shows it does what the
  draft says. It does not show the draft is right, and it is not accuracy.
- One non-native reviewer checked the arithmetic of the first 292 cases. No
  native speaker has reviewed any case or any spelling table.
- Coverage, property tests and fuzzing show the code is exercised and does not
  crash. They say nothing about whether real Hinglish is parsed correctly.

## Confidence is an ordering, not a probability

`confidence` ranks results: 1.0 means every step was an exact table match; a
lower value means a spelling repair, an unusual form or a weak cue was involved.
The values (0.85 for a repaired spelling, 0.6 for a one-edit repair, and so on)
are set in `src/kitna/data/policy.tsv`. They were chosen to order outcomes and
have not been calibrated against data. Do not read 0.85 as "85% likely correct".

## Hyphens: `10-15 hazaar` is exact, `das-pandrah hazaar` is approximate

- Digits joined by a hyphen are an exact range: `10-15 hazaar` = 10000..15000.
- Number **words** joined by a hyphen, or simply adjacent, are the Hindi idiom
  for "about": `das-pandrah hazaar`, `teen-chaar hazaar`, `do teen` come back
  with `approximate=True`.

## English number words need an anchor

Without a `kind` hint, a lone English number word (`one`, `two`, `ten`,
`hundred`) is ignored unless it sits next to a scale word (`two lakh`,
`two hundred`), a currency or unit word (`ten rupaye`, `ten din`), or a listed
Hindi word or any Devanagari word. So "no one came" gives nothing, and so does
"I have two options", which is a miss we accept: a false number is worse than a
missed one. With a hint (`parse_number("ten")`) the word always counts.

## Look-alike words

- `do`: the verb after a verb stem (`de do`, `kar do`) or at the end of a clause
  after an ordinary word (`chai do`); otherwise two. The rule list is short and
  will have gaps on real text.
- `saath`: 60 only next to digits, a scale word, a currency word or a hyphenated
  number (`pachaas-saath`). `pachaas saath` without a hyphen gives only 50
  (pinned as a known-limitation test).
- `ek baar`, `mere saat`: no number.

## Dates and times

- With no `relative_base`, the system clock is used and results depend on when
  you call.
- A date and an adjacent time merge into one `datetime`. `kal raat 12 baje`
  pairs each `kal` candidate with 00:00 of that calendar day; whether speakers
  mean the midnight that starts or ends that day is not modelled.
- Recurring expressions (`har somvaar`) and whole periods (`agle hafte`) return
  nothing.
- Tense cues are word lists and suffixes, scoped to a clause split on
  punctuation and `aur / lekin / phir`. `kal aur parso jaunga` leaves `kal`
  flagged, because the cue is in the other clause.
- A fractional month in a duration is counted as 30 days (`dedh mahina` =
  1 month 15 days).
- `dedh do ghante` is read as 1.5 and a 2-hour duration, not as a range of
  durations.
- IST is assumed; no time zones.

## Rules still awaiting a native speaker

Day-part hours, weak tense cues, `agle <weekday>`, dates with no year, `narso`,
and every spelling are provisional. They all live in
`src/kitna/data/policy.tsv` and the other tables, so a changed answer is a data
edit. Cases that depend on them are tagged `review` and are excluded from the
headline count in `results/phase2/golden_summary.json`.

## Coverage of the language

Standard Hindi number words and common Roman spellings only. No regional number
words, no other Indian languages, no units of measure, ordinals, percentages or
slang amounts.
