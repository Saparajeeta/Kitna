# Ambiguity handling

Kitna's rule: **never pick silently.** If an expression has more than one
reading and nothing in the sentence settles it, the result has
`ambiguous=True`, `value=None` and every reading in `candidates`.

## What is flagged

| Expression | Why | Candidates (today = Thu 12 Nov 2026) |
|---|---|---|
| `kal`, `parso`, `narso` | the same word means past and future | `2026-11-11`, `2026-11-13` |
| `5 baje` | no morning/evening word | `05:00`, `17:00` |
| `12 baje` | noon or midnight | `00:00`, `12:00` |
| `9 se 11 baje` | same, for a range | `09:00..11:00`, `21:00..23:00` |
| `guruvaar` said on a Thursday | today or next week | `2026-11-12`, `2026-11-19` |
| `26 January` | no year | `2026-01-26`, `2027-01-26` |
| `20 tareekh ko` | no month | `2026-10-20`, `2026-11-20` |
| `kal shaam 5 baje` | time is fixed, day is not | `2026-11-11T17:00`, `2026-11-13T17:00` |

## What settles it

In this order:

1. **A strong tense cue in the same clause.** Future: `-unga/-ungi/-enge/-ega`,
   `hoga/hogi`, `jaana hai`. Past: `tha/thi`, `gaya`, `hua`, `kiya` ...
   Clauses are split on punctuation and `aur / lekin / phir`, so
   `kal gaya tha aur parso jaunga` gives yesterday and the day after tomorrow.
   Opposite cues in one clause cancel out and the result stays flagged.
2. **The expression's own default.** A bare weekday means the next one; with a
   past cue it means the most recent one.
3. **A weak cue**, with lowered confidence: an imperative request
   (`kal ka ticket book kar do`) or a bare present `hai` (`kal chhutti hai`).
4. **The caller's `prefer="future"` or `"past"`.**
5. Otherwise: flagged.

A day-part word (`subah`, `dopahar`, `shaam`, `raat`) or `am`/`pm` settles AM/PM.

## Other signals

- `approximate=True`: `lagbhag`, `kareeb`, `ke aaspaas`, `do teen`, `teen-chaar hazaar`.
- `confidence < 1`: a repaired spelling, an unusual form, or a weak cue. It is an
  ordering, not a probability.
- `notes`: plain-language reasons (`"no tense cue: direction unknown"`).
- `warnings`: the system clock was used because no `relative_base` was passed.

Which of these choices are still awaiting native speakers is listed in
[Decisions that need native-speaker input](open_questions.md).
