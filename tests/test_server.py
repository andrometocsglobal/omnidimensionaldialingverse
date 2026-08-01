"""API + WebSocket tests. Run: pytest -q"""

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx2", reason="starlette's TestClient needs httpx2")

from fastapi.testclient import TestClient  # noqa: E402

from server.app import app  # noqa: E402


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_health_and_families(client):
    body = client.get("/api/health").json()
    assert body["ok"] is True and "version" in body
    assert set(client.get("/api/families").json()) == {
        "arithmetic", "geometric", "harmonic", "power"}


def test_compute_geometric_is_exact(client):
    body = client.post("/api/compute", json={
        "family": "geometric", "n": 64, "a": 1, "r": 2}).json()
    assert body["result"] == str(2 ** 64 - 1)
    assert body["exact_match"] and not body["truncated"]


def test_compute_survives_a_float_overflowing_result(client):
    """Used to be a hard 500: float(2**2000) overflows IEEE 754."""
    r = client.post("/api/compute", json={
        "family": "geometric", "n": 2000, "a": 1, "r": 2})
    assert r.status_code == 200
    body = r.json()
    assert body["digits"] == 603 and not body["truncated"]
    assert body["result"] == str(2 ** 2000 - 1)   # still rendered exactly
    assert body["decimal"] is None and body["exact_match"]


def test_compute_survives_a_result_too_long_to_stringify(client):
    """Used to be a hard 500: CPython refuses int -> str past 4300 digits."""
    r = client.post("/api/compute", json={
        "family": "geometric", "n": 20_000, "a": 1, "r": 2})
    assert r.status_code == 200
    body = r.json()
    assert body["truncated"] and body["digits"] == 6021
    assert body["log10"] == pytest.approx(6020.6, abs=0.1)
    assert body["exact_match"]


def test_compute_rejects_bad_input_with_422_not_500(client):
    assert client.post("/api/compute", json={"family": "bogus", "n": 10}).status_code == 422
    assert client.post("/api/compute", json={"family": "arithmetic", "n": -5}).status_code == 422
    assert client.post("/api/compute", json={
        "family": "geometric", "n": 10 ** 9, "a": 1, "r": 2}).status_code == 422
    assert client.post("/api/compute", json={
        "family": "harmonic", "n": 10, "a": -2, "d": 1}).status_code == 422


def test_compute_stays_fast_for_enormous_n(client):
    r = client.post("/api/compute", json={"family": "power", "n": 10 ** 12, "p": 3})
    assert r.status_code == 200
    body = r.json()
    assert body["exact_match"] and body["spot_checked"]


def test_spectrum_and_midpoint(client):
    spec = client.get("/api/spectrum?values=3,5,11,2").json()
    values = [spec[k] for k in sorted(spec, key=int)]
    assert all(values[i] <= values[i + 1] + 1e-9 for i in range(len(values) - 1))

    assert client.get("/api/midpoint?a=2&b=3").json()["midpoint"] == pytest.approx(2.4)
    assert client.get("/api/midpoint?a=1&b=-1").status_code == 422
    assert client.get("/api/spectrum?values=abc").status_code == 422


def test_verify_endpoint(client):
    body = client.get("/api/verify?family=power&n=200&p=4").json()
    assert body["exact_match"] and body["verdict"] == "PASS"
    assert client.get("/api/verify?family=bogus").status_code == 422


def test_websocket_receives_broadcast_of_every_compute(client):
    """The server/client sync claim, actually exercised."""
    with client.websocket_connect("/ws") as ws:
        assert ws.receive_json()["type"] == "state"      # snapshot on join
        client.post("/api/compute", json={
            "family": "geometric", "n": 8, "a": 1, "r": 2, "client": "tester"})
        msg = ws.receive_json()
        assert msg["type"] == "update"
        assert msg["payload"]["result"] == "255"
        assert msg["payload"]["client"] == "tester"


def test_react_client_is_served_by_the_api_process(client):
    """One process serves both, so a single deploy is enough."""
    page = client.get("/app/")
    assert page.status_code == 200
    assert "Omnidimensional" in page.text
    assert client.get("/", follow_redirects=False).status_code in (302, 307)
