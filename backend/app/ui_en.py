"""English presentation for the public, read-only Surface SKU finder.

Source workbook fields and product names remain unchanged so Part Numbers,
prices, and provenance are never translated into new product claims.
"""

import json
import re

LABELS = {
    '全品类 Surface SKU 快速查询': 'Surface SKU Quick Finder',
    '全品类 Surface SKU 查询': 'Surface SKU Finder',
    'RTX Spark 能力顾问': 'RTX Spark Capability Advisor',
    'Surface AI Workplace租赁及订阅': 'Surface AI Workplace Leasing and Subscriptions',
    '可输入完整或部分 Part Number、产品名称、CPU、配置、颜色或联网方式。默认查询 Surface 设备、配件和延保，不展示暂未纳入的 NVIDIA 记录。': 'Search by full or partial Part Number, product name, CPU, configuration, color, or connectivity. Results include Surface devices, accessories, and warranties. NVIDIA records are outside this finder.',
    '关键词／Part Number': 'Keyword / Part Number',
    '例如 EP2-77145、Surface Pro、Ultra 5、16GB': 'e.g. EP2-77145, Surface Pro, Ultra 5, 16GB',
    '处理器大类': 'Processor family',
    '全部处理器': 'All processors',
    '英特尔 Intel': 'Intel',
    '高通 Snapdragon': 'Snapdragon',
    '联网版本': 'Connectivity',
    '全部版本': 'All versions',
    '屏幕大小': 'Screen size',
    '全部尺寸': 'All sizes',
    '英寸': 'inch',
    '大系列': 'Product family',
    '全部系列': 'All families',
    '全部类别': 'All categories',
    '全部内存': 'All memory sizes',
    '全部存储': 'All storage sizes',
    'ERP 价格上限': 'Maximum ERP price (CNY)',
    '例如 15000': 'e.g. 15000',
    '类别': 'Category',
    '内存': 'Memory',
    '存储': 'Storage',
    '报价系数': 'Quote factor',
    '90% 表示九折': '90% means a 10% discount',
    '立即查询': 'Search',
    '清空条件': 'Clear filters',
    '正在读取 V3.1 查询索引…': 'Loading V3.1 search index…',
    '正在查询 V3.1 映射数据库…': 'Searching V3.1 catalog…',
    '查询索引不可用': 'Search index unavailable',
    '查询失败': 'Search failed',
    '读取详情失败': 'Could not load details',
    '已载入 ': 'Loaded ',
    ' 条可查询记录。': ' searchable records.',
    '找到 ': 'Found ',
    ' 条；当前显示 ': ' results; showing ',
    ' 条。价格以原表 ERP 含税价为准。': '. Prices are the source workbook ERP prices including tax.',
    '价格以原表 ERP 含税价为准。': 'Prices are the source workbook ERP prices including tax.',
    '没有符合当前条件的记录。请减少筛选条件或核对 Part Number。': 'No matching records. Try fewer filters or check the Part Number.',
    '尚未导入 V3.1 查询数据库，请先运行授权工作簿导入。': 'The V3.1 catalog has not been imported.',
    '配置详情见完整映射': 'See full record for configuration details',
    '价格待确认': 'Price unavailable',
    '待复核': 'Pending review',
    '查看完整映射': 'View details',
    '下载 PDF 产品资料': 'Download product PDF',
    '复制 Part Number': 'Copy Part Number',
    '完整映射 · ': 'Full record · ',
    '产品类别': 'Product category',
    '产品名称': 'Product name',
    '原始系列': 'Source family',
    '原始描述／配置': 'Source description / configuration',
    '平台': 'Platform',
    'CPU 官方名称': 'Official CPU name',
    '颜色': 'Color',
    '联网': 'Connectivity',
    '电源': 'Power supply',
    '屏幕': 'Display',
    '分辨率／刷新率': 'Resolution / refresh rate',
    '重量': 'Weight',
    '电池': 'Battery',
    '操作系统': 'Operating system',
    'ERP 含税价': 'ERP price incl. tax',
    '匹配级别': 'Match level',
    '复核状态': 'Review status',
    '未知字段': 'Unknown fields',
    '异常／复核说明': 'Review notes',
    '打开微软中国官方来源': 'Open official Microsoft China source',
    '此记录没有逐料号官方页面；映射依据与限制已保留在数据库中。': 'No official page is linked to this exact Part Number. Mapping evidence and limitations are retained in the catalog.',
    '关闭详情': 'Close details',
    '已复制 Part Number：': 'Copied Part Number: ',
    '无法自动复制，请手动选择 Part Number': 'Automatic copy failed. Select and copy the Part Number manually.',
    '请通过小程序重新打开查询页': 'Reopen the finder from the mini program.',
    '请从小程序进入查询后下载 PDF': 'Open this finder from the mini program to download the PDF.',
    '下载授权失败，请重新登录': 'PDF authorization failed. Please sign in again.',
    '请更新小程序版本后重试': 'Update the mini program and try again.',
    'PDF 下载失败，请检查登录授权': 'PDF download failed. Check your account access.',
    '© 2026 上海以和信息技术有限公司。保留所有权利。': '© 2026 Shanghai Yihe Information Technology Co., Ltd. All rights reserved.',
}


