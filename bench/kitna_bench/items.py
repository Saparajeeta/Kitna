"""Loading items and tool definitions; structural and semantic validation."""
from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from .normalize import is_canonical

BENCH = Path(__file__).resolve().parent.parent
SCHEMA_PATH = BENCH / "schema" / "item.schema.json"
TOOLS_PATH = BENCH / "tools.json"
VARIANTS = {"devanagari": "deva", "roman": "roman", "english": "en"}
DOMAINS = ("payments", "travel", "reminders", "shopping", "support")
MAX_SCENARIOS = 200
Item = dict[str, Any]

_DEVA = re.compile(r"[\u0900-\u097F]")
_PHONE = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{9}(?!\d)")
_UPI = re.compile(r"[\w.\-]+@(?!example\b)[a-z]{2,}\b", re.I)
_EMAILISH = re.compile(r"https?://|www\.", re.I)


def load_tools() -> dict[str, dict[str, Any]]:
    """Expand the compact bench/tools.json into full tool schemas, keyed by tool name."""
    raw = json.loads(TOOLS_PATH.read_text(encoding="utf-8"))
    out: dict[str, dict[str, Any]] = {}
    for name, spec in raw.items():
        if name.startswith("_"):
            continue
        props: dict[str, Any] = {}
        for pname, row in spec["params"].items():
            p: dict[str, Any] = {"type": row[0], "description": row[2], "x-kitna-kind": row[1]}
            if len(row) > 3 and row[3]:
                p["enum"] = row[3]
            if len(row) > 4 and row[4] is False:
                p["x-graded"] = False
            props[pname] = p
        out[name] = {"name": name, "description": spec["description"], "domain": spec["domain"],
                     "parameters": {"type": "object", "properties": props, "required": spec["required"]}}
    return out


def tool_for_item(name: str, tools: dict[str, dict[str, Any]]) -> dict[str, Any]:
    t = tools[name]
    return {"name": t["name"], "description": t["description"], "parameters": t["parameters"]}


def load_items(path: Path) -> list[Item]:
    items: list[Item] = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{n}: not valid JSON ({exc})") from exc
    return items


def dump_items(items: list[Item], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(i, ensure_ascii=False, sort_keys=False) + "\n" for i in items),
                    encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def params_of(item: Item, tool: str | None) -> dict[str, dict[str, Any]]:
    for t in item["tools"]:
        if t["name"] == tool:
            props: dict[str, dict[str, Any]] = t["parameters"]["properties"]
            return props
    return {}


def required_of(item: Item, tool: str | None) -> list[str]:
    for t in item["tools"]:
        if t["name"] == tool:
            req: list[str] = t["parameters"]["required"]
            return req
    return []


def privacy_problems(text: str) -> list[str]:
    """Synthetic-only guard: nothing that looks like a real phone number, UPI ID or URL."""
    out = []
    if _PHONE.search(text):
        out.append("looks like a real Indian mobile number")
    if _UPI.search(text):
        out.append("looks like a UPI ID or e-mail address (use name@example)")
    if _EMAILISH.search(text):
        out.append("contains a URL")
    return out


