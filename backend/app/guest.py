"""Deliberately narrow, unauthenticated product preview.

Never return imported workbook rows, prices, internal source references, reports,
or tenant data from this router. Authenticated catalog routes stay protected.
"""

from fastapi import APIRouter, HTTPException

from .capability import estimate_capacity
from .catalog import rows
from .generation import generation_guidance
from .platform_display import PLATFORMS, platform_label
from .productivity import productivity_guidance
from .recommendation import RecommendationInput, recommend
from .spark_updates import agent_guidance, gaming_updates

router = APIRouter(prefix="/api/guest", tags=["guest"])


def _public_platform(code: str | None) -> str:
    return platform_label(code) if str(code or "").upper() in PLATFORMS else "处理器配置待核验"


def public_sku(item: dict) -> dict:
    """Allowlist fields suitable for product selection, excluding ERP data."""
    return {
        "part_number": item["part_number"],
        "product_family": item["product_family"],
        "platform": _public_platform(item["platform_code"]),
        "memory_gb": item["memory_gb"],
        "storage_tb": item["storage_tb"],
        "cpu_model": item["cpu_model"],
        "gpu_model": item["gpu_model"],
        "operating_system": item["operating_system"],
        "configuration_evidence": "导入产品配置；购买前按正式料号核实",
    }


def _find_sku(part_number: str) -> dict:
    # An exact match only. Do not reveal the underlying imported row.
    for item in rows("imported_skus"):
        if item["part_number"] == part_number:
            return item
    raise HTTPException(404, "未找到该产品配置")


def _model_capacity(memory_gb: int | None) -> list[dict]:
    result = []
    for size in (8, 32, 70, 120):
        if memory_gb is None:
            result.append({
                "model_size": f"{size}B 级模型", "required_gb": None,
                "memory_fit": "unknown", "runtime_compatible": "unknown",
                "evidence_level": "未知（未提供统一内存容量）",
                "limitations": "模型版本、量化、上下文、运行时、速度均需实测。",
            })
            continue
        estimate = estimate_capacity(parameters_billion=size, bits_per_weight=4,
                                     unified_memory_gb=memory_gb)
        result.append({
            "model_size": f"{size}B 级模型（假设 4-bit）",
            "required_gb": estimate.required_gb,
            "memory_fit": estimate.fits_in_memory,
            "runtime_compatible": estimate.compatible,
            "evidence_level": "工程估算（仅容量）",
            "limitations": "假设 4-bit、10% 权重开销、系统 12GB、运行时 8GB、KV Cache 8GB；可容纳不代表能启动、兼容或达到可用速度。",
        })
    return result


@router.get("/skus")
def guest_skus():
    return {"items": [public_sku(item) for item in rows("imported_skus")],
            "note": "游客只查看产品配置；价格、内部来源台账、报告及账号信息不公开。"}


@router.post("/recommendations")
def guest_recommendations(data: RecommendationInput):
    # The public experience has no pricing entitlement. Reject budget-based
    # comparisons instead of silently pretending to evaluate a hidden price.
    if data.budget_cny is not None:
        raise HTTPException(422, "游客推荐不处理预算；请登录授权版查看价格与 TCO")
    imported = rows("imported_skus")
    candidates = [{
        "part_number": item["part_number"], "platform_code": item["platform_code"],
        "memory_gb": item["memory_gb"], "storage_tb": item["storage_tb"],
        "erp_price_cny": None, "source_reference": None,
    } for item in imported]
    selection = recommend(data.model_copy(update={"prefer_lower_price": False}), candidates)
    selection["items"] = [{
        "part_number": item["part_number"], "platform": _public_platform(item["platform_code"]),
        "memory_gb": item["memory_gb"], "storage_tb": item["storage_tb"],
        "reason": item["reason"], "evidence_level": "工程估算（候选筛选）",
    } for item in selection["items"]]
    selection["limitations"] = "游客推荐只按公开展示的产品配置做工程候选，不含价格、软件认证、本 SKU FPS 或 Token/s；采购前须核实。"
    return selection


@router.get("/advisor/{part_number}")
def guest_advisor(part_number: str):
    item = _find_sku(part_number)
    memory = item["memory_gb"]
    return {
        "sku": public_sku(item),
        "ai_models": _model_capacity(memory),
        "ai_ecosystem": agent_guidance(part_number, memory or 0),
        "gaming": gaming_updates(part_number),
        "generation": generation_guidance(part_number, memory or 0, item["platform_code"]),
        "productivity": productivity_guidance(part_number, memory or 0, item["platform_code"]),
        "disclaimer": "官方平台资料、工程估算和未知分开呈现；本 SKU 的兼容性、FPS、Token/s 与任务耗时须实测。",
    }