def translate_surface(page: str) -> str:
    page = page.replace('<html lang="zh-CN">', '<html lang="en">', 1)
    for source, target in sorted(LABELS.items(), key=lambda pair: len(pair[0]), reverse=True):
        page = page.replace(source, target)
    page = page.replace('href="/surface" aria-current="page"', 'href="/surface"', 1)
    page = page.replace('href="/en/surface" style=', 'href="/en/surface" aria-current="page" style=', 1)
    page = page.replace('href="/"', 'href="/en"')
    page = page.replace('href="/workplace"', 'href="/en/workplace"')
    return page


ADVISOR_LABELS = {
    'Surface AI Workplace及RTX Spark能力与选型顾问': 'Surface AI Workplace and RTX Spark Capability Advisor',
    'V3.1 产品与能力顾问': 'V3.1 Product and Capability Advisor',
    '按真实料号查询 Surface 设备、配件与延保，探索 RTX Spark 的 AI、游戏、生成式 AI 与生产力能力。': 'Find Surface devices, accessories, and warranties by actual Part Number, then explore RTX Spark capabilities for AI, gaming, generative AI, and productivity.',
    '通过 Surface AI Workplace，按团队需求组合': 'Use Surface AI Workplace to combine',
    '设备租赁与 Microsoft 365、Copilot 订阅': 'device leasing with Microsoft 365 and Copilot subscriptions',
    '，比较配置、分项预算和付款计划。': ', then compare configurations, itemized budgets, and payment schedules.',
    '查找设备、配件与延保': 'Find devices, accessories, and warranties',
    '了解 AI、游戏与生产力能力': 'Explore AI, gaming, and productivity capabilities',
    '组合设备租赁与 M365、Copilot 订阅': 'Combine device leasing with Microsoft 365 and Copilot',
    '游客体验 · 无需登录 →': 'Try as a guest · no sign-in →',
    'RTX Spark 完整顾问 · 无需注册 →': 'Full RTX Spark advisor · no registration →',
    '员工与 DMP 登录': 'Employee and DMP sign-in',
    'RTX Spark 能力配置': 'RTX Spark configuration',
    '正在载入 V3.4 数据…': 'Loading V3.4 data…',
    '按使用需求推荐 RTX Spark 配置': 'Find an RTX Spark configuration for your needs',
    '先选用途，也可以用自己的话描述。系统会合并已识别的需求，给出可比较的 Surface Laptop Ultra 候选；具体软件、游戏和模型仍需验证。': 'Select your intended uses or describe them in your own words. The advisor combines the identified needs and shows comparable Surface Laptop Ultra candidates. Specific software, games, and models still require verification.',
    '主要用途（可多选）': 'Primary uses (select any)',
    '本地 AI 模型': 'Local AI models',
    '图像/视频生成': 'Image / video generation',
    '模型名称（可选）': 'Model name (optional)',
    '模型规模': 'Model size',
    '尚不确定': 'Not sure yet',
    '具体游戏（可多款）': 'Game titles (multiple allowed)',
    '游戏类型': 'Game type',
    '电竞/网游': 'Esports / online games',
    '3A 大型游戏': 'AAA games',
    '目标分辨率': 'Target resolution',
    '目标 FPS': 'Target FPS',
    '软件名称与版本（可选）': 'Software name and version (optional)',
    '生产力工作负载': 'Productivity workload',
    '日常办公': 'Everyday office work',
    '编程开发': 'Software development',
    '视频剪辑': 'Video editing',
    '预算上限（元，可留空）': 'Maximum budget (CNY, optional)',
    '自由描述': 'Describe your needs',
    '查找合适配置': 'Find matching configurations',
    'RTX Spark 产品概览': 'RTX Spark product overview',
    '预览客户能力报告': 'Preview capability report',
    '下载 PDF 报告': 'Download PDF report',
    'AI 模型': 'AI models',
    '游戏': 'Gaming',
    '生成式 AI': 'Generative AI',
    '生产力': 'Productivity',
    '模型部署': 'Model deployment',
    'TCO 成本': 'Total cost of ownership',
    '证据与限制': 'Evidence and limitations',
    '数据说明': 'About the data',
    '快速查询读取经审阅的 Surface SKU V3.1 映射索引；RTX Spark 能力模块继续读取授权 V3.4 工作簿。ERP 含税价以用户提供的原始表格为准。空白 Token/s、FPS 或实测字段保持未知；经验推荐不会显示为官方测试。': 'The quick finder uses the reviewed Surface SKU V3.1 index. RTX Spark capabilities use the authorized V3.4 workbook. ERP prices including tax come from the supplied source workbook. Missing Token/s, FPS, and measured values remain unknown. Engineering recommendations are never presented as official tests.',
    '账号注册与登录': 'Register or sign in',
    '管理员控制台': 'Admin console',
    'API 文档': 'API documentation',
    '快速查询数据': 'Quick finder data',
    '来源台账': 'Source register',
    'Microsoft、Surface、NVIDIA、RTX 等商标归各自权利人所有。本站供员工与内部代理商培训使用。': 'Microsoft, Surface, NVIDIA, RTX, and other trademarks belong to their respective owners. This site is for employee and authorized partner training.',
    '例如 Qwen3': 'e.g. Qwen3',
    '例如 CS2、赛博朋克 2077': 'e.g. CS2, Cyberpunk 2077',
    '例如 Premiere Pro': 'e.g. Premiere Pro',
    '例如 40000': 'e.g. 40000',
    '例如：要玩 3A 游戏，也希望本地运行 70B 模型，用于编程和客户演示': 'e.g. I want to play AAA games and run a 70B model locally for coding and client demos',
    '例如 60': 'e.g. 60',
    '未知': 'Unknown',
    '关闭预览，返回能力顾问': 'Close preview and return to the advisor',
    '请先在账号页登录': 'Please sign in on the account page',
    '请确认组织 License 有效': 'Please check that your organization license is active',
    '报告生成失败': 'Report generation failed',
    '正在生成 PDF…': 'Generating PDF…',
    '微信内请通过小程序打开后再预览 PDF': 'In WeChat, open the mini program to preview the PDF',
    '无法创建 PDF 预览授权，请重新登录后重试': 'Could not authorize PDF preview. Sign in and try again.',
    '无法打开小程序 PDF 预览，请检查版本及下载域名配置': 'Could not open the mini program PDF preview. Check the version and download domain.',
    '正在打开小程序 PDF 预览；请在预览页确认保存': 'Opening the mini program PDF preview. Save it from the preview page.',
    'PDF 生成失败': 'PDF generation failed',
    '正在匹配已导入产品…': 'Matching imported products…',
    '推荐请求失败': 'Recommendation request failed',
    '需求档案': 'Needs profile',
    '待确认：': 'Needs confirmation: ',
    '超出预算': 'Over budget',
    '查看此配置的详细能力并生成报告': 'View capabilities and generate report',
    '当前导入产品中没有匹配候选。': 'No matching candidates in the imported catalog.',
    '生成工作流': 'Generation workflow',
    '图像生成': 'Image generation',
    '视频生成': 'Video generation',
    '推荐排序': 'Ranking preference',
    '优先控制采购价': 'Prioritize purchase cost',
    '优先更大内存': 'Prioritize more memory',
    '正在生成此配置与本次需求的完整报告…': 'Generating a report for this configuration and your needs…',
    '此配置与本次需求的匹配报告': 'Configuration match report',
    '下载 SKU 能力 PDF': 'Download SKU capability PDF',
    '该 SKU 暂无已验证的直接映射；请查看经验推荐与证据限制。': 'This SKU has no verified direct mapping. Review the engineering recommendations and evidence limitations.',
    '目标模型/场景': 'Target model / scenario',
    '游戏名称': 'Game title',
    '推荐模型/工作负载名称': 'Recommended model / workload',
    '软件/工作负载': 'Software / workload',
    '推荐定位': 'Recommendation role',
    '推荐游戏类型': 'Recommended game type',
    '能力记录': 'Capability record',
    '证据等级': 'Evidence level',
    '证据类型': 'Evidence type',
    '数据类型（官方/实测/估算）': 'Data type (official / measured / estimate)',
    '本地运行判断': 'Local runtime assessment',
    '兼容性状态': 'Compatibility status',
    '经验推荐与我的判断': 'Engineering recommendation and assessment',
    '实测结果': 'Measured result',
}


