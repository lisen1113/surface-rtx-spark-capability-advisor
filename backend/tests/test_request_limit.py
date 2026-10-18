from app.request_limit import RequestLimiter, source_address
from fastapi.testclient import TestClient
from app import main


def test_auth_request_limit_and_window_expiry():
    limiter = RequestLimiter()
    path = "/api/auth/register"
    assert all(limiter.check("203.0.113.1", path, 100.0) == 0 for _ in range(10))
    assert limiter.check("203.0.113.1", path, 100.0) >= 3600
    assert limiter.check("203.0.113.2", path, 100.0) == 0
    assert limiter.check("203.0.113.1", path, 3700.0) == 0


def test_only_loopback_proxy_can_supply_forwarded_address():
    assert source_address("127.0.0.1", "203.0.113.9") == "203.0.113.9"
    assert source_address("203.0.113.2", "203.0.113.9") == "203.0.113.2"
    assert source_address("127.0.0.1", "not-an-address") == "127.0.0.1"
    assert source_address("127.0.0.1", "203.0.113.9, 127.0.0.1") == "203.0.113.9"


def test_public_middleware_limits_auth_posts_only(monkeypatch):
    monkeypatch.setenv("CAPABILITY_DEPLOYMENT_MODE", "public")
    monkeypatch.setenv("CAPABILITY_PUBLIC_BASE_URL", "https://advisor.example.invalid")
    monkeypatch.setattr(main, "limiter", RequestLimiter())
    client = TestClient(main.app, base_url="https://advisor.example.invalid",
                        client=("203.0.113.10", 50000))
    for _ in range(10):
        assert client.post("/api/auth/register", json={}).status_code == 422
    blocked = client.post("/api/auth/register", json={})
    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) > 0
    assert blocked.headers["cache-control"] == "no-store"
    assert client.get("/account").status_code == 200
    assert client.post("/api/auth/register", json={},
                       headers={"Host": "evil.example.invalid"}).status_code == 400
