param([int]$Port = 8000)
$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location (Join-Path $Root "backend")
if (-not (Test-Path ".venv")) {
    py -3 -m venv .venv
}
$Python = Join-Path (Get-Location) ".venv\Scripts\python.exe"
& $Python -m pip install -r requirements.txt
Write-Host "Local backend API: http://127.0.0.1:$Port/docs"
& $Python -m uvicorn app.main:app --host 127.0.0.1 --port $Port --reload
