# Changelog

## 0.1.0.dev0 (unreleased pre-alpha)

First development version. Not validated by native speakers; no accuracy claim.

- `parse`, `parse_number`, `parse_money`, `parse_time`, `parse_date`, CLI `kitna parse`.
- Numbers (Hindi 0-99 in Roman and Devanagari, sau/hazaar/lakh/crore/arab, English
  and mixed forms, Indian digit grouping, spoken digit sequences).
- Fraction idioms: sawa, saade, dedh, dhai, paune, paun, aadha, paav.
- Money: currency words and symbols, paise, ranges, tak, approximate markers.
- Time: baje / bajke / bajne mein, day-parts, am/pm, time ranges; durations.
- Dates: aaj/kal/parso/narso, weekdays, agle/pichhle, offsets, absolute dates,
  day-of-month, tense cues, `prefer`, `relative_base`; date + time as `datetime`.
- Ambiguous expressions return every candidate with `ambiguous=True`.
- All spellings and all contested rules are plain TSV files in `src/kitna/data/`.
- Output contract: `Result.to_dict()` with `schema_version` "1", described by
  `src/kitna/data/result.schema.json`. Any removed field or changed meaning bumps the version
  and gets an entry here.
- `Result.warnings`: a relative date or time resolved without `relative_base` carries a
  warning that the system clock was used. `parse(..., strict=True)` raises instead.
  `parse(..., now=callable)` replaces the clock (for tests).
- A lone English number word (`one`, `two`, `ten`) is ignored without a kind hint unless a
  scale, currency, unit or Hindi word is next to it.
- `ek baar` is now a policy row (`number.ek_baar`, open question Q12); behaviour unchanged.
- Docs: mkdocs site, policy and open-question tables generated from `policy.tsv`,
  quickstart examples executed by the tests. Project files: CONTRIBUTING, SECURITY,
  CODE_OF_CONDUCT, CITATION.cff, issue and pull-request templates.
