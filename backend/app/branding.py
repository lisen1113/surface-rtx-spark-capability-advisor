"""Shared visual presentation; does not change product behavior."""

BRAND = '''<div class="site-brand"><div class="site-brand-inner"><a href="/" aria-label="以和首页"><img class="company-mark" src="/assets/yihe-logo.png" alt="上海以和信息技术有限公司"></a><span class="brand-separator"></span><span class="surface-brand"><img src="/assets/microsoft-surface.png" alt="Microsoft Surface"></span></div></div>'''

def apply_theme(html: str) -> str:
    html = html.replace('</head>', '<link rel="stylesheet" href="/assets/theme.css?v=20261028"></head>', 1)
    return html.replace('<body>', '<body>' + BRAND, 1)
