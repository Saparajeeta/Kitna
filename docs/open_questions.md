# Design decisions that need native-speaker input

Kitna was drafted by an AI. The choices below are provisional until native
Hindi/Hinglish speakers answer them. Each one is a row in
`src/kitna/data/policy.tsv`, so an answer is a one-line data change. Parser
cases that depend on them are tagged `review` and are kept out of headline
counts.

To answer: open an issue with the "Native-speaker input" form, or edit the row
and open a pull request.

--8<-- "docs/_generated/open_questions_table.md"

## Not a policy row, but just as open

| # | Question | Where the answer goes |
|---|---|---|
| Q10 | Which Roman spellings do you actually type? `hazaar/hajar`, `lakh/lac`, `baje/bje`, `chhe/che/chhah`, `saade/sade/sadhe`, `dhai/dhaai`, `paune/pone`; do you swap b/w/v? | the spelling tables: [how to add a spelling](add_spelling.md) |
| - | Are the tense-cue word lists right and complete? | `time_words.tsv`, rows starting `cue_` |
| - | Which look-alike words are missing (`do`, `saath`, `ek baar` are handled)? | `context.tsv` |

## Already decided (review round 1, by a non-native reviewer)

Q1 (`do se teen hazaar` = 2000-3000) and the current values of Q2, Q4, Q5, Q6,
Q8, Q9 came from one reviewer who is not a native speaker. They are recorded in
[review/round1_decisions.md](review/round1_decisions.md) and can still be
overturned by native speakers.
