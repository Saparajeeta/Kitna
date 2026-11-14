"""`kitna serve`: the local HTTP service (needs the `serve` extra and httpx for the test client)."""
from __future__ import annotations

import pytest

import kitna
from kitna import cli

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from kitna import server  # noqa: E402


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(server.create_app())


def test_parse_returns_documented_results_and_the_notice(client: TestClient) -> None:
    res = client.post("/parse", json={"text": "Ramesh ko kal 5 baje dhai lakh rupaye",
                                      "relative_base": "2026-11-12T10:00"})
    assert res.status_code == 200
    body = res.json()
    assert body["version"] == kitna.__version__ and "Pre-alpha" in body["notice"]
    kinds = {r["kind"]: r for r in body["results"]}
    assert kinds["money"]["canonical"] == "INR 250000" and kinds["datetime"]["ambiguous"] is True
    assert kinds["money"]["schema_version"] == "1"


def test_kind_filter_date_only_base_and_no_base_warning(client: TestClient) -> None:
    res = client.post("/parse", json={"text": "kal jaunga dhai lakh", "kind": "date", "relative_base": "2026-11-12"})
    assert [r["canonical"] for r in res.json()["results"]] == ["2026-11-13"]
    res = client.post("/parse", json={"text": "kal jaunga"})
    assert res.json()["results"][0]["warnings"]


@pytest.mark.parametrize("payload", [
    {"text": "kal", "kind": "weight"}, {"text": "kal", "relative_base": "12/11/2026"},
    {"text": "kal jaunga", "strict": True}, {"text": "x" * (server.MAX_TEXT + 1)}, {},
])
def test_bad_requests_get_422(client: TestClient, payload: dict[str, object]) -> None:
    assert client.post("/parse", json=payload).status_code == 422


def test_tool_call_check_endpoint(client: TestClient) -> None:
    res = client.post("/tool-call/check", json={
        "call": {"name": "transfer", "arguments": {"amount": 25000}}, "utterance": "dhai lakh rupaye bhej do"})
    body = res.json()
    assert res.status_code == 200 and body["changed"] is True and body["arguments"] == {"amount": 250000}
    assert client.post("/tool-call/check", json={"call": {"arguments": {}}, "utterance": "x"}).status_code == 422


def test_health_root_and_openapi_page(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok", "version": kitna.__version__}
    assert client.get("/").json()["docs"] == "/docs"
    paths = client.get("/openapi.json").json()["paths"]
    assert {"/parse", "/tool-call/check", "/health"} <= set(paths)
    assert client.get("/docs").status_code == 200


def test_cli_serve_calls_run_with_local_default(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[tuple[str, int]] = []
    monkeypatch.setattr(server, "run", lambda host, port: seen.append((host, port)))
    assert cli.main(["serve"]) == 0 and cli.main(["serve", "--host", "0.0.0.0", "--port", "9000"]) == 0
    assert seen == [("127.0.0.1", 8000), ("0.0.0.0", 9000)]
