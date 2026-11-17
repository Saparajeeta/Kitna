"""`kitna serve` without the optional dependencies: a clear message, not a traceback."""
from __future__ import annotations

import builtins
import sys
from typing import Any

import pytest

from kitna import cli


def test_serve_without_fastapi_explains_the_extra(monkeypatch: pytest.MonkeyPatch,
                                                  capsys: pytest.CaptureFixture[str]) -> None:
    real = builtins.__import__

    def fake(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "server" or name.endswith(".server") or (args and args[2] and "run" in args[2] and name == "server"):
            raise ImportError("No module named 'fastapi'")
        return real(name, *args, **kwargs)

    monkeypatch.delitem(sys.modules, "kitna.server", raising=False)
    monkeypatch.setattr(builtins, "__import__", fake)
    assert cli.main(["serve"]) == 2
    assert "pip install 'kitna[serve]'" in capsys.readouterr().err
