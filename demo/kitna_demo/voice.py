"""Optional voice input (off by default; needs the ``voice`` extra and KITNA_VOICE=1).

A pretrained speech model (faster-whisper) runs on this machine; audio is not sent anywhere by this
code. Transcripts can be wrong, especially for mixed Hindi-English speech, so the transcript is
always shown for editing before Kitna reads it. No speech accuracy is claimed or was measured.
"""
from __future__ import annotations

import os
from collections.abc import Callable
from functools import lru_cache
from importlib import util
from typing import Any

NOTICE = ("Speech-to-text can be wrong, especially for mixed Hindi and English. Check and fix the transcript "
          "before reading it. The speech model runs on the machine hosting this page; this app does not send "
          "your audio to any other service and does not keep it. No speech accuracy has been measured.")
MODEL_SIZE = os.environ.get("KITNA_VOICE_MODEL", "small")


def enabled() -> bool:
    return os.environ.get("KITNA_VOICE", "") == "1"


def installed() -> bool:
    return util.find_spec("faster_whisper") is not None


@lru_cache(maxsize=1)
def _model() -> Any:
    from faster_whisper import WhisperModel

    return WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")


def transcribe(path: str | None, *, engine: Callable[[str], str] | None = None) -> str:
    """Transcript of an audio file. ``engine`` replaces the speech model (used by the tests)."""
    if not path:
        raise ValueError("Record or upload some audio first.")
    if engine is not None:
        return engine(path).strip()
    if not installed():
        raise RuntimeError('Voice input needs an extra install: pip install "kitna[voice]"')
    segments, _info = _model().transcribe(path, vad_filter=True)
    return " ".join(seg.text.strip() for seg in segments).strip()
