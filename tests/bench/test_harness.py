from __future__ import annotations

import copy
import csv
import json
import math
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest
from kitna_bench import annotate, freeze, leaderboard, report, runner, stats
from kitna_bench.adapters import (
    AdapterError,
    MockAdapter,
    OpenAICompatAdapter,
    Request,
    build_adapter,
    openai_tools,
    parse_openai_response,
)
from kitna_bench.cli import SEED_FILE, main
from kitna_bench.grader import ERROR_TYPES, grade, response_kind
from kitna_bench.items import BENCH, load_items

MOCK = BENCH / "models.mock.yaml"


@pytest.fixture(scope="module")
def seed() -> dict[str, dict]:
    return {i["id"]: i for i in load_items(SEED_FILE)}


def call(name: str, **args: object) -> list[dict]:
    return [{"name": name, "arguments": args}]


# ---------------------------------------------------------------- grader

def test_correct_call_and_kitna_normalisation(seed: dict) -> None:
    item = seed["seed-pay-001-roman"]
    g = grade(item, call("send_money", payee_name="ramesh", amount_inr=250000), "")
    assert g["correct"] and g["correct_strict"] and g["n_args"] == 2
    g = grade(item, call("send_money", payee_name="रमेश", amount_inr="2.5 lakh"), "")
    assert g["correct"] and not g["correct_strict"]          # alias accepted; '2.5 lakh' only via kitna
    g = grade(seed["seed-trv-002-roman"], call("book_cab", pickup="Indiranagar", drop="Airport",
                                               pickup_time="2026-11-13T05:30:00+05:30"), "")
    assert g["correct"] and g["correct_strict"]


def test_ungraded_free_text_is_ignored(seed: dict) -> None:
    item = seed["seed-rem-002-roman"]
    assert grade(item, call("set_reminder", title="anything at all", at="2026-11-13T18:00"), "")["correct"]
    assert grade(item, call("set_reminder", at="2026-11-13 18:00"), "")["correct"]


@pytest.mark.parametrize(("item_id", "calls", "text", "etype"), [
    ("seed-pay-001-roman", call("pay_bill", biller="mobile", amount_inr=250000), "", "wrong_tool"),
    ("seed-pay-001-roman", call("send_money", payee_name="Ramesh", amount_inr=25000), "", "wrong_scale"),
    ("seed-pay-001-roman", call("send_money", payee_name="Ramesh", amount_inr=2500000), "", "wrong_scale"),
    ("seed-pay-002-roman", call("send_money", payee_name="Sunita", amount_inr=1500, schedule_date="2026-11-11"), "",
     "wrong_date_direction"),
    ("seed-rem-002-roman", call("set_reminder", at="2026-11-13T06:00"), "", "am_pm"),
    ("seed-rem-001-roman", call("set_alarm", time="18:45"), "", "am_pm"),
    ("seed-pay-001-roman", call("send_money", payee_name="Ramesh", amount_inr=200000), "", "fraction_idiom"),
    ("seed-rem-001-roman", call("set_alarm", time="07:15"), "", "fraction_idiom"),
    ("seed-pay-001-roman", call("send_money", payee_name="Ramesh", amount_inr=250000, schedule_date="2026-11-13"),
     "", "hallucinated_argument"),
    ("seed-pay-006-roman", call("send_money", payee_name="Kavita", amount_inr=1000), "", "hallucinated_argument"),
    ("seed-pay-001-roman", [], "Sorry, I cannot help with that.", "refusal"),
    ("seed-pay-001-roman", [], "How much should I send?", "other"),
    ("seed-shp-004-roman", call("track_order", order_id="OD-11111"), "", "other"),
    ("seed-shp-001-roman", call("place_order", item="salt"), "", "other"),
    ("seed-pay-008-roman", call("check_balance", account_type="savings"), "", "wrong_tool"),
])
def test_error_taxonomy(seed: dict, item_id: str, calls: list, text: str, etype: str) -> None:
    g = grade(seed[item_id], calls, text)
    assert not g["correct"] and g["error_type"] == etype, g
    assert etype in ERROR_TYPES


