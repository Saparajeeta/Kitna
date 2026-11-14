"""Model adapters: one interface, an OpenAI-compatible HTTP implementation, and an offline mock."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Protocol

from .items import Item, params_of


@dataclass(frozen=True)
class Request:
    messages: list[dict[str, str]]
    tools: list[dict[str, Any]]          # tool schemas in the item's format
    temperature: float = 0.0
    seed: int | None = None
    item: Item | None = None             # only the mock adapter looks at this
    sample: int = 0
    condition: str = "raw"


@dataclass
class Response:
    tool_calls: list[dict[str, Any]] = field(default_factory=list)   # [{"name": str, "arguments": dict | None}]
    text: str = ""
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    latency_s: float = 0.0
    attempts: int = 1
    raw: Any = None
    error: str | None = None


class Adapter(Protocol):
    """Anything that can answer one request. Implement `complete` to add a provider."""
    def complete(self, request: Request) -> Response: ...


class AdapterError(RuntimeError):
    pass


def openai_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Item tool schemas -> OpenAI `tools` payload (the x- grading hints are not sent to the model)."""
    out = []
    for t in tools:
        props = {name: {k: v for k, v in p.items() if not k.startswith("x-")}
                 for name, p in t["parameters"]["properties"].items()}
        out.append({"type": "function", "function": {
            "name": t["name"], "description": t["description"],
            "parameters": {"type": "object", "properties": props, "required": t["parameters"]["required"]}}})
    return out


class OpenAICompatAdapter:
    """Chat Completions over HTTP: hosted APIs, Ollama (/v1), vLLM, llama.cpp server, LiteLLM...

    Nothing about the model is hardcoded: base URL, model id and the *name* of the
    environment variable holding the key come from models.yaml.
    """

    def __init__(self, *, base_url: str, model: str, api_key_env: str | None = None, timeout_s: float = 60.0,
                 max_retries: int = 4, backoff_s: float = 2.0, extra_body: dict[str, Any] | None = None,
                 send_seed: bool = True) -> None:
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.model = model
        self.api_key = os.environ.get(api_key_env, "") if api_key_env else ""
        if api_key_env and not self.api_key:
            raise AdapterError(f"environment variable {api_key_env} is not set (needed for model {model!r})")
        self.timeout_s, self.max_retries, self.backoff_s = timeout_s, max_retries, backoff_s
        self.extra_body = extra_body or {}
        self.send_seed = send_seed
        self._sleep = time.sleep

    def complete(self, request: Request) -> Response:
        body: dict[str, Any] = {"model": self.model, "messages": request.messages,
                                "tools": openai_tools(request.tools), "tool_choice": "auto",
                                "temperature": request.temperature, **self.extra_body}
        if self.send_seed and request.seed is not None:
            body["seed"] = request.seed
        data = json.dumps(body).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        last = "no attempt made"
        started = time.monotonic()
        for attempt in range(1, self.max_retries + 2):
            try:
                req = urllib.request.Request(self.url, data=data, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:  # noqa: S310
                    payload = json.loads(resp.read().decode("utf-8"))
                out = parse_openai_response(payload)
                out.latency_s, out.attempts = time.monotonic() - started, attempt
                return out
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", "replace")[:300]
                last = f"HTTP {exc.code}: {detail}"
                if exc.code not in (408, 409, 429) and exc.code < 500:
                    break       # a client error will not get better by retrying
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                wait = float(retry_after) if retry_after and retry_after.isdigit() else None
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ConnectionError) as exc:
                last, wait = f"{type(exc).__name__}: {exc}", None
            if attempt <= self.max_retries:
                self._sleep(wait if wait is not None else self.backoff_s * 2 ** (attempt - 1))
        return Response(error=last, latency_s=time.monotonic() - started, attempts=attempt)


def parse_openai_response(payload: dict[str, Any]) -> Response:
    try:
        msg = payload["choices"][0]["message"]
    except (KeyError, IndexError, TypeError):
        return Response(error="response has no choices[0].message", raw=payload)
    calls = []
    for call in msg.get("tool_calls") or []:
        fn = call.get("function") or {}
        raw_args = fn.get("arguments")
        args: Any
        if isinstance(raw_args, dict):
            args = raw_args
        else:
            try:
                args = json.loads(raw_args) if raw_args else {}
            except json.JSONDecodeError:
                args = None
        calls.append({"name": fn.get("name"), "arguments": args if isinstance(args, dict) else None,
                      "raw_arguments": raw_args})
    usage = payload.get("usage") or {}
    return Response(tool_calls=calls, text=msg.get("content") or "", prompt_tokens=usage.get("prompt_tokens"),
                    completion_tokens=usage.get("completion_tokens"), raw=payload)


# ---------------------------------------------------------------- mock

MOCK_BEHAVIORS = ("oracle", "scripted")


