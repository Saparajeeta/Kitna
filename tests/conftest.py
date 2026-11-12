from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import kitna

ROOT = Path(__file__).resolve().parent.parent
CASES_FILE = ROOT / "tests" / "golden" / "draft_cases.jsonl"


def load_cases() -> list[dict[str, Any]]:
    return [json.loads(x) for x in CASES_FILE.read_text(encoding="utf-8").splitlines() if x.strip()]


def to_golden(v: Any) -> Any:
    """Convert a Result value to the JSON form used in the golden files."""
    if isinstance(v, kitna.Range):
        d: dict[str, Any] = {}
        for k in ("min", "max"):
            x = getattr(v, k)
            if isinstance(x, kitna.Money):
                d[k], d["currency"] = x.amount_str, x.currency
            elif x is not None:
                d[k] = to_golden(x)
        return d
    if isinstance(v, kitna.Money):
        return {"amount": v.amount_str, "currency": v.currency}
    if isinstance(v, Decimal):
        return str(v)
    return v
