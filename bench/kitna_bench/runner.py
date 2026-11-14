"""Running models over items: prompt, cost estimate, confirmation, cost cap, resume, raw outputs."""
from __future__ import annotations

import datetime as dt
import json
import platform
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import kitna

from . import PROMPT_VERSION, __version__
from .adapters import Adapter, Request, build_adapter
from .items import BENCH, Item, load_items, sha256_file, validate_items

CONDITIONS = ("raw", "kitna_hints")
SYSTEM_PROMPT = (
    "You are an assistant that can call tools for a user in India. "
    "The current date and time is {now} IST ({weekday}).\n"
    "- If the request is clear and one of the tools fits, call that tool.\n"
    "- If a required value is missing or could mean more than one thing, do not guess: "
    "ask one short clarifying question and call no tool.\n"
    "- If no tool fits, reply normally and call no tool.\n"
    "Argument formats: dates YYYY-MM-DD; times HH:MM (24-hour); date-times YYYY-MM-DDTHH:MM; "
    "durations ISO 8601 (PT1H30M); amounts and counts as plain numbers (250000, not '2.5 lakh'); "
    "names of people, places and products in English letters."
)
HINT_HEADER = ("Values found in the user's message by the Kitna parser (a rule-based tool; it can be wrong, "
               "and 'A | B' means it could not tell which):")


class RunError(RuntimeError):
    pass


def kitna_hints(item: Item) -> str:
    """The ablation input: what the kitna parser reads in the utterance, candidates included."""
    now = dt.datetime.fromisoformat(item["now"])
    lines = [f"- \"{r.text}\" -> {r.kind}: {r.canonical}" + (" (approximate)" if r.approximate else "")
             for r in kitna.parse(item["utterance"], relative_base=now)]
    return HINT_HEADER + "\n" + ("\n".join(lines) if lines else "- nothing found")


def build_messages(item: Item, condition: str) -> list[dict[str, str]]:
    now = dt.datetime.fromisoformat(item["now"])
    system = SYSTEM_PROMPT.format(now=item["now"], weekday=now.strftime("%A"))
    if condition == "kitna_hints":
        system += "\n\n" + kitna_hints(item)
    elif condition != "raw":
        raise RunError(f"unknown condition {condition!r}")
    return [{"role": "system", "content": system}, {"role": "user", "content": item["utterance"]}]


def load_models(path: Path) -> list[dict[str, Any]]:
    import yaml

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    models = data.get("models") or []
    if not models:
        raise RunError(f"{path}: no entries under 'models:'")
    names = [m.get("name") for m in models]
    if None in names or len(set(names)) != len(names):
        raise RunError(f"{path}: every model needs a unique 'name'")
    for m in models:
        if m.get("adapter", "openai_compat") != "mock" and "<" in str(m.get("model", "")):
            raise RunError(f"{path}: model {m['name']!r} still has a placeholder; fill in the real model id")
    return list(models)


def is_mock(model: dict[str, Any]) -> bool:
    return bool(model.get("adapter") == "mock")


def plan(items: list[Item], models: list[dict[str, Any]], conditions: list[str], samples: int) -> dict[str, Any]:
    """Call count and a rough cost estimate. Token counts are guessed from characters, so treat
    the cost as an order of magnitude (Devanagari usually needs more tokens than this assumes)."""
    per_model = []
    tool_chars = {i["id"]: len(json.dumps(i["tools"], ensure_ascii=False)) for i in items}
    for m in models:
        calls = len(items) * len(conditions) * samples
        in_tok = sum((len(build_messages(i, c)[0]["content"]) + len(i["utterance"]) + tool_chars[i["id"]]) // 3
                     for i in items for c in conditions) * samples
        out_tok = calls * 80
        pi, po = m.get("usd_per_1m_input_tokens"), m.get("usd_per_1m_output_tokens")
        cost = None if is_mock(m) or pi is None or po is None else (in_tok * pi + out_tok * po) / 1e6
        per_model.append({"name": m["name"], "calls": calls, "est_input_tokens": in_tok,
                          "est_output_tokens": out_tok, "est_cost_usd": 0.0 if is_mock(m) else cost})
    known = [p["est_cost_usd"] for p in per_model if p["est_cost_usd"] is not None]
    return {"models": per_model, "total_calls": sum(p["calls"] for p in per_model),
            "est_total_cost_usd": sum(known),
            "models_without_prices": [p["name"] for p in per_model if p["est_cost_usd"] is None]}


