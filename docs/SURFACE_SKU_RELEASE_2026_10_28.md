# Surface SKU 查询发布记录

2026-10-28 按用户明确授权部署到 surfacedmp.com。

- 独立入口 `/surface`，RTX Spark 原入口 `/` 保留。
- 查询总记录 237，默认查询 226：Surface 设备 191、配件 17、延保 18；暂不纳入的 NVIDIA 11 条保留。
- 支持英特尔/高通、屏幕、内存、存储、Wi-Fi/5G、价格、关键词组合筛选。配件和延保忽略主机条件。
- 配置含 xP 或 No-PSU 时显示不带电源；其他不附电源备注。
- 每 SKU 可下载 `Surface-Product-<SKU>.pdf`；原表 ERP 价格保持。
- 服务器保留原有 11 条 RTX Spark SKU；仅安装 catalog.py、ui.py、surface_pdf.py；线上 auth.py 校验值未变。
- 先后运行已有 COS 加密备份，Result=success；回退快照 `/opt/capability-advisor/backups/surface-release-20261028T031707Z`。
- 发布包 SHA256：`7d4328b76a0b3ba13319886f493b1d65bf07574e075e879446b8d3c6255ffc82`。私有 ZIP 和原始数据未提交 Git。
- 部署前 19 项相关回归检查通过；服务器只读验收覆盖分类计数、筛选、配件延保、价格及 PDF 生成。

线上人工测试：用原有授权账号登录，访问 `/surface`，组合筛选产品并下载 PDF，核对 SKU 文件名和不带电源备注。
