"""Evidence-separated Windows 11 Pro productivity guidance by Surface SKU."""
from __future__ import annotations

MICROSOFT_STORE = "https://www.microsoft.com/en-us/d/surface-laptop-ultra-for-business/8wg5vqp0x4d1/"
MICROSOFT_DEVICE = "https://www.microsoft.com/en-us/surface/devices/surface-laptop-ultra"
MICROSOFT_COPILOT = "https://support.microsoft.com/en-us/surface/drivers-firmware/learn-more-about-copilot-pcs-and-windows-11-pcs-from-surface"
NVIDIA_PRODUCT = "https://www.nvidia.com/en-us/products/rtx-spark/"
NVIDIA_PORTING = "https://docs.nvidia.com/rtx-spark/rtx-spark-porting-guide/latest/"
NVIDIA_ANNOUNCEMENT = "https://nvidianews.nvidia.com/news/nvidia-microsoft-windows-pcs-agents-rtx-spark"
ADOBE_ARM = "https://helpx.adobe.com/in/x-productkb/multi/windows-arm-support.html"
ADOBE_PHOTOSHOP = "https://helpx.adobe.com/photoshop/kb/windows-arm-support.html"
ADOBE_PREMIERE_GPU = "https://helpx.adobe.com/premiere/desktop/get-started/technical-requirements/gpu-and-gpu-driver-requirements.html"
BLENDER_ARM = "https://docs.blender.org/manual/en/latest/getting_started/installing/windows.html"


def _tier(memory_gb: int) -> tuple[str, str]:
    if memory_gb >= 128:
        return "旗舰专业", "适合大型项目、数据集、场景与多工具并行验证；统一内存仍由 CPU、GPU、显示和应用共同占用。"
    if memory_gb >= 64:
        return "高阶专业", "适合重型创作、开发和多任务；对插件、驱动和 ARM64 原生性逐项验收。"
    if memory_gb >= 48:
        return "进阶专业", "适合中重度创作与开发；避免多个大型工程、模型和媒体缓存同时常驻。"
    if memory_gb >= 32:
        return "主流专业", "适合日常办公、开发和中型创作；大型场景、长时间线和重型容器应控制并发。"
    return "基础专业", "适合办公、协作、编程与轻量创作；大型媒体、3D、AI 和多虚拟化负载不作为默认承诺。"


def _record(name: str, official: str, judgment: str, source: str, *, status="需本 SKU 验证", evidence="官方兼容性资料 + 工程推断") -> dict:
    return {
        "软件/工作负载": name,
        "官方能力/平台声明": official,
        "兼容性状态": status,
        "经验推荐与我的判断": judgment,
        "实测结果": "未知（未发现该 Part Number 的官方生产力基准）",
        "证据等级": evidence,
        "官方来源URL": source,
        "依据与限制": "不以核心数、统一内存容量或平台宣传直接推导应用完成时间。版本、ARM64 原生性、插件、驱动、工程规模、电源与散热均须记录。",
    }


