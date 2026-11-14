# How to add a spelling

You do not need to know Python. The parser's vocabulary is a set of plain text
tables in `src/kitna/data/`.

## Example: you type "hazzar"

1. Open `src/kitna/data/scales.tsv`. Find the row for 1000:

    ```text
    1000	hi	hazaar hazar hajar hajaar हज़ार
    ```

2. Add your spelling at the end, after a space:

    ```text
    1000	hi	hazaar hazar hajar hajaar हज़ार hazzar
    ```

3. Open a pull request. That is all.

## Which file

| You want to add | File | Separator between spellings |
|---|---|---|
| a number 0-99 (`pachees`, `पच्चीस`) | `numbers_hi.tsv` | space |
| sau, hazaar, lakh, crore | `scales.tsv` | space |
| sawa, saade, dedh, dhai, paune | `fractions.tsv` | space |
| baje, subah, weekdays, months, kal/parso, tense cues | `time_words.tsv` | a pipe with spaces around it (phrases may contain spaces) |
| rupaye, lagbhag, tak, kam se kam | `markers.tsv` | a pipe with spaces around it |

## Rules

- Columns are separated by a TAB. Keep it.
- A spelling can belong to one value only. The tests fail otherwise.
- Devanagari is matched ignoring the nukta and chandrabindu/anusvara, so you do
  not need to add `हजार` if `हज़ार` is there.
- If your spelling is also a normal word (`saath` = "with", `bara` = "big"),
  say so in the pull request. It may need a rule in `context.tsv` so that it does
  not fire in ordinary sentences.
- Tell us where the spelling is used if it is regional.

## What happens to spellings that are not in the tables

They go through a repair step: repeated letters are collapsed (`hazzaar`), then
a one-letter difference is allowed for words of six letters or more. Repaired
matches get a lower confidence, and the repair can miss, so a listed spelling is
always better.
