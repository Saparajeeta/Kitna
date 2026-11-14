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