class MockAdapter:
    """Offline stand-in for a model. It reads the gold answer, so its scores mean nothing.

    oracle:   always the gold behaviour (checks that a perfect answer scores 100%).
    scripted: the gold behaviour with deterministic, hash-chosen mistakes of every
              type in the error taxonomy, more often on non-English variants, so
              that the grader, statistics and reports all have something to show.
    """

    def __init__(self, *, behavior: str = "oracle", name: str = "mock", error_rate: float = 0.3) -> None:
        if behavior not in MOCK_BEHAVIORS:
            raise AdapterError(f"mock behavior must be one of {MOCK_BEHAVIORS}")
        self.behavior, self.name, self.error_rate = behavior, name, error_rate

    def _draw(self, item: Item, sample: int, salt: str) -> float:
        h = hashlib.sha256(f"{self.name}|{item['id']}|{sample}|{salt}".encode()).digest()
        return int.from_bytes(h[:8], "big") / 2 ** 64

    def complete(self, request: Request) -> Response:
        item = request.item
        if item is None:
            raise AdapterError("the mock adapter needs the item")
        gold, behavior = item["gold"], item["expected_behavior"]
        hinted = request.condition == "kitna_hints"
        rate = self.error_rate * (1.0 if item["variant"] != "english" else 0.35) * (0.5 if hinted else 1.0)
        wrong = self.behavior == "scripted" and self._draw(item, request.sample, "err") < rate
        usage = {"prompt_tokens": sum(len(m["content"]) for m in request.messages) // 4, "completion_tokens": 30}

        def reply(calls: list[dict[str, Any]], text: str = "") -> Response:
            return Response(tool_calls=calls, text=text, raw={"mock": True, "behavior": self.behavior},
                            prompt_tokens=usage["prompt_tokens"], completion_tokens=usage["completion_tokens"])

        if behavior == "abstain":
            if wrong:
                return reply([{"name": item["tools"][0]["name"], "arguments": {}}])
            return reply([], "I can't do that with the tools I have, but here is some general information.")
        props = params_of(item, gold["tool"])
        if behavior == "clarify":
            if wrong:   # guess instead of asking
                args = dict(gold["arguments"])
                for name in item["clarify_about"]:
                    args[name] = _made_up(props[name]["x-kitna-kind"], item["now"])
                return reply([{"name": gold["tool"], "arguments": args}])
            return reply([], f"Could you confirm the {item['clarify_about'][0].replace('_', ' ')}?")
        args = {k: _native(v, props[k]) for k, v in gold["arguments"].items()}
        for name, p in props.items():
            if not p.get("x-graded", True):
                args[name] = "(free text)"
        if not wrong:
            return reply([{"name": gold["tool"], "arguments": args}])
        pick = int(self._draw(item, request.sample, "kind") * 7)
        kinds = {name: props[name]["x-kitna-kind"] for name in gold["arguments"]}
        numbers = [n for n, k in kinds.items() if k == "number"]
        dates = [n for n, k in kinds.items() if k in ("date", "datetime")]
        times = [n for n, k in kinds.items() if k in ("time", "datetime")]
        if pick == 0 and len(item["tools"]) > 1:
            other = next(t["name"] for t in item["tools"] if t["name"] != gold["tool"])
            return reply([{"name": other, "arguments": {}}])
        if pick == 1 and numbers:
            args[numbers[0]] = int(float(gold["arguments"][numbers[0]]) * 10)
        elif pick == 2 and dates:
            args[dates[0]] = _mirror(gold["arguments"][dates[0]], item["now"])
        elif pick == 3 and times:
            args[times[0]] = _plus_12h(gold["arguments"][times[0]])
        elif pick == 4 and numbers:
            args[numbers[0]] = int(float(gold["arguments"][numbers[0]])) + 500
        elif pick == 5:
            spare = [n for n in props if n not in gold["arguments"] and props[n].get("x-graded", True)]
            if spare:
                args[spare[0]] = _made_up(props[spare[0]]["x-kitna-kind"], item["now"])
            else:
                return reply([], "Sorry, I can't help with that.")
        else:
            return reply([], "Sorry, I can't help with that.")
        return reply([{"name": gold["tool"], "arguments": args}])


def _native(value: str, param: dict[str, Any]) -> Any:
    if param["type"] in ("number", "integer"):
        return float(value) if "." in value else int(value)
    return value


def _made_up(kind: str, now: str) -> Any:
    return {"number": 1000, "date": now[:10], "time": "09:00", "datetime": now[:10] + "T09:00",
            "duration": "PT1H"}.get(kind, "unknown")


def _mirror(value: str, now: str) -> str:
    """The same distance from today, in the other direction (kal read as yesterday)."""
    today = dt.date.fromisoformat(now[:10])
    day = dt.date.fromisoformat(value[:10])
    delta = (day - today).days or 1
    return (today - dt.timedelta(days=delta)).isoformat() + value[10:]


def _plus_12h(value: str) -> str:
    head, hhmm = (value[:11], value[11:]) if "T" in value else ("", value)
    hour = (int(hhmm[:2]) + 12) % 24
    return f"{head}{hour:02d}{hhmm[2:]}"


def build_adapter(spec: dict[str, Any]) -> Adapter:
    kind = spec.get("adapter", "openai_compat")
    if kind == "mock":
        return MockAdapter(behavior=spec.get("behavior", "oracle"), name=spec["name"],
                           error_rate=float(spec.get("error_rate", 0.3)))
    if kind == "openai_compat":
        for key in ("base_url", "model"):
            if not spec.get(key):
                raise AdapterError(f"model entry {spec.get('name')!r} needs {key!r}")
        return OpenAICompatAdapter(
            base_url=spec["base_url"], model=spec["model"], api_key_env=spec.get("api_key_env"),
            timeout_s=float(spec.get("timeout_s", 60)), max_retries=int(spec.get("max_retries", 4)),
            backoff_s=float(spec.get("backoff_s", 2)), extra_body=spec.get("extra_body"),
            send_seed=bool(spec.get("send_seed", True)))
    raise AdapterError(f"unknown adapter {kind!r} (use 'openai_compat' or 'mock')")
