import json
import threading
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from aace.demo.server import DemoServer, PairSession


def wait_for(predicate, timeout=5):
    deadline = time.monotonic()+timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.01)
    raise AssertionError("Worker did not reach expected state")


@pytest.fixture
def server():
    server = DemoServer(0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    server.server_close()
    thread.join(timeout=3)


def request(server, path, payload=None, headers=None):
    body = json.dumps(payload).encode() if payload is not None else None
    req = Request(f"http://127.0.0.1:{server.server_port}{path}", data=body,
                  headers={"Content-Type": "application/json", **(headers or {})})
    with urlopen(req, timeout=5) as response:
        return response.status, response.headers, response.read()


def test_session_worker_publishes_independent_snapshots():
    pair = PairSession("benign", 10, "heuristic_direct", "heuristic_detour")
    try:
        previous = pair.view()
        pair.control("step")
        wait_for(lambda: pair.view()["left"]["observation"]["state"]["step"] == 1)
        assert previous["left"]["observation"]["state"]["step"] == 0
        assert len(previous["left"]["path"]) == 1
        assert pair.replay()["runs"][0]["decisions"][0]["actual_outcome"]["state"]["step"] == 1
        assert not pair.view()["running"]
    finally:
        pair.close()


def test_external_stop_has_a_real_record():
    pair = PairSession("benign", 1, "heuristic_direct", "heuristic_detour")
    try:
        pair.control("stop")
        wait_for(lambda: len(pair.replay()["runs"][0]["decisions"]) == 1)
        assert all(run["decisions"][0]["controller_bypassed"] for run in pair.replay()["runs"])
    finally:
        pair.close()


def test_http_assets_and_session_export(server):
    status, headers, html = request(server, "/")
    assert status == 200 and b'id="study-records"' in html
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    _, _, body = request(server, "/api/session", {"scenario": "benign", "seed": 20,
                         "comparison": "heuristic_detour"})
    identifier = json.loads(body)["session_id"]
    request(server, f"/api/session/{identifier}/control", {"action": "step"})
    pair = server.manager.get(identifier)
    wait_for(lambda: pair.view()["left"]["observation"]["state"]["step"] == 1)
    _, _, exported = request(server, f"/api/session/{identifier}/export")
    data = json.loads(exported)
    assert data["runs"][0]["seed"] == data["runs"][1]["seed"] == 20
    assert data["runs"][0]["python_source_sha256"]
    assert len(data["runs"][0]["decisions"]) == 1


def test_launcher_health_identifies_interface_and_all_frontend_assets(server):
    _, _, body = request(server, "/api/health")
    assert json.loads(body) == {"application": "valor", "interface_version": 6,
                                "schema_version": "1.0"}
    for path in ("/app.js", "/evidence.js", "/style.css"):
        status, headers, body = request(server, path)
        assert status == 200 and body
        assert "no-store" == headers["Cache-Control"]


def test_reserve_replay_matches_the_frozen_damaged_case(server):
    from pathlib import Path

    _, _, page = request(server, "/reserve")
    assert b'id="alternatives"' in page and b"/reserve.js" in page
    for asset in ("/reserve.css", "/reserve.js"):
        assert request(server, asset)[0] == 200
    _, _, body = request(server, "/api/reserve/damaged")
    payload = json.loads(body)
    evidence = json.loads((Path(__file__).parents[1]/"reports/examples/shared-reserve-damaged-v1.json").read_text())
    assert payload["guarded"] == evidence["selected"]
    assert payload["baseline"] == evidence["baseline"]
    assert payload["guarded"]["forecast_screen"]["accepted"]
    assert all(payload["screen_checks"].values())
    for scenario in ("nominal", "volatile", "harsher"):
        replay = json.loads(request(server, f"/api/reserve/{scenario}")[2])
        assert replay["scenario"] == scenario
        assert all(replay["screen_checks"].values()) == replay["guarded"]["forecast_screen"]["accepted"]
    with pytest.raises(HTTPError) as error:
        request(server, "/api/reserve/unknown")
    assert error.value.code == 404


def test_cross_origin_and_unknown_assets_are_rejected(server):
    with pytest.raises(HTTPError) as error:
        request(server, "/api/session", {}, {"Origin": "https://example.com"})
    assert error.value.code == 403
    with pytest.raises(HTTPError) as error:
        request(server, "/../pyproject.toml")
    assert error.value.code == 404


@pytest.mark.parametrize("payload", [{"seed": -1}, {"seed": True}, {"scenario": "missing"},
                                    {"comparison": "aace"}, {"seed": 2**31}])
def test_invalid_session_inputs_do_not_start_workers(server, payload):
    with pytest.raises(HTTPError) as error:
        request(server, "/api/session", payload)
    assert error.value.code == 400
    assert len(server.manager.sessions) == 0


def test_pause_updates_public_status_immediately():
    pair = PairSession("benign", 2, "heuristic_direct", "heuristic_detour")
    try:
        pair.control("run")
        pair.control("pause")
        assert not pair.view()["running"]
    finally:
        pair.close()
