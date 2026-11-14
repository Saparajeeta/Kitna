# API reference

## Functions

::: kitna.api.parse
::: kitna.api.parse_number
::: kitna.api.parse_money
::: kitna.api.parse_time
::: kitna.api.parse_date

## Result and value types

::: kitna._types.Result
::: kitna._types.Money
::: kitna._types.Range
::: kitna._types.Duration
::: kitna._types.KitnaError

## Kinds and Python value types

| kind | `Result.value` | `canonical` example |
|---|---|---|
| `number` | `int`, or `decimal.Decimal` when not whole | `250000`, `3.25` |
| `digits` | `str` | `091` |
| `money` | `Money` | `INR 100.50` |
| `time` | `datetime.time` | `17:15` |
| `duration` | `Duration` | `PT2H30M` |
| `date` | `datetime.date` | `2026-11-13` |
| `datetime` | `datetime.datetime` (naive, IST assumed) | `2026-11-13T07:00` |

Any kind can also be a `Range` (`2000..3000`, `..17:00`). When `ambiguous` is
true, `value` is `None`, `candidates` holds every reading and `canonical` joins
them with ` | `.

## Stable JSON output

`Result.to_dict()` returns a JSON-serialisable dict with `schema_version` `"1"`.
The JSON Schema is shipped in the package:

```python
from importlib import resources
schema = resources.files("kitna").joinpath("data", "result.schema.json").read_text()
```

Compatibility rule: adding a field keeps the version; removing a field or
changing what one means bumps `schema_version` and is recorded in the
[changelog](changelog.md). The test suite validates every golden-case output
and fuzzed output against the schema.

## Command line

```text
kitna parse TEXT [--kind KIND] [--base ISO_DATE_OR_DATETIME] [--prefer future|past] [--strict] [--json]
```

Exit status: 0 if something was found, 1 if nothing was, 2 on a usage error.
