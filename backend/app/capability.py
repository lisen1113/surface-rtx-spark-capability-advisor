"""Explainable capacity checks; these calculations are estimates, never benchmarks."""
from dataclasses import asdict, dataclass
from typing import Literal


FitStatus = Literal["fits", "does_not_fit", "unknown"]


@dataclass(frozen=True)
class CapacityResult:
    weight_gb: float
    quantization_overhead_gb: float
    kv_cache_gb: float
    runtime_reserve_gb: float
    os_reserve_gb: float
    required_gb: float
    available_gb: float
    fits_in_memory: FitStatus
    can_start: FitStatus
    compatible: FitStatus
    usable: FitStatus
    evidence_level: str
    assumptions: list[str]
    limitations: list[str]

    def as_dict(self) -> dict:
        return asdict(self)


def estimate_capacity(
    *,
    parameters_billion: float,
    bits_per_weight: float,
    unified_memory_gb: float,
    quantization_overhead_ratio: float = 0.10,
    kv_cache_gb: float = 8,
    runtime_reserve_gb: float = 8,
    os_reserve_gb: float = 12,
    runtime_compatible: bool | None = None,
) -> CapacityResult:
    """Estimate memory fit while keeping compatibility and usability independent."""
    weight_gb = parameters_billion * bits_per_weight / 8
    quantization_overhead_gb = weight_gb * quantization_overhead_ratio
    required_gb = (
        weight_gb
        + quantization_overhead_gb
        + kv_cache_gb
        + runtime_reserve_gb
        + os_reserve_gb
    )
    fits = required_gb <= unified_memory_gb
    compatible: FitStatus = (
        "unknown" if runtime_compatible is None else "fits" if runtime_compatible else "does_not_fit"
    )
    can_start: FitStatus
    if not fits or runtime_compatible is False:
        can_start = "does_not_fit"
    elif runtime_compatible is True:
        can_start = "fits"
    else:
        can_start = "unknown"

    return CapacityResult(
        weight_gb=round(weight_gb, 2),
        quantization_overhead_gb=round(quantization_overhead_gb, 2),
        kv_cache_gb=round(kv_cache_gb, 2),
        runtime_reserve_gb=round(runtime_reserve_gb, 2),
        os_reserve_gb=round(os_reserve_gb, 2),
        required_gb=round(required_gb, 2),
        available_gb=round(unified_memory_gb, 2),
        fits_in_memory="fits" if fits else "does_not_fit",
        can_start=can_start,
        compatible=compatible,
        usable="unknown",
        evidence_level="engineering_estimate",
        assumptions=[
            "十进制 GB：10^9 字节",
            f"量化元数据及张量开销按权重的 {quantization_overhead_ratio:.0%} 估算",
            "KV Cache 由调用方根据上下文长度与并发量提供",
        ],
        limitations=[
            "内存可容纳不代表运行时兼容、能够启动或达到可用速度",
            "未提供经验证的运行时兼容性时，兼容与启动结论保持 unknown",
            "不推断 Token/s、首 Token 延迟、游戏 FPS 或生产力性能",
        ],
    )
