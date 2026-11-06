"""Chinese commercial workspace, reusing existing login and branding."""
from pathlib import Path
import os
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from ..branding import apply_theme
from .store import ensure_enabled

router = APIRouter()


@router.get("/workplace", response_class=HTMLResponse)
def workplace():
    ensure_enabled()
    page = (Path(__file__).resolve().parents[1] / "assets" / "workplace-public.html").read_text(encoding="utf-8")
    return HTMLResponse(page, headers={"Cache-Control": "no-store"})


@router.get("/workplace/admin", response_class=HTMLResponse)
def workplace_admin():
    ensure_enabled()
    page = (Path(__file__).resolve().parents[1] / "assets" / "commercial.html").read_text(encoding="utf-8")
    if os.getenv('CAPABILITY_DEPLOYMENT_MODE', 'local') == 'local':
        page = page.replace('<h2>管理员登录</h2>', '<h2>管理员登录</h2><p class="notice">当前是本地测试环境，请使用本地管理员账号。线上账号及密码不会自动同步到本地。</p>')
    return HTMLResponse(apply_theme(page), headers={"Cache-Control": "no-store"})
