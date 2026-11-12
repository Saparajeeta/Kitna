"""Kitna: Hinglish and Devanagari quantities to exact canonical values."""
from ._types import KINDS, KitnaError, Money, Range, Result
from .api import parse, parse_money, parse_number
from .normalize import detect_script, normalize_text

__version__ = "0.1.0.dev0"
__all__ = [
    "KINDS", "KitnaError", "Money", "Range", "Result",
    "parse", "parse_money", "parse_number",
    "detect_script", "normalize_text", "__version__",
]
