"""Need-first SKU shortlist. Every threshold here is an engineering assumption."""
from __future__ import annotations

import re
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from .auth import require_entitled_user
from .capability import estimate_capacity
from .catalog import rows

router = APIRouter(prefix="/api", tags=["recommendation"])

Usage = Literal["ai", "gaming", "generation", "productivity"]
AiSize = Literal["unsure", "8B", "32B", "70B", "120B"]
GameNeed = Literal["unsure", "esports", "aaa"]
WorkNeed = Literal["unsure", "office", "coding", "video", "cad"]
GenerationNeed = Literal["unsure", "image", "video"]


class RecommendationInput(BaseModel):
    usages: list[Usage] = Field(default_factory=list, max_length=4)
    description: str = Field(default="", max_length=2000)
    ai_size: AiSize = "unsure"
    game_need: GameNeed = "unsure"
    work_need: WorkNeed = "unsure"
    generation_need: GenerationNeed = "unsure"
    model_name: str = Field(default="", max_length=120)
    game_titles: str = Field(default="", max_length=240)
    target_resolution: Literal["unsure", "1080p", "1440p", "4K"] = "unsure"
    target_fps: int | None = Field(default=None, ge=1, le=500)
    software_name: str = Field(default="", max_length=120)
    budget_cny: float | None = Field(default=None, gt=0)
    prefer_lower_price: bool = True


AI_ASSUMPTIONS = {
    "8B": (6, 3, 2),
    "32B": (8, 4, 4),
    "70B": (12, 8, 8),
    "120B": (12, 8, 8),
}


def _description_signals(description: str) -> dict:
    """Recognize a small explicit vocabulary; do not pretend to understand all prose."""
    t = description.lower()
    usages: set[str] = set()
    if re.search(r"\b(?:ai|llm|rag|agent|模型|推理|知识库)\b|模型|知识库", t):
        usages.add("ai")
    if re.search(r"游戏|电竞|3a|fps|光追", t):
        usages.add("gaming")
    if re.search(r"生成|comfyui|文生图|文生视频", t):
        usages.add("generation")
    if re.search(r"办公|编程|开发|剪辑|视频|设计|cad|渲染", t):
        usages.add("productivity")
    sizes = [int(x) for x in re.findall(r"(?<!\d)(8|32|70|120)\s*b\b", t)]
    size = f"{max(sizes)}B" if sizes else "unsure"
    game = "aaa" if re.search(r"3a|大型游戏|光追", t) else "esports" if re.search(r"电竞|网游", t) else "unsure"
    work = "cad" if re.search(r"cad|三维|3d|渲染", t) else "video" if re.search(r"剪辑|视频|调色", t) else "coding" if re.search(r"编程|开发|代码", t) else "office" if re.search(r"办公|office", t) else "unsure"
    return {"usages": usages, "ai_size": size, "game_need": game, "work_need": work}


