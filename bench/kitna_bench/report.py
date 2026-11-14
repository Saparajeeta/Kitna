"""From raw outputs to scored rows, tables, plots and a Markdown report."""
from __future__ import annotations

import csv
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

from .grader import ERROR_TYPES, grade
from .items import BENCH, Item, load_items
from .stats import holm, mcnemar_exact, paired_bootstrap_diff, wilson

VARIANT_ORDER = ("english", "roman", "devanagari")
KILL_ACCURACY = 0.95
ALPHA = 0.05


def load_raw(run_dir: Path) -> list[dict[str, Any]]:
    """Latest record per call; a later successful retry replaces an earlier failure."""
    latest: dict[str, dict[str, Any]] = {}
    for line in (run_dir / "raw.jsonl").read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        if rec["key"] not in latest or rec.get("error") is None or latest[rec["key"]].get("error") is not None:
            latest[rec["key"]] = rec
    return list(latest.values())


def score(run_dir: Path, items: list[Item]) -> list[dict[str, Any]]:
    by_id = {i["id"]: i for i in items}
    rows = []
    for rec in load_raw(run_dir):
        item = by_id[rec["item_id"]]
        g = grade(item, rec["tool_calls"], rec["text"], rec.get("error"))
        rows.append({"model": rec["model"], "item_id": item["id"], "scenario_id": item["scenario_id"],
                     "domain": item["domain"], "variant": item["variant"], "condition": rec["condition"],
                     "sample": rec["sample"], "phenomena": item["phenomena"], "provenance": item["provenance"],
                     **g, "tool_calls": rec["tool_calls"], "text": rec["text"]})
    rows.sort(key=lambda r: (r["model"], r["condition"], r["item_id"], r["sample"]))
    return rows


