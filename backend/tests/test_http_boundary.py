"""Shared deployments must not serve arbitrary Host headers."""

from fastapi.testclient import TestClient

from app.main import app


def _shared_settings(monkeypatch):
    monkeypatch.setenv("CAPABILITY_DEPLOYMENT_MODE", "shared")
    monkeypatch.setenv("CAPABILITY_REQUIRE_AUTH", "1")
    monkeypatch.setenv("CAPABILITY_SMTP_HOST", "smtp.example.invalid")
    monkeypatch.setenv("CAPABILITY_SMTP_FROM", "advisor@example.invalid")
    monkeypatch.setenv("CAPABILITY_MFA_MASTER_KEY", "x" * 32)
    monkeypatch.setenv("CAPABILITY_PUBLIC_BASE_URL", "https://advisor.example.invalid")
    monkeypatch.delenv("CAPABILITY_DEV_EXPOSE_TOKENS", raising=False)


def test_shared_mode_rejects_unexpected_host(monkeypatch):
    _shared_settings(monkeypatch)
    with TestClient(app, base_url="https://advisor.example.invalid") as client:
        response = client.get("/health", headers={"Host": "attacker.example.invalid"})
        assert response.status_code == 400
        assert response.text == "Host not allowed"
        assert client.get("/health").status_code == 200


def test_loopback_preview_requires_opt_in_and_loopback_peer(monkeypatch):
    _shared_settings(monkeypatch)
    with TestClient(app, base_url="http://127.0.0.1:8011", client=("127.0.0.1", 50000)) as client:
        assert client.get("/health").status_code == 400
        monkeypatch.setenv("CAPABILITY_ALLOW_LOOPBACK_PREVIEW", "1")
        assert client.get("/health").status_code == 200
        assert client.get("/health", headers={"Host": "attacker.example.invalid"}).status_code == 400
    with TestClient(app, base_url="http://127.0.0.1:8011", client=("192.0.2.20", 50000)) as client:
        assert client.get("/health").status_code == 400


def test_security_headers_on_local_responses(monkeypatch):
    monkeypatch.setenv("CAPABILITY_DEPLOYMENT_MODE", "local")
    with TestClient(app) as client:
        response = client.get("/")
    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "same-origin"


def test_sensitive_pages_and_api_responses_are_not_cached(monkeypatch):
    monkeypatch.setenv("CAPABILITY_DEPLOYMENT_MODE", "local")
    with TestClient(app) as client:
        for path in ("/account", "/admin", "/api/about", "/api/unknown"):
            response = client.get(path)
            assert response.headers["cache-control"] == "no-store"
