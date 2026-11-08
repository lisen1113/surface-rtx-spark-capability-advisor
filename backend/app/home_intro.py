"""Homepage introduction and primary product entry points."""
import re
from .advisor_access import public_advisor_enabled


def render(page):
    old_navigation=re.search(r'<nav class="panel">.*?</nav>',page,re.S)
    if not old_navigation:
        return page
    commercial='href="/workplace"' in old_navigation.group(0)
    entries=[('/surface','全品类 Surface SKU 查询','查找设备、配件与延保','01'),
             ('#spark-config','RTX Spark 能力顾问','了解 AI、游戏与生产力能力','02')]
    if commercial:
        entries.append(('/workplace','Surface AI Workplace租赁及订阅','组合设备租赁与 M365、Copilot 订阅','03'))
    navigation='<nav class="home-entry-grid" aria-label="产品与方案入口">'+''.join(
        f'<a class="home-entry{ " workplace-entry" if href=="/workplace" else ""}" href="{href}"><span class="entry-number" aria-hidden="true">{number}</span><span class="entry-copy"><strong>{label}</strong><small>{description}</small></span><span class="entry-arrow" aria-hidden="true">↗</span></a>'
        for href,label,description,number in entries)+'</nav>'
    intro='<div class="sub home-intro"><p>按真实料号查询 Surface 设备、配件与延保，探索 RTX Spark 的 AI、游戏、生成式 AI 与生产力能力。</p>'
    if commercial:
        intro+='<p>通过 Surface AI Workplace，按团队需求组合 <strong>设备租赁与 Microsoft 365、Copilot 订阅</strong>，比较配置、分项预算和付款计划。</p>'
    intro+='</div>'
    auxiliary='<div class="home-account-links"><a href="/guest">游客体验 · 无需登录 →</a><span aria-hidden="true">·</span><a href="/account">员工与 DMP 登录</a></div>'
    if public_advisor_enabled():
        auxiliary=auxiliary.replace('游客体验 · 无需登录 →','RTX Spark 完整顾问 · 无需注册 →')
    page=page[:old_navigation.start()]+page[old_navigation.end():]
    page=re.sub(r'<div class="sub">.*?</div>',intro,page,count=1,flags=re.S)
    page=re.sub(r'<p><a href="/guest".*?</p>',navigation+auxiliary,page,count=1,flags=re.S)
    return page.replace('<div class="bar">','<div class="bar" id="spark-config">',1)