def test_ambiguity_and_negative_items(seed: dict) -> None:
    amb, neg = seed["seed-trv-006-roman"], seed["seed-trv-008-roman"]
    assert grade(amb, [], "Subah 5 baje ya shaam 5 baje?")["correct"]
    g = grade(amb, call("book_cab", pickup="Whitefield", drop="station", pickup_time="2026-11-13T17:00"), "")
    assert not g["correct"] and g["response_kind"] == "call" and g["error_detail"] == "guessed:pickup_time"
    assert not grade(amb, [], "Okay.")["correct"]
    assert grade(neg, [], "Zaroor, kab chalna hai?")["correct"] and grade(neg, [], "Nice idea.")["correct"]
    assert response_kind([], "ठीक है？") == "clarify"


def test_kal_item_differs_by_variant(seed: dict) -> None:
    en, ro = seed["seed-sup-006-en"], seed["seed-sup-006-roman"]
    guess = call("raise_ticket", category="delivery", order_id="OD-51902", incident_date="2026-11-11")
    assert grade(en, guess, "")["correct"]
    assert not grade(ro, guess, "")["correct"]
    assert grade(ro, [], "Kal matlab beeta hua kal ya aane wala kal?")["correct"]


def test_bad_json_arguments_and_adapter_error(seed: dict) -> None:
    item = seed["seed-pay-001-roman"]
    g = grade(item, [{"name": "send_money", "arguments": None}], "")
    assert not g["correct"] and g["n_args_ok"] == 0
    g = grade(item, [], "", error="HTTP 500")
    assert g["response_kind"] == "error" and not g["correct"]


# ---------------------------------------------------------------- adapters

def test_openai_payload_hides_grading_hints(seed: dict) -> None:
    payload = openai_tools(seed["seed-pay-001-roman"]["tools"])
    assert "x-kitna-kind" not in json.dumps(payload) and payload[0]["type"] == "function"
    assert payload[0]["function"]["parameters"]["required"] == ["payee_name", "amount_inr"]


def test_parse_openai_response_variants() -> None:
    r = parse_openai_response({"choices": [{"message": {"content": None, "tool_calls": [
        {"function": {"name": "f", "arguments": "{\"a\": 1}"}}, {"function": {"name": "g", "arguments": "{bad"}}]}}],
        "usage": {"prompt_tokens": 7, "completion_tokens": 3}})
    assert r.tool_calls[0]["arguments"] == {"a": 1} and r.tool_calls[1]["arguments"] is None
    assert (r.prompt_tokens, r.completion_tokens, r.text) == (7, 3, "")
    assert parse_openai_response({"error": "x"}).error


class _Handler(BaseHTTPRequestHandler):
    script: list[int] = []
    seen: list[dict] = []

    def do_POST(self) -> None:  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        type(self).seen.append({"body": body, "auth": self.headers.get("Authorization"), "path": self.path})
        status = type(self).script.pop(0) if type(self).script else 200
        fn = {"name": "set_alarm", "arguments": json.dumps({"time": "06:45"})}
        payload = {"choices": [{"message": {"content": "", "tool_calls": [
            {"id": "c1", "type": "function", "function": fn}]}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 10}} if status == 200 else {"error": "nope"}
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args: object) -> None:
        pass


@pytest.fixture()
def server():
    _Handler.script, _Handler.seen = [], []
    srv = HTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}/v1"
    srv.shutdown()


