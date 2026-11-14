"""``kitna serve``: a small local HTTP service (needs the ``serve`` extra: FastAPI + uvicorn).

Endpoints: ``POST /parse``, ``POST /tool-call/check``, ``GET /health``; interactive docs at ``/docs``.
No rate limit, no authentication, no logging of request text: it is meant to run next to your own
application (bound to 127.0.0.1 by default), not on the open internet.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from . import __version__
from ._types import KINDS, KitnaError
from .api import parse
from .toolcall import postprocess_tool_call

NOTICE = ("Pre-alpha. The rules were drafted by an AI and have not been reviewed by native speakers; "
          "no accuracy has been measured.")
MAX_TEXT = 5000


class ParseRequest(BaseModel):
    text: str = Field(max_length=MAX_TEXT, description="The message to read.",
                      examples=["kal 5 baje dhai lakh bhej do"])
    kind: str | None = Field(default=None, description=f"Optional hint and filter: one of {', '.join(KINDS)}.")
    relative_base: str | None = Field(
        default=None, description="The user's 'today' (YYYY-MM-DD) or 'now' (YYYY-MM-DDTHH:MM). "
                                  "If omitted the server clock is used and results carry a warning.",
        examples=["2026-11-12T10:00"])
    prefer: str | None = Field(default=None, description="'future' or 'past': resolve dates missing a direction.")
    strict: bool = Field(default=False, description="Fail instead of using the server clock.")


class ParseResponse(BaseModel):
    version: str
    notice: str
    results: list[dict[str, Any]]


class ToolCallRequest(BaseModel):
    call: dict[str, Any] = Field(description="OpenAI tool call, Anthropic tool_use block, or {name, arguments}.")
    utterance: str = Field(max_length=MAX_TEXT, description="What the user wrote.")
    kinds: dict[str, str] | None = Field(default=None, description="Argument name -> kind, e.g. {'amount': 'money'}.")
    tool_schema: dict[str, Any] | None = Field(default=None, description="The tool's parameter schema or definition.")
    relative_base: str | None = None
    correct: bool = True


def _base(text: str | None) -> date | datetime | None:
    if not text:
        return None
    try:
        return datetime.fromisoformat(text) if ("T" in text or " " in text) else date.fromisoformat(text)
    except ValueError as ex:
        raise HTTPException(status_code=422, detail=f"relative_base: {ex}") from ex


def parse_endpoint(req: ParseRequest) -> ParseResponse:
    """Read every number, amount, date, time and duration in a message."""
    try:
        results = parse(req.text, kind=req.kind, relative_base=_base(req.relative_base), prefer=req.prefer,
                        strict=req.strict)
    except KitnaError as ex:
        raise HTTPException(status_code=422, detail=str(ex)) from ex
    return ParseResponse(version=__version__, notice=NOTICE, results=[r.to_dict() for r in results])


def tool_call_endpoint(req: ToolCallRequest) -> dict[str, Any]:
    """Confirm, correct or flag the quantity arguments of a model's tool call."""
    try:
        review = postprocess_tool_call(req.call, req.utterance, kinds=req.kinds, schema=req.tool_schema,
                                       relative_base=_base(req.relative_base), correct=req.correct)
    except KitnaError as ex:
        raise HTTPException(status_code=422, detail=str(ex)) from ex
    return {"version": __version__, "notice": NOTICE, **review.to_dict()}


def health_endpoint() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


def root_endpoint() -> dict[str, str]:
    return {"name": "kitna", "version": __version__, "notice": NOTICE, "docs": "/docs", "parse": "POST /parse"}


def create_app() -> FastAPI:
    app = FastAPI(title="Kitna", version=__version__, description=NOTICE)
    app.add_api_route("/", root_endpoint, methods=["GET"], include_in_schema=False)
    app.add_api_route("/health", health_endpoint, methods=["GET"])
    app.add_api_route("/parse", parse_endpoint, methods=["POST"], response_model=ParseResponse)
    app.add_api_route("/tool-call/check", tool_call_endpoint, methods=["POST"])
    return app


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    import uvicorn

    shown = "localhost" if host in ("0.0.0.0", "127.0.0.1") else host
    print(f"Kitna {__version__} listening. Open http://{shown}:{port}/docs  (Ctrl+C to stop)")
    uvicorn.run(create_app(), host=host, port=port, log_level="warning")
