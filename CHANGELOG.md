# Changelog

## 0.1.0.dev0 (unreleased pre-alpha)

First development version. Not validated by native speakers; no accuracy claim.

- `parse`, `parse_number`, `parse_money`, `parse_time`, `parse_date`, CLI `kitna parse`.
- Numbers (Hindi 0-99 in Roman and Devanagari, sau/hazaar/lakh/crore/arab, English
  and mixed forms, Indian digit grouping, spoken digit sequences).
- Fraction idioms: sawa, saade, dedh, dhai, paune, paun, aadha, paav.
- Money: currency words and symbols, paise, ranges, tak, approximate markers.
- Time: baje / bajke / bajne mein, day-parts, am/pm, time ranges; durations.
- Dates: aaj/kal/parso/narso, weekdays, agle/pichhle, offsets, absolute dates,
  day-of-month, tense cues, `prefer`, `relative_base`; date + time as `datetime`.
- Ambiguous expressions return every candidate with `ambiguous=True`.
- All spellings and all contested rules are plain TSV files in `src/kitna/data/`.
- Output contract: `Result.to_dict()` with `schema_version` "1", described by
  `src/kitna/data/result.schema.json`. Any removed field or changed meaning bumps the version
  and gets an entry here.
- `Result.warnings`: a relative date or time resolved without `relative_base` carries a
  warning that the system clock was used. `parse(..., strict=True)` raises instead.
  `parse(..., now=callable)` replaces the clock (for tests).
- A lone English number word (`one`, `two`, `ten`) is ignored without a kind hint unless a
  scale, currency, unit or Hindi word is next to it.
- `ek baar` is now a policy row (`number.ek_baar`, open question Q12); behaviour unchanged.
- Docs: mkdocs site, policy and open-question tables generated from `policy.tsv`,
  quickstart examples executed by the tests. Project files: CONTRIBUTING, SECURITY,
  CODE_OF_CONDUCT, CITATION.cff, issue and pull-request templates.
- English `day after tomorrow` / `day before yesterday` are read as two days away (were read as
  `tomorrow` / `yesterday`).
- Context resolver: with a `relative_base` that has a time, `aaj 2 baje ... karungi` said at 10:00
  is read as 14:00 (02:00 has passed, the verb is future). Policy rows `context.today_future`
  (on), `context.today_past` (off), `confidence.context_time`; open question Q13. **Behaviour
  change:** such phrases were returned as ambiguous before.
- `kitna.postprocess_tool_call`: confirms, corrects or flags the numeric, date, time and duration
  arguments of an OpenAI-style or Anthropic-style tool call against the user's words.
- `kitna serve` (extra `serve`): local FastAPI service with `POST /parse`,
  `POST /tool-call/check`, `GET /health` and an OpenAPI page. Dockerfile (not yet built by anyone).
- Demo rebuilt: highlighted message, ambiguity as a choice, "why" in English and Hindi, action
  preview, live comparison, feedback, share link, reviewer page at `/review`, optional voice tab.

## Benchmark tooling (not part of the `kitna` package; no release yet)

- Item JSON Schema and validator; 15 AI-drafted tool definitions; AI-drafted seed set (40 scenarios x 3
  variants, `provenance: ai_drafted`, for pipeline tests only).
- 160 AI-drafted scenario drafts (tools, gold, English and Devanagari lines, writer briefs) with the Roman
  Hinglish line left for native speakers; writer sheets, import with row validation, guideline, examples.
- Annotation: blind label sheets, Cohen's kappa per argument type and overall, disagreement list.
- Held-out set: freeze, check (CI) and score commands.
- Harness: OpenAI-compatible adapter, mock adapter, cost estimate and confirmation, cost cap, retries,
  resume, raw outputs, run manifest. Grader with Kitna normalisation, error types, statistics (Wilson, exact
  McNemar, paired bootstrap, Holm), ablation, tables, plots, kill-criterion section.
- Analysis plan written before any run. No model has been run.
- Drafts: dataset card, Gradio demo, leaderboard page, post drafts; claims checker.
- Fixed: type-check failure on Python 3.10 (`joinpath` with two arguments); `mypy` now targets 3.10.
