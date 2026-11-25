from fastapi.testclient import TestClient
from app import catalog
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["local"] is True
    assert response.json()["database"] == "ready"


def test_health_reports_database_failure(monkeypatch, tmp_path):
    blocking_file = tmp_path / "not-a-directory"
    blocking_file.write_text("occupied")
    monkeypatch.setattr(catalog, "DB_PATH", blocking_file / "capability.sqlite3")
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["detail"] == "本地数据库不可用"

def test_memory_estimate_is_explicitly_estimate():
    response = client.post("/api/estimate/memory", json={
        "parameters_billion": 70, "bits_per_weight": 4,
        "unified_memory_gb": 128
    })
    assert response.status_code == 200
    body = response.json()
    assert body["estimated_weight_gb"] == 35
    assert body["evidence_level"] == "engineering_estimate"
    assert body["fits_in_memory"] == "fits"
    assert body["compatible"] == "unknown"
    assert body["can_start"] == "unknown"
    assert body["usable"] == "unknown"
    assert "tok_per_second" not in body

def test_capacity_includes_quantization_overhead_and_reserves():
    response = client.post("/api/estimate/memory", json={
        "parameters_billion": 70, "bits_per_weight": 4,
        "unified_memory_gb": 60, "quantization_overhead_ratio": 0.1,
        "kv_cache_gb": 8, "runtime_reserve_gb": 8, "os_reserve_gb": 12,
        "runtime_compatible": True,
    })
    body = response.json()
    assert body["required_gb"] == 66.5
    assert body["fits_in_memory"] == "does_not_fit"
    assert body["can_start"] == "does_not_fit"
    assert body["compatible"] == "fits"

def test_runtime_incompatibility_blocks_start_even_when_memory_fits():
    body = client.post("/api/estimate/memory", json={
        "parameters_billion": 7, "bits_per_weight": 4,
        "unified_memory_gb": 128, "runtime_compatible": False,
    }).json()
    assert body["fits_in_memory"] == "fits"
    assert body["compatible"] == "does_not_fit"
    assert body["can_start"] == "does_not_fit"

def test_invalid_negative_parameter_rejected():
    response = client.post("/api/estimate/memory", json={"parameters_billion": -1, "bits_per_weight": 4})
    assert response.status_code == 422