def format_plan(p: dict[str, Any], max_cost_usd: float | None) -> str:
    lines = ["Planned run", f"  {'model':<28}{'calls':>8}{'est. input tok':>16}{'est. cost (USD)':>18}"]
    for m in p["models"]:
        cost = "price not set" if m["est_cost_usd"] is None else f"{m['est_cost_usd']:.4f}"
        lines.append(f"  {m['name']:<28}{m['calls']:>8}{m['est_input_tokens']:>16}{cost:>18}")
    lines.append(f"  total calls: {p['total_calls']}   estimated cost: USD {p['est_total_cost_usd']:.4f} "
                 "(rough: tokens are guessed from characters)")
    if p["models_without_prices"]:
        lines.append(f"  no price in models.yaml for: {', '.join(p['models_without_prices'])} "
                     "-> their cost is NOT in the estimate and NOT counted against the cap")
    lines.append(f"  cost cap for this run: {'none' if max_cost_usd is None else f'USD {max_cost_usd:.2f}'}")
    return "\n".join(lines)


def _git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=BENCH.parent, capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _rel(path: Path) -> str:
    """Path relative to the repository when inside it, so manifests are portable."""
    try:
        return path.resolve().relative_to(BENCH.parent).as_posix()
    except ValueError:
        return str(path.resolve())


def _versions() -> dict[str, str]:
    from importlib import metadata

    out = {"python": platform.python_version(), "kitna": kitna.__version__, "kitna_bench": __version__}
    for dist in ("numpy", "scipy", "statsmodels", "matplotlib", "jsonschema", "PyYAML"):
        try:
            out[dist.lower()] = metadata.version(dist)
        except metadata.PackageNotFoundError:
            out[dist.lower()] = "not installed"
    return out


def _public_model(m: dict[str, Any]) -> dict[str, Any]:
    keep = ("name", "adapter", "model", "base_url", "behavior", "error_rate", "usd_per_1m_input_tokens",
            "usd_per_1m_output_tokens", "extra_body", "notes", "model_version")
    out = {k: m[k] for k in keep if k in m}
    out.setdefault("adapter", "openai_compat")
    return out


def call_key(model: str, item_id: str, condition: str, sample: int) -> str:
    return f"{model}|{item_id}|{condition}|{sample}"


