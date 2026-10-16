"""Capability Advisor V3 local-first API bootstrap; not production auth."""
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from fastapi import Depends, FastAPI, HTTPException
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

app = FastAPI(title="Surface / RTX Spark PC Capability Advisor", version="3.0.0-dev")
app.mount("/assets", StaticFiles(directory=Path(__file__).resolve().parent / "assets"), name="assets")

app.include_router(catalog_router, dependencies=[Depends(require_entitled_user)])
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
    except (OSError, sqlite3.Error) as exc:
        raise HTTPException(503, "本地数据库不可用") from exc
    return {"status": "ok", "version": "3.0.0-dev", "local": True, "database": "ready"}

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
