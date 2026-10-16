# Windows 11 本地启动 / ERR_CONNECTION_REFUSED 修复说明

## 快速启动
1. 下载/克隆 `codex/bootstrap-v3` 分支（**不要用只有 README 的 main 分支**）。
2. 安装 Python 3.11 或 3.12，并确认 PowerShell 执行 `py -3 --version` 或 `python --version` 有输出。
3. 在**仓库根目录**打开 PowerShell，运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-local.ps1
```

脚本会创建虚拟环境、安装依赖、检查导入、启动服务。**不要关闭 PowerShell 窗口**。等待显示 `Uvicorn running on http://127.0.0.1:8000` 后，浏览器访问：
- http://127.0.0.1:8000/ （中文演示首页）
- http://127.0.0.1:8000/health （健康检查）
- http://127.0.0.1:8000/docs （接口文档）

脚本默认在健康检查成功后自动打开浏览器。启动失败时，打开 `logs/startup.log` 查看错误。
`/health` 只有在本地 SQLite 数据库可访问时才返回 200；数据库目录无权限或文件损坏时返回 503，避免浏览器打开一个无法使用的页面。

## 按需求推荐产品

首页新增“按使用需求推荐产品”：可多选 AI、游戏、生成式 AI、生产力，页面按所选用途展开模型、游戏与目标 FPS、生成工作流或具体软件字段；还可填写预算、排序偏好，或直接输入“要玩 3A 游戏，也要本地运行 70B 模型”之类的描述。系统只识别明确列出的关键词与选项，合并需求后返回已导入 Part Number 的候选、价格、筛选理由和待确认项。描述与明确选项冲突时，以选项为准并提示确认；无法识别用途时要求补充信息。

推荐接口为 `POST /api/recommendations`。其中模型内存采用 Q4 权重、量化开销、KV Cache、运行时和系统预留的工程测算；游戏、生成和生产力的内存起点也是工程筛选档。候选只表示值得进一步验证，不表示软件认证、模型可启动、稳定吞吐或游戏 FPS。价格及配置来自本地导入工作簿，正式采购前须复核。

## 模型部署与企业私有数据

首页“模型部署”标签按当前 Part Number 链接到 `/deployment?sku=<料号>`。指南包括 Windows 11 Pro 架构与驱动检查、LM Studio / Ollama / llama.cpp 入门路线、Linux 服务型框架的验证边界、端到端 PoC、企业私有文档 RAG、微调适用条件、权限与数据泄漏测试。选择 SKU 后，页面从实际内存、存储与 S2/S3 平台生成不同的模型规模试验顺序、Q4 容量筛选和磁盘管理提醒；计算前提明确列出系统、运行时、KV Cache 预留及单用户/2048 token 首轮条件。该结果是工程估算，不证明具体模型兼容、GPU 加速或可用速度。指南不自动安装第三方工具或上传企业数据。运行时、模型、量化、上下文、GPU 后端和实际性能必须在目标设备记录与验收；没有实测的 Token/s 保持未知。

## TCO 初始值与客户调整

TCO 标签通过 `/api/tco/defaults/{part_number}` 读取当前 SKU 的导入 ERP 含税参考价。其余初始值均是明示的预算示例：3 年、20% 期末残值、每年 5% 维护费、80W 平均使用功率、每天 8 小时、每年 250 天、电价 0.8 元/kWh、云端 30 元/百万 Token；月业务量按内存档给出不同演示档，**不代表该 SKU 的实际吞吐或可处理上限**。默认混合方案保留 100% 云端调用，客户完成设备与任务 PoC 后再调整比例。客户可修改全部字段，包括计入 AI 场景的设备成本比例。正式方案须用成交价、企业电价、供应商合同（模型、地区、输入/输出比例）和实测使用量替换示例；本地与云端模型质量和任务范围也须可比。结果是场景差额，不是节省承诺。

回本结论按“计入 AI 场景的设备净成本 ÷（云端月费－本地月运营费）”计算。若分母不大于零，不能给出有限的回本月数；页面会明确显示“当前用量下不回本”，同时按所选测算年限反推所需的最低月业务量。若回本月数超过测算年限，也会显示月数和“超出测算期”。云端单价为零时不存在有限的业务量阈值。客户修改输入并离开字段后，结果自动更新；这些数学结果仍须通过目标任务 PoC 验证可承接业务量。

部署指南与 TCO 都提供“打印报告／另存为 PDF”。打印前页面标题会设为 `Surface-Laptop-Ultra-Deployment-<SKU>` 或 `Surface-Laptop-Ultra-TCO-<SKU>`，作为浏览器建议的 PDF 文件名；页面同时显示建议文件名。TCO 打印稿包含当前输入值与最新计算结果。最终文件名由浏览器或打印驱动控制，保存时请核对 SKU 后缀。

TCO 打印稿采用独立的 A4 报告布局，包含 SKU 与生成日期、成本结论、测算输入和假设限制；页脚使用“以和 · 上海以和信息技术有限公司”的文字标识及版权声明。该文字标识不是未经确认的企业图形 Logo。

