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
    assert "产品技术规格" in page
    assert "合并后的规格值" in page
    assert "数据来源" in page
    assert "中国微软商城 · 系列规格" in page
    assert "限制与核对事项" in page
    assert "3270 × 2180" in page
    assert "DARK STEEL" not in page  # Color is read from each imported SKU, not invented in the template.
    assert "导入颜色名称与中国微软商城" in page
    assert "续航测试用预生产 6144 核 GPU / 64GB / 1TB" in page
    assert "www.microsoftstore.com.cn/surface/surface-laptop-ultra-for-business" in page
    assert "中国市场保修" in page and "3 年有限硬件保修" in page
    assert "140 W 电源适配器仅特定市场/配置提供" in page
    assert "$('#metrics').hidden=true" in page
