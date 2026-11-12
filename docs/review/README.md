# Phase-1 review: how to mark up the cases

1. Read `docs/taxonomy.md`, answer the Open questions (Q1-Q10).
2. Open `phase1_cases_review.csv` (UTF-8, opens in Excel / Google Sheets). For each row fill:
   - `verdict`: `ok`, `wrong` (expected value is wrong), or `unnatural` (nobody says/types this);
   - `corrected_value` when wrong;
   - `reviewer_comment` for anything else, including spellings to add.
   Rows tagged `review` are the ones the author is least sure about; start there.
3. Send the file back (or commit it as `phase1_cases_review_<initials>.csv`).

After review the agent will apply corrections, set `status` to `validated` or
`rejected` per case, and record who reviewed what and when in
`docs/review/REVIEW_LOG.md`. Until that file exists, no case may be called
validated (enforced by `tests/test_golden_format.py`).

The canonical file is `tests/golden/draft_cases.jsonl`; regenerate the CSV with
`python scripts/validate_cases.py --export-csv docs/review/phase1_cases_review.csv`.
