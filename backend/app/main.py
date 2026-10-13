"""Capability Advisor V3 local-first API bootstrap; not production auth."""
from datetime import datetime, timezone
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Surface / RTX Spark PC Capability Advisor", version="3.0.0-dev")

class MemoryEstimateInput(BaseModel):
    parameters_billion: float = Field(gt=0, le=1000)
    bits_per_weight: float = Field(gt=0, le=32)
    os_reserve_gb: float = Field(default=12, ge=0)
    runtime_reserve_gb: float = Field(default=8, ge=0)
    kv_cache_gb: float = Field(default=8, ge=0)
    unified_memory_gb: float = Field(default=128, gt=0)

@app.get("/health")
def health():
    return {"status": "ok", "version": "3.0.0-dev", "local": True}

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
def estimate_memory(data: MemoryEstimateInput):
    # Decimal GB convention: 1B parameters * 1 bit / 8 = 0.125GB.
    weight_gb = data.parameters_billion * data.bits_per_weight / 8
    reserves = data.os_reserve_gb + data.runtime_reserve_gb + data.kv_cache_gb
    available = max(data.unified_memory_gb - reserves, 0)
    return {
        "estimated_weight_gb": round(weight_gb, 2),
        "available_budget_gb": round(available, 2),
        "theoretical_weight_fit": weight_gb <= available,
        "evidence_level": "engineering_estimate",
        "limitations": [
            "不含量化元数据及框架特殊开销",
            "无法保证 GPU 可分配内存或运行速度",
            "该估算不等于 SKU 兼容性、Token/s 或官方实测",
        ],
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
