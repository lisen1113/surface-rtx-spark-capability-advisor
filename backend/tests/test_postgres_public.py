"""Real PostgreSQL smoke test, enabled by an ephemeral CI database URL."""
from datetime import timedelta
import os
from pathlib import Path
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app import auth, catalog
from app.auth import iso, now
from app.auth_store import connection
from app.main import app


def test_public_registration_verification_license_and_login(monkeypatch, tmp_path):
    dsn = os.getenv("CAPABILITY_TEST_POSTGRES_URL")
    if not dsn:
        pytest.skip("Requires an isolated PostgreSQL test database")
    psycopg = pytest.importorskip("psycopg")
    schema = Path(__file__).resolve().parents[1] / "sql" / "auth_postgres_v1.sql"
    with psycopg.connect(dsn) as db:
        db.execute(schema.read_text(encoding="utf-8"))

    catalog_path = tmp_path / "capability.sqlite3"
    with sqlite3.connect(catalog_path) as db:
        db.executescript(catalog.SCHEMA)
    monkeypatch.setattr(catalog, "DB_PATH", catalog_path)
    monkeypatch.setenv("CAPABILITY_AUTH_DATABASE_URL", dsn)
    monkeypatch.setenv("CAPABILITY_DEPLOYMENT_MODE", "public")
    monkeypatch.setenv("CAPABILITY_REQUIRE_AUTH", "1")
    monkeypatch.setenv("CAPABILITY_SMTP_HOST", "smtp.example.invalid")
    monkeypatch.setenv("CAPABILITY_SMTP_FROM", "advisor@example.invalid")
    monkeypatch.setenv("CAPABILITY_SMTP_USERNAME", "advisor@example.invalid")
    monkeypatch.setenv("CAPABILITY_SMTP_PASSWORD", "test-only-credential")
    monkeypatch.setenv("CAPABILITY_MFA_MASTER_KEY", "x" * 32)
    monkeypatch.setenv("CAPABILITY_PUBLIC_BASE_URL", "https://advisor.example.invalid")
    monkeypatch.delenv("CAPABILITY_DEV_EXPOSE_TOKENS", raising=False)
    sent = []
    monkeypatch.setattr(auth, "_send_verification_mail", lambda email, token: sent.append(token) or True)

    with TestClient(app, base_url="https://advisor.example.invalid") as client:
        assert client.get("/health").status_code == 200
        assert client.get("/api/catalog/skus").status_code == 401
        registered = client.post("/api/auth/register", json={
            "organization_name": "集成测试企业", "email": "integration@example.invalid",
            "password": "Integration-password-123"})
        assert registered.status_code == 201, registered.text
        assert "development_token" not in registered.json()
        assert client.post("/api/auth/verify-email", json={"token": sent[0]}).status_code == 200

        with connection() as db:
            row = db.execute("SELECT id,organization_id FROM users WHERE email=?", ("integration@example.invalid",)).fetchone()
            db.execute("UPDATE users SET status='approved' WHERE id=?", (row["id"],))
            db.execute("UPDATE organizations SET status='approved' WHERE id=?", (row["organization_id"],))
            db.execute("INSERT INTO licenses (organization_id,seats,expires_at,status,updated_at) VALUES (?,?,?,'active',?)",
                       (row["organization_id"], 1, iso(now() + timedelta(days=1)), iso(now())))
            db.commit()
        logged_in = client.post("/api/auth/login", json={"email": "integration@example.invalid", "password": "Integration-password-123"})
        assert logged_in.status_code == 200, logged_in.text
        headers = {"Authorization": "Bearer " + logged_in.json()["access_token"]}
        assert client.get("/api/catalog/skus", headers=headers).status_code == 200