def recommend(data: RecommendationInput, skus: list[dict]) -> dict:
    signals = _description_signals(data.description)
    usages = sorted(set(data.usages) | signals["usages"])
    if signals["ai_size"] != "unsure":
        usages = sorted(set(usages) | {"ai"})
    if signals["game_need"] != "unsure":
        usages = sorted(set(usages) | {"gaming"})
    if signals["work_need"] != "unsure":
        usages = sorted(set(usages) | {"productivity"})
    if data.ai_size != "unsure" or data.model_name:
        usages = sorted(set(usages) | {"ai"})
    if data.game_need != "unsure" or data.game_titles:
        usages = sorted(set(usages) | {"gaming"})
    if data.work_need != "unsure" or data.software_name:
        usages = sorted(set(usages) | {"productivity"})
    if data.generation_need != "unsure":
        usages = sorted(set(usages) | {"generation"})
    ai_size = data.ai_size if data.ai_size != "unsure" else signals["ai_size"]
    game_need = data.game_need if data.game_need != "unsure" else signals["game_need"]
    work_need = data.work_need if data.work_need != "unsure" else signals["work_need"]
    notes = []
    if data.ai_size != "unsure" and signals["ai_size"] != "unsure" and data.ai_size != signals["ai_size"]:
        notes.append("所选模型规模与描述中的规模不同；本次按明确选项计算，请确认。")
    if not usages:
        return {"status": "needs_input", "message": "请选择至少一项用途，或在描述中说明 AI、游戏、生成或生产力需求。", "items": [], "needs_confirmation": notes}

    # These tiers guide a shortlist; they do not certify software support or performance.
    minimum = 24
    reasons = []
    if "ai" in usages and ai_size != "unsure":
        os_gb, runtime_gb, kv_gb = AI_ASSUMPTIONS[ai_size]
        required = estimate_capacity(parameters_billion=int(ai_size[:-1]), bits_per_weight=4,
                                     unified_memory_gb=128, os_reserve_gb=os_gb,
                                     runtime_reserve_gb=runtime_gb, kv_cache_gb=kv_gb).required_gb
        available_tiers = sorted({int(s["memory_gb"]) for s in skus if s.get("memory_gb")})
        fitting = [tier for tier in available_tiers if tier >= required]
        if fitting:
            minimum = max(minimum, fitting[0])
        else:
            minimum = float("inf")
        reasons.append(f"{ai_size} Q4 内存估算约 {required:g}GB（含系统、运行时和 KV Cache 预留）；仅判断容量。")
    elif "ai" in usages:
        notes.append("尚未指定模型规模、量化和上下文长度；AI 容量匹配需进一步确认。")
    if data.model_name:
        notes.append(f"模型 {data.model_name} 的具体版本、量化与运行时尚未核验；本次只按所选规模估算。")
    if "gaming" in usages and game_need == "aaa":
        minimum = max(minimum, 32)
        reasons.append("3A 游戏按至少 32GB 建立工程候选；游戏版本、Windows on Arm 兼容性和目标 FPS 待验证。")
    elif "gaming" in usages:
        notes.append("尚未提供具体游戏、分辨率和目标 FPS；无法判断游戏兼容性或帧率。")
    if data.game_titles:
        notes.append(f"游戏 {data.game_titles} 的 Windows on Arm 兼容性及 {data.target_resolution} / {data.target_fps or '未指定'} FPS 目标需逐项实测。")
    if "productivity" in usages:
        work_tiers = {"office": 24, "coding": 32, "video": 64, "cad": 64}
        work_labels = {"office": "日常办公", "coding": "编程开发", "video": "视频剪辑", "cad": "CAD / 3D"}
        if work_need in work_tiers:
            minimum = max(minimum, work_tiers[work_need])
            reasons.append(f"{work_labels[work_need]}工作负载采用 {work_tiers[work_need]}GB 起步的工程筛选档；具体软件与插件需核验。")
        else:
            notes.append("尚未提供具体软件、版本和项目规模；生产力适配需进一步确认。")
    if data.software_name:
        notes.append(f"软件 {data.software_name} 的 ARM64/x64 支持、插件和项目规模需核验。")
    if "generation" in usages:
        generation_tier = 64 if data.generation_need == "video" else 48
        minimum = max(minimum, generation_tier)
        reasons.append(f"生成式 AI 以 {generation_tier}GB 作为当前工作流的工程候选起点；具体模型、节点和输出规格需验证。")

    candidates = []
    for sku in skus:
        memory = int(sku.get("memory_gb") or 0)
        price = sku.get("erp_price_cny")
        if memory < minimum:
            continue
        over_budget = bool(data.budget_cny and (price is None or price > data.budget_cny))
        candidates.append({
            "part_number": sku["part_number"], "platform_code": sku["platform_code"],
            "memory_gb": memory, "storage_tb": sku.get("storage_tb"),
            "price_cny": price, "over_budget": over_budget,
            "source_reference": sku.get("source_reference"),
            "reason": f"{memory}GB 满足本次 {minimum:g}GB 工程筛选档；实际容量、兼容性和性能仍按具体工作负载验证。",
            "evidence_level": "工程估算（筛选）+ 导入的产品配置与价格",
        })
    candidates.sort(key=lambda x: (x["over_budget"], x["price_cny"] is None,
                                   x["price_cny"] if data.prefer_lower_price else -x["memory_gb"],
                                   x["part_number"]))
    if not candidates:
        notes.append("当前已导入产品中没有满足该工程筛选档的配置；可调整需求或考虑其他设备/云端方案。")
    elif candidates[0]["over_budget"]:
        notes.append("没有符合预算的候选；以下显示超预算的配置供比较。")
    return {
        "status": "shortlist" if candidates else "no_match",
        "interpreted_need": {"usages": usages, "ai_size": ai_size, "game_need": game_need, "work_need": work_need,
                             "generation_need": data.generation_need,
                             "model_name": data.model_name, "game_titles": data.game_titles,
                             "target_resolution": data.target_resolution, "target_fps": data.target_fps,
                             "software_name": data.software_name,
                             "budget_cny": data.budget_cny, "minimum_memory_tier_gb": minimum if minimum != float("inf") else None},
        "reasoning": reasons, "needs_confirmation": notes, "items": candidates[:8],
        "limitations": "推荐为工程候选，不构成 SKU 实测、软件认证、游戏 FPS 或模型 Token/s 承诺。价格来自导入工作簿，采购前须复核。",
    }


@router.post("/recommendations")
def recommend_products(data: RecommendationInput, _user=Depends(require_entitled_user)):
    return recommend(data, rows("imported_skus"))
