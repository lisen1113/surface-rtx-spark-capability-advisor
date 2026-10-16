# 公网正式部署就绪门槛

当前分支仍是本机演示与草稿 PR，**不可直接暴露公网**。`CAPABILITY_DEPLOYMENT_MODE=public` 仅提供必要的配置启动门槛，不代表安全审计或正式发布已通过。`main` 不应在以下项目完成前合并。

用户拟使用 `surfacedmp.com`、腾讯云轻量服务器、CentOS 7.8 64 位。[CentOS Linux 7 已于 2024-06-30 结束维护](https://centos.org/centos-linux/)，不应作为新的公网正式部署目标。先盘点该实例上的现有服务与数据，再在用户批准后创建并验证快照/离机备份，规划迁移到当前受支持的系统。[腾讯云说明重装会清空系统盘](https://cloud.tencent.com/document/product/1207/44576)；仅有快照并不等于恢复演练。不要自动重装或假定该域名已解析、HTTPS 已可用。

## 启动前自动门槛

公网模式启动时，应用会检查 `CAPABILITY_REQUIRE_AUTH=1`、开发令牌展示已关闭、SMTP 主机和发件地址、至少 32 字节的管理员 MFA 主密钥，以及 `CAPABILITY_PUBLIC_BASE_URL` 为 HTTPS 站点根地址。任何一项缺失都会拒绝启动。配置应由目标服务器的密钥管理系统注入，不要写进 Git、截图或聊天。

示意变量名（不是可直接投入生产的配置）：

```text
CAPABILITY_DEPLOYMENT_MODE=public
CAPABILITY_REQUIRE_AUTH=1
CAPABILITY_PUBLIC_BASE_URL=https://advisor.example.com
CAPABILITY_SMTP_HOST=...
CAPABILITY_SMTP_FROM=...
CAPABILITY_MFA_MASTER_KEY=<由密钥管理系统注入>
```

服务仍需只监听受控内网地址，由 HTTPS 反向代理终止 TLS、限制可接受 Host、设置安全头和请求体上限；应用检查 HTTPS URL 字符串**不能证明**真实网络连接已加密。不可直接将 `scripts/start-local.ps1` 的 Uvicorn 开发进程开放公网。

## 正式发布前人工与目标环境验收

1. 确定域名、目标云平台/服务器、操作系统、网络边界、证书签发与更新负责人；在隔离预发布环境验证 HTTPS、反向代理、Host 与重定向。
2. 完成生产数据库方案、结构迁移、加密备份与恢复演练。当前 SQLite 快速启动不是已验证的公网多用户数据库方案；AGENTS.md 要求的 PostgreSQL 生产选项尚未实现。
3. 以真实 SMTP 服务验证注册、验证码、密码重置、失败重试与邮件送达；管理员完成 TOTP 启用、密钥托管和线下恢复流程。
4. 做独立安全评估：会话及令牌存储、XSS/CSRF 适用性、跨租户访问、速率限制、依赖漏洞、日志脱敏、权限最小化与数据保留/删除策略。
5. 目标 Windows 11 ARM64 设备验证依赖、驱动、模型许可、GPU 后端和实际工作负载。官方平台声明、容量估算不得作为该 SKU 的 Token/s、FPS 实测。
6. 核实授权工作簿的对外使用权、SKU 价格有效期、微软商用 Surface ADR 身份及商标/Logo 使用；完成法务确认。
7. 由业务方在预发布站点完成账号审批、License 过期/席位、FAQ、需求推荐、报告 PDF 文件名、TCO 和备份恢复验收，并记录签署结果。

只有目标环境的上述证据齐全，才可把草稿 PR 标记为待正式评审；评审与发布审批仍独立于自动测试。切勿把本机 `http://127.0.0.1:8010/` 的通过结果称为公网可部署。
