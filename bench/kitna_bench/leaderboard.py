"""Static leaderboard page built only from real runs under results/bench/."""
from __future__ import annotations

import csv
import html
import json
from pathlib import Path
from typing import Any

CSS = """
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:1040px;margin:2rem auto;padding:0 1rem;
color:#1b1b1f;line-height:1.5}
h1{margin-bottom:.2rem} .sub{color:#555;margin-top:0}
table{border-collapse:collapse;width:100%;margin:1rem 0;font-size:.92rem}
th,td{border-bottom:1px solid #ddd;padding:.45rem .55rem;text-align:left;vertical-align:top}
th{background:#f4f4f7} td.num{text-align:right;font-variant-numeric:tabular-nums}
.note{background:#fff8e1;border-left:4px solid #f0b400;padding:.7rem 1rem;margin:1rem 0}
.empty{background:#eef3ff;border-left:4px solid #4a6cf7;padding:1rem;margin:1.5rem 0}
code{background:#f1f1f4;padding:.1rem .3rem;border-radius:3px} footer{color:#666;font-size:.85rem;margin-top:2rem}
"""


def _pct(text: str) -> str:
    return "n/a" if text in ("", None) else f"{100 * float(text):.1f}%"


def collect(results: Path) -> list[dict[str, Any]]:
    """One entry per (run, model, variant) for the raw condition, real runs on non-seed items only."""
    rows: list[dict[str, Any]] = []
    if not results.exists():
        return rows
    for manifest_path in sorted(results.glob("*/manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        run_dir = manifest_path.parent
        if not manifest.get("is_real_run") or manifest.get("splits") == ["seed"] or not manifest.get("complete"):
            continue
        summary = run_dir / "summary.csv"
        if not summary.exists():
            continue
        models = {m["name"]: m for m in manifest["models"]}
        with summary.open(encoding="utf-8", newline="") as fh:
            for s in csv.DictReader(fh):
                if s["condition"] != "raw":
                    continue
                m = models.get(s["model"], {})
                rows.append({**s, "run_id": manifest["run_id"], "run_date": (manifest["finished_utc"] or "")[:10],
                             "model_id": m.get("model", ""), "model_version": m.get("model_version", "not recorded"),
                             "items_sha": manifest["items_sha256"][:12], "kitna": manifest["versions"]["kitna"],
                             "path": f"results/bench/{run_dir.name}/summary.md"})
    return rows


def build(results: Path, out: Path) -> dict[str, Any]:
    rows = collect(results)
    e = html.escape
    parts = ["<!doctype html><html lang='en'><head><meta charset='utf-8'>",
             "<meta name='viewport' content='width=device-width,initial-scale=1'>",
             f"<title>Kitna benchmark leaderboard</title><style>{CSS}</style></head><body>",
             "<h1>Kitna benchmark</h1>",
             "<p class='sub'>Tool-calling in Indian contexts: Devanagari, Romanized Hinglish and English.</p>"]
    if not rows:
        parts.append("<div class='empty'><strong>No results yet.</strong> No real model has been run on the "
                     "human-written benchmark. Mock-adapter runs and runs on the AI-drafted seed items are never "
                     "shown here. This page is rebuilt from <code>results/bench/</code> by "
                     "<code>python scripts/bench.py leaderboard</code>.</div>")
    else:
        parts.append("<div class='note'>Every row links to the run it came from. Intervals are 95% Wilson "
                     "intervals. Ambiguity and negative items are scored separately from call items. Read the "
                     "<a href='../docs/analysis_plan.md'>analysis plan</a> before comparing models.</div>")
        parts.append("<table><thead><tr><th>Model (name in run)</th><th>Model id</th><th>Model version</th>"
                     "<th>Run date</th><th>Variant</th><th>Call items</th><th>Per-item accuracy</th>"
                     "<th>95% interval</th><th>Asked on ambiguity items</th><th>No tool on negatives</th>"
                     "<th>Run</th></tr></thead><tbody>")
        for r in sorted(rows, key=lambda r: (r["run_date"], r["model"], r["variant"]), reverse=False):
            parts.append(
                f"<tr><td>{e(r['model'])}</td><td><code>{e(r['model_id'])}</code></td>"
                f"<td>{e(str(r['model_version']))}</td><td>{e(r['run_date'])}</td><td>{e(r['variant'])}</td>"
                f"<td class='num'>{e(r['call_items'])}</td><td class='num'>{_pct(r['item_accuracy'])}</td>"
                f"<td class='num'>{_pct(r['item_acc_ci_low'])} to {_pct(r['item_acc_ci_high'])}</td>"
                f"<td class='num'>{_pct(r['asked_rate'])}</td><td class='num'>{_pct(r['abstained_rate'])}</td>"
                f"<td><a href='../{e(r['path'])}'>{e(r['run_id'])}</a><br><small>items {e(r['items_sha'])}, "
                f"kitna {e(r['kitna'])}</small></td></tr>")
        parts.append("</tbody></table>")
    parts.append("<footer>Benchmark data: CC BY 4.0. Code: Apache-2.0. Tool schemas, gold arguments and the "
                 "English and Devanagari lines are AI-drafted; Roman Hinglish lines are written by people. "
                 "<a href='https://github.com/Saparajeeta/Kitna'>Repository</a></footer></body></html>")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts) + "\n", encoding="utf-8")
    return {"rows": len(rows), "runs": len({r["run_id"] for r in rows}), "out": str(out)}
