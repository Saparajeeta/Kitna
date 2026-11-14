# Guideline for annotators (second labels)

*This guideline was drafted by an AI assistant. If a rule here reads wrong to
you as a speaker, say so in the `comment` column: that is exactly the feedback
the project needs.*

You are checking whether the "right answer" stored for each sentence is what a
speaker would actually mean. You do this **without seeing the stored answer**.
Please do not open `bench/items/`, do not run the Kitna parser on the sentences,
and do not compare notes with the other annotator until both sheets are done.

## What you get

A file `labels_<your id>.csv`. Open it in any spreadsheet program. Each row is
one sentence a user might type to an assistant.

| Column | Meaning | Who fills it |
|---|---|---|
| `item_id`, `variant` | Identifier; `variant` is english, roman or devanagari | already filled |
| `now` | The date and time at which the user is speaking | already filled |
| `utterance` | What the user typed | already filled |
| `tools` | The actions the assistant can take, with their argument names | already filled |
| `behavior (call / clarify / abstain)` | What a careful assistant should do | **you** |
| `tool` | Which tool, if `call` | **you** |
| `arguments (name=value; name=value)` | The values, if `call` | **you** |
| `unsure_about` | Argument names you were not sure of | you, optional |
| `comment` | Anything odd: unnatural wording, two readings, a typo | you, optional |

## Choosing the behavior

- **call**: the sentence asks for one of the listed actions and gives every
  value needed, with one clear reading.
- **clarify**: the sentence asks for a listed action, but a needed value is
  missing or has more than one reasonable reading and nothing in the sentence
  settles it. Example of the kind of thing meant: a time with no morning or
  evening word and no other hint. Leave `tool` and `arguments` empty.
- **abstain**: none of the listed actions fits (small talk, a question about
  something else). Leave `tool` and `arguments` empty.

If you would personally just assume a reading (for instance, that a doctor's
appointment at a bare hour is in the daytime), write `call` with that reading
and name the argument in `unsure_about`. We want your natural judgement, not a
rule applied mechanically.

## Writing the values

Write `name=value` pairs separated by `;`, using the argument names shown in
the `tools` column.

- **Amounts**: plain digits, no commas: `amount=250000`.
- **Dates**: `YYYY-MM-DD`, worked out from the `now` column: `date=2026-11-13`.
- **Times**: 24-hour `HH:MM`: `time=17:00`.
- **Date and time together**: `YYYY-MM-DDTHH:MM`.
- **Durations**: minutes or hours in plain words is fine (`duration=2 hours 30 minutes`).
- **Names and other text**: as written in the sentence.
- Leave out arguments the sentence does not mention.

## Things to keep in mind

- Label each row on its own. The three variants of a scenario are meant to say
  the same thing, but if one of them does not, label what *that* sentence says
  and add a comment.
- Tense and context matter for words that can point both ways in time. Use the
  whole sentence.
- If a sentence is something nobody would type, say so in `comment`. Unnatural
  sentences are removed or rewritten; that is a useful result, not a failure.
- There is no target agreement score to hit. Disagreements are kept and
  reported.

## Afterwards

The owner runs `scripts/bench.py agreement` on the two sheets. It writes
`agreement.json` (Cohen's kappa for behavior, tool and each argument kind) and
`disagreements.csv`. Disagreements are then discussed with both annotators
present, and each one ends as: stored answer corrected, sentence rewritten,
scenario moved to clarify, or scenario dropped. The outcome of each is recorded.
