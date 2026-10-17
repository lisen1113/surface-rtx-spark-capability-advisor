from fastapi.testclient import TestClient

from app.main import app
from app.deployment import sku_deployment_plan


def test_deployment_guide_is_reachable_and_evidence_bounded():
    client = TestClient(app)
    response = client.get("/deployment?sku=example")
    assert response.status_code == 200
    page = response.text
    for section in ("从空机到第一次回答", "企业私有数据", "验收记录", "Part Number"):
        assert section in page
    assert "RAG 不是训练" in page
    assert "不预设可运行的参数规模或 Token/s" in page
    assert "127.0.0.1" in page
    assert "learn.microsoft.com" in page
    assert 'id="print-guide"' in page
    assert "window.print()" in page
    assert "@media print" in page
    assert "Surface-Laptop-Ultra-Deployment-" in page
    assert "建议 PDF 文件名" in page
    assert "PAIR 官方项目将 Windows ARM64 标为实验支持" in page
    assert "不聚合显存" in page
    assert "24GB 指特定 2-bit 量化权重" in page


def test_home_exposes_deployment_tab():
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert 'data-tab="deployment"' in response.text
    assert "/deployment?sku=" in response.text


def test_sku_guidance_changes_with_memory_storage_and_platform():
    def sku(memory, storage, platform):
        return {"part_number": f"TEST-{memory}-{storage}-{platform}", "memory_gb": memory,
                "storage_tb": storage, "platform_code": platform, "cpu_model": "test",
                "gpu_model": "test", "operating_system": "Windows 11 Pro", "source_reference": "fixture"}

    small = sku_deployment_plan(sku(24, 0.5, "S2"))
    middle = sku_deployment_plan(sku(48, 1, "S3"))
    large = sku_deployment_plan(sku(128, 2, "S3"))
    assert [t["size_label"] for t in small["trials"]] == ["3B Q4", "8B Q4"]
    assert [t["size_label"] for t in middle["trials"]] == ["14B Q4", "32B Q4"]
    assert [t["size_label"] for t in large["trials"]] == ["70B Q4", "120B Q4"]
    assert "0.5TB" in small["storage_note"] and "2TB" in large["storage_note"]
    assert small["platform_note"] != middle["platform_note"]
    assert all(t["compatible"] == "unknown" and t["usable"] == "unknown"
               for plan in (small, middle, large) for t in plan["trials"])
    assert large["evidence_level"] == "engineering_estimate"
    assert "不能把 Nemotron 3.5 Bolt" in large["capacity_boundary"]


def test_unknown_sku_is_not_given_a_generic_plan():
    response = TestClient(app).get("/api/deployment/sku/not-a-real-part-number")
    assert response.status_code == 404
