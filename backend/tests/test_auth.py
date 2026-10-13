from datetime import timedelta
import hashlib
import secrets

from fastapi.testclient import TestClient
from app.auth import hasher, iso, now
from app.catalog import connection
from app.main import app

client = TestClient(app)

def seed_admin() -> tuple[int, str]:
    email = f"admin-{secrets.token_hex(4)}@example.com"
    token = secrets.token_urlsafe(24)
    created = iso(now())
    with connection() as conn:
        row = conn.execute("INSERT INTO users (email,password_hash,role,status,email_verified,created_at,approved_at) VALUES (?,?,'admin','approved',1,?,?)", (email, hasher.hash("Admin-password-123"), created, created))
        conn.execute("INSERT INTO sessions VALUES (?,?,?,?,NULL)", (hashlib.sha256(token.encode()).hexdigest(), row.lastrowid, created, iso(now()+timedelta(hours=1))))
        conn.commit()
    return row.lastrowid, token

def test_registration_approval_license_and_login_flow():
    _, admin_token = seed_admin()
    email = f"user-{secrets.token_hex(4)}@example.com"
    registered = client.post("/api/auth/register", json={"organization_name":"测试企业","email":email,"password":"Strong-password-123"})
    assert registered.status_code == 201
    with connection() as conn:
        user = dict(conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone())
    assert client.post("/api/auth/login", json={"email":email,"password":"Strong-password-123"}).status_code == 403
    headers={"Authorization":f"Bearer {admin_token}"}
    assert client.post(f"/api/admin/users/{user['id']}/verify-email", headers=headers).status_code == 200
    assert client.post(f"/api/admin/users/{user['id']}/approve", headers=headers).status_code == 200
    assert client.post("/api/auth/login", json={"email":email,"password":"Strong-password-123"}).status_code == 403
    assert client.put("/api/admin/licenses", headers=headers, json={"organization_id":user["organization_id"],"seats":1,"expires_at":iso(now()+timedelta(days=30))}).status_code == 200
    login = client.post("/api/auth/login", json={"email":email,"password":"Strong-password-123"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    assert client.get("/api/auth/me", headers={"Authorization":f"Bearer {token}"}).json()["organization_id"] == user["organization_id"]
    assert client.post("/api/auth/logout", headers={"Authorization":f"Bearer {token}"}).status_code == 204
    assert client.get("/api/auth/me", headers={"Authorization":f"Bearer {token}"}).status_code == 401

def test_failed_login_locks_after_five_attempts():
    email = f"locked-{secrets.token_hex(4)}@example.com"
    created=iso(now())
    with connection() as conn:
        conn.execute("INSERT INTO users (email,password_hash,role,status,email_verified,created_at) VALUES (?,?,'admin','approved',1,?)", (email,hasher.hash("Correct-password-123"),created))
        conn.commit()
    for _ in range(5):
        response=client.post("/api/auth/login",json={"email":email,"password":"Wrong-password-123"})
        assert response.status_code == 401
    assert client.post("/api/auth/login",json={"email":email,"password":"Correct-password-123"}).status_code == 429

def test_password_reset_is_single_use_and_revokes_sessions(monkeypatch):
    _, admin_token = seed_admin()
    monkeypatch.setenv("CAPABILITY_DEV_EXPOSE_TOKENS", "1")
    with connection() as conn:
        email = conn.execute("SELECT email FROM users WHERE role='admin' ORDER BY id DESC LIMIT 1").fetchone()[0]
    requested = client.post("/api/auth/password-reset/request", json={"email": email})
    token = requested.json()["development_token"]
    confirmed = client.post("/api/auth/password-reset/confirm", json={"token":token,"new_password":"New-admin-password-456"})
    assert confirmed.status_code == 200
    assert client.get("/api/auth/me", headers={"Authorization":f"Bearer {admin_token}"}).status_code == 401
    assert client.post("/api/auth/password-reset/confirm", json={"token":token,"new_password":"Another-password-789"}).status_code == 400
    assert client.post("/api/auth/login", json={"email":email,"password":"New-admin-password-456"}).status_code == 200

def test_password_reset_request_does_not_disclose_unknown_email(monkeypatch):
    monkeypatch.delenv("CAPABILITY_DEV_EXPOSE_TOKENS", raising=False)
    response = client.post("/api/auth/password-reset/request", json={"email":"missing@example.com"})
    assert response.status_code == 200
    assert "development_token" not in response.json()
