"""English presentation for the legacy anonymous advisor page."""

import json
import re

from .ui_en import ADVISOR_LABELS

LABELS = {
    **ADVISOR_LABELS,
    '游客体验｜Surface 能力顾问': 'Guest access | Surface Capability Advisor',
    '游客体验': 'Guest access',
    '无需登录即可查看产品配置、工程候选与 AI、游戏、生成式 AI、生产力能力映射。价格、内部知识库、客户报告和管理功能仅向获授权账号开放。': 'Browse configurations, engineering candidates, and AI, gaming, generative AI, and productivity capability mappings without signing in. Prices, internal knowledge, customer reports, and administration require an authorized account.',
    '登录授权版': 'Sign in for authorized access',
    '选择产品配置': 'Select a product configuration',
    '正在载入…': 'Loading…',
    '按使用需求推荐产品': 'Find products for your needs',
    '游客可使用与授权版相同的用途筛选；价格、预算排序和客户报告仍需授权。候选只按配置与工程假设筛选，不保证软件兼容或性能。': 'Guests can use the same needs filters as authorized users. Pricing, budget ranking, and customer reports require authorization. Candidates are screened by configuration and engineering assumptions; compatibility and performance are not guaranteed.',
    '具体游戏（可选）': 'Game title (optional)',
    '例如 CS2': 'e.g. CS2',
    '电竞 / 网游': 'Esports / online games',
    '期望 FPS（仅作为需求，不是实测）': 'Target FPS (a requirement, not a measurement)',
    '生成式 AI 工作流': 'Generative AI workflow',
    '描述您的用途（可选）': 'Describe your use (optional)',
    '例如：本地运行 32B 模型并用于编程；请勿输入客户机密': 'e.g. run a 32B model locally for coding; do not include customer secrets',
    '查看工程候选': 'View engineering candidates',
    '能力映射': 'Capability mapping',
    '证据边界：官方平台声明不是本料号实测；内存容量估算不是兼容性、FPS、Token/s 或完成时间承诺。请在目标设备上验证。': 'Evidence boundary: official platform claims are not measurements of this Part Number. Memory estimates do not promise compatibility, FPS, Token/s, or completion time. Verify on the target device.',
    '© 2026 上海以和信息技术有限公司 ·': '© 2026 Shanghai Yihe Information Technology Co., Ltd. ·',
    '产品': 'Product',
    '处理器平台': 'Processor platform',
    '统一内存': 'Unified memory',
    '系统': 'Operating system',
    '能力说明': 'Capability information',
    '查看官方来源': 'View official source',
    '正在载入能力映射…': 'Loading capability mapping…',
    '读取配置失败': 'Could not load configuration',
    '产品列表读取失败': 'Could not load product list',
    '暂无可公开展示的产品配置': 'No public configurations are available yet',
    '正在筛选…': 'Screening candidates…',
    '请求过于频繁，请稍后重试': 'Too many requests. Try again later.',
    '推荐请求失败': 'Recommendation request failed',
}


def translate_guest(page: str) -> str:
    page = page.replace('<html lang="zh-CN">', '<html lang="en">', 1)
    parts = re.split(r'(<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>)', page, flags=re.S | re.I)
    for position in range(0, len(parts), 2):
        for source, target in sorted(LABELS.items(), key=lambda item: len(item[0]), reverse=True):
            parts[position] = parts[position].replace(source, target)
    page = ''.join(parts)
    page = page.replace('</header>', '<nav aria-label="Language"><a lang="zh-CN" href="/guest">中文</a> | <a lang="en" href="/en/guest" aria-current="page">English</a></nav></header>', 1)
    page = page.replace('href="/account"', 'href="/en/account"')
    page = page.replace('href="/"', 'href="/en"')
    runtime = '''<script>(function(){const labels=__LABELS__;function update(node){if(node.nodeType===3){const raw=node.nodeValue,trimmed=raw.trim();if(labels[trimmed])node.nodeValue=raw.replace(trimmed,labels[trimmed]);return}if(node.nodeType!==1||node.closest('script,style'))return;const walker=document.createTreeWalker(node,NodeFilter.SHOW_TEXT);while(walker.nextNode())update(walker.currentNode)}const observer=new MutationObserver(records=>{for(const record of records)for(const node of record.addedNodes)update(node)});observer.observe(document.body,{childList:true,subtree:true});})();</script>'''.replace('__LABELS__', json.dumps(LABELS, ensure_ascii=False))
    return page.replace('</body>', runtime + '</body>', 1)