def _rate(k: int, n: int) -> dict[str, Any]:
    lo, hi = wilson(k, n)
    return {"n": n, "k": k, "rate": k / n if n else math.nan, "ci_low": lo, "ci_high": hi}


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One line per model x condition x variant, from sample 0 (temperature 0)."""
    cells: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        if r["sample"] == 0:
            cells[(r["model"], r["condition"], r["variant"])].append(r)
    out = []
    for (model, cond, variant), rs in sorted(cells.items(), key=lambda kv: (
            kv[0][0], kv[0][1], VARIANT_ORDER.index(kv[0][2]))):
        calls = [r for r in rs if r["expected"] == "call"]
        clar = [r for r in rs if r["expected"] == "clarify"]
        neg = [r for r in rs if r["expected"] == "abstain"]
        acc = _rate(sum(r["correct"] for r in calls), len(calls))
        strict = _rate(sum(r["correct_strict"] for r in calls), len(calls))
        tool = _rate(sum(bool(r["tool_match"]) for r in calls), len(calls))
        n_args = sum(r["n_args"] for r in calls)
        asked = _rate(sum(r["response_kind"] == "clarify" for r in clar), len(clar))
        guessed = _rate(sum(r["response_kind"] == "call" for r in clar), len(clar))
        abst = _rate(sum(r["correct"] for r in neg), len(neg))
        out.append({
            "model": model, "condition": cond, "variant": variant,
            "call_items": acc["n"], "item_accuracy": acc["rate"], "item_acc_ci_low": acc["ci_low"],
            "item_acc_ci_high": acc["ci_high"], "item_accuracy_strict_grader": strict["rate"],
            "tool_accuracy": tool["rate"],
            "graded_args": n_args,
            "arg_accuracy": (sum(r["n_args_ok"] for r in calls) / n_args) if n_args else math.nan,
            "ambiguity_items": asked["n"], "asked_rate": asked["rate"], "asked_ci_low": asked["ci_low"],
            "asked_ci_high": asked["ci_high"], "guessed_rate": guessed["rate"],
            "negative_items": abst["n"], "abstained_rate": abst["rate"], "abstained_ci_low": abst["ci_low"],
            "abstained_ci_high": abst["ci_high"],
            "adapter_errors": sum(r["response_kind"] == "error" for r in rs),
        })
    return out


def _paired_scenarios(rows: list[dict[str, Any]], items: list[Item]) -> set[str]:
    """Scenarios whose three variants all expect the same call: the only ones compared across languages."""
    by_scen: dict[str, list[Item]] = defaultdict(list)
    for i in items:
        by_scen[i["scenario_id"]].append(i)
    return {s for s, g in by_scen.items() if len(g) == 3 and all(i["expected_behavior"] == "call" for i in g)
            and "variant_specific_gold" not in g[0]["phenomena"]}


def paired_tests(rows: list[dict[str, Any]], items: list[Item], condition: str = "raw") -> list[dict[str, Any]]:
    """English vs Roman and English vs Devanagari on identical scenarios; Holm across all tests."""
    ok = _paired_scenarios(rows, items)
    res: dict[tuple[str, str], dict[str, bool]] = defaultdict(dict)
    for r in rows:
        if r["sample"] == 0 and r["condition"] == condition and r["scenario_id"] in ok:
            res[(r["model"], r["variant"])][r["scenario_id"]] = bool(r["correct"])
    out = []
    for model in sorted({m for m, _ in res}):
        for other in ("roman", "devanagari"):
            en, ot = res.get((model, "english"), {}), res.get((model, other), {})
            common = sorted(set(en) & set(ot))
            if not common:
                continue
            a, b = [en[s] for s in common], [ot[s] for s in common]
            out.append({"model": model, "condition": condition, "comparison": f"english_vs_{other}",
                        **mcnemar_exact(a, b), **{f"diff_{k}": v for k, v in paired_bootstrap_diff(a, b).items()},
                        "acc_english": sum(a) / len(a), "acc_other": sum(b) / len(b)})
    for row, h in zip(out, holm([r["p_value"] for r in out], ALPHA), strict=True):
        row.update(h)
    return out


def ablation_tests(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """raw vs kitna_hints on the same call items, per model and variant; Holm across all tests."""
    res: dict[tuple[str, str, str], dict[str, bool]] = defaultdict(dict)
    for r in rows:
        if r["sample"] == 0 and r["expected"] == "call":
            res[(r["model"], r["variant"], r["condition"])][r["item_id"]] = bool(r["correct"])
    out = []
    for model, variant in sorted({(m, v) for m, v, _ in res}, key=lambda mv: (mv[0], VARIANT_ORDER.index(mv[1]))):
        raw, hint = res.get((model, variant, "raw"), {}), res.get((model, variant, "kitna_hints"), {})
        common = sorted(set(raw) & set(hint))
        if not common:
            continue
        a, b = [hint[s] for s in common], [raw[s] for s in common]
        out.append({"model": model, "variant": variant, "comparison": "kitna_hints_vs_raw", **mcnemar_exact(a, b),
                    **{f"diff_{k}": v for k, v in paired_bootstrap_diff(a, b).items()},
                    "acc_kitna_hints": sum(a) / len(a), "acc_raw": sum(b) / len(b)})
    for row, h in zip(out, holm([r["p_value"] for r in out], ALPHA), strict=True):
        row.update(h)
    return out


def arg_kind_table(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Per-argument accuracy split by argument kind (number, date, time, ...), call items, sample 0."""
    cells: dict[tuple[str, str, str, str], list[bool]] = defaultdict(list)
    for r in rows:
        if r["sample"] == 0 and r["expected"] == "call":
            for a in r["args"].values():
                cells[(r["model"], r["condition"], r["variant"], a["kind"])].append(bool(a["ok"]))
    out = []
    for (m, c, v, k), oks in sorted(cells.items(), key=lambda kv: (kv[0][0], kv[0][1],
                                                                    VARIANT_ORDER.index(kv[0][2]), kv[0][3])):
        rate = _rate(sum(oks), len(oks))
        out.append({"model": m, "condition": c, "variant": v, "argument_kind": k, "arguments": rate["n"],
                    "accuracy": rate["rate"], "ci_low": rate["ci_low"], "ci_high": rate["ci_high"]})
    return out


