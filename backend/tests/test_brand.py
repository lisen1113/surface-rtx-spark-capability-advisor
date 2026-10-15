from fastapi.testclient import TestClient

from app.main import app


def test_user_supplied_logo_is_served_and_referenced_in_print_views():
    client = TestClient(app)
    logo = client.get("/assets/yihe-logo.png")
    assert logo.status_code == 200
    assert logo.headers["content-type"] == "image/png"
    assert logo.content.startswith(b"\x89PNG\r\n\x1a\n")
    assert len(logo.content) > 1000
    assert "/assets/yihe-logo.png" in client.get("/").text
    assert "/assets/yihe-logo.png" in client.get("/deployment").text


def test_product_selector_and_official_specs_are_explained():
    page = TestClient(app).get("/").text
    assert "j.items.sort((a,b)=>" in page
    assert "价格待确认" in page
    assert "所选料号：导入资料详情" in page
    assert "微软官方系列技术规格" in page
    assert "3270 × 2180" in page
    assert "非此 Part Number 的独立检测报告" in page
