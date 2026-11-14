"""'Kitna vs others': run the same text through number-parser and dateparser, live.

Nothing here is stored or hardcoded. Each row shows the exact call that was made and what came back
on this machine, with the installed version. A library that is not installed is reported as such.
These are general-purpose libraries that were not built for Romanized Hindi; one message is an
illustration, not a measurement.
"""
from __future__ import annotations

import datetime as dt
import warnings
from dataclasses import dataclass, field
from html import escape
from importlib import metadata

import kitna

INSTALL_HINT = 'pip install "kitna[compare]"'


@dataclass
class Outcome:
    library: str
    version: str | None  # None: not installed
    rows: list[tuple[str, str]] = field(default_factory=list)  # (the call made, what it returned)
    error: str | None = None


def _version(dist: str) -> str | None:
    try:
        return metadata.version(dist)
    except metadata.PackageNotFoundError:
        return None


def run_number_parser(text: str) -> Outcome:
    out = Outcome("number-parser", _version("number-parser"))
    if out.version is None:
        return out
    try:
        from number_parser import parse, parse_number
    except Exception as ex:  # noqa: BLE001 - shown to the user, not hidden
        out.error = f"{type(ex).__name__}: {ex}"
        return out
    for lang in ("hi", "en"):
        for label, fn in ((f"parse(text, language='{lang}')", parse), (f"parse_number(text, language='{lang}')",
                                                                        parse_number)):
            try:
                got = fn(text, language=lang)
            except Exception as ex:  # noqa: BLE001
                got = f"error: {type(ex).__name__}: {ex}"
            if got == text:
                got = f"{got!r}  (text returned unchanged: nothing recognised)"
            else:
                got = repr(got) if not isinstance(got, str) or not got.startswith("error:") else got
            out.rows.append((label, "None  (no number found)" if got == "None" else got))
    return out


def run_dateparser(text: str, base: dt.datetime) -> Outcome:
    out = Outcome("dateparser", _version("dateparser"))
    if out.version is None:
        return out
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import dateparser
            from dateparser.search import search_dates
    except Exception as ex:  # noqa: BLE001
        out.error = f"{type(ex).__name__}: {ex}"
        return out
    settings = {"RELATIVE_BASE": base, "DATE_ORDER": "DMY"}
    shown = f"settings={{'RELATIVE_BASE': {base:%Y-%m-%dT%H:%M}, 'DATE_ORDER': 'DMY'}}"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            got = dateparser.parse(text, languages=["hi", "en"], settings=settings)
            res = "None  (no date or time found)" if got is None else got.strftime("%Y-%m-%dT%H:%M")
        except Exception as ex:  # noqa: BLE001
            res = f"error: {type(ex).__name__}: {ex}"
        out.rows.append((f"dateparser.parse(text, languages=['hi', 'en'], {shown})", res))
        try:
            found = search_dates(text, languages=["hi", "en"], settings=settings)
            res = "None  (no date or time found)" if not found else "; ".join(
                f"{frag!r} → {when:%Y-%m-%dT%H:%M}" for frag, when in found)
        except Exception as ex:  # noqa: BLE001
            res = f"error: {type(ex).__name__}: {ex}"
        out.rows.append((f"search_dates(text, languages=['hi', 'en'], {shown})", res))
    return out


def run_kitna(text: str, base: dt.datetime) -> Outcome:
    out = Outcome("kitna", kitna.__version__)
    results = kitna.parse(text, relative_base=base)
    res = "[]  (nothing found)" if not results else "; ".join(
        f"{r.text!r} → {r.canonical.replace(' | ', '  OR  ')}" + ("  (flagged ambiguous)" if r.ambiguous else "")
        for r in results)
    out.rows.append((f"kitna.parse(text, relative_base={base:%Y-%m-%dT%H:%M})", res))
    return out


def run_all(text: str, base: dt.datetime) -> list[Outcome]:
    return [run_kitna(text, base), run_number_parser(text), run_dateparser(text, base)]


def table(outcomes: list[Outcome], text: str) -> str:
    if not text.strip():
        return '<div class="k-empty">Type a message in the first tab (or here), then run the comparison.</div>'
    parts = [f'<p class="k-cmp-note"><strong>Live comparison.</strong> Run just now on this machine for the text '
             f'“{escape(text)}”. Nothing below is stored or pre-written. number-parser and dateparser are '
             'general-purpose libraries that were not designed for Romanized Hindi; one message is an '
             'illustration, not a measurement.</p>']
    for o in outcomes:
        if o.version is None:
            parts.append(f'<section class="k-cmp"><h4>{escape(o.library)} <span class="k-ver">not installed</span>'
                         f'</h4><p>This library is not installed here, so it was not run. To compare: '
                         f'<code>{escape(INSTALL_HINT)}</code></p></section>')
            continue
        rows = "".join(f"<tr><td><code>{escape(call)}</code></td><td>{escape(got)}</td></tr>" for call, got in o.rows)
        err = f"<p>Could not be loaded: {escape(o.error)}</p>" if o.error else ""
        parts.append(f'<section class="k-cmp"><h4>{escape(o.library)} <span class="k-ver">version '
                     f'{escape(o.version)}</span></h4>{err}<table><thead><tr><th scope="col">Call made</th>'
                     f'<th scope="col">What it returned</th></tr></thead><tbody>{rows}</tbody></table></section>')
    return "".join(parts)
