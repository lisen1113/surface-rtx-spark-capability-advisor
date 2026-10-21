import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MINI = ROOT / "miniprogram"


def test_miniprogram_pilot_separates_public_and_internal_entries_without_credentials():
    manifest = json.loads((MINI / "app.json").read_text(encoding="utf-8"))
    config = json.loads((MINI / "project.config.example.json").read_text(encoding="utf-8"))
    home = (MINI / "pages/home/index.wxml").read_text(encoding="utf-8")
    advisor_script = (MINI / "pages/advisor/index.js").read_text(encoding="utf-8")
    advisor_markup = (MINI / "pages/advisor/index.wxml").read_text(encoding="utf-8")
    company_script = (MINI / "pages/company/index.js").read_text(encoding="utf-8")

    assert config["appid"].startswith("REPLACE_WITH_")
    assert manifest["pages"][0] == "pages/home/index"
    assert 'url="/pages/company/index"' in home
    assert 'url="/pages/advisor/index"' in home
    assert "https://yiheit.net/" in company_script
    assert "https://surfacedmp.com/account" in advisor_script
    assert "<web-view" in advisor_markup
    assert "binderror=" in advisor_markup
    for text in (home, advisor_script, company_script):
        assert "cap_token" not in text
        assert "AppSecret" not in text


def test_local_miniprogram_config_is_gitignored():
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "miniprogram/project.config.json" in ignore
    assert "miniprogram/project.private.config.json" in ignore


def test_pdf_preview_page_uses_one_use_ticket_not_bearer_token():
    manifest = json.loads((MINI / "app.json").read_text(encoding="utf-8"))
    assert "pages/report/index" in manifest["pages"]
    script = (MINI / "pages/report/index.js").read_text(encoding="utf-8")
    assert "wx.downloadFile" in script
    assert "wx.openDocument" in script
    assert "showMenu: true" in script
    assert "mobile-download/" in script
    assert "cap_token" not in script
