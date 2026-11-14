# Kitna

Kitna ("how much") turns Hinglish (Romanized Hindi mixed with English) and
Devanagari quantities, money, times and dates into exact canonical values, and
tells you when an expression is ambiguous instead of guessing.

!!! warning "Pre-alpha, no accuracy claim"
    Version 0.1.0.dev0. The rules, spellings and test cases were drafted by an AI
    and have **not** been reviewed by a native speaker. Agreement with those
    draft cases is a self-consistency check, not accuracy. The first accuracy
    figure will come from a held-out set written by native speakers
    ([protocol](heldout_protocol.md)); that set does not exist yet.

```console
$ kitna parse "kal subah saade saat baje 2.5 lakh rupaye bhej dunga" --base 2026-11-12
datetime	2026-11-13T07:30	confidence=1.0	'kal subah saade saat baje'
money	INR 250000	confidence=1.0	'2.5 lakh rupaye'
```

- [Install](install.md) and [Quickstart](quickstart.md)
- [What it parses](taxonomy.md), [how ambiguity is reported](ambiguity.md)
- [What it does not do](limitations.md)
- [Help: add a spelling](add_spelling.md) or [answer an open question](open_questions.md)

The second half of the project, a tool-calling benchmark in Devanagari,
Romanized Hinglish and English, is planned and not built:
[methodology](benchmark_methodology.md).
