# 腾讯云 COS 异地加密备份（待目标环境验收）

当前目标服务器已经完成**本机私有备份及隔离数据库恢复演练**。用户选择腾讯云 COS 作为异地目标，但尚未配置存储桶、地域和专用访问授权；因此不能声称异地备份已成功。

1. 在与应用服务器不同的故障域创建**私有** COS 存储桶，记录完整 `BucketName-APPID` 和地域代码。关闭公共读写，开启版本控制、适当保留策略及访问审计。腾讯云 [Python SDK 上传文档](https://cloud.tencent.com/document/product/436/65820)列出高级上传所需对象权限；[下载文档](https://cloud.tencent.com/document/product/436/65821)列出 `cos:GetObject`。授权仅限此桶的 `capability-advisor/` 前缀，并允许上传/下载验证所需的最小操作；优先使用短期凭据或受限子账号，不能使用主账号密钥。
2. 在服务器受保护的专用环境中分别配置 `CAPABILITY_COS_BUCKET`、`CAPABILITY_COS_REGION`、`COS_SECRET_ID`、`COS_SECRET_KEY`，短期凭据另加 `COS_SESSION_TOKEN`。`CAPABILITY_BACKUP_KEY_B64` 必须是独立随机生成的 **32 字节**密钥的 Base64 表示。密钥与 COS 凭据分开托管，并在服务器之外封存恢复副本；不写入仓库、工单或聊天。没有这把密钥，COS 副本无法恢复。所有凭据只由专用备份进程读取，不提供给 Web 应用或前端。`deploy/init_cos_env.py <完整桶名> <地域代码>` 会在服务器终端隐藏接收专用密钥及已封存的备份密钥，并排他创建仅 root 可读的 `/etc/capability-cos-backup.env`；不覆盖已有配置。不要直接复用网站的 `/etc/capability-advisor.env`。
3. 在服务器专用环境安装 `deploy/requirements-cos.txt`，先安装但**不自动启用** `deploy/capability-cos-backup.service`。人工启动一次性服务后，`run_cos_backup.py` 创建新本机备份，`cos_offsite_backup.py` 校验备份、流式打包并用 AES-256-GCM 加密，只将密文上传到 COS 的时间戳对象键。随后从 COS 下载密文，比对 SHA-256 并验证认证标签和归档结构；失败必须报警，不能标记为备份成功。对象键只包含备份时间，不包含客户信息。初次验证和隔离恢复通过后，再另外评审定时器、告警和保留策略。
4. 另行把 COS 副本下载到隔离恢复环境，使用托管的密钥解密，恢复 PostgreSQL 到**临时数据库**，核对账号/组织/License/MFA 及产品目录，再记录演练日期、操作人和恢复耗时。下载校验通过仍不能替代此恢复演练。不要将解密归档放在公网目录，不要覆盖线上数据库。

本工具的下载验证目前最多接受 256 MiB 密文；超过时会拒绝并报警，须先扩展为有界流式验证后再上线。自动轮换、监控和删除策略应在首次端到端恢复演练后启用。**COS 配置完成、上传成功和隔离恢复通过之前，不满足公网发布门槛。**
