# Pipeline check with a mock adapter: NOT model results

This directory shows that the harness, grader, statistics and report run end to end
offline. The three "models" are `MockAdapter` instances that **read the gold answers**
and, for two of them, make scripted mistakes. The items are the AI-drafted seed set.

Nothing in here says anything about any real model, and no number in here may be
quoted anywhere. The leaderboard builder skips this directory.

Reproduce: `python scripts/bench.py run --models bench/models.mock.yaml --out /tmp/check`

`raw.jsonl` and `scored.jsonl` (one line per call) are not committed; the command above
recreates them.
