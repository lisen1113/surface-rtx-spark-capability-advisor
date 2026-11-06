# surface-rtx-spark-capability-advisor

硬件租赁已按用户示例增加 12 / 24 / 36 月固定计价系数 1.15 / 1.30 / 1.45，管理员可按品牌及租期调整残值，并设置 Surface ERP 成本比例。原始 ERP 与历史报价保留，月租尾差在末期调整。

新增本地独立客户入口 `/workplace`（无需登录）及管理员入口 `/workplace/admin`：Surface 租赁、M365/Copilot 标准价组合、客户资料、预算/正式报价和 Azure 独立合同用量。软件成本按公开标准价的 85% 核算，客户按标准价报价。使用隔离预览库的启动、配置与验证见 [商业工作台说明](docs/COMMERCIAL_WORKSPACE.md)。2026-11-06 经授权更新 surfacedmp.com，并上传小程序开发版本 3.2.20261106.1；审核与正式发布尚待微信平台完成，详见 [发布记录](docs/WORKPLACE_RELEASE_2026_11_06.md)。

本地能力顾问使用授权导入的 SKU 数据。首页“按使用需求推荐产品”可组合选项与自由描述；在候选卡片点击“查看此配置的详细能力并生成报告”，会在当前页面展开绑定本次需求及所选 Part Number 的报告，并可打印或另存 PDF。报告区分导入数据、工程筛选和待验证项目，不将系列级声明当成该 SKU 的 FPS 或 Token/s 实测。

V3.1 首页新增 Surface SKU 快速查询：可按完整或部分 Part Number、类别、大系列、CPU、内存、配置、颜色、联网和 ERP 价格上限筛选设备、配件及延保，并按用户输入的报价系数显示报价结果。ERP 含税价与 ADR Price 始终来自用户授权工作簿；微软中国官网资料只用于产品规格与延保内容核对。原有 RTX Spark V3.4 能力数据和报告链路保持独立，不会被 V3.1 查询索引覆盖。

Windows 本地启动与数据导入见 [本地运行说明](docs/LOCAL_RUN.md) 和 [数据导入说明](docs/SOURCE_IMPORT.md)。

AI 模型页提供按 SKU 的“快速体验”入口；[中文部署指南](backend/app/deployment.py)按首个 Agent、办公、创作、开发、本地推理及 PAIR 多机任务串联 [NVIDIA RTX Spark 官方战术手册](https://build.nvidia.com/rtx-spark)。知识库补充 MCP、CLI、Skills 的区别与最小权限验收。官方手册的推荐和示例不代替具体料号、应用版本及客户任务的实机验证。

`surfacedmp.com` 已于 2026-10-18 进入员工与内部代理商的**受限公网试点**；这不等于面向公众的正式发布。测试用户已验证登录、返回顾问与 PDF 下载，HTTPS、访问保护、邮件、管理员 MFA 和加密备份恢复均有验收记录。独立第三方安全测试及实体 Windows ARM64/GPU 持续负载验证仍待完成；草稿 PR 保持未合并。详情见 [部署就绪状态](docs/DEPLOYMENT_READINESS.md) 与 [切换/回退记录](docs/PUBLIC_CUTOVER.md)。不要把本机演示服务直接开放公网。

微信小程序试点首页采用以和品牌页眉，提供公开官网、游客体验与内部顾问三个入口。游客可查看白名单内的产品配置、工程候选及 AI/游戏/生成式 AI/生产力说明；价格、知识库、报告、TCO 与管理功能仍需登录授权。访问边界见 [游客模式说明](docs/GUEST_MODE.md)；业务域名校验、AppID 本地配置和 iOS/Android 真机验收见 [小程序内嵌试点](docs/MINIPROGRAM_PILOT.md)。游客模式目前在开发分支，尚未部署到生产，也未宣称微信内 PDF 保存通过。
