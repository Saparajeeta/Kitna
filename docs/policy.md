# The policy table

Linguistic choices that reasonable speakers could disagree about are not in the
code. They are rows in one file, `src/kitna/data/policy.tsv`, read by
`kitna.policy`. Changing an answer means editing the `value` column.

The table below is generated from that file (`scripts/gen_policy_docs.py`; the
test suite fails if it is out of date).

--8<-- "docs/_generated/policy_table.md"

## Reading the rows

- **`confidence.*`**: factors that lower a result's confidence. They order
  results; they are not probabilities and were not fitted to data.
- **`daypart.*`**: for each word, the clock hours (1-12) it usually goes with and
  whether they are AM or PM. Any other hour gets the `fallback` meridiem and the
  `confidence.odd_daypart` factor. Example: `raat` has `pm=7-11 am=12,1-4`, so
  `raat 9 baje` is 21:00, `raat 2 baje` is 02:00, `raat 12 baje` is 00:00.
- **`weekday.*`, `date.*`**: what to do when a weekday or a date is
  under-specified. `flag` means "return every candidate".
- **`cue.weak_*`**: words treated as weak hints that `kal` means tomorrow.
- **`number.ek_baar`**: switches the `ek baar` look-alike rule in `context.tsv`.

Allowed values are checked when the file is loaded; an unsupported value raises
`PolicyError` naming the row.

## Changing a rule

1. Edit the row's `value` in `policy.tsv`.
2. Update or add the affected golden cases (they are tagged `review`).
3. Run `python scripts/gen_policy_docs.py` and `pytest`.
4. In the pull request, say which open question this answers and who answered it.
