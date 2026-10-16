from datetime import timedelta
import hashlib
import secrets

from fastapi.testclient import TestClient
from app.auth import hasher, iso, now
from app.catalog import connection
from app.main import app

client = TestClient(app)


def licensed_user(expires_delta: timedelta) -> str:
    created = iso(now())
    token = secrets.token_urlsafe(24)
    with connection() as conn:
        org = conn.execute("INSERT INTO organizations (name,status,created_at) VALUES (?,'approved',?)", (f"租户-{secrets.token_hex(4)}", created))
        user = conn.execute("INSERT INTO users (organization_id,email,password_hash,role,status,email_verified,created_at,approved_at) VALUES (?,?,?,'owner','approved',1,?,?)", (org.lastrowid, f"protected-{secrets.token_hex(4)}@example.com", hasher.hash("Protected-password-123"), created, created))
        conn.execute("INSERT INTO licenses VALUES (?,?,?,'active',?)", (org.lastrowid, 2, iso(now()+expires_delta), created))
        conn.execute("INSERT INTO sessions VALUES (?,?,?,?,NULL)", (hashlib.sha256(token.encode()).hexdigest(), user.lastrowid, created, iso(now()+timedelta(hours=1))))
        conn.commit()
    return token


def test_protected_calculation_requires_login_when_enabled(monkeypatch):
    monkeypatch.setenv("CAPABILITY_REQUIRE_AUTH", "1")
    response = client.post("/api/tco/calculate", json={"purchase_price_cny": 10000})
    assert response.status_code == 401


def test_protected_calculation_accepts_active_license(monkeypatch):
    monkeypatch.setenv("CAPABILITY_REQUIRE_AUTH", "1")
    token = licensed_user(timedelta(days=30))
    response = client.post("/api/tco/calculate", headers={"Authorization":f"Bearer {token}"}, json={"purchase_price_cny":10000})
    assert response.status_code == 200


def test_protected_calculation_rechecks_expired_license(monkeypatch):
    monkeypatch.setenv("CAPABILITY_REQUIRE_AUTH", "1")
    token = licensed_user(timedelta(minutes=-1))
    response = client.post("/api/tco/calculate", headers={"Authorization":f"Bearer {token}"}, json={"purchase_price_cny":10000})
    assert response.status_code == 403
    assert "过期" in response.json()["detail"]


def test_protected_catalog_knowledge_faq_and_deployment_require_license(monkeypatch):
    monkeypatch.setenv("CAPABILITY_REQUIRE_AUTH", "1")
    paths = ("/api/catalog/imported-skus", "/api/knowledge/frameworks", "/api/faq",
             "/api/deployment/sku/EP2-56792")
    for path in paths:
        assert client.get(path).status_code == 401
    token = licensed_user(timedelta(days=30))
    headers = {"Authorization": f"Bearer {token}"}
    for path in paths:
        assert client.get(path, headers=headers).status_code in (200, 404)
    expired = licensed_user(timedelta(minutes=-1))
    for path in paths:
        assert client.get(path, headers={"Authorization": f"Bearer {expired}"}).status_code == 403


def test_public_pages_forward_session_token_to_protected_apis():
    for path in ("/", "/deployment"):
        page = client.get(path)
        assert page.status_code == 200
        assert "sessionStorage.getItem('cap_token')" in page.text
        assert "Authorization:'Bearer '+token" in page.text
