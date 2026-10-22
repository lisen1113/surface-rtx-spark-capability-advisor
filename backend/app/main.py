"""Capability Advisor V3 local-first API bootstrap."""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
import os
import sqlite3
from urllib.parse import urlsplit
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .catalog import connection, router as catalog_router
from .capability import estimate_capacity
from .auth import require_entitled_user, router as auth_router
from .tco import router as tco_router
from .knowledge import router as knowledge_router
from .faq import router as faq_router
from .report import router as report_router
from .auth_ui import router as auth_ui_router
from .ui import router as ui_router
from .recommendation import router as recommendation_router
from .deployment import router as deployment_router
from .guest import router as guest_router
from .guest_ui import router as guest_ui_router
from .deployment_readiness import assert_deployment_configuration
from .auth_store import connection as auth_connection
from .request_limit import AUTH_LIMITS, limiter, source_address


@asynccontextmanager
async def lifespan(_app: FastAPI):
    assert_deployment_configuration()
    if os.getenv("CAPABILITY_DEPLOYMENT_MODE") == "public":
        # Refuse to start when either persistent store or its schema is absent.
        with connection() as catalog_db:
            catalog_db.execute("SELECT 1 FROM imported_skus LIMIT 1")
        with auth_connection() as identity_db:
            identity_db.execute("SELECT 1 FROM users LIMIT 1")
            admin = identity_db.execute(
                "SELECT 1 FROM users u JOIN admin_mfa m ON m.user_id=u.id "
                "WHERE u.role='admin' AND u.status='approved' "
                "AND u.email_verified=1 LIMIT 1"
            ).fetchone()
            if admin is None:
                raise RuntimeError("Public deployment requires an approved, verified administrator with MFA enabled")
    yield


app = FastAPI(title="Surface / RTX Spark PC Capability Advisor", version="3.0.0-dev", lifespan=lifespan)


@app.middleware("http")
async def shared_host_boundary(request: Request, call_next):
    """Only the configured public host may reach a shared/public deployment.

    Reverse proxies must forward the original Host and terminate TLS; this
    check is a defense in depth boundary, not proof that TLS is configured.
    """
    if os.getenv("CAPABILITY_DEPLOYMENT_MODE", "local") in {"shared", "public"}:
        expected = urlsplit(os.getenv("CAPABILITY_PUBLIC_BASE_URL", ""))
        received = request.headers.get("host", "")
        private_preview = (os.getenv("CAPABILITY_ALLOW_LOOPBACK_PREVIEW") == "1"
                           and request.client is not None
                           and request.client.host in {"127.0.0.1", "::1"}
                           and received.casefold() in {"127.0.0.1:8011", "localhost:8011"})
        if not expected.netloc or (received.casefold() != expected.netloc.casefold() and not private_preview):
            return PlainTextResponse("Host not allowed", status_code=400)
        if (os.getenv("CAPABILITY_DEPLOYMENT_MODE") == "public"
                and request.method == "POST" and request.url.path in AUTH_LIMITS):
            peer = request.client.host if request.client else "unknown"
            address = source_address(peer, request.headers.get("x-forwarded-for"))
            retry = limiter.check(address, request.url.path)
            if retry:
                return PlainTextResponse("请求过于频繁，请稍后再试", status_code=429,
                                         headers={"Retry-After": str(retry), "Cache-Control": "no-store"})
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    if request.url.path.startswith("/api/") or request.url.path in {"/account", "/admin"}:
        response.headers["Cache-Control"] = "no-store"
    return response

app.mount("/assets", StaticFiles(directory=Path(__file__).resolve().parent / "assets"), name="assets")

app.include_router(catalog_router, dependencies=[Depends(require_entitled_user)])
app.include_router(guest_router)
app.include_router(guest_ui_router)
app.include_router(auth_router)
app.include_router(tco_router)
app.include_router(knowledge_router, dependencies=[Depends(require_entitled_user)])
app.include_router(faq_router, dependencies=[Depends(require_entitled_user)])
app.include_router(report_router)
app.include_router(auth_ui_router)
app.include_router(ui_router)
app.include_router(recommendation_router)
app.include_router(deployment_router)

class MemoryEstimateInput(BaseModel):
    parameters_billion: float = Field(gt=0, le=1000)
    bits_per_weight: float = Field(gt=0, le=32)
    os_reserve_gb: float = Field(default=12, ge=0)
    runtime_reserve_gb: float = Field(default=8, ge=0)
    kv_cache_gb: float = Field(default=8, ge=0)
    unified_memory_gb: float = Field(default=128, gt=0)
    quantization_overhead_ratio: float = Field(default=0.10, ge=0, le=1)
    runtime_compatible: bool | None = None

@app.get("/health")
def health():
    try:
        with connection() as conn:
            conn.execute("SELECT 1 FROM imported_skus LIMIT 1")
        if os.getenv("CAPABILITY_DEPLOYMENT_MODE") == "public":
            with auth_connection() as conn:
                conn.execute("SELECT 1 FROM users LIMIT 1")
    except Exception as exc:
        detail = "数据库不可用" if os.getenv("CAPABILITY_DEPLOYMENT_MODE") == "public" else "本地数据库不可用"
        raise HTTPException(503, detail) from exc
    return {"status": "ok", "version": "3.0.0-dev", "local": os.getenv("CAPABILITY_DEPLOYMENT_MODE", "local") == "local", "database": "ready"}

@app.get("/api/about")
def about():
    return {
        "product": "Surface / RTX Spark PC Capability Advisor",
        "version": "3.0.0-dev",
        "copyright": "© 2026 上海以和信息技术有限公司。保留所有权利。",
        "disclaimer": "Microsoft、Surface、NVIDIA、RTX 等商标归各自权利人所有。",
        "status": "development_bootstrap"
    }

@app.post("/api/estimate/memory")
def estimate_memory(data: MemoryEstimateInput, _user=Depends(require_entitled_user)):
    result = estimate_capacity(**data.model_dump()).as_dict()
    # Keep the original fields during the V3 bootstrap API transition.
    result["estimated_weight_gb"] = result["weight_gb"]
    result["available_budget_gb"] = round(
        max(data.unified_memory_gb - data.os_reserve_gb - data.runtime_reserve_gb - data.kv_cache_gb, 0), 2
    )
    result["theoretical_weight_fit"] = result["fits_in_memory"] == "fits"
    result["checked_at"] = datetime.now(timezone.utc).isoformat()
    return result