def validate_item(item: Item) -> list[str]:
    """Problems with one item, beyond what the JSON Schema already checks."""
    import jsonschema

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errs = [f"schema: {'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
            for e in jsonschema.Draft202012Validator(schema).iter_errors(item)]
    if errs:
        return errs
    out: list[str] = []
    if item["id"] != f"{item['scenario_id']}-{VARIANTS[item['variant']]}":
        out.append("id must be '<scenario_id>-<deva|roman|en>' matching the variant")
    has_deva = bool(_DEVA.search(item["utterance"]))
    if item["variant"] == "devanagari" and not has_deva:
        out.append("devanagari variant has no Devanagari characters")
    if item["variant"] != "devanagari" and has_deva:
        out.append(f"{item['variant']} variant contains Devanagari characters")
    out += [f"utterance {p}" for p in privacy_problems(item["utterance"])]
    names = [t["name"] for t in item["tools"]]
    if len(set(names)) != len(names):
        out.append("duplicate tool names")
    gold, behavior = item["gold"], item["expected_behavior"]
    if (behavior == "abstain") != (gold["tool"] is None):
        out.append("expected_behavior 'abstain' goes with gold.tool null, and only with it")
    if (behavior == "clarify") != item["ambiguous"]:
        out.append("ambiguous must be true exactly when expected_behavior is 'clarify'")
    if (behavior == "clarify") != bool(item["clarify_about"]):
        out.append("clarify_about must be non-empty exactly when expected_behavior is 'clarify'")
    if gold["tool"] is None:
        if gold["arguments"]:
            out.append("negative item must have no gold arguments")
    elif gold["tool"] not in names:
        out.append(f"gold.tool {gold['tool']!r} is not one of the item's tools")
    else:
        props = params_of(item, gold["tool"])
        for name, value in gold["arguments"].items():
            if name not in props:
                out.append(f"gold argument {name!r} is not a parameter of {gold['tool']}")
                continue
            p = props[name]
            if "enum" in p and value not in p["enum"]:
                out.append(f"gold {name}={value!r} is not in the enum")
            if not is_canonical(value, p["x-kitna-kind"]):
                out.append(f"gold {name}={value!r} is not in canonical {p['x-kitna-kind']} form")
        for name in item["clarify_about"]:
            if name not in props:
                out.append(f"clarify_about {name!r} is not a parameter of {gold['tool']}")
            if name in gold["arguments"]:
                out.append(f"{name!r} is both a gold argument and in clarify_about")
        if behavior == "call":
            for name in required_of(item, gold["tool"]):
                if name not in gold["arguments"] and props[name].get("x-graded", True):
                    out.append(f"required parameter {name!r} has no gold value")
        for name in gold.get("aliases", {}):
            if name not in gold["arguments"]:
                out.append(f"aliases given for {name!r}, which has no gold value")
    if item["provenance"] == "ai_drafted" and not item["author_id"].startswith("ai:"):
        out.append("ai_drafted items need author_id 'ai:<name>'")
    if item["provenance"] == "human_written" and item["author_id"].startswith("ai:"):
        out.append("human_written items need a writer id such as w01")
    if item["split"] == "seed" and item["provenance"] != "ai_drafted":
        out.append("the seed split is AI-drafted only")
    for lab in item["labels"]:
        if lab["tool"] is not None and lab["tool"] not in names:
            out.append(f"label by {lab['annotator_id']}: unknown tool {lab['tool']!r}")
    if len({lab["annotator_id"] for lab in item["labels"]}) != len(item["labels"]):
        out.append("two labels from the same annotator")
    return out


def validate_items(items: list[Item], *, require_complete: bool = True) -> list[str]:
    """Problems across a file. `require_complete`: every scenario must have all three variants."""
    out: list[str] = []
    seen: set[str] = set()
    groups: dict[str, list[Item]] = defaultdict(list)
    for n, item in enumerate(items, 1):
        ident = item.get("id", f"<row {n}>") if isinstance(item, dict) else f"<row {n}>"
        probs = validate_item(item)
        out += [f"{ident}: {p}" for p in probs]
        if probs and any(p.startswith("schema:") for p in probs):
            continue
        if item["id"] in seen:
            out.append(f"{ident}: duplicate id")
        seen.add(item["id"])
        groups[item["scenario_id"]].append(item)
    for sid, group in groups.items():
        variants = sorted(i["variant"] for i in group)
        if require_complete and variants != sorted(VARIANTS):
            out.append(f"{sid}: needs exactly one item per variant, has {variants}")
        for key in ("domain", "now", "tools", "split"):
            if any(i[key] != group[0][key] for i in group):
                out.append(f"{sid}: {key} differs between variants")
        if "variant_specific_gold" not in group[0]["phenomena"]:
            for key in ("gold", "expected_behavior", "clarify_about"):
                if any(i[key] != group[0][key] for i in group):
                    out.append(f"{sid}: {key} differs between variants "
                               "(tag the scenario 'variant_specific_gold' if that is intended)")
        if any(sorted(i["phenomena"]) != sorted(group[0]["phenomena"]) for i in group):
            out.append(f"{sid}: phenomena differ between variants")
    real = {sid for sid, g in groups.items() if g[0]["split"] != "seed"}
    if len(real) > MAX_SCENARIOS:
        out.append(f"{len(real)} non-seed scenarios: the benchmark is capped at {MAX_SCENARIOS}")
    return out


def summarize(items: list[Item]) -> dict[str, Any]:
    scen: dict[str, Item] = {}
    for i in items:
        scen.setdefault(i["scenario_id"], i)
    def count(key: str, rows: list[Item]) -> dict[str, int]:
        c: dict[str, int] = defaultdict(int)
        for r in rows:
            c[str(r[key])] += 1
        return dict(sorted(c.items()))
    return {"rows": len(items), "scenarios": len(scen), "by_domain": count("domain", list(scen.values())),
            "by_variant": count("variant", items), "by_expected_behavior": count("expected_behavior", items),
            "by_provenance": count("provenance", items), "by_split": count("split", list(scen.values())),
            "rows_with_two_or_more_labels": sum(1 for i in items if len(i["labels"]) >= 2)}