def error_table(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[tuple[str, str, str], dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in rows:
        if r["sample"] == 0 and r["error_type"]:
            counts[(r["model"], r["condition"], r["variant"])][r["error_type"]] += 1
    return [{"model": m, "condition": c, "variant": v, **{e: counts[(m, c, v)].get(e, 0) for e in ERROR_TYPES}}
            for m, c, v in sorted(counts, key=lambda k: (k[0], k[1], VARIANT_ORDER.index(k[2])))]


def sample_consistency(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Only when 3 samples were drawn: mean accuracy over samples and how often all agree."""
    cells: dict[tuple[str, str, str], dict[str, list[bool]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        cells[(r["model"], r["condition"], r["variant"])][r["item_id"]].append(bool(r["correct"]))
    out = []
    for (m, c, v), per_item in sorted(cells.items(), key=lambda kv: (kv[0][0], kv[0][1],
                                                                      VARIANT_ORDER.index(kv[0][2]))):
        multi = [x for x in per_item.values() if len(x) > 1]
        if not multi:
            continue
        out.append({"model": m, "condition": c, "variant": v, "items": len(multi),
                    "mean_correct_over_samples": sum(sum(x) / len(x) for x in multi) / len(multi),
                    "all_samples_same_verdict": sum(len(set(x)) == 1 for x in multi) / len(multi)})
    return out


def kill_criterion(summary: list[dict[str, Any]], paired: list[dict[str, Any]], is_real: bool) -> dict[str, Any]:
    """Pre-registered in docs/analysis_plan.md section 8."""
    roman = [s for s in summary if s["condition"] == "raw" and s["variant"] == "roman" and s["call_items"]]
    if not is_real or not roman:
        return {"evaluated": False, "ceiling_reached": None,
                "reason": "not evaluated: this is not a real run" if not is_real else "no Roman call items"}
    high = all(s["item_accuracy"] >= KILL_ACCURACY for s in roman)
    sig = any(p["comparison"] == "english_vs_roman" and p["reject"] for p in paired)
    return {"evaluated": True, "ceiling_reached": bool(high and not sig),
            "all_models_roman_accuracy_at_least_95pct": high,
            "any_significant_english_vs_roman_difference": sig,
            "reason": ("every model is at or above 95% on Roman Hinglish and no English-vs-Roman difference is "
                       "significant: report it plainly and reframe the project as a parser and grader"
                       if high and not sig else "the ceiling condition is not met")}


def manual_review_sample(rows: list[dict[str, Any]], items: list[Item], n: int = 60, seed: int = 20261112
                         ) -> list[dict[str, Any]]:
    """A seeded sample for a human to re-judge: half auto-wrong, half auto-right, where available."""
    by_id = {i["id"]: i for i in items}
    rng = random.Random(seed)
    first = [r for r in rows if r["sample"] == 0]
    wrong = [r for r in first if not r["correct"]]
    right = [r for r in first if r["correct"]]
    rng.shuffle(wrong)
    rng.shuffle(right)
    take = wrong[: n // 2] + right[: n - min(len(wrong), n // 2)]
    return [{"model": r["model"], "condition": r["condition"], "item_id": r["item_id"],
             "utterance": by_id[r["item_id"]]["utterance"], "expected": r["expected"],
             "gold_tool": by_id[r["item_id"]]["gold"]["tool"],
             "gold_arguments": json.dumps(by_id[r["item_id"]]["gold"]["arguments"], ensure_ascii=False),
             "model_tool_calls": json.dumps([{k: c.get(k) for k in ("name", "arguments")} for c in r["tool_calls"]],
                                            ensure_ascii=False),
             "model_text": r["text"], "auto_correct": r["correct"], "auto_error_type": r["error_type"] or "",
             "auto_error_detail": r["error_detail"], "reviewer_agrees_with_auto (yes/no)": "",
             "reviewer_error_type": "", "reviewer_note": ""} for r in take]


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.4f}" if isinstance(v, float) and not math.isnan(v) else
                            ("" if isinstance(v, float) else v)) for k, v in r.items()})


def _pct(x: Any) -> str:
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100 * x:.1f}%"


def _md_table(header: list[str], rows: list[list[str]]) -> str:
    return "\n".join(["| " + " | ".join(header) + " |", "|" + "---|" * len(header),
                      *("| " + " | ".join(r) + " |" for r in rows)]) + "\n"


def _plots(out: Path, summary: list[dict[str, Any]], errors: list[dict[str, Any]], banner: str) -> list[str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    made = []
    (out / "plots").mkdir(exist_ok=True)
    raw = [s for s in summary if s["condition"] == "raw" and s["call_items"]]
    models = sorted({s["model"] for s in raw})
    if raw:
        fig, ax = plt.subplots(figsize=(max(6.0, 1.8 * len(models) + 2), 4.2))
        width = 0.26
        for vi, variant in enumerate(VARIANT_ORDER):
            xs, ys, lo, hi = [], [], [], []
            for mi, m in enumerate(models):
                cell = [s for s in raw if s["model"] == m and s["variant"] == variant]
                if cell:
                    xs.append(mi + (vi - 1) * width)
                    ys.append(cell[0]["item_accuracy"])
                    lo.append(cell[0]["item_accuracy"] - cell[0]["item_acc_ci_low"])
                    hi.append(cell[0]["item_acc_ci_high"] - cell[0]["item_accuracy"])
            ax.bar(xs, ys, width, yerr=[lo, hi], capsize=3, label=variant)
        ax.set_xticks(range(len(models)), models, rotation=15, ha="right")
        ax.set_ylim(0, 1.05)
        ax.set_ylabel("per-item accuracy on call items (Wilson 95% interval)")
        ax.set_title(banner, fontsize=9)
        ax.legend()
        fig.tight_layout()
        fig.savefig(out / "plots" / "accuracy_by_variant.png", dpi=130)
        plt.close(fig)
        made.append("plots/accuracy_by_variant.png")
    err = [e for e in errors if e["condition"] == "raw"]
    if err:
        labels = [f"{e['model']}\n{e['variant']}" for e in err]
        fig, ax = plt.subplots(figsize=(max(6.0, 0.9 * len(err) + 2), 4.6))
        bottom = [0] * len(err)
        for et in ERROR_TYPES:
            vals = [e[et] for e in err]
            ax.bar(range(len(err)), vals, bottom=bottom, label=et)
            bottom = [b + v for b, v in zip(bottom, vals, strict=True)]
        ax.set_xticks(range(len(err)), labels, fontsize=7)
        ax.set_ylabel("errors (count)")
        ax.set_title(banner, fontsize=9)
        ax.legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(out / "plots" / "error_types.png", dpi=130)
        plt.close(fig)
        made.append("plots/error_types.png")
    return made


def build_report(run_dir: Path, *, plots: bool = True, review_n: int = 60) -> dict[str, Any]:
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    items_path = Path(manifest["items_file"])
    items = load_items(items_path if items_path.is_absolute() else BENCH.parent / items_path)
    ids = {r["item_id"] for r in load_raw(run_dir)}
    items = [i for i in items if i["id"] in ids]
    rows = score(run_dir, items)
    summary, paired, ablation = summarize(rows), paired_tests(rows, items), ablation_tests(rows)
    errors, consistency = error_table(rows), sample_consistency(rows)
    is_real = bool(manifest["is_real_run"])
    seed_only = manifest.get("splits") == ["seed"]
    kill = kill_criterion(summary, paired, is_real and not seed_only)
    with (run_dir / "scored.jsonl").open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    _write_csv(run_dir / "summary.csv", summary)
    _write_csv(run_dir / "paired_tests.csv", paired)
    _write_csv(run_dir / "ablation_tests.csv", ablation)
    _write_csv(run_dir / "error_types.csv", errors)
    _write_csv(run_dir / "argument_accuracy_by_kind.csv", arg_kind_table(rows))
    _write_csv(run_dir / "sample_consistency.csv", consistency)
    _write_csv(run_dir / "manual_review_sample.csv", manual_review_sample(rows, items, review_n))
    banner = ("MOCK ADAPTER - pipeline check, not model results" if not is_real else
              ("AI-drafted seed items - not benchmark results" if seed_only else f"run {manifest['run_id']}"))
    made = _plots(run_dir, summary, errors, banner) if plots else []

    md = [f"# Run `{manifest['run_id']}`\n"]
    if not is_real:
        md.append("> **This is a pipeline check with a mock adapter.** The \"model\" reads the gold answers and "
                  "makes scripted mistakes. Nothing below is a model result and nothing below may be quoted.\n")
    if seed_only:
        md.append("> **Items are the AI-drafted seed set**, not the benchmark. No native speaker wrote or "
                  "labelled them.\n")
    md.append(f"- Started {manifest['started_utc']}, finished {manifest['finished_utc']}, "
              f"complete: {manifest['complete']}" + (f" ({manifest['stopped_reason']})"
                                                     if manifest.get("stopped_reason") else ""))
    md.append(f"- Items: `{manifest['items_file']}` ({manifest['n_scenarios']} scenarios, {manifest['n_items']} "
              f"rows, sha256 `{manifest['items_sha256'][:12]}`), provenance {manifest['item_provenance']}")
    md.append(f"- Commit `{manifest['git_commit'][:10]}`" + (" (uncommitted changes present)"
                                                              if manifest["git_dirty"] else "")
              + f", kitna {manifest['versions']['kitna']}, prompt v{manifest['prompt_version']}, "
              f"seed {manifest['seed']}, samples {manifest['samples']}")
    md.append("- Models: " + "; ".join(
        f"`{m['name']}` ({m['adapter']}" + (f", model `{m['model']}`" if m.get("model") else "")
        + (f", version {m['model_version']}" if m.get("model_version") else "") + ")" for m in manifest["models"])
        + "\n")
    md.append("## Accuracy on items where a tool call is expected (temperature 0)\n")
    md.append(_md_table(
        ["model", "condition", "variant", "items", "per-item accuracy", "95% Wilson", "strict grader",
         "right tool", "per-argument accuracy"],
        [[s["model"], s["condition"], s["variant"], str(s["call_items"]), _pct(s["item_accuracy"]),
          f"{_pct(s['item_acc_ci_low'])} to {_pct(s['item_acc_ci_high'])}", _pct(s["item_accuracy_strict_grader"]),
          _pct(s["tool_accuracy"]), _pct(s["arg_accuracy"])] for s in summary]))
    md.append("\"Strict grader\" accepts only the machine format the tool schema asks for; the main column also "
              "accepts values the kitna parser can read (for example `2.5 lakh` or `6 PM`).\n")
    md.append("## Ambiguity items (scored separately): did the model ask or guess?\n")
    md.append(_md_table(["model", "condition", "variant", "items", "asked", "95% Wilson", "guessed"],
                        [[s["model"], s["condition"], s["variant"], str(s["ambiguity_items"]), _pct(s["asked_rate"]),
                          f"{_pct(s['asked_ci_low'])} to {_pct(s['asked_ci_high'])}", _pct(s["guessed_rate"])]
                         for s in summary]))
    md.append("## Negative items (scored separately): did the model call no tool?\n")
    md.append(_md_table(["model", "condition", "variant", "items", "no tool called", "95% Wilson"],
                        [[s["model"], s["condition"], s["variant"], str(s["negative_items"]),
                          _pct(s["abstained_rate"]),
                          f"{_pct(s['abstained_ci_low'])} to {_pct(s['abstained_ci_high'])}"] for s in summary]))
    md.append("## English vs. Hindi variants on the same scenarios (paired, exact McNemar, Holm-adjusted)\n")
    md.append(_md_table(
        ["model", "comparison", "pairs", "only English right", "only other right", "difference (95% bootstrap)",
         "p", "p (Holm)", "significant"],
        [[p["model"], p["comparison"], str(p["n_pairs"]), str(p["only_first_right"]), str(p["only_second_right"]),
          f"{100 * p['diff_diff']:+.1f} pts ({100 * p['diff_ci_low']:+.1f} to {100 * p['diff_ci_high']:+.1f})",
          f"{p['p_value']:.4f}", f"{p['p_holm']:.4f}", "yes" if p["reject"] else "no"] for p in paired])
        if paired else "No paired scenarios.\n")
    md.append("## Ablation: kitna-parsed values added to the prompt vs. the raw utterance\n")
    md.append(_md_table(
        ["model", "variant", "pairs", "only with hints right", "only raw right", "difference (95% bootstrap)",
         "p (Holm)", "significant"],
        [[a["model"], a["variant"], str(a["n_pairs"]), str(a["only_first_right"]), str(a["only_second_right"]),
          f"{100 * a['diff_diff']:+.1f} pts ({100 * a['diff_ci_low']:+.1f} to {100 * a['diff_ci_high']:+.1f})",
          f"{a['p_holm']:.4f}", "yes" if a["reject"] else "no"] for a in ablation])
        if ablation else "Not run (needs both `raw` and `kitna_hints` conditions).\n")
    md.append("## Error types (automatic classification, raw condition)\n")
    md.append(_md_table(["model", "variant", *ERROR_TYPES],
                        [[e["model"], e["variant"], *(str(e[t]) for t in ERROR_TYPES)]
                         for e in errors if e["condition"] == "raw"]) if errors else "No errors.\n")
    md.append("The classifier is rule-based. `manual_review_sample.csv` is a seeded sample for a person to check "
              "it; until someone fills it in, treat these counts as unverified.\n")
    if consistency:
        md.append("## Three-sample consistency (secondary)\n")
        md.append(_md_table(["model", "condition", "variant", "items", "mean correct", "all samples agree"],
                            [[c["model"], c["condition"], c["variant"], str(c["items"]),
                              _pct(c["mean_correct_over_samples"]), _pct(c["all_samples_same_verdict"])]
                             for c in consistency]))
    md.append("## Kill criterion\n")
    if kill["evaluated"]:
        md.append(f"**Ceiling reached: {'YES' if kill['ceiling_reached'] else 'no'}.** {kill['reason']}.\n")
    else:
        md.append(f"Not evaluated ({kill['reason']}; the criterion applies to real models on the human-written "
                  "benchmark, see `docs/analysis_plan.md`).\n")
    for name in made:
        md.append(f"![{name}]({name})\n")
    (run_dir / "summary.md").write_text("\n".join(md), encoding="utf-8")
    result = {"run_id": manifest["run_id"], "is_real_run": is_real, "seed_items_only": seed_only,
              "rows_scored": len(rows), "kill_criterion": kill,
              "files": ["summary.md", "summary.csv", "paired_tests.csv", "ablation_tests.csv", "error_types.csv",
                        "argument_accuracy_by_kind.csv", "sample_consistency.csv", "manual_review_sample.csv",
                        "scored.jsonl", *made]}
    (run_dir / "report.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
