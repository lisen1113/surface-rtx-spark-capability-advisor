param(
    [ValidateRange(1,65535)][int]$Port = 8000,
    [switch]$NoBrowser,
    [switch]$SkipInstall
)
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Backend = Join-Path $Root 'backend'
$LogDir = Join-Path $Root 'logs'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogFile = Join-Path $LogDir 'startup.log'
function Log([string]$Message) {
    $line = ('[{0}] {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message)
    Write-Host $line
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
}
function Fail([string]$Message) {
    Log ('ERROR: ' + $Message)
    Write-Host ('Log: ' + $LogFile) -ForegroundColor Yellow
    exit 1
}
Set-Location $Backend
Log ('Starting Capability Advisor on http://127.0.0.1:' + $Port)
$existing = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($existing) { Fail ("Port $Port is already occupied. Try -Port 8001, or stop the existing process.") }

$Python = Join-Path $Backend '.venv\Scripts\python.exe'
if (-not (Test-Path $Python)) {
    $launcher = Get-Command py -ErrorAction SilentlyContinue
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($launcher) {
        Log 'Creating Python virtual environment using py -3...'
        & py -3 -m venv .venv 2>&1 | ForEach-Object { Log "$_" }
    } elseif ($pythonCommand) {
        Log 'Creating Python virtual environment using python...'
        & python -m venv .venv 2>&1 | ForEach-Object { Log "$_" }
    } else {
        Fail 'Python not found. Install Python 3.11+ from python.org, enable PATH, and reopen PowerShell.'
    }
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $Python)) {
        Fail 'Virtual environment creation failed. Check Python installation and Windows ARM64/x64 compatibility.'
    }
}
& $Python --version 2>&1 | ForEach-Object { Log "$_" }
if ($LASTEXITCODE -ne 0) { Fail 'Virtual environment Python is broken. Delete backend/.venv and retry.' }

if (-not $SkipInstall) {
    Log 'Installing backend dependencies...'
    & $Python -m pip install -r requirements.txt 2>&1 | ForEach-Object { Log "$_" }
    if ($LASTEXITCODE -ne 0) { Fail 'Dependency installation failed. Check logs/startup.log for pip errors.' }
}
Log 'Checking FastAPI imports...'
& $Python -c 'from app.main import app; print("Backend imports OK")' 2>&1 | ForEach-Object { Log "$_" }
if ($LASTEXITCODE -ne 0) { Fail 'Backend import failed. Check logs/startup.log.' }

$BaseUrl = 'http://127.0.0.1:' + $Port
Log ('Browser address: ' + $BaseUrl + '/')
Log 'Keep this PowerShell window open while using the app. Ctrl+C stops it.'
if (-not $NoBrowser) {
    # Open after server starts; opening early can cause ERR_CONNECTION_REFUSED.
    $job = Start-Job -ScriptBlock {
        param($url)
        for ($i=0; $i -lt 50; $i++) {
            Start-Sleep -Milliseconds 300
            try {
                $r = Invoke-WebRequest -Uri ($url + '/health') -UseBasicParsing -TimeoutSec 2
                if ($r.StatusCode -eq 200) { Start-Process $url; return }
            } catch {}
        }
    } -ArgumentList $BaseUrl
}
try {
    & $Python -m uvicorn app.main:app --host 127.0.0.1 --port $Port
    if ($LASTEXITCODE -ne 0) { Fail ('Uvicorn exited with code ' + $LASTEXITCODE) }
} finally {
    if ($job) { Remove-Job $job -Force -ErrorAction SilentlyContinue }
}
