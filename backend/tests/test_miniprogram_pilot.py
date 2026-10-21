import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MINI = ROOT / "miniprogram"


def test_miniprogram_pilot_is_account_first_and_contains_no_credentials():
    manifest = json.loads((MINI / "app.json").read_text(encoding="utf-8"))
    config = json.loads((MINI / "project.config.example.json").read_text(encoding="utf-8"))
    page = MINI / manifest["pages"][0]
    script = page.with_suffix(".js").read_text(encoding="utf-8")
    markup = page.with_suffix(".wxml").read_text(encoding="utf-8")

    assert config["appid"].startswith("REPLACE_WITH_")
    assert "https://surfacedmp.com/account" in script
    assert "<web-view" in markup
    assert "binderror=" in markup
    assert "cap_token" not in script
    assert "AppSecret" not in script


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
