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
    page = page.replace('</header>', '<nav aria-label="语言 / Language"><a lang="zh-CN" href="/workplace" aria-current="page">中文</a> | <a lang="en" href="/en/workplace">English</a></nav></header>', 1)
    return HTMLResponse(page, headers={"Cache-Control": "no-store"})


@router.get('/en/workplace', response_class=HTMLResponse)
def workplace_en():
    from ..workplace_en import translate_workplace
    response = workplace()
    page = response.body.decode('utf-8').replace('href="/workplace" aria-current="page"', 'href="/workplace"', 1)
    page = page.replace('href="/en/workplace">English', 'href="/en/workplace" aria-current="page">English', 1)
    return HTMLResponse(translate_workplace(page),
                        headers={"Cache-Control": "no-store"})


@router.get("/workplace/admin", response_class=HTMLResponse)
def workplace_admin():
    ensure_enabled()
    page = (Path(__file__).resolve().parents[1] / "assets" / "commercial.html").read_text(encoding="utf-8")
    if os.getenv('CAPABILITY_DEPLOYMENT_MODE', 'local') == 'local':
        page = page.replace('<h2>管理员登录</h2>', '<h2>管理员登录</h2><p class="notice">当前是本地测试环境，请使用本地管理员账号。线上账号及密码不会自动同步到本地。</p>')
    return HTMLResponse(apply_theme(page), headers={"Cache-Control": "no-store"})
