from datetime import timedelta
import hashlib
import secrets

from fastapi.testclient import TestClient
from app import auth
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
    headers={"Authorization":f"Bearer {admin_token}"}
    listed = client.get("/api/admin/users", headers=headers)
    assert listed.status_code == 200
    listed_user = next(item for item in listed.json()["items"] if item["id"] == user["id"])
    assert listed_user["organization_id"] == user["organization_id"]
    assert listed_user["organization_name"] == "测试企业"
    assert client.post("/api/auth/login", json={"email":email,"password":"Strong-password-123"}).status_code == 403
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


def test_remembered_member_session_restores_without_password():
    email = f"remember-{secrets.token_hex(4)}@example.com"
    created = iso(now())
    with connection() as conn:
        org_id = conn.execute("INSERT INTO organizations (name,status,created_at) VALUES ('记忆会话测试','approved',?)", (created,)).lastrowid
        conn.execute("INSERT INTO users (organization_id,email,password_hash,role,status,email_verified,created_at) VALUES (?,?,?,'owner','approved',1,?)",
                     (org_id,email,hasher.hash("Strong-password-123"),created))
        conn.execute("INSERT INTO licenses (organization_id,seats,expires_at,status,updated_at) VALUES (?,?,?,'active',?)",
                     (org_id,1,iso(now()+timedelta(days=30)),created))
        conn.commit()
    browser = TestClient(app)
    login = browser.post("/api/auth/login",json={"email":email,"password":"Strong-password-123","remember_me":True})
    assert login.status_code == 200
    assert "cap_remember=" in login.headers["set-cookie"]
    assert "httponly" in login.headers["set-cookie"].lower()
    assert "samesite=strict" in login.headers["set-cookie"].lower()
    assert login.cookies["cap_remember"] != login.json()["access_token"]
    restored = browser.get("/api/auth/restore")
    assert restored.status_code == 200
    assert restored.json()["access_token"] != login.json()["access_token"]
    assert restored.cookies["cap_remember"] != login.cookies["cap_remember"]
    assert browser.post("/api/auth/logout",headers={"Authorization":"Bearer "+restored.json()["access_token"]}).status_code == 204
    assert browser.get("/api/auth/restore").status_code == 401


def test_admin_login_never_sets_remember_cookie():
    admin_id, _ = seed_admin()
    with connection() as conn:
        email = conn.execute("SELECT email FROM users WHERE id=?", (admin_id,)).fetchone()["email"]
    response = TestClient(app).post("/api/auth/login",json={"email":email,"password":"Admin-password-123","remember_me":True})
    assert response.status_code == 200
    assert "cap_remember=\"\"" in response.headers.get("set-cookie", "") or "cap_remember=;" in response.headers.get("set-cookie", "")

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


def test_password_reset_request_has_five_minute_cooldown(monkeypatch):
    monkeypatch.setenv("CAPABILITY_DEV_EXPOSE_TOKENS", "1")
    monkeypatch.delenv("CAPABILITY_REQUIRE_AUTH", raising=False)
    _, _ = seed_admin()
    with connection() as conn:
        email = conn.execute("SELECT email FROM users WHERE role='admin' ORDER BY id DESC LIMIT 1").fetchone()[0]
    first = client.post("/api/auth/password-reset/request", json={"email": email})
    assert first.status_code == 200
    first_token = first.json()["development_token"]
    immediate = client.post("/api/auth/password-reset/request", json={"email": email})
    assert immediate.status_code == 200
    assert "development_token" not in immediate.json()
    with connection() as conn:
        rows = conn.execute("SELECT token_hash FROM password_reset_tokens WHERE user_id="
                            "(SELECT id FROM users WHERE email=?)", (email,)).fetchall()
        assert len(rows) == 1
        conn.execute("UPDATE password_reset_tokens SET created_at=? WHERE token_hash=?",
                     (iso(now() - timedelta(minutes=6)), hashlib.sha256(first_token.encode()).hexdigest()))
        conn.commit()
    later = client.post("/api/auth/password-reset/request", json={"email": email})
    assert later.status_code == 200
    assert later.json()["development_token"] != first_token
    assert client.post("/api/auth/password-reset/confirm", json={
        "token": first_token, "new_password": "Another-password-789"}).status_code == 400


