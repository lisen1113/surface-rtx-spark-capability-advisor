"""Unauthenticated, read-only advisor entry point."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/guest", response_class=HTMLResponse)
def guest_page():
    page = (Path(__file__).resolve().parent / "assets" / "guest.html").read_text(encoding="utf-8")
    return HTMLResponse(page, headers={"Cache-Control": "no-store"})
