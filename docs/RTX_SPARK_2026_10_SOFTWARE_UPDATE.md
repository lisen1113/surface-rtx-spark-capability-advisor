# RTX Spark 2026-10 软件更新：映射边界

核查日期：2026-10-17。主来源：[NVIDIA 2026-10-13 软件生态公告](https://blogs.nvidia.com/blog/local-ai-rtx-spark-laptops-software-updates/)。本次仅补入有明确来源的产品/软件状态与 PoC 验收建议；不修改授权工作簿原始行，也不将生态公告充作逐 SKU 基准测试。

| 补充方向 | 官方资料可支持的表述 | 本产品仍需核验 |
|---|---|---|
| Nemotron 3.5 Bolt 74B-A9B | NVIDIA 公告列出 74B 总参数、9B 活跃参数和指定 2-bit 约 24GB 模型包及若干推理工具路径。 | 权重与许可证、目标工具版本、总内存/KV 开销、实际 GPU 后端、准确性和 Token/s；不能用普通 74B Q4 算式替代。 |
| PAIR | [官方项目](https://github.com/NVIDIA/Personal-AI-Router)说明它按独立请求在局域网节点间路由；Windows ARM64 为实验支持。 | 单节点模型与引擎支持、双机发现/配对、网络边界和数据去向；不合并内存，也不拆分同一推理请求。 |
| Agent 沙箱/混合路由 | NVIDIA 公告列出 OpenShell、MXC 与一些应用的本地/云端路由能力。 | 各应用实际发布版本、默认权限、密钥保护、客户数据是否离网和云端费用；“支持”不等于默认安全。 |
| 创作软件 | 公告区分 Broadcast 2.3 已提供、Adobe 部分优化处于测试版、Blender 5.3 测试版与后续光线重建功能。 | ARM64 软件/插件/驱动组合及具体任务；视频后处理帧率不等于游戏 FPS 或生成模型吞吐。 |
| 游戏与开发环境 | 公告列出游戏生态、DLSS 更新和 Windows on Arm 开发工具进展。 | 逐游戏、启动器/反作弊/驱动与帧率；逐版本核对 PyTorch-CUDA、Python/Conda、wheel 和 GPU 后端。 |

所有映射明确分开“官方公告”“工程建议”“本 SKU 待验证”。公告中的相对倍数、示例视频帧率、平台应用数量或 Python wheel 覆盖率都不得改写成某个 Part Number 的实测结论。发布前按官网当前版本复核可用状态，尤其不要把测试版或计划功能写成正式版现有能力。
