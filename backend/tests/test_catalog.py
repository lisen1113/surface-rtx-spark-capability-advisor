from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

def test_catalog_seed():
 response = client.get("/api/catalog/skus")
 assert response.status_code == 200
 items = response.json()["items"]
 assert any(x["sku"] == "S2" for x in items)
 assert all(x["evidence_level"] == "user_supplied_unverified" for x in items)

def test_model_placeholders_not_benchmarks():
 response = client.get("/api/catalog/models")
 assert response.status_code == 200
 assert all(x["evidence_level"] == "unknown" for x in response.json()["items"])

def test_sources_include_limitations():
 sources = client.get("/api/catalog/sources").json()["items"]
 assert len(sources) >= 3
 assert all(s["limitations"] and s["source_url"].startswith("https://") for s in sources)
