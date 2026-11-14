# Drafts for public posts

Nothing in this folder has been published. All of it was drafted by an AI.

Rules, enforced by `scripts/check_claims.py`:

- Numbers appear only as bracketed placeholders such as `[N items]` until a file in
  `results/` backs them. Replace a placeholder only with a value copied from that file, and
  add the claim to `docs/claims_checklist.md`.
- Agreement with the AI-drafted parser cases is a self-consistency check, not accuracy. Test
  counts, coverage, property tests and fuzzing stay out of headlines and resume lines.
- Do not say "first" or "only". Related work: `docs/related_work.md`.
