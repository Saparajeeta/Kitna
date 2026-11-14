# Quickstart

Every example on this page is executed by the test suite
(`tests/test_docs.py`), so the outputs shown are real.

```pycon
>>> import datetime as dt, json
>>> import kitna
>>> B = dt.datetime(2026, 11, 12, 10, 0)   # "now": a Thursday morning

```

## Numbers, fractions, money

```pycon
>>> kitna.parse("dhai lakh")[0].value
250000
>>> kitna.parse("paune do lakh rupaye")[0].canonical
'INR 175000'
>>> kitna.parse("do se teen hazaar rupaye")[0].canonical
'INR 2000..INR 3000'
>>> kitna.parse("lagbhag paanch sau rupaye")[0].approximate
True
>>> kitna.parse("zero nau ek", kind="digits")[0].value
'091'

```

## Times and durations

```pycon
>>> kitna.parse("shaam sawa paanch baje")[0].canonical
'17:15'
>>> r = kitna.parse("5 baje")[0]            # morning or evening? not stated
>>> (r.ambiguous, r.value, r.canonical)
(True, None, '05:00 | 17:00')
>>> kitna.parse("dhai ghante")[0].canonical
'PT2H30M'

```

## Dates need a "today"

```pycon
>>> kitna.parse("kal", relative_base=B)[0].canonical           # yesterday or tomorrow
'2026-11-11 | 2026-11-13'
>>> kitna.parse("kal main Delhi gaya tha", relative_base=B)[0].canonical
'2026-11-11'
>>> kitna.parse("kal subah 7 baje jaunga", relative_base=B)[0].canonical
'2026-11-13T07:00'
>>> [r.canonical for r in kitna.parse("kal gaya tha aur parso jaunga", relative_base=B)]
['2026-11-11', '2026-11-14']
>>> kitna.parse_date("26 January", B, prefer="future").canonical
'2027-01-26'

```

If you leave out `relative_base`, the system clock is used and the result says so:

```pycon
>>> kitna.parse("kal jaunga", now=lambda: dt.datetime(2030, 1, 15, 9, 30))[0].warnings
('relative_base was not given: resolved against the system clock, so the result depends on when parse() was called',)

```

Pass `strict=True` to get an error instead of a clock-dependent answer.

## Things that are not quantities

```pycon
>>> kitna.parse("mujhe paani de do")        # "do" is the verb "give"
[]
>>> kitna.parse("no one came")              # a lone English "one" needs an anchor
[]

```

## Several results, and confidence

```pycon
>>> [(r.kind, r.canonical) for r in kitna.parse("Ramesh ko kal shaam 6 baje 1500 rupaye bhejna hai", relative_base=B)]
[('datetime', '2026-11-13T18:00'), ('money', 'INR 1500')]
>>> kitna.parse_number("tees hazzar").confidence     # misspelling repaired
0.85

```

Confidence is an ordering, not a probability: see [limitations](limitations.md).

## JSON output

```pycon
>>> d = kitna.parse("5 baje tak")[0].to_dict()
>>> d["schema_version"], d["value"], d["candidates"]
('1', None, [{'min': None, 'max': '05:00'}, {'min': None, 'max': '17:00'}])

```

The same structure comes from `kitna parse "5 baje tak" --json`. Its JSON Schema
ships with the package as `kitna/data/result.schema.json`; see the [API page](api.md).

## The clock and the verb can settle "today"

Said at 10:00 with a future verb, 2 o'clock today can only be the afternoon. This is a context
resolver: a contested rule kept in `policy.tsv` (open question Q13), so the confidence is lower.

```pycon
>>> r = kitna.parse("aaj 2 baje call karungi", relative_base=B)[0]
>>> r.canonical, r.confidence
('2026-11-12T14:00', 0.9)
>>> kitna.parse("aaj 11 baje aaunga", relative_base=B)[0].canonical   # both still to come: not decided
'2026-11-12T11:00 | 2026-11-12T23:00'

```

## Checking a tool call

```pycon
>>> call = {"name": "transfer", "arguments": {"amount": 25000, "when": "2026-11-13T05:00"}}
>>> review = kitna.postprocess_tool_call(call, "kal 5 baje dhai lakh rupaye bhej dena", relative_base=B)
>>> review.arguments
{'amount': 250000, 'when': '2026-11-13T05:00'}
>>> [(a.name, a.status) for a in review.reviews]
[('amount', 'corrected'), ('when', 'ambiguous')]
>>> review.needs_confirmation
True

```

More: [Use Kitna in your app](integrations.md).
