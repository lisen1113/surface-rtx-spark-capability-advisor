# 腾讯云 COS 异地加密备份（待目标环境验收）

截至 2026-10-17，目标服务器已经完成**本机私有备份及隔离数据库恢复演练**；专用 COS 子账户已绑定限定目录策略，首次密文上传、下载及认证校验通过。COS 密文的**独立 PostgreSQL 恢复演练**尚待执行，不能据此声称整个备份恢复闭环已验收。

1. 使用**私有** COS 存储桶，记录完整 `BucketName-APPID` 和地域代码。关闭公共读写，开启版本控制、适当保留策略及访问审计。当前用户所建桶与应用服务器均在上海，可抗单机故障，**不可声称跨地域容灾**。腾讯云 [Python SDK 上传文档](https://cloud.tencent.com/document/product/436/65820)给出简单上传 `put_object`；[下载文档](https://cloud.tencent.com/document/product/436/65821)给出 `name/cos:GetObject`。仅对该桶 `capability-advisor/` 前缀授予 `name/cos:PutObject`、`name/cos:GetObject`，以及下载前元数据核查可能使用的 `name/cos:HeadObject`；不授予删除、建桶或全量管理权限。优先使用短期凭据或受限子账号，不能使用主账号密钥。
2. 在服务器受保护的专用环境中分别配置 `CAPABILITY_COS_BUCKET`、`CAPABILITY_COS_REGION`、`COS_SECRET_ID`、`COS_SECRET_KEY`，短期凭据另加 `COS_SESSION_TOKEN`。`CAPABILITY_BACKUP_KEY_B64` 必须是独立随机生成的 **32 字节**密钥的 Base64 表示。密钥与 COS 凭据分开托管，并在服务器之外封存恢复副本；不写入仓库、工单或聊天。没有这把密钥，COS 副本无法恢复。所有凭据只由专用备份进程读取，不提供给 Web 应用或前端。`deploy/init_cos_env.py <完整桶名> <地域代码>` 会在服务器终端隐藏接收专用密钥及已封存的备份密钥，并排他创建仅 root 可读的 `/etc/capability-cos-backup.env`；不覆盖已有配置。不要直接复用网站的 `/etc/capability-advisor.env`。
3. 在服务器的独立 `backup-venv` 中安装 `deploy/requirements-cos.txt`，避免修改网站应用依赖；先安装但**不自动启用** `deploy/capability-cos-backup.service`。人工启动一次性服务后，`run_cos_backup.py` 创建新本机备份，`cos_offsite_backup.py` 校验备份、流式打包并用 AES-256-GCM 加密，只将密文上传到 COS 的时间戳对象键。随后从 COS 下载密文，比对 SHA-256 并验证认证标签和归档结构；失败必须报警，不能标记为备份成功。对象键只包含备份时间，不包含客户信息。初次验证和隔离恢复通过后，再另外评审定时器、告警和保留策略。
4. 使用 `deploy/restore_cos_backup.py capability-advisor/<UTC时间戳>.tar.gcm` 做隔离恢复演练。此脚本需由 root 在服务器上运行，并从 root-only 的独立备份环境文件加载所需变量；只接受固定前缀的时间戳对象键。它把 COS 密文下载到私有临时目录，经 AES-GCM 认证后逐个写出预期的三个文件、复核校验和与 SQLite 完整性，再恢复 PostgreSQL 到随机命名的**临时数据库**，核对账号/组织/License/MFA 的行数及产品目录 SKU 数，最后删除临时数据库与本地明文。不能把线上 `advisor` 数据库作为恢复目标，也不能在日志或命令行里打印密钥。还应记录演练日期、操作人和耗时。

本工具的下载验证目前最多接受 256 MiB 密文；超过时会拒绝并报警，须先扩展为有界流式验证后再上线。自动轮换、监控和删除策略应在首次端到端恢复演练后启用。**COS 配置完成、上传成功和隔离恢复通过之前，不满足公网发布门槛。**
