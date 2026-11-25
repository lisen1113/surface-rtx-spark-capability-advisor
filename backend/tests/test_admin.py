from datetime import timedelta
from fastapi.testclient import TestClient
from app.auth import iso, now
from app.main import app
from tests.test_auth import seed_admin

client=TestClient(app)

def test_admin_lists_users_licenses_and_audit():
 _,token=seed_admin(); headers={"Authorization":f"Bearer {token}"}
 users=client.get('/api/admin/users',headers=headers)
 assert users.status_code==200 and users.json()['items']
 audit=client.get('/api/admin/audit?limit=10',headers=headers)
 assert audit.status_code==200
 assert client.get('/api/admin/licenses',headers=headers).status_code==200

def test_admin_endpoints_reject_anonymous():
 for path in ('/api/admin/users','/api/admin/licenses','/api/admin/audit'):
  assert client.get(path).status_code==401
