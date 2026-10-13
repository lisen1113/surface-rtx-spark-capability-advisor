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

## 重要限制
本分支仍是初期演示。暂未实现正式身份认证、License、完整 SKU 数据导入或可交付的 Windows ARM64 兼容性测试。默认仅监听 127.0.0.1，不要将此开发服务器暴露公网。
