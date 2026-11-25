from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
HEADERS = "sku,product,cpu_cores,gpu_cores,memory_gb,os,evidence_level,source_url,note\n"


def test_valid_sku_preview_is_read_only():
    content = HEADERS + "SLU-001,Surface Laptop Ultra,18,5120,128,Windows 11 Pro,official_claim,https://example.com/spec,平台规格\n"
    body = client.post("/api/catalog/import/skus/preview", content=content, headers={"content-type": "text/csv"}).json()
    assert body["valid"] is True
    assert body["rows_received"] == 1
    assert body["rows_valid"] == 1
    assert body["mutated"] is False
    assert body["normalized_rows"][0]["memory_gb"] == 128


def test_duplicate_and_missing_provenance_are_rejected():
    content = HEADERS + (
        "SLU-001,Surface Laptop Ultra,18,5120,128,Windows 11 Pro,official_claim,,first\n"
        "SLU-001,Surface Laptop Ultra,20,6144,128,Windows 11 Pro,official_claim,http://invalid,second\n"
    )
    body = client.post("/api/catalog/import/skus/preview", content=content, headers={"content-type": "text/csv"}).json()
    codes = {error["code"] for error in body["errors"]}
    assert body["valid"] is False
    assert body["rows_valid"] == 0
    assert {"duplicate", "required_for_evidence", "https_required"} <= codes


def test_unknown_evidence_allows_blank_source_but_not_bad_number():
    content = HEADERS + "DRAFT-1,待核实 SKU,nope,,,Windows 11,unknown,,占位\n"
    body = client.post("/api/catalog/import/skus/preview", content=content, headers={"content-type": "text/csv"}).json()
    assert body["valid"] is False
    assert any(error["code"] == "invalid_integer" for error in body["errors"])
