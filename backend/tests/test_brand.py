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
    assert "<th scope=\"row\">${escapeHtml(name)}</th><td><b>${escapeHtml(value)}</b></td>" in page
    assert "类别 / 参数" not in page
    assert "处理器档位、内存、存储、颜色与参考价按所选 SKU 显示" in page
    assert "9 个 Cortex-X925 性能核" not in page  # Core detail is computed from SKU tier.
    assert "cpuCores/2" in page
    assert "共享统一内存（非独立显存" in page
    assert "300 GB/s（RTX Spark 平台接口规格，非此 SKU 实测吞吐）" in page
    assert "3270 × 2180" in page
    assert "DARK STEEL" not in page  # Color is read from each imported SKU, not invented in the template.
    assert "官方特定测试配置" in page
    assert "www.microsoftstore.com.cn/surface/surface-laptop-ultra-for-business" in page
    assert "3 年有限硬件保修" in page
    assert "$('#metrics').hidden=true" in page
