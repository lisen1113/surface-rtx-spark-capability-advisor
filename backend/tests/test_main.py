from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["local"] is True

def test_memory_estimate_is_explicitly_estimate():
    response = client.post("/api/estimate/memory", json={
        "parameters_billion": 70, "bits_per_weight": 4,
        "unified_memory_gb": 128
    })
    assert response.status_code == 200
    body = response.json()
    assert body["estimated_weight_gb"] == 35
    assert body["evidence_level"] == "engineering_estimate"
    assert "tok_per_second" not in body

def test_invalid_negative_parameter_rejected():
    response = client.post("/api/estimate/memory", json={"parameters_billion": -1, "bits_per_weight": 4})
    assert response.status_code == 422