def translate_advisor(page: str) -> str:
    """Translate the public home shell without changing API keys or input values."""
    labels = {**LABELS, **ADVISOR_LABELS}
    page = page.replace('<html lang="zh-CN">', '<html lang="en">', 1)
    # Keep script bodies intact: Chinese keywords in request parsing are logic,
    # not display text. Text added by scripts is handled by the browser observer.
    parts = re.split(r'(<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>)', page, flags=re.S | re.I)
    for position in range(0, len(parts), 2):
        for source, target in sorted(labels.items(), key=lambda pair: len(pair[0]), reverse=True):
            parts[position] = parts[position].replace(source, target)
    page = ''.join(parts)
    page = page.replace('href="/" aria-current="page"', 'href="/"', 1)
    page = page.replace('href="/en" style="color:#fff"',
                        'href="/en" aria-current="page" style="color:#fff"', 1)
    # Change public navigation to the corresponding English route. Protected
    # account and admin routes retain their existing URLs and authorization.
    page = page.replace('href="/surface"', 'href="/en/surface"')
    page = page.replace('href="/workplace"', 'href="/en/workplace"')
    page = page.replace('href="/account"', 'href="/en/account"')
    page = page.replace('href="/admin"', 'href="/en/admin"')
    page = page.replace('href="/guest"', 'href="/en"')
    page = page.replace('href="/deployment?', 'href="/en/deployment?')
    runtime = r'''<script>(function(){
const labels=__LABELS__;
function translate(root){const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);const nodes=[];while(walker.nextNode())nodes.push(walker.currentNode);for(const node of nodes){if(node.parentElement?.closest('script,style'))continue;const raw=node.nodeValue,trimmed=raw.trim();if(labels[trimmed])node.nodeValue=raw.replace(trimmed,labels[trimmed]);}}
const observer=new MutationObserver(records=>{for(const record of records)for(const node of record.addedNodes){if(node.nodeType===1)translate(node);else if(node.nodeType===3&&labels[node.nodeValue.trim()])node.nodeValue=node.nodeValue.replace(node.nodeValue.trim(),labels[node.nodeValue.trim()]);}});
translate(document.body);observer.observe(document.body,{childList:true,subtree:true});
})();</script>'''.replace('__LABELS__', json.dumps(labels, ensure_ascii=False))
    return page.replace('</body>', runtime + '</body>', 1)
