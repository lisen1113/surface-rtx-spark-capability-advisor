# 公网正式部署就绪门槛

当前分支仍是草稿 PR，**不可直接暴露公网**。已增加 PostgreSQL 账号/License 数据层和只读 SQLite 产品目录，公网模式要求 `CAPABILITY_AUTH_DATABASE_URL`，但目标服务器集成测试、安全验收和发布步骤尚未完成。仅通过环境变量门槛不代表上线许可；`main` 不应在以下项目完成前合并。

部署目标是 `surfacedmp.com` 的独立新服务器。该域名旧站内容已被用户声明不再需要，但现有 CentOS 7.8 服务器仍承载 `yiheit.net` 公司官网，**不得重装、停机或修改该服务器**；旧站文件也不要在新站验收前删除。CentOS Linux 7 已于 [2024-06-30 结束维护](https://centos.org/centos-linux/)；官网迁移另立项目，不能混入能力顾问上线任务。腾讯云明确说明[重装会清空系统盘并使实例关机](https://cloud.tencent.com/document/product/1207/44576)，因此不采用“重装旧机”方案。不要假定新服务器已购买、域名已切换或 HTTPS 已完成。

## 新服务器现状（2026-10-16，按用户控制台截图核对）

- 新购腾讯云轻量应用服务器 `surface-advisor-shanghai`，上海地域，公网 IPv4 `123.207.183.23`；2 vCPU / 4 GB、60 GB SSD、5 Mbps、500 GB/月。Ubuntu Server 24.04.4 LTS x86_64；系统更新及重启后内核 `6.8.0-147-generic`。
- 已创建初始系统盘快照且控制台状态为正常。仅看到默认防火墙规则：22/TCP、80/TCP 和 ICMP 对全部 IPv4 开放；443/TCP 尚未开放，域名尚未切换。SSH 私钥由用户自行保管，不进入聊天或仓库。
- 这台服务器只运行 Web/API/数据库，不运行 RTX Spark 本地模型。旧 CentOS 服务器及 `yiheit.net` 不在本任务变更范围内。
- 购买或基础系统准备完成**不代表应用可发布**；数据库、SMTP、HTTPS、备份恢复、安全审查和业务验收仍未完成。
- 隔离预览的可复现操作见 [STAGING_PREVIEW.md](STAGING_PREVIEW.md)；其运行在 127.0.0.1，不是公网发布。

## 容量选择背景

- 只运行能力顾问 Web/API/数据库，不在该服务器部署 RTX Spark 模型推理；故不需要 GPU 实例。
- 初期公网试点建议腾讯云轻量应用服务器 **4 vCPU、8 GB 内存、至少 120 GB SSD、x86_64、Ubuntu Server 24.04 LTS**。这是为应用、数据库、反向代理、备份及更新保留余量的工程建议，不是用户数或吞吐量实测保证。腾讯云[产品页列有 4 核 8 GB 套餐](https://cloud.tencent.com/product/lighthouse)；具体磁盘、带宽、价格和可选镜像以购买时所选地域页面为准。Ubuntu 24.04 LTS 的标准安全维护期至 [2029 年 5 月](https://documentation.ubuntu.com/release-notes/24.04/)。
- 用户选择中国内地地域，并确认 `surfacedmp.com` 已完成备案；备案号、备案主体、腾讯云接入状态、经营性/非经营性类型以及备案网站名称/服务内容是否与新项目一致，仍需在控制台核对。同一腾讯云接入商换到另一腾讯云 IP，非经营性备案通常[不强制重新备案](https://cloud.tencent.com/document/product/243/19617)；如备案服务信息改变，按腾讯云[变更服务指引](https://cloud.tencent.com/document/product/243/19145)办理。若实际需办理接入或变更，重新核对新资源的购买时长要求。
- 最低成本可以先按月开通新机作**非公开技术验收**，但不要仅凭“域名以前备案过”判断 1 个月套餐足以正式切换；腾讯云在办理备案时对轻量服务器要求[累计购买至少 3 个月且备案期间剩余至少 1 个月](https://cloud.tencent.com/document/product/243/18908)。购买前先核对优惠资格、续费价与是否需要备案手续。
- 新机分配独立公网 IP；只在预发布验收、HTTPS 和正式批准后变更 `surfacedmp.com` 对应 DNS。不要修改 `yiheit.net` 的 DNS、证书或旧机反向代理。

## 启动前自动门槛

公网模式启动时，应用会检查 PostgreSQL URL、`CAPABILITY_REQUIRE_AUTH=1`、开发令牌展示已关闭、SMTP 主机和发件地址、至少 32 字节的管理员 MFA 主密钥，以及 `CAPABILITY_PUBLIC_BASE_URL` 为 HTTPS 站点根地址。任何一项缺失都会拒绝启动。配置应由目标服务器的密钥管理系统注入，不要写进 Git、截图或聊天。

示意变量名（不是可直接投入生产的配置）：

```text
CAPABILITY_DEPLOYMENT_MODE=public
CAPABILITY_REQUIRE_AUTH=1
CAPABILITY_PUBLIC_BASE_URL=https://advisor.example.com
CAPABILITY_AUTH_DATABASE_URL=postgresql://<独立数据库账号>@127.0.0.1:5432/<数据库名>
CAPABILITY_SMTP_HOST=...
CAPABILITY_SMTP_FROM=ls@yiheit.net
CAPABILITY_SMTP_USERNAME=ls@yiheit.net
CAPABILITY_SMTP_PASSWORD=<仅服务器密钥环境中注入>
CAPABILITY_MFA_MASTER_KEY=<由密钥管理系统注入>
```

用户指定腾讯企业邮箱 `ls@yiheit.net` 作为验证码发件地址。腾讯云的[企业邮客户端设置文档](https://main.qcloudimg.com/raw/document/product/pdf/613_46019_cn.pdf)给出普通 SMTP 服务 `smtp.exmail.qq.com`、SSL、465 端口；仍须在该邮箱管理后台核实客户端访问权限与授权码。授权码仅在服务器密钥环境中配置；不在聊天、代码或文档中填写。生产依赖使用 `backend/requirements-production.txt`；在专用 PostgreSQL 数据库运行 `backend/sql/auth_postgres_v1.sql`。账号库不得开放公网 5432 端口。产品目录 SQLite 文件在公网模式以只读方式打开；导入/更新须离线构建新版目录文件后重新部署。备份需要同时覆盖 PostgreSQL 和目录文件。

客户 PDF 下载由服务端生成，文件名包含所选 Part Number，并沿用登录/License 校验。为保证中文和英文混排可读，在服务器私有目录安装 [Noto Sans SC 的 OFL 许可 TTF](https://github.com/google/fonts/tree/main/ofl/notosanssc)，例如 `/opt/capability-advisor/fonts/NotoSansSC-VF.ttf`，或通过 `CAPABILITY_PDF_FONT_PATH` 指定实际路径；不要将字体文件混入授权产品目录或原始工作簿。未安装时会退回 PDF 内建中文字体，发布前仍须实测中文渲染与打印。

服务仍需只监听受控内网地址，由 HTTPS 反向代理终止 TLS、限制可接受 Host、设置安全头和请求体上限；应用检查 HTTPS URL 字符串**不能证明**真实网络连接已加密。共享/公网模式会在应用层拒绝与 `CAPABILITY_PUBLIC_BASE_URL` 不一致的 `Host`，并发送 `nosniff`、禁止嵌入及同源 Referrer 安全头；反向代理必须保留正确的原始 `Host`，不能依赖这些应用头替代代理配置。不可直接将 `scripts/start-local.ps1` 的 Uvicorn 开发进程开放公网。

新机使用 `deploy/capability-advisor.service` 将应用限制在 `127.0.0.1:8011`，`deploy/Caddyfile` 是待 DNS/证书就绪后启用的 HTTPS 反向代理模板。服务所需 `/etc/capability-advisor.env` 由服务器管理员以仅 root 可读的权限建立；密钥和邮箱授权码不进入仓库。启用前必须在新机本地逐项检查服务、数据库、SMTP 投递、HTTPS 证书、备份恢复和登录/License 流程。不要因为配置文件已复制就提前启动公网监听。

若需在 DNS 切换前通过 SSH 本地端口转发验收真实公网模式账号，可临时安装 `deploy/loopback-preview.conf`。此开关仅接受服务器本机回环来源且 `Host` 为 `127.0.0.1:8011` 或 `localhost:8011`，应用仍只监听 `127.0.0.1:8011`。**正式 DNS/HTTPS 切换前必须删除该 override 并重启服务**；不可将 8011 放入云防火墙公网规则。管理员首次登录后应立刻启用 TOTP MFA；密钥、动态码和密码不得截图或发到聊天。

## 正式发布前人工与目标环境验收

1. 确定域名、目标云平台/服务器、操作系统、网络边界、证书签发与更新负责人；在隔离预发布环境验证 HTTPS、反向代理、Host 与重定向。
2. 在目标服务器完成 PostgreSQL 初始化、账号/License 集成测试、加密备份与恢复演练。现有本机 SQLite 快速启动不可充当公网多用户账号库。
3. 以真实 SMTP 服务验证注册、验证码、密码重置、失败重试与邮件送达；管理员完成 TOTP 启用、密钥托管和线下恢复流程。
4. 做独立安全评估：会话及令牌存储、XSS/CSRF 适用性、跨租户访问、速率限制、依赖漏洞、日志脱敏、权限最小化与数据保留/删除策略。
5. 目标 Windows 11 ARM64 设备验证依赖、驱动、模型许可、GPU 后端和实际工作负载。官方平台声明、容量估算不得作为该 SKU 的 Token/s、FPS 实测。
6. 核实授权工作簿的对外使用权、SKU 价格有效期、微软商用 Surface ADR 身份及商标/Logo 使用；完成法务确认。
7. 由业务方在预发布站点完成账号审批、License 过期/席位、FAQ、需求推荐、报告 PDF 文件名、TCO 和备份恢复验收，并记录签署结果。

只有目标环境的上述证据齐全，才可把草稿 PR 标记为待正式评审；评审与发布审批仍独立于自动测试。切勿把本机 `http://127.0.0.1:8010/` 的通过结果称为公网可部署。
