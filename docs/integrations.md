# Use Kitna in your app

Three ways in, all optional and all pre-alpha: the rules are AI-drafted and not yet reviewed by
native speakers, and no accuracy has been measured.

## 1. Check a model's tool call

`kitna.postprocess_tool_call(call, utterance)` reads the user's words, compares every numeric,
date, time and duration argument of the call with them, and returns a review.

```python
import datetime, kitna

call = {"name": "transfer", "arguments": {"to": "Ramesh", "amount": 25000, "when": "2026-11-13T05:00"}}
review = kitna.postprocess_tool_call(
    call, "Ramesh ko kal 5 baje dhai lakh rupaye bhej dena",
    relative_base=datetime.datetime(2026, 11, 12, 10, 0))

review.arguments            # {'to': 'Ramesh', 'amount': 250000, 'when': '2026-11-13T05:00'}
review.needs_confirmation   # True: 'kal 5 baje' is 5 AM or 5 PM, and the call picked one silently
for arg in review.reviews:
    print(arg.name, arg.status, arg.reason)
```

Each argument gets one status:

| Status | Meaning | What the helper does |
|---|---|---|
| `confirmed` | The value matches what the message says | nothing |
| `corrected` | The message clearly says something else | replaces the value (unless `correct=False`) |
| `ambiguous` | The message has more than one reading | leaves the value; set `needs_confirmation` |
| `unverified` | Nothing to compare with, several possible matches, or Kitna's own reading is not firm | leaves the value |
| `skipped` | Not a quantity (names, flags, free text) | nothing |

Details that matter:

- Accepted layouts: OpenAI (`{"function": {"name", "arguments": "<json string>"}}`), Anthropic
  (`{"name", "input": {...}}`) and flat (`{"name", "arguments": {...}}`). The returned
  `review.call` has the same layout as the input; the input is not modified.
- Which arguments are checked: pass `kinds={"amount": "money", "pin": "skip"}`, or pass the tool's
  `schema` (JSON Schema `format: date / time / date-time / duration`, numeric `type`, or an explicit
  `"x-kitna-kind"`). Without either, numbers and ISO-looking strings are checked and other strings
  are skipped, so a string amount such as `"3500"` needs `kinds` or a schema.
- A value is overwritten only when Kitna's reading has confidence of at least `min_confidence`
  (default 0.95). Readings from repaired spellings, weak tense cues or context resolvers are
  reported as `unverified`, not applied.
- A correction applies Kitna's draft rules. Log `review.to_dict()` and keep a human confirmation
  step for anything that moves money.

A complete offline example with a stand-in model: `python examples/tool_call_guard.py`.

::: kitna.toolcall.postprocess_tool_call
::: kitna.toolcall.ToolCallReview
::: kitna.toolcall.ArgumentReview

## 2. HTTP service

```bash
pip install "kitna[serve] @ git+https://github.com/Saparajeeta/Kitna"
kitna serve                      # http://127.0.0.1:8000 ; API page at /docs
```

```bash
curl -s http://127.0.0.1:8000/parse -H "content-type: application/json" \
     -d '{"text": "kal 5 baje dhai lakh rupaye", "relative_base": "2026-11-12T10:00"}'
```

| Route | Body | Returns |
|---|---|---|
| `POST /parse` | `text`, optional `kind`, `relative_base`, `prefer`, `strict` | `version`, `notice`, `results` (each as `Result.to_dict()`) |
| `POST /tool-call/check` | `call`, `utterance`, optional `kinds`, `tool_schema`, `relative_base`, `correct` | the review as JSON |
| `GET /health` | - | `{"status": "ok", "version": ...}` |
| `GET /docs`, `/openapi.json` | - | the OpenAPI page and document |

Bad input returns HTTP 422 with a message. The service listens on `127.0.0.1` by default, keeps no
state, writes nothing, and has **no rate limit and no authentication**: fine on your own machine,
not for the open internet without your own gateway. Send `relative_base` with every request;
without it the server's clock is used and each result carries a warning.

## 3. Docker

```bash
docker build -t kitna .
docker run --rm -p 8000:8000 kitna
```

The image runs `kitna serve --host 0.0.0.0` as a non-root user. **The Dockerfile has not been
built or run by the author** (no Docker in the build sandbox); treat the first build as a test.
