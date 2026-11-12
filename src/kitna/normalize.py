"""Script detection, Unicode normalisation, tokenising and spelling lookup.

Pure functions. The only cached state is the immutable data tables.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache
from importlib import resources

_DEVA = re.compile(r"[\u0900-\u097F]")
_LATIN = re.compile(r"[A-Za-z]")
_DEVA_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
_NUKTA = "\u093c"
_CHANDRABINDU, _ANUSVARA = "\u0901", "\u0902"

_TOKEN = re.compile(
    r"(?P<rs>(?<![A-Za-z])[Rr][Ss]\.?(?![A-Za-z]))"
    r"|(?P<reserved>[0-9०-९]{1,4}[-/][0-9०-९]{1,2}[-/][0-9०-९]{1,4}|[0-9०-९]{1,2}:[0-9०-९]{2})"
    r"|(?P<num>[0-9०-९]+(?:,[0-9०-९]+)*(?:\.[0-9०-९]+)?)"
    r"|(?P<word>[A-Za-z]+|[\u0900-\u0963\u0970-\u097F]+)"
    r"|(?P<sym>₹|/-|[-–])"
    r"|(?P<punct>[.,;:!?\u0964\u0965\n()])"
)


def detect_script(text: str) -> str:
    """Return ``"devanagari"``, ``"roman"``, ``"mixed"`` or ``"none"``."""
    d, r = bool(_DEVA.search(text)), bool(_LATIN.search(text))
    if d and r:
        return "mixed"
    return "devanagari" if d else "roman" if r else "none"


def normalize_text(text: str) -> str:
    """NFC, lower-case, Devanagari digits to ASCII. Length may change."""
    return unicodedata.normalize("NFC", text).lower().translate(_DEVA_DIGITS)


def word_key(word: str) -> str:
    """Matching key for one word.

    Lower-cased NFC. For Devanagari the nukta is dropped and chandrabindu is
    folded into anusvara, so हज़ार / हजार and पाँच / पांच share a key, whether
    the nukta letter was typed as one code point or two.
    """
    w = normalize_text(word)
    if _DEVA.search(w):
        w = w.replace(_NUKTA, "").replace(_CHANDRABINDU, _ANUSVARA)
    return w


def squeeze(word: str) -> str:
    """Collapse repeated letters: ``hazzaar`` -> ``hazar``."""
    return re.sub(r"(.)\1+", r"\1", word)


@dataclass(frozen=True, slots=True)
class Token:
    text: str  # as written
    norm: str  # word_key(text); for numbers the ASCII digits without commas
    start: int
    end: int
    #: "word" | "num" | "sym" | "punct" | "reserved" (numeric dates and clock times,
    #: left for the date/time parsers; never read as plain numbers)
    type: str
    glued: bool  # no space between this token and the previous one


def tokenize(text: str) -> tuple[Token, ...]:
    """Split ``text`` into tokens whose spans index the original string."""
    out: list[Token] = []
    prev_end = -1
    for m in _TOKEN.finditer(text):
        t = m.lastgroup or "word"
        raw = m.group()
        if t == "rs":
            t, norm = "word", "rs"
        elif t == "num":
            norm = raw.translate(_DEVA_DIGITS).replace(",", "")
        else:
            norm = word_key(raw)
        out.append(Token(raw, norm, m.start(), m.end(), t, m.start() == prev_end))
        prev_end = m.end()
    return tuple(out)


# --------------------------------------------------------------------------- data tables


@dataclass(frozen=True, slots=True)
class Entry:
    cat: str  # "num" | "scale" | "frac"
    value: Decimal  # for "frac": the amount
    name: str  # canonical spelling
    en: bool = False
    ftype: str = ""  # for "frac": "add" | "fixed"


@dataclass(frozen=True)
class Lexicon:
    words: dict[str, Entry]
    squeezed: dict[str, Entry]
    markers: tuple[tuple[str, tuple[str, ...]], ...]  # (role, phrase tokens), longest first
    rules: dict[str, tuple[tuple[frozenset[str], frozenset[str]], ...]]
    versions: dict[str, str]


class DataTableError(RuntimeError):
    """A data table is malformed (for example one spelling under two values)."""


def _rows(name: str) -> tuple[str, list[list[str]]]:
    text = resources.files("kitna").joinpath("data", name).read_text(encoding="utf-8")
    version, rows = "", []
    for line in text.splitlines():
        if line.startswith("# version:"):
            version = line.split(":", 1)[1].strip()
        if not line.strip() or line.startswith("#"):
            continue
        rows.append([c.strip() for c in line.split("\t")])
    if not version:
        raise DataTableError(f"{name}: missing '# version:' header")
    return version, rows


@lru_cache(maxsize=1)
def lexicon() -> Lexicon:
    """Load and validate the data tables (cached; the result is immutable)."""
    words: dict[str, Entry] = {}
    versions: dict[str, str] = {}

    def put(spelling: str, e: Entry, src: str) -> None:
        k = word_key(spelling)
        old = words.get(k)
        if old is not None and (old.cat, old.value, old.ftype) != (e.cat, e.value, e.ftype):
            raise DataTableError(f"{src}: spelling {spelling!r} is listed under two different values")
        words.setdefault(k, e)

    for fname, en in (("numbers_hi.tsv", False), ("numbers_en.tsv", True)):
        versions[fname], rows = _rows(fname)
        for value, spellings in rows:
            sp = spellings.split()
            for s in sp:
                put(s, Entry("num", Decimal(value), sp[0], en), fname)
    versions["scales.tsv"], rows = _rows("scales.tsv")
    for value, lang, spellings in rows:
        sp = spellings.split()
        for s in sp:
            put(s, Entry("scale", Decimal(value), sp[0], lang == "en"), "scales.tsv")
    versions["fractions.tsv"], rows = _rows("fractions.tsv")
    for name, ftype, amount, spellings in rows:
        if ftype not in ("add", "fixed"):
            raise DataTableError(f"fractions.tsv: unknown type {ftype!r}")
        for s in spellings.split():
            put(s, Entry("frac", Decimal(amount), name, False, ftype), "fractions.tsv")

    # squeezed keys are a spelling-repair fallback; drop any that would be ambiguous
    sq: dict[str, Entry | None] = {}
    for k, e in words.items():
        s = squeeze(k)
        if s in sq and sq[s] is not None and sq[s] != e:
            prev = sq[s]
            assert prev is not None
            if (prev.cat, prev.value, prev.ftype) != (e.cat, e.value, e.ftype):
                sq[s] = None
                continue
        sq.setdefault(s, e)
    squeezed = {k: e for k, e in sq.items() if e is not None}

    versions["markers.tsv"], rows = _rows("markers.tsv")
    markers: list[tuple[str, tuple[str, ...]]] = []
    for role, phrases in rows:
        for p in phrases.split("|"):
            toks = tuple(t.norm for t in tokenize(p))
            if toks:
                markers.append((role, toks))
    markers.sort(key=lambda m: -len(m[1]))

    versions["context.tsv"], rows = _rows("context.tsv")
    rules: dict[str, list[tuple[frozenset[str], frozenset[str]]]] = {}
    for rule, ws, ctx in rows:
        rules.setdefault(rule, []).append((
            frozenset(word_key(w) for w in ws.split() if w != "-"),
            frozenset(word_key(w) for w in ctx.split() if w != "-"),
        ))
    return Lexicon(words, squeezed, tuple(markers), {k: tuple(v) for k, v in rules.items()}, versions)


def _within_one_edit(a: str, b: str) -> bool:
    """True if a and b differ by one insert, delete, substitute or adjacent swap."""
    la, lb = len(a), len(b)
    if abs(la - lb) > 1 or a == b:
        return False
    if la == lb:
        diff = [i for i in range(la) if a[i] != b[i]]
        if len(diff) == 1:
            return True
        if len(diff) != 2 or diff[1] != diff[0] + 1:
            return False
        return a[diff[0]] == b[diff[1]] and a[diff[1]] == b[diff[0]]
    if la > lb:
        a, b = b, a
    i = 0
    while i < len(a) and a[i] == b[i]:
        i += 1
    return a[i:] == b[i + 1:]


EXACT, SQUEEZED, EDITED = 1.0, 0.85, 0.6


@lru_cache(maxsize=4096)
def lookup(key: str) -> tuple[Entry, float] | None:
    """Find a number, scale or fraction word.

    Returns the entry and a confidence: 1.0 for a spelling in the tables, 0.85
    when it matched only after collapsing repeated letters, 0.6 when it is one
    edit away from exactly one table value (words of six or more letters only).
    """
    lex = lexicon()
    e = lex.words.get(key)
    if e is not None:
        return e, EXACT
    if len(key) < 4 or any(key in ctx for _, ctx in lex.rules.get("no_fuzzy", ())):
        return None
    e = lex.squeezed.get(squeeze(key))
    if e is not None:
        return e, SQUEEZED
    if len(key) >= 6 and key.isascii():
        hits = {(c.cat, c.value, c.ftype): c for k, c in lex.words.items()
                if len(k) >= 6 and k[0] == key[0] and k.isascii() and _within_one_edit(key, k)}
        if len(hits) == 1:
            return next(iter(hits.values())), EDITED
    return None
