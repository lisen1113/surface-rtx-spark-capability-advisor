import base64

from fastapi.testclient import TestClient

from app import auth
from app.catalog import connection
from app.main import app
from app.mfa import totp
from tests.test_auth import seed_admin

client = TestClient(app)


def test_totp_matches_rfc_6238_sha1_vector():
    # RFC 6238 Appendix B: 8-digit result 94287082 at T=59; this UI uses 6 digits.
    assert totp(b"12345678901234567890", 59 // 30) == "287082"


def test_protected_admin_enrolls_mfa_and_reauthenticates(monkeypatch):
    monkeypatch.setenv("CAPABILITY_REQUIRE_AUTH", "1")
    monkeypatch.setenv("CAPABILITY_MFA_MASTER_KEY", "test-only-master-key-with-at-least-32-bytes")
    user_id, old_token = seed_admin()
    fixed = auth.now()
    monkeypatch.setattr(auth, "now", lambda: fixed)
    headers = {"Authorization": f"Bearer {old_token}"}
    assert client.get("/api/admin/users", headers=headers).status_code == 403
    status = client.get("/api/admin/mfa/status", headers=headers).json()
    assert status == {"enabled": False, "required": True, "configured": True}
    assert client.post("/api/admin/mfa/enroll", headers=headers, json={"password": "wrong"}).status_code == 401
    enrolled = client.post("/api/admin/mfa/enroll", headers=headers, json={"password": "Admin-password-123"})
    assert enrolled.status_code == 200
    encoded = enrolled.json()["secret"]
    secret = base64.b32decode(encoded + "=" * (-len(encoded) % 8))
    assert enrolled.json()["otpauth_uri"].startswith("otpauth://totp/")
    previous_code = totp(secret, int(fixed.timestamp()) // 30 - 1)
    assert client.post("/api/admin/mfa/confirm", headers=headers, json={"code": previous_code}).status_code == 200
    assert client.get("/api/auth/me", headers=headers).status_code == 401
    with connection() as conn:
        assert conn.execute("SELECT 1 FROM admin_mfa WHERE user_id=?", (user_id,)).fetchone()
        email = conn.execute("SELECT email FROM users WHERE id=?", (user_id,)).fetchone()[0]
    assert client.post("/api/auth/login", json={"email": email, "password": "Admin-password-123"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": email, "password": "Admin-password-123", "mfa_code": previous_code}).status_code == 401
    current_code = totp(secret, int(fixed.timestamp()) // 30)
    logged_in = client.post("/api/auth/login", json={"email": email, "password": "Admin-password-123", "mfa_code": current_code})
    assert logged_in.status_code == 200
    new_headers = {"Authorization": f"Bearer {logged_in.json()['access_token']}"}
    assert client.get("/api/admin/users", headers=new_headers).status_code == 200
    assert client.post("/api/auth/login", json={"email": email, "password": "Admin-password-123", "mfa_code": current_code}).status_code == 401
    for _ in range(3):
        assert client.post("/api/auth/login", json={"email": email, "password": "Admin-password-123", "mfa_code": current_code}).status_code == 401
    assert client.post("/api/auth/login", json={"email": email, "password": "Admin-password-123", "mfa_code": current_code}).status_code == 401
    assert client.post("/api/auth/login", json={"email": email, "password": "Admin-password-123", "mfa_code": current_code}).status_code == 429


def test_protected_admin_requires_server_mfa_key(monkeypatch):
    monkeypatch.setenv("CAPABILITY_REQUIRE_AUTH", "1")
    monkeypatch.delenv("CAPABILITY_MFA_MASTER_KEY", raising=False)
    _, token = seed_admin()
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/admin/users", headers=headers).status_code == 503
    assert client.post("/api/admin/mfa/enroll", headers=headers, json={"password": "Admin-password-123"}).status_code == 503
