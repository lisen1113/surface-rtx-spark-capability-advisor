from fastapi.testclient import TestClient

from app.main import app
from app.recommendation import RecommendationInput, recommend


SKUS = [
    {"part_number": "S2-24", "platform_code": "S2", "memory_gb": 24, "storage_tb": 1, "erp_price_cny": 23000, "source_reference": "workbook"},
    {"part_number": "S3-48", "platform_code": "S3", "memory_gb": 48, "storage_tb": 1, "erp_price_cny": 34000, "source_reference": "workbook"},
    {"part_number": "S3-128", "platform_code": "S3", "memory_gb": 128, "storage_tb": 2, "erp_price_cny": 49000, "source_reference": "workbook"},
]


def test_free_text_combines_multiple_needs_without_claiming_performance():
    result = recommend(RecommendationInput(description="想玩 3A 游戏，也要本地运行 70B 模型，做编程"), SKUS)
    assert result["interpreted_need"]["usages"] == ["ai", "gaming", "productivity"]
    assert result["interpreted_need"]["minimum_memory_tier_gb"] == 128
    assert [item["part_number"] for item in result["items"]] == ["S3-128"]
    assert "66.5GB" in result["reasoning"][0]
    assert "FPS" in result["limitations"]


def test_budget_and_explicit_options_are_respected():
    result = recommend(RecommendationInput(ai_size="32B", budget_cny=35000), SKUS)
    assert result["items"][0]["part_number"] == "S3-48"
    assert result["items"][0]["over_budget"] is False
    assert result["items"][1]["over_budget"] is True


def test_unknown_description_asks_for_clarification():
    result = recommend(RecommendationInput(description="帮我选一台好电脑"), SKUS)
    assert result["status"] == "needs_input"
    assert result["items"] == []


def test_model_size_in_english_description_is_an_ai_need():
    result = recommend(RecommendationInput(description="3A game and 70B model"), SKUS)
    assert result["interpreted_need"]["usages"] == ["ai", "gaming"]
    assert [item["part_number"] for item in result["items"]] == ["S3-128"]


def test_specific_game_target_is_kept_as_unverified_requirement():
    result = recommend(RecommendationInput(game_titles="CS2", target_resolution="1440p", target_fps=120), SKUS)
    assert result["interpreted_need"]["game_titles"] == "CS2"
    assert any("1440p / 120 FPS" in note for note in result["needs_confirmation"])
    assert result["items"][0]["part_number"] == "S2-24"


def test_video_generation_uses_higher_engineering_tier():
    result = recommend(RecommendationInput(generation_need="video"), SKUS)
    assert result["interpreted_need"]["minimum_memory_tier_gb"] == 64
    assert result["items"][0]["part_number"] == "S3-128"


def test_productivity_reason_uses_chinese_label_without_changing_tier():
    result = recommend(RecommendationInput(usages=["productivity"], work_need="coding"), SKUS)
    assert result["interpreted_need"]["minimum_memory_tier_gb"] == 32
    assert "编程开发工作负载" in result["reasoning"][0]
    assert "coding 工作负载" not in result["reasoning"][0]


def test_need_form_and_api_are_available():
    client = TestClient(app)
    html = client.get("/").text
    assert "按使用需求推荐" in html
    assert "自由描述" in html
    response = client.post("/api/recommendations", json={"description": "70B 模型"})
    assert response.status_code == 200
    assert response.json()["interpreted_need"]["ai_size"] == "70B"
