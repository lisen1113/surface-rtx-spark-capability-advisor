"""Dated vendor updates, separate from imported SKU measurements."""

NVIDIA_UPDATE = "https://blogs.nvidia.com/blog/local-ai-rtx-spark-laptops-software-updates/"
NVIDIA_PAIR = "https://github.com/NVIDIA/Personal-AI-Router"
NVIDIA_PLAYBOOKS = "https://build.nvidia.com/rtx-spark"


def agent_guidance(part_number: str, memory_gb: int) -> list[dict]:
    context = f"{part_number}｜{memory_gb}GB 统一内存。"
    return [
        {
            "推荐模型/工作负载名称": "Nemotron 3.5 Bolt 74B-A9B 本地 Agent",
            "官方能力/平台声明": "NVIDIA 2026-10-13 公告：74B 总参数、9B 活跃参数的 MoE；其发布的 2-bit 版本模型权重约 24GB，并列出 llama.cpp、vLLM、Ollama、Unsloth、LM Studio 路径。",
            "本地运行判断": "官方模型发布信息；本 SKU 能否加载、GPU 加速与速度未知",
            "经验推荐与我的判断": context + "24GB 是所述模型权重体积，不是整机所需内存；还须留系统、运行时、上下文/KV 和并发余量。不要用普通 74B Q4 估算代替该 MoE 的具体量化包；核对实际权重、许可证与后端后逐机试验。",
            "性能指标": "未知（无本 Part Number 实测 Token/s）",
            "证据等级": "NVIDIA 官方发布说明 + 工程验证要求",
            "官方来源URL": NVIDIA_UPDATE,
            "依据与限制": "仅描述 NVIDIA 指定的模型版本和量化；并非对任一 Surface SKU 的运行或性能保证。",
        },
        {
            "推荐模型/工作负载名称": "NVIDIA PAIR 多设备本地推理路由",
            "官方能力/平台声明": "NVIDIA PAIR 1.0.0 战术手册列出 RTX Spark 的 Windows ARM64 安装包，以及 llama.cpp、Ollama、LM Studio 引擎；在受信任局域网内按独立请求路由。",
            "本地运行判断": "官方工具能力；本 SKU/网络组合待验证",
            "经验推荐与我的判断": context + "先在单机建立基线，再用第二节点测试发现、配对、模型版本与路由日志；逐节点确认引擎、模型许可、网络访问控制和数据去向。",
            "性能指标": "未知（无本 Part Number 多节点吞吐实测）",
            "证据等级": "NVIDIA 官方项目说明 + 工程验证要求",
            "官方来源URL": "https://build.nvidia.com/rtx-spark/pair",
            "依据与限制": "PAIR 不合并 GPU/统一内存，也不把同一请求拆到多机；路由能力不证明每个节点的模型都能运行。",
        },
        {
            "推荐模型/工作负载名称": "AI Agent 连接 Windows 应用：MCP、CLI 与 CUDA-X Skills",
            "官方能力/平台声明": "NVIDIA 2026-10-13 公告介绍 NVIDIA App、Broadcast、PAIR、Omniverse、RTX Remix 的 MCP 连接，以及 NVIDIA Skills 库；具体连接器须按应用版本核实。",
            "本地运行判断": "生态入口；本 SKU 的应用、MCP 服务及代理组合未实测",
            "经验推荐与我的判断": context + "先选一个只读、非敏感任务；确认代理客户端与目标应用版本、MCP/CLI 安装来源和权限，再演示读取或生成草稿。Skills 是代理工作流程，不等于 MCP 服务，也不意味着自动取得应用权限。",
            "性能指标": "未知（无本 Part Number Agent 任务实测）",
            "证据等级": "NVIDIA 官方生态公告 + 工程验收建议",
            "官方来源URL": NVIDIA_UPDATE,
            "依据与限制": "连接能力取决于实际应用和客户端版本；不要让代理默认获得邮件发送、文件删除或系统设置更改权限。",
        },
        {
            "推荐模型/工作负载名称": "RTX Spark 官方 AI 战术手册：首个 Agent / 创作 / 开发",
            "官方能力/平台声明": "NVIDIA 提供分场景的入门、生产力、创作、开发、推理与 PAIR 战术手册。",
            "本地运行判断": "官方操作指南；本 SKU 的安装成功率和速度待验证",
            "经验推荐与我的判断": context + "非技术用户先完成首个 Agent 与一个只读任务；开发者再按官方推理与开发手册核对 ARM64、模型许可、后端和驱动。详细步骤见本产品的模型部署页。",
            "性能指标": "未知（无本 Part Number 工作流实测）",
            "证据等级": "NVIDIA 官方战术手册 + 本站工程引导",
            "官方来源URL": NVIDIA_PLAYBOOKS,
            "依据与限制": "手册中的示例模型、时间和命令不是所有 SKU 的兼容性或性能保证；下载前检查来源和权限。",
        },
        {
            "推荐模型/工作负载名称": "本地 Agent、沙箱与本地/云端混合路由",
            "官方能力/平台声明": "NVIDIA 公告列出 Agent 应用集成、OpenShell/MXC 隔离与本地/云端路由；不同应用的功能、发布时间和默认配置各异。",
            "本地运行判断": "官方生态公告；具体应用配置待验证",
            "经验推荐与我的判断": context + "试点时先关闭非必要云路由和工具权限，用脱敏任务验证沙箱、凭据保护、审批与审计；若启用云端，单独审批数据处理与费用。",
            "性能指标": "未知（未进行 Agent 任务实测）",
            "证据等级": "NVIDIA 官方生态公告 + 安全工程建议",
            "官方来源URL": NVIDIA_UPDATE,
            "依据与限制": "安装 Agent 或宣称支持沙箱，不等于默认已隔离所有工具、密钥和客户数据。",
        },
    ]


def gaming_updates(part_number: str) -> list[dict]:
    return [
        {
            "游戏名称": "RTX Spark 游戏生态与反作弊",
            "官方能力/平台声明": "NVIDIA 2026-10-13 公告称 RTX Spark 平台已有多款游戏与反作弊适配。",
            "兼容性状态": "平台级公告；逐游戏/商店/版本待验证",
            "经验推荐与我的判断": f"{part_number} 须分别检查目标游戏、启动器、反作弊、驱动和在线功能；记录实际安装与运行结果。",
            "性能指标": "未知（无本 Part Number FPS 实测）",
            "证据等级": "NVIDIA 官方平台公告 + 本 SKU 待验证",
            "官方来源URL": NVIDIA_UPDATE,
            "依据与限制": "游戏名称出现在生态公告中，不表示该 SKU 的帧率、画质、稳定性或所有在线模式已验收。",
        },
        {
            "游戏名称": "DLSS 5 / 帧生成新模式",
            "官方能力/平台声明": "NVIDIA 公告介绍 DLSS 5 新模型及帧生成 Performance Mode；功能取决于游戏版本、驱动、应用设置与发布时间。",
            "兼容性状态": "官方技术公告；目标游戏实现待验证",
            "经验推荐与我的判断": f"在 {part_number} 上比较原生、上采样和帧生成模式时，分别记录基础帧率、输出帧率、延迟与画质，不混用口径。",
            "性能指标": "未知（不套用公告中的其他配置相对提升）",
            "证据等级": "NVIDIA 官方技术公告 + 工程测试建议",
            "官方来源URL": NVIDIA_UPDATE,
            "依据与限制": "平台级相对提升及特定游戏案例不是本 SKU 的 FPS 保证。",
        },
    ]
