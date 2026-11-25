from app.platform_display import platform_label, public_configuration
from app.generation import generation_guidance
from app.productivity import productivity_guidance
from app.ui import index
from fastapi import Response


def test_internal_codes_have_public_processor_descriptions():
    assert platform_label("S2") == "NVIDIA RTX Spark™ N1X（18 核 CPU / 5120 核 GPU）"
    assert platform_label("S3") == "NVIDIA RTX Spark™ N1X（20 核 CPU / 6144 核 GPU）"
    assert public_configuration("S3 128GB") == platform_label("S3") + " 128GB"
    assert platform_label(None) == "未知处理器"


def test_generated_guidance_and_home_use_public_labels():
    for guide in (generation_guidance, productivity_guidance):
        text = str(guide("EP2-TEST", 128, "S3"))
        assert "NVIDIA RTX Spark™ N1X" in text
        assert "|S3|" not in text and "｜S3｜" not in text
    html = index(Response())
    assert "const platformLabel=" in html
    assert "escapeHtml(platformLabel(x.platform_code))" in html
