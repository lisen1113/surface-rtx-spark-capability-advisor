"""Read-only external smoke checks for the deployed Surface channel."""
import json
import re
import subprocess
import time
import httpx

checks = {}
with httpx.Client(timeout=25, follow_redirects=True) as client:
    for path, expected in [('/health', 200), ('/surface', 200), ('/', 200),
                           ('/api/catalog/quick-search', 401),
                           ('/api/catalog/quick-search/EP2-77145/pdf', 401)]:
        for attempt in range(4):
            try:
                response = client.get('https://surfacedmp.com' + path)
                break
            except httpx.TransportError:
                if attempt == 3:
                    raise
                time.sleep(1)
        assert response.status_code == expected, (path, response.status_code)
        checks[path] = response.status_code
        if path == '/surface':
            html = response.text
            for field in ('quick-network', 'quick-screen', 'quick-storage', 'quick-platform'):
                assert 'id="' + field + '"' in html
            assert 'id="needform"' not in html
            script = re.search(r'<script>(.*?)</script>', html, re.S).group(1)
            subprocess.run(['node', '--check'], input=script, text=True, encoding='utf-8', check=True)
        if path == '/':
            assert 'href="/surface"' in response.text
            assert 'id="quick-lookup"' not in response.text
print(json.dumps({'status': 'passed', 'https_checks': checks}, indent=2))
