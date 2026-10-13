import json
from fastapi.testclient import TestClient
from app.catalog import connection
from app.main import app

client = TestClient(app)

def test_advisor_combines_direct_and_recommendation_records():
    with connection() as conn:
        conn.execute("DELETE FROM imported_skus WHERE part_number='TEST-PN'")
        conn.execute("INSERT INTO imported_skus VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            "TEST-PN", "Surface Laptop Ultra", "S3 128GB", "S3", 128, 1, "DARK STEEL", 1,
            "CNY", "N1X", "Blackwell", None, "unified", None, None, "Windows 11 Pro",
            "https://example.com", "待核验", "test", "hash-test"))
        conn.execute("DELETE FROM source_records WHERE source_sha256='hash-test'")
        conn.execute("INSERT INTO source_records VALUES (?,?,?,?)", ("hash-test", "AI能力映射", 2, json.dumps({"Part Number": "TEST-PN", "目标模型/场景": "70B"}, ensure_ascii=False)))
        conn.execute("INSERT INTO source_records VALUES (?,?,?,?)", ("hash-test", "AI经验推荐矩阵", 2, json.dumps({"适用SKU内存档": "TEST-PN", "推荐定位": "高阶"}, ensure_ascii=False)))
        conn.commit()
    try:
        body = client.get("/api/catalog/advisor/TEST-PN").json()
        assert body["sku"]["memory_gb"] == 128
        assert body["ai"][0]["目标模型/场景"] == "70B"
        assert body["ai_recommendations"][0]["推荐定位"] == "高阶"
        assert len(body["generation"]) >= 8
        assert all(item["性能指标"].startswith("未知") for item in body["generation"])
        assert all("官方来源URL" in item and "证据等级" in item for item in body["generation"])
        assert len(body["productivity"]) >= 10
        assert all(item["实测结果"].startswith("未知") for item in body["productivity"])
        assert all("官方来源URL" in item and "证据等级" in item for item in body["productivity"])
    finally:
        with connection() as conn:
            conn.execute("DELETE FROM imported_skus WHERE part_number='TEST-PN'")
            conn.execute("DELETE FROM source_records WHERE source_sha256='hash-test'")
            conn.commit()

def test_unknown_part_number_is_404():
    assert client.get("/api/catalog/advisor/DOES-NOT-EXIST").status_code == 404

def test_home_page_exposes_all_advisor_modules():
    html = client.get("/").text
    for label in ("Surface Laptop Ultra 能力映射", "AI 模型", "游戏", "生成式 AI", "生产力", "AI FAQ", "TCO 成本", "证据与限制"):
        assert label in html
