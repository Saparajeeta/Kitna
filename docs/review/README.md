# How to review the cases (about two hours)

Who: a native Hindi/Hinglish speaker. The arithmetic was already checked in
round 1 (`round1_decisions.md`); spend the time on **naturalness, regional
usage and spelling**, not on the numbers.

1. Answer the open questions in `docs/taxonomy.md` section 5.
2. Open `phase1_cases_review.csv` (UTF-8; Excel or Google Sheets). Filter the
   `tags` column to rows containing any of `review`, `ambiguity`, `tense-cue`,
   `daypart`, `spelling`, `noise` (112 of 345 rows). For each, fill:
   - `verdict`: `ok`, `wrong` (expected value is wrong) or `unnatural` (nobody says or types this);
   - `corrected_value` when wrong;
   - `reviewer_comment`: anything else, especially spellings you would type instead.
3. Skim the remaining rows; mark only what looks off.
4. Send the file back, or commit it as `phase1_cases_review_<initials>.csv`.

After a native review, corrections are applied, each case gets
`status: validated` or `rejected`, and reviewer, date and scope go into
`docs/review/REVIEW_LOG.md`. Until that file exists no case may be marked
validated (enforced by `tests/test_golden_format.py`).

The canonical file is `tests/golden/draft_cases.jsonl`. Regenerate the CSV with
`python scripts/validate_cases.py --export-csv docs/review/phase1_cases_review.csv`.
