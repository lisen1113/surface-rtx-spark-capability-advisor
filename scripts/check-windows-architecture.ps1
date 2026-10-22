param(
    [string]$PythonExe = 'python',
    [switch]$RequireNativePython
)
$ErrorActionPreference = 'Stop'

$osArchitecture = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()
$shellArchitecture = [System.Runtime.InteropServices.RuntimeInformation]::ProcessArchitecture.ToString()
$pythonCode = 'import json,platform,sys,sysconfig; print(json.dumps({"machine":platform.machine(),"platform":sysconfig.get_platform(),"version":sys.version.split()[0],"executable":sys.executable}))'
$pythonOutput = & $PythonExe -c $pythonCode
if ($LASTEXITCODE -ne 0 -or -not $pythonOutput) {
    throw "Python 检查失败：请确认 -PythonExe 指向待验收的解释器。"
}
$python = $pythonOutput | ConvertFrom-Json
$pythonArchitecture = switch -Regex ($python.machine) {
    '^(ARM64|aarch64)$' { 'Arm64'; break }
    '^(AMD64|x86_64)$' { 'X64'; break }
    default { 'Unknown' }
}

Write-Host "Windows 系统架构：$osArchitecture"
Write-Host "PowerShell 进程架构：$shellArchitecture"
Write-Host "Python 版本与架构：$($python.version) / $pythonArchitecture ($($python.platform))"
Write-Host "Python 路径：$($python.executable)"

try {
    Get-CimInstance Win32_VideoController | ForEach-Object {
        Write-Host "显卡/驱动（系统报告）：$($_.Name) / $($_.DriverVersion)"
    }
} catch {
    Write-Warning '无法读取系统报告的显卡驱动；请在设备管理器中人工记录。'
}

if ($osArchitecture -ne $pythonArchitecture) {
    Write-Warning '系统与 Python 架构不一致；这可能是仿真环境，不能作为原生架构验收。'
    if ($RequireNativePython) { exit 2 }
} else {
    Write-Host '系统与 Python 架构一致；仍需逐项验证依赖、GPU 后端和实际工作负载。'
}