def test_openai_compat_adapter_over_http(server: str, seed: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KITNA_TEST_KEY", "sekret")
    ad = OpenAICompatAdapter(base_url=server, model="some-model", api_key_env="KITNA_TEST_KEY", backoff_s=0.5)
    waits: list[float] = []
    ad._sleep = waits.append
    _Handler.script = [429, 503]
    item = seed["seed-rem-001-roman"]
    resp = ad.complete(Request(messages=runner.build_messages(item, "raw"), tools=item["tools"], seed=5))
    assert resp.error is None and resp.attempts == 3 and waits == [0.5, 1.0]
    assert resp.tool_calls[0]["name"] == "set_alarm" and resp.tool_calls[0]["arguments"] == {"time": "06:45"}
    sent = _Handler.seen[-1]
    assert sent["auth"] == "Bearer sekret" and sent["path"] == "/v1/chat/completions"
    assert sent["body"]["model"] == "some-model" and sent["body"]["temperature"] == 0.0 and sent["body"]["seed"] == 5
    assert "2026-11-12T10:00 IST (Thursday)" in sent["body"]["messages"][0]["content"]


def test_adapter_gives_up_and_does_not_retry_client_errors(server: str, seed: dict) -> None:
    item = seed["seed-rem-001-roman"]
    req = Request(messages=runner.build_messages(item, "raw"), tools=item["tools"])
    ad = OpenAICompatAdapter(base_url=server, model="m", max_retries=2, backoff_s=0)
    ad._sleep = lambda s: None
    _Handler.script = [500, 500, 500]
    resp = ad.complete(req)
    assert resp.error and "HTTP 500" in resp.error and resp.attempts == 3
    _Handler.script, before = [401], len(_Handler.seen)
    assert "HTTP 401" in (ad.complete(req).error or "") and len(_Handler.seen) == before + 1
    dead = OpenAICompatAdapter(base_url="http://127.0.0.1:9/v1", model="m", max_retries=1, backoff_s=0, timeout_s=1)
    dead._sleep = lambda s: None
    assert dead.complete(req).error


def test_adapter_config_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NOPE_KEY", raising=False)
    with pytest.raises(AdapterError, match="NOPE_KEY"):
        build_adapter({"name": "x", "base_url": "http://h/v1", "model": "m", "api_key_env": "NOPE_KEY"})
    with pytest.raises(AdapterError, match="base_url"):
        build_adapter({"name": "x", "model": "m"})
    with pytest.raises(AdapterError):
        build_adapter({"name": "x", "adapter": "telepathy"})
    assert isinstance(build_adapter({"name": "m", "adapter": "mock"}), MockAdapter)


def test_mock_is_deterministic_and_oracle_is_perfect(seed: dict) -> None:
    a, b = MockAdapter(behavior="scripted", name="m"), MockAdapter(behavior="scripted", name="m")
    oracle = MockAdapter()
    for item in seed.values():
        req = Request(messages=runner.build_messages(item, "raw"), tools=item["tools"], item=item)
        ra, rb = a.complete(req), b.complete(req)
        assert (ra.tool_calls, ra.text) == (rb.tool_calls, rb.text)
        ro = oracle.complete(req)
        assert grade(item, ro.tool_calls, ro.text)["correct"], item["id"]


# ---------------------------------------------------------------- runner

def _run(tmp: Path, **kw: object) -> dict:
    args: dict = {"items_path": SEED_FILE, "models_path": MOCK, "out_dir": tmp, "conditions": ["raw"],
                  "echo": lambda s: None}
    args.update(kw)
    return runner.run(**args)


def test_hints_condition_adds_parser_output(seed: dict) -> None:
    raw = runner.build_messages(seed["seed-pay-001-roman"], "raw")
    hint = runner.build_messages(seed["seed-pay-001-roman"], "kitna_hints")
    assert raw[1] == hint[1] and "Kitna parser" not in raw[0]["content"]
    assert '"dhai lakh rupaye" -> money: INR 250000' in hint[0]["content"]
    amb = runner.build_messages(seed["seed-trv-006-roman"], "kitna_hints")[0]["content"]
    assert " | " in amb                                      # candidates are passed on, not a silent pick


def test_run_is_resumable_and_writes_a_manifest(tmp_path: Path) -> None:
    m = _run(tmp_path, limit=4)
    assert m["complete"] and not m["is_real_run"] and m["calls_made_this_invocation"] == 4 * 3 * 3
    assert m["item_provenance"] == ["ai_drafted"] and m["items_file"] == "bench/items/seed_v0.jsonl"
    for key in ("git_commit", "seed", "versions", "prompt_version", "items_sha256", "models", "started_utc"):
        assert m[key] not in (None, "")
    lines = (tmp_path / "raw.jsonl").read_text(encoding="utf-8").splitlines()
    (tmp_path / "raw.jsonl").write_text("\n".join(lines[:10]) + "\n", encoding="utf-8")   # simulate a crash
    m2 = _run(tmp_path, limit=4)
    assert m2["calls_made_this_invocation"] == 36 - 10 and m2["started_utc"] == m["started_utc"]
    assert _run(tmp_path, limit=4)["calls_made_this_invocation"] == 0
    with pytest.raises(runner.RunError, match="different items or a different prompt"):
        other = tmp_path / "other.jsonl"
        other.write_text("\n".join(SEED_FILE.read_text(encoding="utf-8").splitlines()[:3]) + "\n", encoding="utf-8")
        _run(tmp_path, items_path=other)


def _real_models(tmp: Path, url: str, price: float | None = 1000.0) -> Path:
    p = tmp / "models.yaml"
    cost = f", usd_per_1m_input_tokens: {price}, usd_per_1m_output_tokens: {price}" if price is not None else ""
    p.write_text(f"models:\n  - {{name: local, base_url: '{url}', model: some-model{cost}}}\n", encoding="utf-8")
    return p


def test_real_runs_need_a_cap_and_a_confirmation(tmp_path: Path, server: str) -> None:
    models = _real_models(tmp_path, server)
    echoed: list[str] = []
    with pytest.raises(runner.RunError, match="--max-cost-usd"):
        _run(tmp_path / "r", models_path=models, limit=1)
    with pytest.raises(runner.RunError, match="not confirmed"):
        _run(tmp_path / "r", models_path=models, limit=1, max_cost_usd=5.0, confirm=lambda q: "no",
             echo=echoed.append)
    assert not (tmp_path / "r" / "raw.jsonl").exists() and _Handler.seen == []
    assert "total calls: 3" in echoed[0] and "estimated cost: USD" in echoed[0]
    m = _run(tmp_path / "r", models_path=models, limit=1, max_cost_usd=5.0, confirm=lambda q: "yes")
    assert m["is_real_run"] and m["complete"] and len(_Handler.seen) == 3
    assert m["cost_usd_recorded"] == pytest.approx(3 * 110 * 1000 / 1e6)


def test_cost_cap_stops_the_run_and_it_can_continue(tmp_path: Path, server: str) -> None:
    models = _real_models(tmp_path, server)        # each call costs USD 0.11 at these made-up prices
    m = _run(tmp_path / "r", models_path=models, limit=2, max_cost_usd=0.25, assume_yes=True)
    assert not m["complete"] and "cost cap reached" in m["stopped_reason"] and len(_Handler.seen) == 3
    m = _run(tmp_path / "r", models_path=models, limit=2, max_cost_usd=5.0, assume_yes=True)
    assert m["complete"] and len(_Handler.seen) == 6


def test_placeholders_and_bad_options_are_refused(tmp_path: Path) -> None:
    with pytest.raises(runner.RunError, match="placeholder"):
        runner.load_models(BENCH / "models.example.yaml")
    with pytest.raises(runner.RunError, match="samples"):
        _run(tmp_path, samples=2)
    with pytest.raises(runner.RunError, match="unknown condition"):
        _run(tmp_path, conditions=["telepathy"])


def test_failed_calls_are_retried_on_the_next_run(tmp_path: Path, server: str) -> None:
    models = _real_models(tmp_path, server, price=None)
    text = models.read_text(encoding="utf-8").replace("some-model", "some-model, max_retries: 0")
    models.write_text(text, encoding="utf-8")
    _Handler.script = [500]
    m = _run(tmp_path / "r", models_path=models, limit=1, max_cost_usd=1.0, assume_yes=True)
    assert not m["complete"] and m["failed_calls_this_invocation"] == 1
    m = _run(tmp_path / "r", models_path=models, limit=1, max_cost_usd=1.0, assume_yes=True)
    assert m["complete"] and m["calls_made_this_invocation"] == 1
    assert len(report.load_raw(tmp_path / "r")) == 3
    assert all(r["error"] is None for r in report.load_raw(tmp_path / "r"))


# ---------------------------------------------------------------- statistics

def test_wilson_matches_the_closed_form() -> None:
    lo, hi = stats.wilson(8, 10)
    assert lo == pytest.approx(0.4902, abs=1e-3) and hi == pytest.approx(0.9433, abs=1e-3)
    assert all(math.isnan(x) for x in stats.wilson(0, 0))
    assert stats.wilson(10, 10)[1] == pytest.approx(1.0)


def test_mcnemar_exact() -> None:
    a = [True] * 10 + [True] * 8 + [False] * 1 + [False] * 5
    b = [True] * 10 + [False] * 8 + [True] * 1 + [False] * 5
    r = stats.mcnemar_exact(a, b)
    assert (r["only_first_right"], r["only_second_right"], r["both_right"], r["both_wrong"]) == (8, 1, 10, 5)
    assert r["p_value"] == pytest.approx(2 * (1 + 9) / 2 ** 9)        # exact binomial, two-sided
    assert stats.mcnemar_exact([True, False], [True, False])["p_value"] == 1.0
    with pytest.raises(ValueError):
        stats.mcnemar_exact([True], [True, False])


def test_bootstrap_and_holm() -> None:
    a, b = [True] * 30 + [False] * 10, [True] * 20 + [False] * 20
    r1, r2 = stats.paired_bootstrap_diff(a, b), stats.paired_bootstrap_diff(a, b)
    assert r1 == r2 and r1["diff"] == pytest.approx(0.25) and r1["ci_low"] <= 0.25 <= r1["ci_high"]
    h = stats.holm([0.01, 0.04, 0.03])
    assert [round(x["p_holm"], 2) for x in h] == [0.03, 0.06, 0.06] and [x["reject"] for x in h] == [True, False, False]
    assert stats.holm([]) == []


def test_cohen_kappa_known_value() -> None:
    a = ["y"] * 20 + ["y"] * 5 + ["n"] * 10 + ["n"] * 15
    b = ["y"] * 20 + ["n"] * 5 + ["y"] * 10 + ["n"] * 15
    r = stats.cohen_kappa(a, b)
    assert r["percent_agreement"] == pytest.approx(0.7) and r["kappa"] == pytest.approx(0.4)   # textbook example
    assert stats.cohen_kappa(["x", "x"], ["x", "x"])["kappa"] is None       # one category: undefined, not 1.0
    assert stats.cohen_kappa([], [])["kappa"] is None


# ---------------------------------------------------------------- report, leaderboard

def test_report_files_and_banners(tmp_path: Path) -> None:
    _run(tmp_path, conditions=["raw", "kitna_hints"], samples=3)
    rep = report.build_report(tmp_path)
    for name in rep["files"]:
        assert (tmp_path / name).exists(), name
    md = (tmp_path / "summary.md").read_text(encoding="utf-8")
    assert "pipeline check with a mock adapter" in md and "AI-drafted seed set" in md
    assert "## Kill criterion" in md and "Not evaluated" in md and rep["kill_criterion"]["evaluated"] is False
    with (tmp_path / "summary.csv").open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    oracle = [r for r in rows if r["model"] == "mock-oracle"]
    assert len(oracle) == 6 and {r["item_accuracy"] for r in oracle} == {"1.0000"}
    assert {r["asked_rate"] for r in oracle} == {"1.0000"} and {r["abstained_rate"] for r in oracle} == {"1.0000"}
    en = next(r for r in oracle if r["variant"] == "english" and r["condition"] == "raw")
    ro = next(r for r in oracle if r["variant"] == "roman" and r["condition"] == "raw")
    assert (en["call_items"], ro["call_items"], ro["ambiguity_items"], ro["negative_items"]) == ("26", "25", "10", "5")
    with (tmp_path / "paired_tests.csv").open(encoding="utf-8") as fh:
        paired = list(csv.DictReader(fh))
    assert {p["n_pairs"] for p in paired} == {"25"} and len(paired) == 6    # kal item excluded from pairing
    with (tmp_path / "manual_review_sample.csv").open(encoding="utf-8") as fh:
        review = list(csv.DictReader(fh))
    assert 0 < len(review) <= 60 and "reviewer_note" in review[0]


def test_kill_criterion_logic() -> None:
    def cell(acc: float) -> dict:
        return {"condition": "raw", "variant": "roman", "call_items": 100, "item_accuracy": acc}
    no_diff = [{"comparison": "english_vs_roman", "reject": False}]
    assert report.kill_criterion([cell(0.97), cell(0.99)], no_diff, True)["ceiling_reached"] is True
    assert report.kill_criterion([cell(0.97), cell(0.90)], no_diff, True)["ceiling_reached"] is False
    sig = [{"comparison": "english_vs_roman", "reject": True}]
    assert report.kill_criterion([cell(0.97)], sig, True)["ceiling_reached"] is False
    assert report.kill_criterion([cell(0.97)], no_diff, False)["evaluated"] is False


def test_leaderboard_shows_only_real_runs_on_real_items(tmp_path: Path) -> None:
    run_dir = tmp_path / "results" / "mockrun"
    _run(run_dir)
    report.build_report(run_dir, plots=False)
    out = tmp_path / "lb" / "index.html"
    assert leaderboard.build(tmp_path / "results", out)["rows"] == 0
    assert "No results yet" in out.read_text(encoding="utf-8")
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    manifest.update(is_real_run=True)                      # still seed items: must stay hidden
    (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert leaderboard.build(tmp_path / "results", out)["rows"] == 0
    manifest.update(splits=["dev"])
    manifest["models"][0]["model_version"] = "2099-01-01"
    (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    info = leaderboard.build(tmp_path / "results", out)
    html = out.read_text(encoding="utf-8")
    assert info["rows"] == 9 and "2099-01-01" in html and manifest["finished_utc"][:10] in html


# ---------------------------------------------------------------- annotation

def _label(sheet: Path, fn) -> None:
    with sheet.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r.update(fn(r))
    with sheet.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=annotate.SHEET_COLUMNS)
        w.writeheader()
        w.writerows(rows)


def test_double_labelling_round_trip(tmp_path: Path, seed: dict) -> None:
    items = list(seed.values())
    info = annotate.make_sheets(items, tmp_path, annotators=["a01", "a02"], fraction=0.5)
    assert info["scenarios"] == 20 and info["rows_per_annotator"] == 60
    text = (tmp_path / "labels_a01.csv").read_text(encoding="utf-8-sig")
    assert "250000" not in text and "amount_inr (number)" in text          # no gold values, parameter help present
    order = [[r["item_id"] for r in csv.DictReader((tmp_path / f"labels_{a}.csv").open(encoding="utf-8-sig"))]
             for a in ("a01", "a02")]
    assert sorted(order[0]) == sorted(order[1]) and order[0] != order[1]

    def gold_label(style: str):
        def fn(row: dict) -> dict:
            item = seed[row["item_id"]]
            args = dict(item["gold"]["arguments"])
            if style == "words" and args.get("amount_inr") == "250000":
                args["amount_inr"] = "2.5 lakh"                  # same value, different surface form
            if style == "words" and row["item_id"] == "seed-rem-001-roman":
                args["time"] = "18:45"                           # a real disagreement
            return {annotate.SHEET_COLUMNS[5]: item["expected_behavior"], "tool": item["gold"]["tool"] or "",
                    annotate.SHEET_COLUMNS[7]: "; ".join(f"{k}={v}" for k, v in args.items())}
        return fn

    _label(tmp_path / "labels_a01.csv", gold_label("canonical"))
    _label(tmp_path / "labels_a02.csv", gold_label("words"))
    a, b = annotate.read_sheet(tmp_path / "labels_a01.csv"), annotate.read_sheet(tmp_path / "labels_a02.csv")
    res = annotate.agreement(items, a, b, names=("a01", "a02"))
    assert res["items_labelled_by_both"] == 60
    table = {r["what"]: r for r in res["agreement"]}
    assert table["behavior"]["kappa"] == pytest.approx(1.0) and table["tool"]["percent_agreement"] == 1.0
    has_alarm = "seed-rem-001-roman" in a
    assert len(res["disagreements"]) == (1 if has_alarm else 0)
    assert table["argument:number"]["percent_agreement"] == 1.0   # '2.5 lakh' == '250000' after normalising
    files = annotate.write_agreement(res, tmp_path / "out")
    assert files == ["agreement.json", "disagreements.csv"]
    merged = annotate.attach_labels(items, {"a01": a, "a02": b})
    assert sum(len(i["labels"]) == 2 for i in merged) == 60
    from kitna_bench.items import validate_items
    assert validate_items(merged) == []


def test_sheet_errors_are_reported_with_line_numbers(tmp_path: Path, seed: dict) -> None:
    annotate.make_sheets(list(seed.values()), tmp_path, annotators=["a01", "a02"], fraction=0.1)
    _label(tmp_path / "labels_a01.csv", lambda r: {annotate.SHEET_COLUMNS[5]: "maybe", "tool": "x"})
    with pytest.raises(ValueError, match=r"labels_a01.csv:2: behavior must be"):
        annotate.read_sheet(tmp_path / "labels_a01.csv")
    with pytest.raises(ValueError, match="at least two"):
        annotate.make_sheets(list(seed.values()), tmp_path, annotators=["a01"])


# ---------------------------------------------------------------- held-out freeze

def _heldout(directory: Path, n: int = 3, provenance: str = "human_written") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    rows = [{"id": f"h{i}", "text": t, "kind": k, "base": "2026-11-12T10:00", "expected": e, "writer_id": "w01",
             "provenance": provenance}
            for i, (t, k, e) in enumerate([("dhai lakh", "number", "250000"), ("5 baje", "time", "05:00 | 17:00"),
                                           ("teen sau", "number", "999")][:n])]
    path = directory / "v1.jsonl"
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    return path


def test_freeze_check_and_score(tmp_path: Path) -> None:
    d = tmp_path / "heldout"
    assert freeze.check(d) == [] and freeze.status(d) == "no held-out set exists yet"
    path = _heldout(d)
    assert any("not frozen" in p for p in freeze.check(d))
    with pytest.raises(freeze.FreezeError, match="not frozen"):
        freeze.score("v1", d)
    rec = freeze.freeze("v1", d)
    assert rec["items"] == 3 and freeze.check(d) == [] and freeze.status(d) == "frozen: v1"
    with pytest.raises(freeze.FreezeError, match="never re-frozen"):
        freeze.freeze("v1", d)
    res = freeze.score("v1", d)
    assert res["overall"]["items"] == 3 and res["overall"]["exact"] == 1
    assert res["overall"]["ambiguity_flagged_as_expected"] == 1 and res["overall"]["wrong"] == 1
    path.write_text(path.read_text(encoding="utf-8").replace("999", "300"), encoding="utf-8")     # tampering
    assert any("changed after it was frozen" in p for p in freeze.check(d))
    with pytest.raises(freeze.FreezeError):
        freeze.score("v1", d)


def test_freeze_refuses_ai_text_and_small_sets(tmp_path: Path) -> None:
    _heldout(tmp_path / "a", provenance="ai_drafted")
    with pytest.raises(freeze.FreezeError, match="human_written"):
        freeze.freeze("v1", tmp_path / "a")
    _heldout(tmp_path / "b")
    with pytest.raises(freeze.FreezeError, match="at least 150"):
        freeze.freeze("v1", tmp_path / "b", min_items=150)


def test_repository_heldout_state_is_consistent() -> None:
    assert freeze.check() == []
    assert main(["heldout", "check"]) == 0


def test_cli_validate_and_plan(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    assert main(["validate", str(SEED_FILE)]) == 0
    bad = tmp_path / "bad.jsonl"
    row = copy.deepcopy(load_items(SEED_FILE)[0])
    row["gold"]["tool"] = "nope"
    bad.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
    assert main(["validate", str(bad)]) == 1
    assert main(["plan", "--models", str(MOCK)]) == 0
    out = capsys.readouterr().out
    assert "total calls: 720" in out and "Nothing was sent" in out


def test_heldout_readings_compare_without_regard_to_order() -> None:
    assert freeze._readings("17:00 | 05:00") == freeze._readings("05:00 | 17:00")
    assert freeze._readings("05:00") != freeze._readings("05:00 | 17:00")
