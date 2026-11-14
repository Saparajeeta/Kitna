"""Command line for the benchmark tooling. Run: python scripts/bench.py <command> --help"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from .items import BENCH, dump_items, load_items, summarize, validate_items

ROOT = BENCH.parent
SEED_FILE = BENCH / "items" / "seed_v0.jsonl"
DRAFTS_FILE = BENCH / "authoring" / "scenarios_v1_draft.jsonl"


def _validate(args: argparse.Namespace) -> int:
    bad = 0
    for name in args.files:
        path = Path(name)
        items = load_items(path)
        problems = validate_items(items, require_complete=not args.allow_incomplete)
        print(f"{path}: {json.dumps(summarize(items), ensure_ascii=False)}")
        for p in problems:
            print(f"  PROBLEM {p}")
        bad += len(problems)
    print("OK" if not bad else f"{bad} problem(s)")
    return 1 if bad else 0


def _seed(args: argparse.Namespace) -> int:
    from .seed import build_seed

    items = build_seed()
    text = "".join(json.dumps(i, ensure_ascii=False) + "\n" for i in items)
    if args.check:
        if not SEED_FILE.exists() or SEED_FILE.read_text(encoding="utf-8") != text:
            print(f"{SEED_FILE} is out of date: run `python scripts/bench.py seed`", file=sys.stderr)
            return 1
        print(f"{SEED_FILE} is up to date ({len(items)} rows)")
        return 0
    dump_items(items, SEED_FILE)
    print(f"wrote {SEED_FILE} ({len(items)} rows, {len(items) // 3} scenarios, all provenance=ai_drafted)")
    return 0


def _drafts(args: argparse.Namespace) -> int:
    from .authoring import write_drafts
    from .drafts import build_drafts

    text = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in build_drafts())
    if args.check:
        if not DRAFTS_FILE.exists() or DRAFTS_FILE.read_text(encoding="utf-8") != text:
            print(f"{DRAFTS_FILE} is out of date: run `python scripts/bench.py drafts`", file=sys.stderr)
            return 1
        print(f"{DRAFTS_FILE} is up to date")
        return 0
    rows = write_drafts(DRAFTS_FILE)
    print(f"wrote {DRAFTS_FILE} ({len(rows)} AI-drafted scenarios, Roman line left for human writers)")
    return 0


def _writer_sheets(args: argparse.Namespace) -> int:
    from .authoring import load_drafts, write_writer_sheets

    counts = write_writer_sheets(load_drafts(DRAFTS_FILE), Path(args.out), args.writers)
    for w, n in counts.items():
        print(f"{args.out}/writer_{w}.csv: {n} scenarios")
    return 0


def _import(args: argparse.Namespace) -> int:
    from .authoring import import_sheets, load_drafts

    res = import_sheets(load_drafts(DRAFTS_FILE), [Path(s) for s in args.sheets], split=args.split)
    for p in res["problems"]:
        print(f"PROBLEM {p}")
    print(f"scenarios written: {res['scenarios_written']}; still missing: {len(res['scenarios_missing'])}; "
          f"writers: {', '.join(res['writers']) or 'none'}")
    if res["problems"]:
        print("nothing written: fix the problems above and import again", file=sys.stderr)
        return 1
    if res["scenarios_missing"] and not args.allow_missing:
        print("nothing written: some scenarios have no Roman line yet (use --allow-missing for a partial file)",
              file=sys.stderr)
        return 1
    dump_items(res["items"], Path(args.out))
    print(f"wrote {args.out} ({len(res['items'])} rows)")
    return 0


def _label_sheets(args: argparse.Namespace) -> int:
    from .annotate import make_sheets

    info = make_sheets(load_items(Path(args.items)), Path(args.out), annotators=args.annotators,
                       fraction=args.fraction, seed=args.seed)
    print(json.dumps(info))
    return 0


def _agreement(args: argparse.Namespace) -> int:
    from .annotate import agreement, attach_labels, read_sheet, write_agreement

    items = load_items(Path(args.items))
    sheets = {}
    for path in (args.a, args.b):
        name = Path(path).stem.replace("labels_", "")
        sheets[name] = read_sheet(Path(path))
    (na, a), (nb, b) = sheets.items()
    res = agreement(items, a, b, names=(na, nb))
    files = write_agreement(res, Path(args.out))
    print(f"items labelled by both: {res['items_labelled_by_both']}; disagreements: {len(res['disagreements'])}")
    for row in res["agreement"]:
        k = "undefined" if row["kappa"] is None else f"{row['kappa']:.3f}"
        pa = "n/a" if row["percent_agreement"] is None else f"{100 * row['percent_agreement']:.1f}%"
        print(f"  {row['what']:<24} n={row['n']:<5} agreement={pa:<8} kappa={k}")
    print(f"wrote {', '.join(str(Path(args.out) / f) for f in files)}")
    if args.attach:
        dump_items(attach_labels(items, sheets), Path(args.attach))
        print(f"wrote {args.attach} with labels attached")
    return 0


def _heldout(args: argparse.Namespace) -> int:
    from . import freeze as fz

    try:
        if args.action == "check":
            problems = fz.check()
            for p in problems:
                print(f"PROBLEM {p}")
            print("held-out check: " + ("FAILED" if problems else f"ok ({fz.status()})"))
            return 1 if problems else 0
        if args.action == "freeze":
            print(json.dumps(fz.freeze(args.version, min_items=args.min_items), indent=2))
            return 0
        res = fz.score(args.version)
        out = ROOT / "results" / "heldout" / f"{args.version}_kitna-{res['kitna']}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {out}: {json.dumps(res['overall'])}")
        return 0
    except fz.FreezeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _run(args: argparse.Namespace) -> int:
    from .report import build_report
    from .runner import RunError, format_plan, load_models, plan, run

    conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]
    try:
        if args.command == "plan":
            items = load_items(Path(args.items))
            print(format_plan(plan(items, load_models(Path(args.models)), conditions, args.samples),
                              args.max_cost_usd))
            print("Nothing was sent. Use `run` to start.")
            return 0
        out = Path(args.out) if args.out else ROOT / "results" / "bench" / dt.datetime.now(dt.timezone.utc).strftime(
            "%Y%m%dT%H%M%SZ")
        manifest = run(items_path=Path(args.items), models_path=Path(args.models), out_dir=out,
                       conditions=conditions, samples=args.samples, max_cost_usd=args.max_cost_usd,
                       assume_yes=args.yes, limit=args.limit, seed=args.seed)
        rep = build_report(out, plots=not args.no_plots)
        print(f"report: {out / 'summary.md'}  (real run: {manifest['is_real_run']}, files: {len(rep['files'])})")
        return 0 if manifest["complete"] else 2
    except RunError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _report(args: argparse.Namespace) -> int:
    from .report import build_report

    rep = build_report(Path(args.run_dir), plots=not args.no_plots)
    print(json.dumps(rep, indent=2))
    return 0


def _leaderboard(args: argparse.Namespace) -> int:
    from .leaderboard import build

    info = build(Path(args.results), Path(args.out))
    print(json.dumps(info))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="bench.py", description="Kitna benchmark tooling")
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate", help="validate item files against the schema and the cross-row rules")
    p.add_argument("files", nargs="+")
    p.add_argument("--allow-incomplete", action="store_true", help="do not require all three variants")
    p.set_defaults(fn=_validate)

    p = sub.add_parser("seed", help="(re)write the AI-drafted 40-scenario seed set")
    p.add_argument("--check", action="store_true")
    p.set_defaults(fn=_seed)

    p = sub.add_parser("drafts", help="(re)write the AI-drafted v1 scenario drafts (no Roman line)")
    p.add_argument("--check", action="store_true")
    p.set_defaults(fn=_drafts)

    p = sub.add_parser("writer-sheets", help="make one CSV per human writer from the drafts")
    p.add_argument("--writers", nargs="+", required=True, metavar="w01")
    p.add_argument("--out", default=str(BENCH / "authoring" / "sheets"))
    p.set_defaults(fn=_writer_sheets)

    p = sub.add_parser("import", help="merge filled writer sheets with the drafts into an items file")
    p.add_argument("--sheets", nargs="+", required=True)
    p.add_argument("--out", default=str(BENCH / "items" / "dev_v1.jsonl"))
    p.add_argument("--split", default="dev", choices=["dev", "test"])
    p.add_argument("--allow-missing", action="store_true")
    p.set_defaults(fn=_import)

    p = sub.add_parser("label-sheets", help="make blind labelling sheets for two or more annotators")
    p.add_argument("--items", required=True)
    p.add_argument("--annotators", nargs="+", required=True, metavar="a01")
    p.add_argument("--out", default=str(BENCH / "annotation"))
    p.add_argument("--fraction", type=float, default=1.0, help="share of scenarios to double-label")
    p.add_argument("--seed", type=int, default=20261112)
    p.set_defaults(fn=_label_sheets)

    p = sub.add_parser("agreement", help="Cohen's kappa, percent agreement and the disagreement list")
    p.add_argument("--items", required=True)
    p.add_argument("--a", required=True, help="labels_a01.csv")
    p.add_argument("--b", required=True, help="labels_a02.csv")
    p.add_argument("--out", default=str(ROOT / "results" / "annotation"))
    p.add_argument("--attach", help="also write an items file with both label sets attached")
    p.set_defaults(fn=_agreement)

    p = sub.add_parser("heldout", help="freeze / check / score the held-out parser set")
    p.add_argument("action", choices=["freeze", "check", "score"])
    p.add_argument("version", nargs="?", default="v1")
    p.add_argument("--min-items", type=int, default=150)
    p.set_defaults(fn=_heldout)

    for name, text in (("plan", "print the call count and cost estimate; send nothing"),
                       ("run", "run models on items, then build the report (resumable)")):
        p = sub.add_parser(name, help=text)
        p.add_argument("--models", required=True, help="models.yaml (see bench/models.example.yaml)")
        p.add_argument("--items", default=str(SEED_FILE))
        p.add_argument("--conditions", default="raw,kitna_hints")
        p.add_argument("--samples", type=int, default=1, choices=[1, 3])
        p.add_argument("--max-cost-usd", type=float, default=None)
        p.add_argument("--seed", type=int, default=20261112)
        if name == "run":
            p.add_argument("--out", help="run directory (default results/bench/<UTC timestamp>); reuse to resume")
            p.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
            p.add_argument("--limit", type=int, help="only the first N scenarios (smoke test)")
            p.add_argument("--no-plots", action="store_true")
        p.set_defaults(fn=_run)

    p = sub.add_parser("report", help="rebuild tables, plots and summary.md for a run directory")
    p.add_argument("run_dir")
    p.add_argument("--no-plots", action="store_true")
    p.set_defaults(fn=_report)

    p = sub.add_parser("leaderboard", help="build the static leaderboard page from results/bench")
    p.add_argument("--results", default=str(ROOT / "results" / "bench"))
    p.add_argument("--out", default=str(ROOT / "leaderboard" / "index.html"))
    p.set_defaults(fn=_leaderboard)

    args = ap.parse_args(argv)
    return int(args.fn(args))
