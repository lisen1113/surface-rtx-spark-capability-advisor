import pytest
from fastapi.testclient import TestClient

from app.deployment_readiness import assert_deployment_configuration, deployment_configuration_errors
from app.main import app


def test_local_mode_keeps_offline_demo_available(monkeypatch):
    monkeypatch.delenv("CAPABILITY_DEPLOYMENT_MODE", raising=False)
    assert deployment_configuration_errors() == []
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200


@pytest.mark.parametrize("mode", ["shared", "public"])
def test_deployment_rejects_anonymous_or_incomplete_configuration(monkeypatch, mode):
    monkeypatch.setenv("CAPABILITY_DEPLOYMENT_MODE", mode)
    for name in ("CAPABILITY_REQUIRE_AUTH", "CAPABILITY_SMTP_HOST", "CAPABILITY_SMTP_FROM",
                 "CAPABILITY_MFA_MASTER_KEY", "CAPABILITY_PUBLIC_BASE_URL"):
        monkeypatch.delenv(name, raising=False)
    errors = deployment_configuration_errors()
    assert any("CAPABILITY_REQUIRE_AUTH" in item for item in errors)
    assert any("SMTP" in item for item in errors)
    assert any("HTTPS" in item for item in errors)
    with pytest.raises(RuntimeError, match="Deployment configuration incomplete"):
        with TestClient(app):
            pass


def test_shared_deployment_accepts_configured_https_origin_without_exposing_values(monkeypatch):
    mode = "shared"
    monkeypatch.setenv("CAPABILITY_DEPLOYMENT_MODE", mode)
    monkeypatch.setenv("CAPABILITY_REQUIRE_AUTH", "1")
    monkeypatch.setenv("CAPABILITY_SMTP_HOST", "smtp.example.invalid")
    monkeypatch.setenv("CAPABILITY_SMTP_FROM", "advisor@example.invalid")
    monkeypatch.setenv("CAPABILITY_MFA_MASTER_KEY", "x" * 32)
    monkeypatch.setenv("CAPABILITY_PUBLIC_BASE_URL", "https://advisor.example.invalid")
    monkeypatch.delenv("CAPABILITY_DEV_EXPOSE_TOKENS", raising=False)
    assert_deployment_configuration()
    monkeypatch.setenv("CAPABILITY_DEV_EXPOSE_TOKENS", "1")
    assert "CAPABILITY_DEV_EXPOSE_TOKENS must be disabled" in deployment_configuration_errors()
    monkeypatch.setenv("CAPABILITY_PUBLIC_BASE_URL", "http://advisor.example.invalid")
    assert "CAPABILITY_PUBLIC_BASE_URL must be an HTTPS origin" in deployment_configuration_errors()


def test_public_mode_requires_postgres_even_with_other_settings_present(monkeypatch):
    monkeypatch.setenv("CAPABILITY_DEPLOYMENT_MODE", "public")
    monkeypatch.setenv("CAPABILITY_REQUIRE_AUTH", "1")
    monkeypatch.setenv("CAPABILITY_SMTP_HOST", "smtp.example.invalid")
    monkeypatch.setenv("CAPABILITY_SMTP_FROM", "advisor@example.invalid")
    monkeypatch.setenv("CAPABILITY_MFA_MASTER_KEY", "x" * 32)
    monkeypatch.setenv("CAPABILITY_PUBLIC_BASE_URL", "https://advisor.example.invalid")
    monkeypatch.delenv("CAPABILITY_DEV_EXPOSE_TOKENS", raising=False)
    monkeypatch.delenv("CAPABILITY_AUTH_DATABASE_URL", raising=False)
    assert any("CAPABILITY_AUTH_DATABASE_URL" in error for error in deployment_configuration_errors())
    with pytest.raises(RuntimeError, match="CAPABILITY_AUTH_DATABASE_URL"):
        assert_deployment_configuration()
    monkeypatch.setenv("CAPABILITY_AUTH_DATABASE_URL", "postgresql://localhost/advisor")
    assert deployment_configuration_errors() == []


def test_unknown_deployment_mode_fails_closed(monkeypatch):
    monkeypatch.setenv("CAPABILITY_DEPLOYMENT_MODE", "publc")
    assert deployment_configuration_errors() == ["CAPABILITY_DEPLOYMENT_MODE must be local, shared, or public"]
