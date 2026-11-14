"""Double labelling: sheets for annotators, agreement (Cohen's kappa), disagreement list."""
from __future__ import annotations

import csv
import datetime as dt
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

from .items import Item, params_of
from .normalize import QUANTITY_KINDS, kitna_value, text_key
from .stats import cohen_kappa

SHEET_COLUMNS = ["item_id", "variant", "now", "utterance", "tools", "behavior (call / clarify / abstain)", "tool",
                 "arguments (name=value; name=value)", "unsure_about", "comment"]
NO_VALUE = "<none>"


def _tool_help(item: Item) -> str:
    parts = []
    for t in item["tools"]:
        ps = ", ".join(f"{n} ({p['x-kitna-kind']}" + (": " + "/".join(p["enum"]) if "enum" in p else "") + ")"
                       for n, p in t["parameters"]["properties"].items() if p.get("x-graded", True))
        parts.append(f"{t['name']}: {ps}")
    return " || ".join(parts)


def make_sheets(items: list[Item], out_dir: Path, *, annotators: list[str], fraction: float = 1.0,
                seed: int = 20261112) -> dict[str, Any]:
    """One CSV per annotator with the same (seeded) sample of items and no gold values.

    The sample is taken by scenario, so each annotator sees all three variants of a scenario.
    Row order is shuffled separately for each annotator.
    """
    if len(annotators) < 2:
        raise ValueError("double labelling needs at least two annotators")
    if not 0 < fraction <= 1:
        raise ValueError("fraction must be in (0, 1]")
    scen = sorted({i["scenario_id"] for i in items})
    rng = random.Random(seed)
    rng.shuffle(scen)
    chosen = set(scen[: max(1, round(len(scen) * fraction))])
    picked = [i for i in items if i["scenario_id"] in chosen]
    out_dir.mkdir(parents=True, exist_ok=True)
    for a in annotators:
        rows = list(picked)
        random.Random(f"{seed}:{a}").shuffle(rows)
        with (out_dir / f"labels_{a}.csv").open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(SHEET_COLUMNS)
            for i in rows:
                w.writerow([i["id"], i["variant"], i["now"], i["utterance"], _tool_help(i), "", "", "", "", ""])
    return {"annotators": annotators, "scenarios": len(chosen), "rows_per_annotator": len(picked),
            "files": [f"labels_{a}.csv" for a in annotators], "seed": seed}


def read_sheet(path: Path) -> dict[str, dict[str, Any]]:
    """item_id -> {behavior, tool, arguments}. Raises ValueError listing every unreadable row."""
    out: dict[str, dict[str, Any]] = {}
    problems = []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        for n, row in enumerate(csv.DictReader(fh), 2):
            behavior = (row.get(SHEET_COLUMNS[5]) or "").strip().lower()
            if not behavior and not (row.get("tool") or "").strip():
                continue    # not labelled yet
            if behavior not in ("call", "clarify", "abstain"):
                problems.append(f"{path.name}:{n}: behavior must be call, clarify or abstain")
                continue
            args: dict[str, str] = {}
            for part in (row.get(SHEET_COLUMNS[7]) or "").split(";"):
                if not part.strip():
                    continue
                if "=" not in part:
                    problems.append(f"{path.name}:{n}: argument {part.strip()!r} is not name=value")
                    continue
                k, v = part.split("=", 1)
                args[k.strip()] = v.strip()
            tool = (row.get("tool") or "").strip() or None
            if behavior == "abstain":
                tool = None
            out[row["item_id"]] = {"behavior": behavior, "tool": tool, "arguments": args}
    if problems:
        raise ValueError("\n".join(problems))
    return out


def _canon(item: Item, tool: str | None, name: str, value: str | None) -> str:
    if value is None or value == "":
        return NO_VALUE
    kind = params_of(item, tool).get(name, {}).get("x-kitna-kind", "string")
    if kind in QUANTITY_KINDS:
        return kitna_value(value, kind, dt.datetime.fromisoformat(item["now"])) or f"<unreadable:{value}>"
    return text_key(value)


def agreement(items: list[Item], a: dict[str, dict[str, Any]], b: dict[str, dict[str, Any]], *,
              names: tuple[str, str] = ("a", "b")) -> dict[str, Any]:
    """Agreement between two annotators on the items both labelled.

    Units: one per item for `behavior` and `tool`; one per (item, argument name) for argument
    values, where the argument names are the union of what either annotator filled in. Values
    are normalised first, so `2.5 lakh` and `250000` count as the same label.
    """
    by_id = {i["id"]: i for i in items}
    common = sorted(set(a) & set(b) & set(by_id))
    units: dict[str, tuple[list[str], list[str]]] = defaultdict(lambda: ([], []))
    disagreements: list[dict[str, Any]] = []
    for iid in common:
        item, la, lb = by_id[iid], a[iid], b[iid]
        for field in ("behavior", "tool"):
            va, vb = str(la[field]), str(lb[field])
            units[field][0].append(va)
            units[field][1].append(vb)
            if va != vb:
                disagreements.append({"item_id": iid, "utterance": item["utterance"], "field": field,
                                      names[0]: va, names[1]: vb})
        if la["tool"] != lb["tool"]:
            continue    # argument names are not comparable across different tools
        for name in sorted(set(la["arguments"]) | set(lb["arguments"])):
            kind = params_of(item, la["tool"]).get(name, {}).get("x-kitna-kind", "unknown_parameter")
            va = _canon(item, la["tool"], name, la["arguments"].get(name))
            vb = _canon(item, lb["tool"], name, lb["arguments"].get(name))
            for key in (f"argument:{kind}", "argument:all"):
                units[key][0].append(va)
                units[key][1].append(vb)
            if va != vb:
                disagreements.append({"item_id": iid, "utterance": item["utterance"], "field": f"{name} ({kind})",
                                      names[0]: va, names[1]: vb})
    table = [{"what": key, **cohen_kappa(xs, ys)} for key, (xs, ys) in sorted(units.items())]
    return {"annotators": list(names), "items_labelled_by_both": len(common),
            "items_only_one_labelled": len((set(a) ^ set(b)) & set(by_id)), "agreement": table,
            "disagreements": disagreements,
            "note": ("kappa is null when undefined (no units, or a single category). Free-text arguments are "
                     "compared after removing case, spaces and punctuation.")}


def write_agreement(result: dict[str, Any], out_dir: Path) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "agreement.json").write_text(
        json.dumps({k: v for k, v in result.items() if k != "disagreements"}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    cols = ["item_id", "utterance", "field", *result["annotators"], "adjudicated_value", "adjudicator_note"]
    with (out_dir / "disagreements.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for d in result["disagreements"]:
            w.writerow({**d, "adjudicated_value": "", "adjudicator_note": ""})
    return ["agreement.json", "disagreements.csv"]


def attach_labels(items: list[Item], sheets: dict[str, dict[str, dict[str, Any]]]) -> list[Item]:
    """Copy annotator labels into each item's `labels` list (annotator id -> sheet)."""
    out = []
    for item in items:
        new = dict(item)
        labels = [lab for lab in item["labels"] if lab["annotator_id"] not in sheets]
        for annotator, sheet in sorted(sheets.items()):
            if item["id"] in sheet:
                lab = sheet[item["id"]]
                labels.append({"annotator_id": annotator, "tool": lab["tool"], "arguments": lab["arguments"],
                               "behavior": lab["behavior"]})
        new["labels"] = labels
        out.append(new)
    return out
