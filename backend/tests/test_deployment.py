from fastapi.testclient import TestClient

from app.main import app


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


def test_home_exposes_deployment_tab():
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert 'data-tab="deployment"' in response.text
    assert "/deployment?sku=" in response.text