## 常见故障
- `ERR_CONNECTION_REFUSED`：服务未运行/已经退出、端口错误或浏览器打开过早。检查 PowerShell 的 Uvicorn 输出。
- `No module named fastapi`：运行脚本安装依赖，或 `cd backend; .\.venv\Scripts\python.exe -m pip install -r requirements.txt`。
- `py not recognized`：安装 Python 3.11/3.12，勾选 PATH；脚本也会尝试 `python`。
- `Address already in use`：`powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-local.ps1 -Port 8001`；浏览器也必须访问 8001。
- `No module named app`：请从仓库根目录运行脚本，不要直接从错误目录运行 `uvicorn`。
- ARM64 安装依赖失败：确认 Python 解释器架构和 pip wheel 可用性，记录错误；不要将 x64 与 ARM64 虚拟环境混用。
- 重建环境：关闭服务，删除 `backend\.venv`，重新运行脚本。

## 测试
```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

草稿 PR 的持续集成会在 `windows-latest` 与 `ubuntu-latest` 上分别使用 Python 3.12、3.13 运行同一组测试，并在 Windows 检查启动脚本语法。GitHub 托管的 Windows runner 是 x64，因此它不能替代实体 Windows on Arm 设备验收。

## Windows x64 / ARM64 验收矩阵

| 检查项 | Windows x64 | Windows ARM64 | 判定标准 |
|---|---|---|---|
| Python 3.12 原生解释器 | CI + 本机 | 必须在实体机执行 | `python -c "import platform; print(platform.machine())"` 与目标架构一致 |
| 依赖安装 | CI 覆盖 | 必须验证 ARM64 wheel；失败时记录具体包与版本 | 不使用另一架构遗留的 `.venv` |
| 本地启动 | PowerShell 脚本 | 同一脚本 | `/health` 返回 200，首页、账号页和管理员页可打开 |
| SQLite 数据读取 | 自动测试 | 实体机抽查 | V3.4 导入后的 SKU 数量、来源台账和映射可读取 |
| 账号与 License | 自动测试 | 实体机抽查 | 注册、验证、审批、授权、登录、注销和密码重置均正常 |

ARM64 验收前先删除由 x64 Python 创建的 `backend\.venv`，再用 ARM64 Python 重新创建。若某个依赖只能通过 x64 仿真安装，应将其记录为兼容性限制，不能宣称原生 ARM64 支持。

本机快速验收命令：

```powershell
python -c "import platform,sys; print(sys.version); print(platform.machine())"
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-local.ps1 -Port 8010 -NoBrowser
```

## 首位管理员

系统没有默认管理员密码。首次部署时，在当前 PowerShell 会话设置管理员邮箱和至少 12 位强密码，然后运行初始化脚本：

```powershell
$env:CAPABILITY_ADMIN_EMAIL='admin@example.com'
$env:CAPABILITY_ADMIN_PASSWORD='replace-with-a-strong-password'
.\backend\.venv\Scripts\python.exe .\scripts\bootstrap-admin.py
Remove-Item Env:CAPABILITY_ADMIN_PASSWORD
```

初始化仅允许执行一次。注册用户必须完成邮箱验证、管理员审批，并获得未过期且有可用席位的组织 License 后才能登录。

## 注册邮箱验证与密码重置邮件

注册会生成 24 小时有效的一次性邮箱验证码；用户在 `/account` 输入验证码后，仍需管理员审批和组织 License。验证码可在 5 分钟后重发，新验证码会撤销旧验证码。密码重置请求也设有每账号 5 分钟冷却时间，重复请求统一返回受理提示且不再次发信；新令牌会撤销旧令牌。密码重置令牌有效期为 30 分钟，使用后撤销该账号的旧会话。两类令牌仅保存 SHA-256 摘要，不写入审计记录或 URL。

部署方需配置 SMTP 主机与发件地址；开启 `CAPABILITY_REQUIRE_AUTH=1` 后，缺少邮件配置会拒绝新的注册和密码重置请求，避免出现无法完成验证的账号。下面以 STARTTLS 为例，具体值由邮件服务提供方或企业密钥管理系统注入：

```powershell
$env:CAPABILITY_SMTP_HOST='smtp.example.com'
$env:CAPABILITY_SMTP_PORT='587'
$env:CAPABILITY_SMTP_TLS_MODE='starttls'
$env:CAPABILITY_SMTP_FROM='advisor@example.com'
$env:CAPABILITY_SMTP_USERNAME='advisor@example.com'
# CAPABILITY_SMTP_PASSWORD 应由密钥管理系统注入，不写入脚本或仓库。
```

也支持 `CAPABILITY_SMTP_TLS_MODE=ssl`（默认端口 465）。本地离线开发可临时设置 `CAPABILITY_DEV_EXPOSE_TOKENS=1`，账号页会自动填入开发验证码；该方式仅在未开启 `CAPABILITY_REQUIRE_AUTH` 时生效，且服务必须仅绑定 `127.0.0.1`。未配置 SMTP 的离线演示仍可由管理员人工核验邮箱，生产部署应使用用户自行验证的邮件流程。

## 重要限制
本分支已具备本地身份认证、审批、License 强制校验、可配置 SMTP 邮箱验证与密码重置、以及 V3.4 数据导入；实际生产邮件服务凭据、管理员 MFA、CSRF 防护和生产级反向代理仍需部署与验收。默认仅监听 127.0.0.1，不要将此开发服务器直接暴露公网。

本机演示默认允许未登录用户查看计算和报告。准备共享部署时必须先设置 `$env:CAPABILITY_REQUIRE_AUTH='1'`；开启后，内存估算、TCO 与客户报告会在每次请求时校验 Bearer 会话及组织 License，已过期 License 会立即被拒绝。正式部署还应由反向代理配置 HTTPS，并在邮件服务与管理员 MFA 完成前保持内网访问。
