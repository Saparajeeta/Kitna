"""Freezing the held-out parser set (docs/heldout_protocol.md, rules 5 and 6).

`freeze` records the SHA-256 of tests/heldout/vN.jsonl in tests/heldout/vN.sha256, once.
`check` (run in CI) fails if a frozen file no longer matches its checksum, if a checksum
has no file, or if a held-out file exists without having been frozen.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from pathlib import Path

HELDOUT = Path(__file__).resolve().parent.parent.parent / "tests" / "heldout"
_NAME = re.compile(r"^v[0-9]+$")


class FreezeError(RuntimeError):
    pass


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze(version: str, directory: Path = HELDOUT, *, min_items: int = 1) -> dict[str, object]:
    if not _NAME.match(version):
        raise FreezeError("version must look like v1")
    data, lock = directory / f"{version}.jsonl", directory / f"{version}.sha256"
    if lock.exists():
        raise FreezeError(f"{lock.name} already exists: a frozen set is never re-frozen or edited. "
                          "Corrections go into the next version.")
    if not data.exists():
        raise FreezeError(f"{data} does not exist")
    lines = [ln for ln in data.read_text(encoding="utf-8").splitlines() if ln.strip()]
    for n, line in enumerate(lines, 1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise FreezeError(f"{data.name}:{n}: not valid JSON") from exc
        if row.get("provenance") != "human_written":
            raise FreezeError(f"{data.name}:{n}: held-out items must have provenance 'human_written'")
    if len(lines) < min_items:
        raise FreezeError(f"{data.name} has {len(lines)} items; at least {min_items} needed")
    digest = _sha(data)
    record = {"file": data.name, "sha256": digest, "items": len(lines),
              "frozen_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    lock.write_text(f"{digest}  {data.name}\n", encoding="utf-8")
    (directory / f"{version}.frozen.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def check(directory: Path = HELDOUT) -> list[str]:
    """Problems found; an empty list means every frozen set is intact (or none exists yet)."""
    if not directory.exists():
        return []
    problems = []
    for lock in sorted(directory.glob("v*.sha256")):
        data = directory / (lock.stem + ".jsonl")
        want = lock.read_text(encoding="utf-8").split()[0] if lock.read_text(encoding="utf-8").split() else ""
        if not data.exists():
            problems.append(f"{lock.name} exists but {data.name} is missing")
        elif _sha(data) != want:
            problems.append(f"{data.name} was changed after it was frozen (checksum mismatch)")
    for data in sorted(directory.glob("v*.jsonl")):
        if not (directory / (data.stem + ".sha256")).exists():
            problems.append(f"{data.name} is not frozen: run `python scripts/bench.py heldout freeze {data.stem}`")
    return problems


def status(directory: Path = HELDOUT) -> str:
    locks = sorted(directory.glob("v*.sha256")) if directory.exists() else []
    if not locks:
        return "no held-out set exists yet"
    return "frozen: " + ", ".join(p.stem for p in locks)


def _readings(canonical: str) -> frozenset[str]:
    """The readings in a canonical string; their order does not matter when comparing."""
    return frozenset(part.strip() for part in canonical.split(" | "))


def score(version: str, directory: Path = HELDOUT) -> dict[str, object]:
    """Run the parser on a FROZEN held-out set. Row format: docs/heldout_protocol.md.

    Each row: {"id", "text", "kind", "base" (ISO date-time), "expected" (canonical string; use
    "A | B" when the writer says both readings are possible), "writer_id", "provenance"}.
    """
    import kitna
    from kitna.normalize import detect_script

    from .stats import wilson

    data, lock = directory / f"{version}.jsonl", directory / f"{version}.sha256"
    if not lock.exists():
        raise FreezeError(f"{version} is not frozen; freeze it before scoring")
    if check(directory):
        raise FreezeError("; ".join(check(directory)))
    rows = [json.loads(ln) for ln in data.read_text(encoding="utf-8").splitlines() if ln.strip()]
    outcomes: list[dict[str, str]] = []
    for row in rows:
        base = dt.datetime.fromisoformat(row["base"])
        got = [r for r in kitna.parse(row["text"], kind=row["kind"], relative_base=base) if r.kind == row["kind"]]
        expected = str(row["expected"])
        if not got:
            outcome = "miss"
        elif _readings(got[0].canonical) == _readings(expected):
            outcome = "ambiguity_flagged_as_expected" if " | " in expected else "exact"
        else:
            outcome = "wrong"
        outcomes.append({"id": row["id"], "kind": row["kind"], "script": detect_script(row["text"]),
                         "outcome": outcome, "got": got[0].canonical if got else ""})

    def table(key: str) -> dict[str, dict[str, object]]:
        out: dict[str, dict[str, object]] = {}
        for value in sorted({o[key] for o in outcomes}) if key != "all" else ["all"]:
            sub = [o for o in outcomes if key == "all" or o[key] == value]
            ok = sum(o["outcome"] in ("exact", "ambiguity_flagged_as_expected") for o in sub)
            lo, hi = wilson(ok, len(sub))
            out[value] = {"items": len(sub), "correct": ok, "wilson_95": [lo, hi],
                          **{name: sum(o["outcome"] == name for o in sub)
                             for name in ("exact", "ambiguity_flagged_as_expected", "wrong", "miss")}}
        return out

    return {"heldout_version": version, "sha256": _sha(data), "kitna": kitna.__version__,
            "run_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "overall": table("all")["all"], "by_kind": table("kind"), "by_script": table("script"),
            "rows": outcomes}
