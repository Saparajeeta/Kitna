# Held-out set protocol (for the first real accuracy number)

The draft golden cases cannot give an accuracy figure: their author also wrote
the parser. The accuracy number will come from a held-out set that follows these
rules. **The set does not exist yet.**

1. **Who writes it.** Native Hindi/Hinglish speakers, not the parser's author and
   not an AI model.
2. **Blind.** Writers must not have run the parser, read its tests or seen the
   spelling tables before writing. They get only `docs/review/README.md`-style
   instructions and the list of kinds (number, money, time, duration, date).
3. **Content.** Each writer types expressions the way they normally would, with
   the value they mean, for a stated "today" and "now". Target: 150-200 items
   over at least two writers. All names and numbers are made up.
4. **Second label.** A different speaker labels each item's value without seeing
   the first label. Disagreements are kept and reported, not silently resolved.
5. **Frozen split.** The file is committed once as `tests/heldout/v1.jsonl`
   together with its SHA-256 in `tests/heldout/v1.sha256`. It is never edited.
   Corrections go into a new version (`v2`) with a note; old results stay.
6. **Never tuned on.** No parser rule, table entry or policy value may be changed
   because of a held-out item. Failures are reported as they are. New test cases
   inspired by failures go into the development set with different wording.
7. **Reporting.** One table: items, exact-value matches, flagged-ambiguous where
   the writer marked ambiguity, wrong values, misses; with Wilson intervals,
   split by kind and by script. Run date, kitna version and policy version are
   stated. The development-set figure is never presented as accuracy.

The parser's test suite does not read `tests/heldout/`; a single script will,
and its output goes to `results/`.

## File format and commands

The tooling for rules 5 to 7 exists and is tested on temporary files; it has
never been run on a real set, because none exists.

One JSON object per line in `tests/heldout/v1.jsonl`:

```json
{"id": "h1-001", "text": "…", "kind": "money", "base": "2026-11-12T10:00",
 "expected": "INR 250000", "writer_id": "w01", "provenance": "human_written"}
```

- `kind` is one of number, money, time, duration, date, datetime.
- `expected` uses the canonical strings listed in `docs/api.md`. When the
  writer says two readings are both possible, join them with ` | `, for example `05:00 | 17:00` (order does not matter).
- `provenance` must be `human_written`; freezing refuses anything else.

```bash
python scripts/bench.py heldout freeze v1   # once; refuses fewer than 150 items or a second freeze
python scripts/bench.py heldout check       # run in CI and pre-commit; fails if a frozen file changed
python scripts/bench.py heldout score v1    # writes results/heldout/v1_kitna-<version>.json
```

`score` counts four outcomes per item (exact, ambiguity flagged as the writer
expected, wrong, miss) with Wilson intervals, overall and by kind and script.
It compares only the first result of the requested kind, so an item whose
sentence holds two quantities of one kind should be split into two items.
