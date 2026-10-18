"""Customer-facing processor descriptions for internal platform codes.

The core-count mapping is supplied by the project owner, not a benchmark.
Keep platform_code unchanged in storage and API matching.
"""
import re

PLATFORMS = {
    "S2": (18, 5120),
    "S3": (20, 6144),
}


def platform_label(code: str | None) -> str:
    specs = PLATFORMS.get(str(code or "").upper())
    if specs is None:
        return str(code or "未知处理器")
    cpu_cores, gpu_cores = specs
    return f"NVIDIA RTX Spark™ N1X（{cpu_cores} 核 CPU / {gpu_cores} 核 GPU）"


def public_configuration(value: object) -> str:
    """Remove pre-release platform tags from imported configuration prose."""
    return re.sub(r"\bS[23]\b", lambda match: platform_label(match.group()), str(value or ""))
