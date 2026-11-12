# Data tables

The tables the parser uses live in [`src/kitna/data/`](../src/kitna/data/) so that
they ship inside the installed package. They are plain tab-separated text files:

| File | What |
|---|---|
| `numbers_hi.tsv` | Hindi 0-99, Roman and Devanagari spellings |
| `numbers_en.tsv` | English number words |
| `scales.tsv` | sau, hazaar, lakh, crore, arab and English scales |
| `fractions.tsv` | sawa, saade, dedh, dhai, paune, paun, aadha, paav |
| `markers.tsv` | currency words, "about", "at least", "up to", range words |
| `context.tsv` | rules for look-alikes (`de do`, `ek baar`, `mere saath`) |

To add a spelling you actually type: open the file, find the row, add your
spelling at the end, open a pull request. No Python needed. `pytest` checks that
no spelling is listed under two different values.

All spellings are currently AI-drafted and awaiting native-speaker review.
