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
    return HTMLResponse(apply_theme(page), headers={"Cache-Control": "no-store"})
