# 独立服务器隔离预览（非正式公网发布）

目标实例：腾讯云 `surface-advisor-shanghai`，Ubuntu 24.04 x86_64。该流程只把应用绑定在新机 `127.0.0.1:8011`，通过用户自己建立的 SSH 隧道查看。**不切换 `surfacedmp.com`，不开放 8011 端口，也不操作 `yiheit.net` 旧机。**

## 私有预览包

在受信任的本机仓库执行 `python scripts/build_staging_package.py --output artifacts/staging-preview.zip`。生成器只复制应用代码和必要的目录/映射数据；新建数据库只包含 `skus`、`models`、`evidence`、`source_imports`、`source_records`、`imported_skus`、`imported_evidence`，**不包含用户、组织、License、会话、验证码、密码重置令牌、MFA 或审计记录，也不包含原始 `.xlsx`/`.docx`**。数据仍可能含授权 SKU 价格和来源记录，ZIP 属于私有部署资料，不得提交 Git、公开分享或放入网站静态目录。

上传前在本机核对 SHA-256；把 ZIP 仅上传到新机 `ubuntu` 用户家目录，在服务器上运行 `sha256sum` 并核对一致。不要通过未认证的 `raw.githubusercontent.com` 下载私有仓库。不要上传本机完整 `data/capability.sqlite3`：其中有真实账户与会话数据。

## 新机启动（由持有服务器会话的用户执行）

1. 确认新机初始快照状态正常、系统更新后运行新内核，且防火墙没有放行 8011。Ubuntu 系统可能需要先安装 `python3-venv`，先检查再安装。
2. 在 `/home/ubuntu` 中创建独立的 `surface-advisor-preview` 目录，用 `python3 -m zipfile -e staging-preview.zip surface-advisor-preview` 解压；检查其中有 `backend/app/main.py`、`data/capability.sqlite3`、`start-staging.sh`。
3. 进入目录，以普通 `ubuntu` 账号运行 `bash start-staging.sh`。脚本创建 `.venv`、安装 `backend/requirements.txt`，以 `CAPABILITY_DEPLOYMENT_MODE=local` 启动 Uvicorn，仅监听 `127.0.0.1:8011`。这是匿名**隔离演示**，绝不能改成 `0.0.0.0` 或开放公网 8011。
4. 在用户自己的 Windows 电脑建立仅本机的 SSH 端口转发，例如 `ssh -i <本机私钥路径> -L 8011:127.0.0.1:8011 ubuntu@123.207.183.23`；保持该终端连接，再在本机浏览器打开 `http://127.0.0.1:8011/`。私钥路径仅在用户电脑输入，私钥内容不要发送给 Codex、腾讯云网页表单或 GitHub。若本机 8011 已占用，可只改 `-L` 左侧本机端口。
5. 验收首页、SKU、需求推荐、FAQ、部署路线、TCO 和报告。关闭 SSH 隧道后，本机浏览器不应再能连接预览站点；停止服务器上前台进程后，`127.0.0.1:8011` 也不应响应。

该方案不是 HTTPS 公网部署，也不覆盖正式 SMTP、账号授权、PostgreSQL、备份恢复、安全审查与业务签收。公网模式继续拒绝 SQLite 启动；不得以预览验收替代发布审批。
