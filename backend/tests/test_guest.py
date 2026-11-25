"""Guest access is a narrow public projection, not a License bypass."""

from fastapi.testclient import TestClient

from app import catalog
from app.guest import public_sku
from app.main import app


client = TestClient(app)


def test_unknown_internal_platform_code_is_not_exposed():
    item = {"part_number": "X", "product_family": "Surface", "platform_code": "SECRET-CODE",
            "memory_gb": 24, "storage_tb": 1, "cpu_model": None, "gpu_model": None,
            "operating_system": "Windows"}
    assert public_sku(item)["platform"] == "处理器配置待核验"


def test_guest_selection_and_mapping_redact_internal_workbook_fields(tmp_path, monkeypatch):
    monkeypatch.setattr(catalog, "DB_PATH", tmp_path / "catalog.sqlite3")
    monkeypatch.delenv("CAPABILITY_DEPLOYMENT_MODE", raising=False)
    monkeypatch.setenv("CAPABILITY_REQUIRE_AUTH", "1")
    with catalog.connection() as conn:
        conn.execute(
            "INSERT INTO imported_skus "
            "(part_number,product_family,raw_configuration,platform_code,memory_gb,storage_tb,"
            "erp_price_cny,currency_note,cpu_model,gpu_model,operating_system,source_reference,"
            "data_status,note,source_sha256) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("GUEST-TEST", "Surface Laptop Ultra", "PRIVATE-RAW-CONFIG", "S3", 128, 1,
             99999, "PRIVATE-CURRENCY", "N1X", "Blackwell", "Windows 11 Pro",
             "PRIVATE-SOURCE", "待核验", "PRIVATE-NOTE", "PRIVATE-HASH"),
        )
        conn.execute(
            "INSERT INTO imported_skus "
            "(part_number,product_family,raw_configuration,platform_code,memory_gb,storage_tb,"
            "erp_price_cny,cpu_model,gpu_model,operating_system,source_reference,source_sha256) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            ("GUEST-SECOND", "Surface Laptop Ultra", "SECOND-PRIVATE-RAW", "S2", 24, 0.5,
             23188, "N1X", "Blackwell", "Windows 11 Pro", "SECOND-PRIVATE-SOURCE", "SECOND-HASH"),
        )
        conn.commit()

    page = client.get("/guest")
    assert page.status_code == 200
    assert "游客体验" in page.text and "登录授权版" in page.text

    listing = client.get("/api/guest/skus")
    assert listing.status_code == 200
    items = {item["part_number"]: item for item in listing.json()["items"]}
    assert set(items) == {"GUEST-TEST", "GUEST-SECOND"}
    for part_number, memory_gb, storage_tb in (("GUEST-TEST", 128, 1), ("GUEST-SECOND", 24, 0.5)):
        assert items[part_number]["memory_gb"] == memory_gb
        assert items[part_number]["storage_tb"] == storage_tb
        assert items[part_number]["cpu_model"] == "N1X"
        assert items[part_number]["gpu_model"] == "Blackwell"
        assert items[part_number]["platform"].startswith("NVIDIA RTX Spark")
    assert "S3" not in listing.text

    advice = client.get("/api/guest/advisor/GUEST-TEST")
    assert advice.status_code == 200
    assert len(advice.json()["ai_models"]) == 4
    assert advice.json()["ai_models"][0]["runtime_compatible"] == "unknown"
    assert advice.json()["gaming"] and advice.json()["generation"] and advice.json()["productivity"]
    assert client.get("/api/guest/advisor/NOT-FOUND").status_code == 404

    shortlist = client.post("/api/guest/recommendations", json={"usages": ["ai"], "ai_size": "70B"})
    assert shortlist.status_code == 200
    assert shortlist.json()["items"][0]["part_number"] in items
    assert shortlist.json()["items"][0]["evidence_level"].startswith("工程估算")
    described = client.post("/api/guest/recommendations", json={
        "description": "需要本地运行 32B 模型并用于编程",
    })
    assert described.status_code == 200
    assert described.json()["interpreted_need"]["ai_size"] == "32B"
    assert set(described.json()["interpreted_need"]["usages"]) == {"ai", "productivity"}
    assert described.json()["items"]
    detailed = client.post("/api/guest/recommendations", json={
        "usages": ["ai", "gaming", "generation", "productivity"],
        "ai_size": "32B", "model_name": "Example Model",
        "game_need": "aaa", "game_titles": "Example Game",
        "target_resolution": "1080p", "target_fps": 60,
        "generation_need": "image", "work_need": "coding",
        "software_name": "Example IDE",
    })
    assert detailed.status_code == 200
    assert detailed.json()["interpreted_need"]["ai_size"] == "32B"
    assert detailed.json()["interpreted_need"]["target_fps"] == 60
    assert detailed.json()["items"]
    assert client.post("/api/guest/recommendations", json={"usages": ["ai"], "budget_cny": 100000}).status_code == 422

    for response in (listing, advice, shortlist, described, detailed):
        for secret in ("99999", "23188", "PRIVATE-RAW-CONFIG", "PRIVATE-CURRENCY", "PRIVATE-SOURCE",
                       "PRIVATE-NOTE", "PRIVATE-HASH", "SECOND-PRIVATE-RAW", "SECOND-PRIVATE-SOURCE",
                       "SECOND-HASH", "erp_price_cny", "source_reference"):
            assert secret not in response.text

    assert client.get("/api/catalog/imported-skus").status_code == 401
    assert client.get("/api/faq").status_code == 401
    assert client.get("/api/reports/GUEST-TEST.pdf").status_code == 401


def test_guest_page_is_linked_from_account_without_unlocking_admin():
    assert 'href="/guest"' in client.get("/account").text
    homepage = client.get("/")
    assert homepage.status_code == 200
    assert 'href="/guest"' in homepage.text
    assert 'href="/account"' in homepage.text
    guest_page = client.get("/guest")
    assert 'id="need-form"' in guest_page.text
    assert 'id="description"' in guest_page.text
    assert client.get("/api/admin/users").status_code == 401
