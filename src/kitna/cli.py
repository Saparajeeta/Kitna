"""Command line: ``kitna parse "dhai lakh"``."""
from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import date, datetime

from . import __version__
from ._types import KINDS, KitnaError
from .api import parse


def _base(s: str) -> date | datetime:
    try:
        return datetime.fromisoformat(s) if "T" in s or " " in s else date.fromisoformat(s)
    except ValueError as ex:
        raise argparse.ArgumentTypeError(f"not an ISO date or date-time: {s!r}") from ex


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="kitna", description="Hinglish / Devanagari quantities to canonical values.")
    ap.add_argument("--version", action="version", version=f"kitna {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("parse", help="parse one piece of text")
    p.add_argument("text")
    p.add_argument("--kind", choices=KINDS, help="hint and filter")
    p.add_argument("--base", type=_base, metavar="ISO", help="'today' or 'now' for relative dates (default: clock)")
    p.add_argument("--prefer", choices=("future", "past"), help="resolve dates that lack a year, month or direction")
    p.add_argument("--strict", action="store_true", help="fail on relative dates when --base is missing")
    p.add_argument("--json", action="store_true", help="one JSON object per result (result.schema.json)")
    a = ap.parse_args(argv)
    try:
        results = parse(a.text, kind=a.kind, relative_base=a.base, prefer=a.prefer, strict=a.strict)
    except KitnaError as ex:
        print(f"kitna: {ex}", file=sys.stderr)
        return 2
    for r in results:
        if a.json:
            print(json.dumps(r.to_dict(), ensure_ascii=False))
        else:
            flags = "".join(f"  [{f}]" for f, on in (("ambiguous", r.ambiguous), ("approximate", r.approximate)) if on)
            print(f"{r.kind}\t{r.canonical}\tconfidence={r.confidence}{flags}\t{r.text!r}")
            for w in r.warnings:
                print(f"kitna: warning: {w}", file=sys.stderr)
    return 0 if results else 1


if __name__ == "__main__":
    raise SystemExit(main())
