"""Evidence-separated Windows 11 creative/generative capability guidance."""
from __future__ import annotations

NVIDIA_PRODUCT = "https://www.nvidia.com/en-us/products/rtx-spark/"
NVIDIA_COMFY = "https://blogs.nvidia.com/blog/rtx-ai-garage-flux-ltx-video-comfyui-gdc/"
NVIDIA_PORTING = "https://docs.nvidia.com/rtx-spark/rtx-spark-porting-guide/latest/"
NVIDIA_VIDEO = "https://docs.nvidia.com/video-technologies/pynvvideocodec/read-me/system-requirements-common.html"
MICROSOFT_SURFACE = "https://blogs.windows.com/devices/2026/05/31/introducing-surface-laptop-ultra-made-for-world-makers/"
MICROSOFT_WINDOWS_ML = "https://learn.microsoft.com/windows/ai/new-windows-ml/overview"


def _tier(memory_gb: int) -> tuple[str, str]:
    if memory_gb >= 128:
        return "旗舰实验", "优先从官方参考工作流开始，可逐项增加分辨率、帧数、节点与并发；仍须记录峰值统一内存和稳定性。"
    if memory_gb >= 64:
        return "高阶创作", "适合建立图像与短视频本地工作流；先用 batch=1 验证，再逐项增加负载。"
    if memory_gb >= 48:
        return "进阶创作", "图像工作流优先；视频从短片段、低分辨率和 batch=1 开始，避免同时常驻大模型。"
    if memory_gb >= 32:
        return "主流创作", "优先轻量或量化图像模型；视频生成属于受限试验，应降低帧数、分辨率和节点复杂度。"
    return "入门试验", "优先轻量图像模型与单任务运行；大型视频模型、高分辨率及多任务并发不作为默认推荐。"


def _record(name: str, official: str, judgment: str, source: str, *, status="需本 SKU 验证", evidence="官方平台资料 + 工程推断") -> dict:
    return {
        "推荐模型/工作负载名称": name,
        "官方能力/平台声明": official,
        "本地运行判断": status,
        "经验推荐与我的判断": judgment,
        "性能指标": "未知（未发现该 Part Number 的官方绝对耗时或吞吐实测）",
        "证据等级": evidence,
        "官方来源URL": source,
        "依据与限制": "平台级能力不能直接换算为该 SKU 的生成耗时、FPS 或 Token/s；应用版本、模型、精度、步骤、分辨率、驱动、电源与散热均会改变结果。",
    }


def generation_guidance(part_number: str, memory_gb: int, platform_code: str) -> list[dict]:
    tier, tier_guidance = _tier(memory_gb)
    context = f"{part_number}｜{platform_code}｜{memory_gb}GB 统一内存｜Windows 11 Pro｜{tier}。{tier_guidance}"
    return [
        _record(
            "ComfyUI 图像生成（FLUX.2 Klein / NVFP4）",
            "NVIDIA 官方说明 FLUX.2 Klein 已提供 NVFP4/FP8 方向，并将 ComfyUI 定位为 RTX 本地图像与视频生成工作流；相关百分比和倍数来自其他明确测试平台，不能套用到本 SKU。",
            context + " 建议从 1024×1024、batch=1、固定模型与步骤开始，记录是否成功、峰值内存和单次耗时。",
            NVIDIA_COMFY,
        ),
        _record(
            "ComfyUI 视频生成（LTX-2 / LTX-2.3）",
            "NVIDIA 官方展示 LTX-2 系列、ComfyUI、NVFP4/FP8 与 RTX Video 组合的本地视频生成和 4K 放大能力；这属于平台/工作流能力，不是 Surface 各内存 SKU 的完成时间保证。",
            context + " 先用短片段、较低分辨率、batch=1 验证；24/32GB 配置不默认承诺 22B 视频模型完整工作流可稳定运行。",
            NVIDIA_COMFY,
        ),
        _record(
            "RTX Video 超分辨率与生成视频后处理",
            "NVIDIA 官方将 RTX Video Super Resolution 集成到 ComfyUI，用于生成视频的实时 4K 放大，并说明支持在本地 RTX 工作流中使用。",
            context + " 生成与放大应分阶段测量；输出 4K 不代表基础生成阶段原生以 4K 完成。",
            NVIDIA_COMFY,
            evidence="NVIDIA 官方功能说明 + 本 SKU 待验证",
        ),
        _record(
            "Blender / OptiX 大型 3D 场景与 AI 辅助创作",
            "NVIDIA 对 RTX Spark 最高配置声明可处理最高约 90GB 的 3D 场景，并支持 OptiX、DLSS；该上限面向最高 128GB 平台，不适用于所有 SKU。",
            context + (" 可将大型场景作为重点验证方向，但 90GB 是平台上限声明而非本机稳定场景保证。" if memory_gb >= 128 else " 不应使用 90GB 平台上限作为该内存配置的承诺。"),
            NVIDIA_PRODUCT,
        ),
        _record(
            "12K 4:2:2 视频剪辑与硬件编解码",
            "NVIDIA 官方对 RTX Spark 平台声明支持 12K 4:2:2 编辑，并列出 Blackwell 硬件 H.264、HEVC、AV1 编解码能力；具体编辑软件、格式、轨道数与效果链仍需验证。",
            context + " 先验证素材格式、硬件解码是否命中、单轨回放与导出，再逐步增加轨道、调色和 AI 效果。",
            NVIDIA_PRODUCT,
        ),
        _record(
            "Windows on Arm 原生 CUDA / PyTorch / 视频 AI 管线",
            "NVIDIA 官方移植指南说明 RTX Spark 为 Windows on Arm 平台，CUDA 13.4 支持原生开发；PyNvVideoCodec 官方列出 Windows ARM64 与 RTX Spark 支持。x64 应用可经 Prism 模拟，但兼容性依赖应用和插件。",
            context + " 优先使用原生 ARM64 组件；任何 ComfyUI 自定义节点、Python wheel、编解码器或插件都必须逐项验证，模拟运行不能视为原生支持。",
            f"{NVIDIA_PORTING} ; {NVIDIA_VIDEO}",
            evidence="NVIDIA 官方兼容性说明 + 工程验证要求",
        ),
        _record(
            "Windows ML 图像、视频与生成式 AI 推理",
            "Microsoft 官方说明 Windows ML 支持 x64 与 ARM64，GPU 适合图像、视频和生成式 AI 高吞吐推理；特定硬件优化执行提供程序要求 Windows 11 24H2（Build 26100）或更高。",
            context + " Windows ML 可作为应用集成路径，但模型算子覆盖、执行提供程序和驱动版本须实测；不据此推断速度。",
            MICROSOFT_WINDOWS_ML,
            evidence="Microsoft 官方兼容性说明 + 本 SKU 待验证",
        ),
        _record(
            "Surface Laptop Ultra 创作平台定位",
            "Microsoft 官方确认 Surface Laptop Ultra 与 NVIDIA 共同设计，采用 RTX Spark、Blackwell RTX GPU、最高 128GB 统一内存并支持完整 CUDA。",
            context + " 此记录用于确认产品与平台归属；实际能力以所选 Part Number 的内存、平台档位和软件验证结果为准。",
            MICROSOFT_SURFACE,
            status="官方产品定位；具体工作负载待验证",
            evidence="Microsoft 官方产品资料",
        ),
    ]
