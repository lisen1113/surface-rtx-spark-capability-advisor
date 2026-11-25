param(
    [ValidateRange(1,65535)][int]$Port = 8010,
    [string]$Token = ''
)
$ErrorActionPreference = 'Stop'
$BaseUrl = 'http://127.0.0.1:' + $Port
$Headers = @{}
if ($Token) { $Headers.Authorization = 'Bearer ' + $Token }

function Check([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw ('验收失败：' + $Message) }
    Write-Host ('通过：' + $Message)
}
function Get-Json([string]$Path) {
    return Invoke-RestMethod -Uri ($BaseUrl + $Path) -Headers $Headers -TimeoutSec 15
}
function Post-Json([string]$Path, [hashtable]$Body) {
    $json = $Body | ConvertTo-Json -Depth 8 -Compress
    return Invoke-WebRequest -Uri ($BaseUrl + $Path) -Method Post -Headers $Headers `
        -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($json)) `
        -UseBasicParsing -TimeoutSec 20
}

try {
    $health = Get-Json '/health'
    Check ($health.status -eq 'ok' -and $health.database -eq 'ready') '服务与本地数据库可用'
    $homePage = Invoke-WebRequest -Uri ($BaseUrl + '/') -UseBasicParsing -TimeoutSec 15
    Check ($homePage.StatusCode -eq 200 -and $homePage.Content.Contains('按使用需求推荐产品')) '中文首页可访问'
    $catalog = Get-Json '/api/catalog/imported-skus'
    $items = @($catalog.items)
    Check ($items.Count -ge 1) '存在已导入的产品 SKU'
    Check ((@($items | Select-Object -ExpandProperty part_number -Unique)).Count -eq $items.Count) 'SKU 料号没有重复'
    $sku = $items[0].part_number
    $advisor = Get-Json ('/api/catalog/advisor/' + [uri]::EscapeDataString($sku))
    Check ($advisor.sku.part_number -eq $sku) '产品配置及能力映射可读取'
    $faq = Get-Json '/api/faq?limit=1'
    Check ($faq.indexed_total -ge 200 -and @($faq.items).Count -eq 1) 'AI FAQ 至少 200 条且可检索'
    $deployment = Get-Json ('/api/deployment/sku/' + [uri]::EscapeDataString($sku))
    Check ($deployment.part_number -eq $sku -and @($deployment.trials).Count -ge 1) '按 SKU 生成模型部署试验路线'
    $tco = Get-Json ('/api/tco/defaults/' + [uri]::EscapeDataString($sku))
    Check ($tco.part_number -eq $sku -and $null -ne $tco.values) '按 SKU 读取可编辑 TCO 初始值'
    $need = @{ usages = @('productivity'); work_need = 'office'; description = '办公与客户演示' }
    $recommendation = Post-Json '/api/recommendations' $need
    $result = $recommendation.Content | ConvertFrom-Json
    Check ($result.status -eq 'shortlist' -and @($result.items).Count -ge 1) '选项加自由描述可推荐候选产品'
    $partNumber = $result.items[0].part_number
    $need.part_number = $partNumber
    $report = Post-Json '/api/reports/recommendation' $need
    $reportTitle = '<title>按描述需求配置报告-' + $partNumber + '</title>'
    Check ($report.Content.Contains($reportTitle) -and $report.Content.Contains('© 2026 上海以和信息技术有限公司。保留所有权利。')) '报告与 SKU、版权声明一致'
    Write-Host ('自动验收通过。抽查 SKU：' + $sku + '；推荐报告 SKU：' + $partNumber)
    Write-Host '仍须人工确认：浏览器打印 PDF 文件名、实际软件/GPU/模型 PoC、正式邮件/MFA 与 Windows ARM64。'
} catch {
    Write-Error ('验收未通过：' + $_.Exception.Message + '。若已开启登录保护，请在账号页登录并以 -Token 参数传入有效会话令牌。')
    exit 1
}
