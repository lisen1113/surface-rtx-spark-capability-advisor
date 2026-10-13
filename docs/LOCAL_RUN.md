# Local Windows bootstrap (backend only)
Prerequisites: Python 3.12, Windows 11, internet once to install pip packages.
Run from repository root in PowerShell:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-local.ps1
```
Then open http://127.0.0.1:8000/docs and http://127.0.0.1:8000/health
Run tests:
```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```
ARM64 note: Python and dependency wheels must be available for your architecture; otherwise document a compatible Python interpreter or build alternative. This starter does NOT include authentication, database persistence, UI, or complete advisors yet. Do not expose this development endpoint publicly.
