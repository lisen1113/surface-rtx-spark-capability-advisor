from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def candidate_for(payload):
    response = client.post("/api/recommendations", json=payload)
    assert response.status_code == 200
    return response.json()["items"][0]["part_number"]


def test_need_report_is_bound_to_selected_sku_and_submitted_need():
    payload = {
        "usages": ["productivity"], "work_need": "office",
        "software_name": "Microsoft 365", "description": "办公和客户演示 <script>alert(1)</script>",
    }
    part_number = candidate_for(payload)
    response = client.post("/api/reports/recommendation", json={**payload, "part_number": part_number})
    assert response.status_code == 200
    html = response.text
    assert part_number in html
    assert "本次用户需求" in html
    assert "Microsoft 365" in html
    assert "日常办公" in html
    assert "完整配置描述" in html and "中国微软商城系列技术规格" in html
    assert "生产力：所选场景指导" in html
    assert "Blender 3D" not in html
    assert "游戏：该 SKU 的场景映射" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "<script>alert(1)</script>" not in html
    assert "打印／另存为 PDF" in html
    assert html.split("<footer>", 1)[1].split("</footer>", 1)[0] == "© 2026 上海以和信息技术有限公司。保留所有权利。"


def test_need_report_rejects_sku_outside_shortlist_and_unknown_sku():
    payload = {"usages": ["ai"], "ai_size": "120B"}
    skus = client.get("/api/catalog/imported-skus").json()["items"]
    small = next(s for s in skus if s["memory_gb"] == 24)
    response = client.post("/api/reports/recommendation", json={**payload, "part_number": small["part_number"]})
    assert response.status_code == 422
    response = client.post("/api/reports/recommendation", json={**payload, "part_number": "NOT-A-SKU"})
    assert response.status_code == 404


def test_need_report_combines_selected_ai_game_and_generation_sections():
    payload = {"usages": ["ai", "gaming", "generation"], "ai_size": "8B", "game_need": "esports", "generation_need": "image", "game_titles": "CS2"}
    part_number = candidate_for(payload)
    response = client.post("/api/reports/recommendation", json={**payload, "part_number": part_number})
    assert response.status_code == 200
    assert "本地 AI：该 SKU 的场景映射" in response.text
    assert "游戏：该 SKU 的场景映射" in response.text
    assert "生成式 AI：所选工作流指导" in response.text
    assert "生产力：所选场景指导" not in response.text
    assert "CS2" in response.text


def test_need_report_obeys_protected_route_setting(monkeypatch):
    monkeypatch.setenv("CAPABILITY_REQUIRE_AUTH", "1")
    response = client.post("/api/reports/recommendation", json={"part_number": "EP2-56981", "usages": ["ai"]})
    assert response.status_code == 401


def test_need_report_button_creates_inline_report_instead_of_scrolling_to_top():
    html = client.get("/").text
    assert "查看此配置的详细能力并生成报告" in html
    assert "async function showNeedReport(partNumber)" in html
    assert "frame.srcdoc=html" in html
    assert "need-report-print" in html
    assert "window.scrollTo({top:0" not in html
