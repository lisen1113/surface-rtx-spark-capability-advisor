# surface-rtx-spark-capability-advisor

本地能力顾问使用授权导入的 SKU 数据。首页“按使用需求推荐产品”可组合选项与自由描述；在候选卡片点击“查看此配置的详细能力并生成报告”，会在当前页面展开绑定本次需求及所选 Part Number 的报告，并可打印或另存 PDF。报告区分导入数据、工程筛选和待验证项目，不将系列级声明当成该 SKU 的 FPS 或 Token/s 实测。

Windows 本地启动与数据导入见 [本地运行说明](docs/LOCAL_RUN.md) 和 [数据导入说明](docs/SOURCE_IMPORT.md)。

AI 模型页提供按 SKU 的“快速体验”入口；[中文部署指南](backend/app/deployment.py)按首个 Agent、办公、创作、开发、本地推理及 PAIR 多机任务串联 [NVIDIA RTX Spark 官方战术手册](https://build.nvidia.com/rtx-spark)。知识库补充 MCP、CLI、Skills 的区别与最小权限验收。官方手册的推荐和示例不代替具体料号、应用版本及客户任务的实机验证。

`surfacedmp.com` 已于 2026-10-18 进入员工与内部代理商的**受限公网试点**；这不等于面向公众的正式发布。测试用户已验证登录、返回顾问与 PDF 下载，HTTPS、访问保护、邮件、管理员 MFA 和加密备份恢复均有验收记录。独立第三方安全测试及实体 Windows ARM64/GPU 持续负载验证仍待完成；草稿 PR 保持未合并。详情见 [部署就绪状态](docs/DEPLOYMENT_READINESS.md) 与 [切换/回退记录](docs/PUBLIC_CUTOVER.md)。不要把本机演示服务直接开放公网。

微信小程序第一阶段提供仅承载现有账号页的 `web-view` 试点容器；业务域名校验、AppID 本地配置和 iOS/Android 真机验收步骤见 [小程序内嵌试点](docs/MINIPROGRAM_PILOT.md)。尚未宣称微信内 PDF 保存或免登录已通过。