def run(*, items_path: Path, models_path: Path, out_dir: Path, conditions: list[str], samples: int = 1,
        sample_temperature: float = 0.7, max_cost_usd: float | None = None, assume_yes: bool = False,
        limit: int | None = None, seed: int = 20261112, confirm: Callable[[str], str] = input,
        echo: Callable[[str], None] = print, adapters: dict[str, Adapter] | None = None) -> dict[str, Any]:
    """Run every model on every item. Safe to re-run: finished calls in raw.jsonl are skipped."""
    if samples not in (1, 3):
        raise RunError("samples must be 1 (temperature 0 only) or 3")
    for c in conditions:
        if c not in CONDITIONS:
            raise RunError(f"unknown condition {c!r}; choose from {CONDITIONS}")
    items = load_items(items_path)
    problems = validate_items(items)
    if problems:
        raise RunError(f"{items_path} does not validate ({len(problems)} problems; first: {problems[0]})")
    if limit:
        keep = sorted({i["scenario_id"] for i in items})[:limit]
        items = [i for i in items if i["scenario_id"] in keep]
    models = load_models(models_path)
    real = [m for m in models if not is_mock(m)]
    p = plan(items, models, conditions, samples)
    echo(format_plan(p, max_cost_usd))
    if real:
        if max_cost_usd is None:
            raise RunError("a run with real models needs --max-cost-usd (the run stops when it is reached)")
        if not (BENCH.parent / "docs" / "analysis_plan.md").exists():
            raise RunError("docs/analysis_plan.md is missing: the analysis plan must exist before a real run")
        if not assume_yes:
            answer = confirm(f"Send {sum(m['calls'] for m in p['models'] if m['name'] in {r['name'] for r in real})}"
                             " requests to real model endpoints? Type 'yes' to continue: ")
            if answer.strip().lower() != "yes":
                raise RunError("not confirmed; nothing was sent")
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_path, manifest_path = out_dir / "raw.jsonl", out_dir / "manifest.json"
    items_sha = sha256_file(items_path)
    manifest: dict[str, Any] = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("items_sha256") != items_sha or manifest.get("prompt_version") != PROMPT_VERSION:
            raise RunError(f"{out_dir} holds a run on different items or a different prompt; use a new --out")
    done: set[str] = set()
    spent = 0.0
    if raw_path.exists():
        for line in raw_path.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            if rec.get("error") is None:
                done.add(rec["key"])
            spent += rec.get("cost_usd") or 0.0
    now_utc = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    manifest = {
        "what_this_is": ("PIPELINE CHECK WITH A MOCK ADAPTER: the 'model' reads the gold answers. "
                         "These are not model results and must not be quoted." if not real else
                         "Benchmark run. Read docs/analysis_plan.md before quoting anything."),
        "is_real_run": bool(real), "run_id": out_dir.name,
        "started_utc": manifest.get("started_utc", now_utc), "last_resumed_utc": now_utc, "finished_utc": None,
        "items_file": _rel(items_path), "items_sha256": items_sha, "n_items": len(items),
        "n_scenarios": len({i["scenario_id"] for i in items}),
        "item_provenance": sorted({i["provenance"] for i in items}), "splits": sorted({i["split"] for i in items}),
        "conditions": conditions, "samples": samples, "temperature_sample_0": 0.0,
        "temperature_other_samples": sample_temperature if samples > 1 else None, "seed": seed,
        "prompt_version": PROMPT_VERSION, "models": [_public_model(m) for m in models],
        "git_commit": _git("rev-parse", "HEAD"), "git_dirty": bool(_git("status", "--porcelain")),
        "analysis_plan_tag": _git("tag", "--list", "analysis-plan-v*", "--sort=-v:refname").split("\n")[0] or None,
        "versions": _versions(), "command": " ".join(sys.argv), "max_cost_usd": max_cost_usd,
        "complete": False, "stopped_reason": None,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    built = adapters or {m["name"]: build_adapter(m) for m in models}
    stopped: str | None = None
    made = failed = 0
    with raw_path.open("a", encoding="utf-8") as fh:
        for m in models:
            for item in items:
                for cond in conditions:
                    for s in range(samples):
                        key = call_key(m["name"], item["id"], cond, s)
                        if key in done:
                            continue
                        if max_cost_usd is not None and spent >= max_cost_usd:
                            stopped = f"cost cap reached (USD {spent:.4f} of {max_cost_usd:.2f})"
                            break
                        req = Request(messages=build_messages(item, cond), tools=item["tools"],
                                      temperature=0.0 if s == 0 else sample_temperature, seed=seed + s,
                                      item=item if is_mock(m) else None, sample=s, condition=cond)
                        resp = built[m["name"]].complete(req)
                        pi, po = m.get("usd_per_1m_input_tokens"), m.get("usd_per_1m_output_tokens")
                        cost = None
                        if not is_mock(m) and pi is not None and po is not None:
                            cost = ((resp.prompt_tokens or 0) * pi + (resp.completion_tokens or 0) * po) / 1e6
                        spent += cost or 0.0
                        made += 1
                        failed += resp.error is not None
                        fh.write(json.dumps({
                            "key": key, "model": m["name"], "item_id": item["id"], "condition": cond, "sample": s,
                            "temperature": req.temperature, "utc": dt.datetime.now(dt.timezone.utc).isoformat(
                                timespec="seconds"),
                            "tool_calls": resp.tool_calls, "text": resp.text, "error": resp.error,
                            "prompt_tokens": resp.prompt_tokens, "completion_tokens": resp.completion_tokens,
                            "cost_usd": cost, "latency_s": round(resp.latency_s, 3), "attempts": resp.attempts,
                            "raw": resp.raw}, ensure_ascii=False) + "\n")
                        fh.flush()
                    if stopped:
                        break
                if stopped:
                    break
            if stopped:
                break
    manifest.update({"finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                     "complete": stopped is None and failed == 0, "stopped_reason": stopped,
                     "calls_made_this_invocation": made, "failed_calls_this_invocation": failed,
                     "cost_usd_recorded": round(spent, 6)})
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    echo(f"{made} calls made, {failed} failed, {len(done)} already done. " + (
        f"STOPPED: {stopped}. Re-run the same command with a higher cap to continue." if stopped else
        ("Some calls failed; re-run the same command to retry them." if failed else "Run complete.")))
    return manifest