def productivity_guidance(part_number: str, memory_gb: int, platform_code: str) -> list[dict]:
    tier, guidance = _tier(memory_gb)
    context = f"{part_number}｜{platform_code}｜{memory_gb}GB｜Windows 11 Pro｜{tier}。{guidance}"
    return [
        _record(
            "Microsoft 365、Teams、浏览器与日常商务多任务",
            "Microsoft 将 Surface Laptop Ultra 定位于高要求创作、开发、AI、工程和 3D；并明确说明仅邮件、会议、Microsoft 365 和网页办公时，普通 Surface Laptop/Pro 可能更合适。",
            context + " 日常办公兼容性风险较低，但购买价值主要来自重型专业负载，而非普通文档处理。",
            MICROSOFT_STORE,
            status="官方支持的 Windows 11 Pro 通用场景",
            evidence="Microsoft 官方产品资料 + 工程定位",
        ),
        _record(
            "Visual Studio / VS Code / Git / 编译与多项目开发",
            "Microsoft 官方将该产品定位为 demanding software development，并提到可在开发工具并行运行时进行代理原型、代码审查和较大模型测试。",
            context + " 优先使用 ARM64 原生工具链；编译时间、解决方案规模和容器并发没有该 SKU 官方数据，应在真实仓库测量。",
            MICROSOFT_STORE,
        ),
        _record(
            "WSL2、容器与本地 AI 开发环境",
            "NVIDIA 官方说明 RTX Spark 为 Windows on Arm，现有 x86/x64 应用可经 Prism 运行，但兼容性取决于应用及依赖；原生 ARM64、ARM64EC 与模拟是不同路径。",
            context + " 先核对镜像架构、Python wheel、CUDA 组件、USB/网络驱动和 IDE 扩展；x64 模拟成功不等于原生性能或完整兼容。",
            NVIDIA_PORTING,
        ),
        _record(
            "Adobe Photoshop（Windows on Arm）",
            "Adobe 提供 Windows ARM 支持说明；Photoshop 官方页面同时列出 ARM 版本限制，例如当前不能导入、置入或打开视频格式。",
            context + " 基础图像编辑可列入验证清单；视频相关、第三方插件、脚本、字体和色彩设备须逐项核对，不沿用 x64 工作站经验。",
            f"{ADOBE_ARM} ; {ADOBE_PHOTOSHOP}",
            status="官方 ARM 支持存在，但有功能限制",
            evidence="Adobe 官方兼容性说明 + 工程验证要求",
        ),
        _record(
            "Adobe Premiere Pro / Media Encoder",
            "NVIDIA 宣布 Adobe 正针对 RTX Spark 重构 Photoshop 与 Premiere，并给出平台级相对性能主张；Adobe 说明 Windows ARM 版 Premiere/Media Encoder 部分功能与 Intel Windows 版本不同。",
            context + " 视为持续演进兼容性，不承诺 NVIDIA 公布的倍数适用于本 SKU；先测编解码格式、插件、Media Encoder 功能、时间线与导出。",
            f"{NVIDIA_ANNOUNCEMENT} ; {ADOBE_ARM} ; {ADOBE_PREMIERE_GPU}",
            status="官方适配中；版本与功能需核对",
            evidence="NVIDIA/Adobe 官方声明；本 SKU 无绝对实测",
        ),
        _record(
            "Blender 3D 建模、Cycles/OptiX 与大型场景",
            "Blender 官方文档确认 Windows 同时支持 x64 与 ARM64 安装包；NVIDIA 对最高 128GB RTX Spark 平台声明 OptiX/DLSS 和最高约 90GB 场景能力。",
            context + (" 可重点验证大型场景，但 90GB 是最高平台能力声明，不是本机稳定上限。" if memory_gb >= 128 else " 不可把最高平台的 90GB 场景声明套用到该内存配置。") + " 需确认 Cycles GPU 后端、插件和渲染器支持。",
            f"{BLENDER_ARM} ; {NVIDIA_PRODUCT}",
        ),
        _record(
            "专业视频剪辑、调色与 4:2:2 媒体工作流",
            "Microsoft 与 NVIDIA 官方资料说明 RTX Spark 支持 4:2:2 硬件编解码、时间线处理和最高平台的 12K 4:2:2 创作定位。该声明不代表任意软件、编解码器或轨道组合均达到相同性能。",
            context + " 以真实素材验证 H.264/HEVC/AV1、位深、色度采样、轨道数、调色节点、降噪和导出；未获得厂商 ARM64 支持声明的软件保持未知。",
            f"{MICROSOFT_STORE} ; {NVIDIA_PRODUCT}",
            status="硬件能力有官方声明；应用兼容性待验证",
        ),
        _record(
            "CAD、工程分析与专业可视化",
            "Microsoft 将 Surface Laptop Ultra for Business 定位于 CAD、3D 建模、仿真和分析，依托 RTX 图形、AI 加速、CUDA 与最高 128GB 统一内存。",
            context + " 该定位不是具体 CAD/CAE 软件认证；采购前必须核对 ARM64/x64 支持、许可证组件、显卡认证驱动、硬件加密狗和插件。",
            MICROSOFT_STORE,
            status="官方场景定位；具体软件认证未知",
            evidence="Microsoft 官方产品定位 + 工程采购检查",
        ),
        _record(
            "Windows Copilot+、Studio Effects、实时字幕与本地 AI 辅助",
            "Microsoft 将设备列为 Copilot+ PC，并列出 Recall、Click to Do、改进的 Windows Search、Live Captions、Cocreator、Studio Effects 等受支持 Windows AI 体验；可用性受版本、地区、语言和策略影响。",
            context + " 企业部署需先确认 Windows 更新通道、隐私策略、数据边界、地区和租户许可，不能仅凭硬件推断所有功能立即可用。",
            MICROSOFT_COPILOT,
            status="官方平台功能；受版本、地区与策略约束",
            evidence="Microsoft 官方功能说明",
        ),
        _record(
            "NVIDIA Broadcast、视频会议降噪与摄像头效果",
            "NVIDIA RTX Spark 产品资料列出 NVIDIA Broadcast，并描述摄像头背景处理和麦克风降噪等 RTX AI 场景。",
            context + " 与 Teams、Zoom 或采集设备组合时需验证 ARM64 应用、虚拟设备、驱动和会议策略；不据此推断电池续航。",
            NVIDIA_PRODUCT,
            status="NVIDIA 官方平台功能；应用组合待验证",
            evidence="NVIDIA 官方产品资料 + 工程验证要求",
        ),
    ]
