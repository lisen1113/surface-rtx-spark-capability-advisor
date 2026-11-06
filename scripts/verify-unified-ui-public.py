"""External read-only checks for the unified UI release."""
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path
import httpx

ROOT = Path(__file__).resolve().parents[1]
checks = {}
with httpx.Client(timeout=25, follow_redirects=True) as client:
    def get(path):
        for attempt in range(4):
            try:
                return client.get('https://surfacedmp.com' + path)
            except httpx.TransportError:
                if attempt == 3:
                    raise
                time.sleep(1)
    for path in ('/surface', '/', '/account?next=%2Fsurface', '/guest', '/deployment'):
        response = get(path)
        assert response.status_code == 200, (path, response.status_code)
        assert 'href="/assets/theme.css?v=20261028"' in response.text, path
        assert 'class="site-brand"' in response.text and '/assets/microsoft-surface.png' in response.text
        for script in re.findall(r'<script>(.*?)</script>', response.text, re.S):
            subprocess.run(['node', '--check'], input=script, text=True, encoding='utf-8', check=True)
        checks[path] = 'shared theme / brand / script passed'
    for name in ('theme.css', 'microsoft-surface.png'):
        response = get('/assets/' + name)
        assert response.status_code == 200
        expected = (ROOT / 'backend/app/assets' / name).read_bytes()
        assert hashlib.sha256(response.content).digest() == hashlib.sha256(expected).digest(), name
        checks[name] = 'deployed asset hash matched'
    for path in ('/api/catalog/quick-search', '/api/catalog/quick-search/EP2-77145/pdf'):
        assert get(path).status_code == 401, path
        checks[path] = 'authentication enforced'
    health = get('/health')
    assert health.status_code == 200 and health.json()['database'] == 'ready'
    checks['health'] = health.json()
print(json.dumps({'status':'passed','checks':checks}, ensure_ascii=False, indent=2))