def test_password_reset_can_retry_after_mail_delivery_failure(monkeypatch):
    monkeypatch.setenv("CAPABILITY_REQUIRE_AUTH", "1")
    monkeypatch.setenv("CAPABILITY_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("CAPABILITY_SMTP_FROM", "advisor@example.com")
    _, _ = seed_admin()
    with connection() as conn:
        email = conn.execute("SELECT email FROM users WHERE role='admin' ORDER BY id DESC LIMIT 1").fetchone()[0]

    def failed_mail(*_args, **_kwargs):
        from fastapi import HTTPException
        raise HTTPException(503, "验证邮件发送失败，请稍后重试")

    monkeypatch.setattr(auth, "_send_password_reset_mail", failed_mail)
    first = client.post("/api/auth/password-reset/request", json={"email": email})
    assert first.status_code == 503
    monkeypatch.setattr(auth, "_send_password_reset_mail", lambda *_args, **_kwargs: True)
    retry = client.post("/api/auth/password-reset/request", json={"email": email})
    assert retry.status_code == 200
    with connection() as conn:
        rows = conn.execute("SELECT used_at FROM password_reset_tokens WHERE user_id="
                            "(SELECT id FROM users WHERE email=?) ORDER BY created_at", (email,)).fetchall()
    assert len(rows) == 2
    assert sum(row["used_at"] is None for row in rows) == 1


def test_user_verifies_email_with_single_use_token(monkeypatch):
    monkeypatch.setenv("CAPABILITY_DEV_EXPOSE_TOKENS", "1")
    monkeypatch.delenv("CAPABILITY_REQUIRE_AUTH", raising=False)
    monkeypatch.delenv("CAPABILITY_SMTP_HOST", raising=False)
    email = f"verify-{secrets.token_hex(4)}@example.com"
    registered = client.post("/api/auth/register", json={
        "organization_name": "邮箱自助验证企业", "email": email, "password": "Strong-password-123"})
    assert registered.status_code == 201
    token = registered.json()["development_token"]
    assert registered.json()["verification_mail_sent"] is False
    assert client.post("/api/auth/verify-email", json={"token": token}).json()["status"] == "verified_pending_admin_approval"
    assert client.post("/api/auth/verify-email", json={"token": token}).status_code == 400
    with connection() as conn:
        user = conn.execute("SELECT email_verified,status FROM users WHERE email=?", (email,)).fetchone()
    assert user["email_verified"] == 1 and user["status"] == "pending"


def test_verification_resend_invalidates_old_code_and_throttles(monkeypatch):
    monkeypatch.setenv("CAPABILITY_DEV_EXPOSE_TOKENS", "1")
    monkeypatch.delenv("CAPABILITY_REQUIRE_AUTH", raising=False)
    monkeypatch.delenv("CAPABILITY_SMTP_HOST", raising=False)
    email = f"resend-{secrets.token_hex(4)}@example.com"
    first = client.post("/api/auth/register", json={
        "organization_name": "重发测试企业", "email": email, "password": "Strong-password-123"}).json()["development_token"]
    immediate = client.post("/api/auth/verify-email/resend", json={"email": email})
    assert immediate.status_code == 200 and "development_token" not in immediate.json()
    with connection() as conn:
        conn.execute("UPDATE email_verification_tokens SET created_at=? WHERE token_hash=?",
                     (iso(now() - timedelta(minutes=6)), hashlib.sha256(first.encode()).hexdigest()))
        conn.commit()
    second = client.post("/api/auth/verify-email/resend", json={"email": email}).json()["development_token"]
    assert second != first
    assert client.post("/api/auth/verify-email", json={"token": first}).status_code == 400
    assert client.post("/api/auth/verify-email", json={"token": second}).status_code == 200


def test_protected_registration_requires_mail_configuration(monkeypatch):
    monkeypatch.setenv("CAPABILITY_REQUIRE_AUTH", "1")
    monkeypatch.delenv("CAPABILITY_SMTP_HOST", raising=False)
    response = client.post("/api/auth/register", json={
        "organization_name": "生产注册测试", "email": f"prod-{secrets.token_hex(4)}@example.com",
        "password": "Strong-password-123"})
    assert response.status_code == 503


def test_configured_smtp_sends_verification_and_reset_codes(monkeypatch):
    sent = []

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            assert (host, port, timeout) == ("smtp.example.com", 587, 10)

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def starttls(self, *, context):
            assert context is not None

        def send_message(self, message):
            sent.append(message)

    monkeypatch.setattr(auth.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setenv("CAPABILITY_REQUIRE_AUTH", "1")
    monkeypatch.setenv("CAPABILITY_DEV_EXPOSE_TOKENS", "1")
    monkeypatch.setenv("CAPABILITY_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("CAPABILITY_SMTP_FROM", "advisor@example.com")
    monkeypatch.delenv("CAPABILITY_SMTP_USERNAME", raising=False)
    monkeypatch.delenv("CAPABILITY_SMTP_PASSWORD", raising=False)
    email = f"mail-{secrets.token_hex(4)}@example.com"
    registered = client.post("/api/auth/register", json={
        "organization_name": "邮件测试企业", "email": email, "password": "Strong-password-123"})
    assert registered.status_code == 201
    assert registered.json()["verification_mail_sent"] is True
    assert "development_token" not in registered.json()
    assert sent[0]["To"] == email and "邮箱验证" in sent[0]["Subject"]
    requested = client.post("/api/auth/password-reset/request", json={"email": email})
    assert requested.status_code == 200 and "development_token" not in requested.json()
    assert sent[1]["To"] == email and "密码重置" in sent[1]["Subject"]
    assert sent[0].get_content() != sent[1].get_content()
