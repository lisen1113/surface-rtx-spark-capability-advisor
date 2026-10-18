from app.generation import generation_guidance
from app.productivity import productivity_guidance
from app.spark_updates import agent_guidance, gaming_updates


def test_october_updates_preserve_sku_and_evidence_boundaries():
    ai = agent_guidance("TEST-24", 24)
    games = gaming_updates("TEST-24")
    generation = generation_guidance("TEST-24", 24, "S2")
    productivity = productivity_guidance("TEST-24", 24, "S2")

    assert len(ai) == 5 and len(games) == 2
    assert all("https://" in item["官方来源URL"] for group in (ai, games, generation, productivity) for item in group)
    assert all(item["性能指标"].startswith("未知") for item in ai + games + generation)
    assert "不合并" in ai[1]["依据与限制"]
    assert "PAIR 1.0.0" in ai[1]["官方能力/平台声明"]
    assert "Windows ARM64" in ai[1]["官方能力/平台声明"]
    assert any("MCP、CLI" in item["推荐模型/工作负载名称"] for item in ai)
    assert "不要用普通 74B Q4" in ai[0]["经验推荐与我的判断"]
    assert any("帧生成与 HDR" in item["推荐模型/工作负载名称"] for item in generation)
    assert any("Broadcast 2.3" in item["软件/工作负载"] for item in productivity)
