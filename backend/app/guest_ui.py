"""Unauthenticated, read-only advisor entry point."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse
from .advisor_access import public_advisor_enabled
from .branding import apply_theme

router = APIRouter()


@router.get("/guest", response_class=HTMLResponse)
def guest_page():
    if public_advisor_enabled():
        return RedirectResponse("/?advisor=public", status_code=307)
    page = (Path(__file__).resolve().parent / "assets" / "guest.html").read_text(encoding="utf-8")
    page = page.replace('</header>', '<nav aria-label="语言 / Language"><a lang="zh-CN" href="/guest" aria-current="page">中文</a> | <a lang="en" href="/en/guest">English</a></nav></header>', 1)
    return HTMLResponse(apply_theme(page), headers={"Cache-Control": "no-store"})


@router.get('/en/guest', response_class=HTMLResponse)
def guest_page_en():
    if public_advisor_enabled():
        return RedirectResponse('/en?advisor=public', status_code=307)
    from .guest_en import translate_guest
    page = (Path(__file__).resolve().parent / 'assets' / 'guest.html').read_text(encoding='utf-8')
    return HTMLResponse(translate_guest(apply_theme(page)), headers={"Cache-Control": "no-store"})
