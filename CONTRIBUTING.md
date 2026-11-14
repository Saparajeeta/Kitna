# Contributing to Kitna

Thank you. The most valuable contributions right now do not need Python.

## 1. Add or correct a spelling (no code)

Every spelling the parser knows is a row in a plain text table under
[`src/kitna/data/`](src/kitna/data/). All current spellings were drafted by an
AI and are waiting for native speakers.

1. Find the table: `numbers_hi.tsv` (0-99), `scales.tsv` (sau, hazaar, lakh ...),
   `fractions.tsv` (sawa, saade ...), `time_words.tsv` (baje, subah, weekdays,
   months, tense cues), `markers.tsv` (rupaye, lagbhag, tak ...).
2. Find the row for the word and add your spelling at the end (a space between
   spellings in the number tables, ` | ` in `time_words.tsv` and `markers.tsv`).
3. Open a pull request using the "spelling" checklist. Say where the spelling is
   used if it is regional.

`pytest` rejects a spelling that is listed under two different values. If your
spelling is also an ordinary word (like `saath` = "with"), say so in the PR: it
may need a row in `context.tsv`.

## 2. Answer an open question

[docs/open_questions.md](docs/open_questions.md) lists rules that need a native
speaker (for example what `agle shanivaar` means on a Thursday). Open an issue
with the "native-speaker input" form. Each answer is one edited row in
`src/kitna/data/policy.tsv`.

## 3. Review parser cases

Follow [docs/review/README.md](docs/review/README.md). Reviews are recorded in
`docs/review/REVIEW_LOG.md` with who reviewed what and when; a case is only
marked `validated` after that.

## 4. Code

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pre-commit install          # optional
ruff check . && mypy && pytest
```

Rules:

- The core has zero runtime dependencies and makes no network calls.
- Functions are pure and deterministic. The only clock access is the documented
  default for `relative_base`.
- A contested linguistic choice goes into `policy.tsv`, not into code.
- Never return a guess for an ambiguous expression: return every candidate.
- Every change comes with a test. Any change to `Result.to_dict()` needs a
  changelog entry and, if a field is removed or changes meaning, a
  `RESULT_SCHEMA_VERSION` bump.
- Do not add, edit or look at `tests/heldout/` when changing the parser
  ([docs/heldout_protocol.md](docs/heldout_protocol.md)).
- No invented numbers. A figure in the README or docs must come from a file in
  `results/`.

## Review process

A maintainer reviews pull requests. Spelling and policy changes need a
native-speaker sign-off (the contributor's own, stated in the PR, is enough for
spellings they use themselves). Commit messages follow
[Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`,
`data:`, `docs:`, `test:`).

By contributing you agree that code is licensed Apache-2.0 and benchmark data
CC BY 4.0, and you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).
