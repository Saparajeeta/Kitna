# Native-speaker review log

## Aparajeeta Singh — 2026-11-12

- Permission to record name publicly: explicitly given in the project conversation.
- Languages: Hindi (native and fluent), English (fluent).
- Regional background: Uttar Pradesh. The reviewer describes her Hindi/Hinglish as common
  across India; this review does not establish agreement across regions.
- Scope: all 362 draft parser cases. Original submitted CSV preserved unchanged as
  `phase1_cases_review_AS.csv`: 360 OK, 2 wrong, including comments on two OK cases.
- This is one speaker's review of existing, AI-drafted development cases, not blind
  evaluation, inter-annotator agreement, or an accuracy measurement.

### Explicit follow-up decisions

- **Q7 / DAT-029:** `agle shanivaar` on Thursday 12 November 2026 may refer to
  14 or 21 November. Keep both readings and ask the user to clarify. Policy
  `weekday.agle=flag` replaces `next_occurrence`.
- **Q9 / FRA-043:** recognise nonstandard `saade ek` as 1.5, with a warning and
  reduced confidence. Standard wording is `dedh`. This permission is specific to
  `saade ek`; it does not extend to `saade do` or bare `saade`.
- **Q11 / DAT-072:** bare `kal` stays ambiguous by default. The reviewer accepted
  that an explicit developer option `prefer="future"` requests the future reading.
  The submitted wrong verdict is retained in the original CSV; this follow-up
  clarifies that no parser change is required for that case.
- **Q12 / NUM-097:** `ek baar` means "once / one time". Keep frequency extraction
  outside the current scope; no standalone quantity is extracted.

### What this does not settle

The OK verdicts record acceptance of the displayed examples, not explicit answers to
all general policy questions. No separate review of the Hindi explanatory text has
been submitted. Further speakers and regional feedback are still welcome. Cases retain
`draft` status and existing `review` tags until policy-level review is consolidated;
the CSV and this log record this first completed review independently of that status.

The generated working CSV may change after fixes; the submitted `_AS.csv` must not
be regenerated or overwritten.
