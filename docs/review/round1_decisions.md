# Review round 1 (received 2026-11-12)

**Reviewer:** one person, self-described as *not* a native speaker.
**What was checked:** arithmetic and calendar math on all 292 first-draft rows
(the 1-99 words, lakh/crore and fraction math, paune/sawa/saade times, every
date against base Thursday 2026-11-12). Result reported: no wrong expected values.
**What was not checked:** regional usage, everyday naturalness, typing habits.

Because of that, every case keeps `status: draft`. This is not native-speaker
validation and must not be described as such.

## Changes applied

- Q1-Q9 decisions as listed in `docs/taxonomy.md` section 4.
- `FRA-043 saade ek` changed from "1.5, low confidence" to a negative case.
- `DAT-029 agle shanivaar` changed from flagged to 2026-11-14 (Q7 lean; still tagged `review`).
- 53 cases added (345 total) for the gaps the reviewer listed: time ranges,
  relative time, date+time, weekdays with a past cue, per-clause cues, `kal tak`,
  homograph negatives, English plurals, mixed script and nukta forms,
  day-of-month without a month, reduplicated ranges, `prefer="future"`.
- New kind `datetime`; ranges allowed for time and date; `results` for
  sentences with several dates; `prefer` field on cases.

## Still needed from a native speaker

See `docs/taxonomy.md` section 5 (Q3b, Q7, Q9b, Q10, Q11, Q12, Q13) and
`docs/review/README.md` for the two-hour review route.
