"""Serve a local-only visual proposal with read-only catalog samples."""
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
os.environ['CAPABILITY_CATALOG_PATH'] = str(ROOT / 'data/sku-preview.sqlite3')
os.environ['CAPABILITY_DEPLOYMENT_MODE'] = 'public'
from app.catalog import connection, _lookup_item

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/logo.png':
            content = (ROOT / 'miniprogram/assets/yihe-logo.png').read_bytes()
            kind = 'image/png'
        elif path == '/surface-logo.png':
            content = (ROOT / 'miniprogram/assets/microsoft-surface.png').read_bytes()
            kind = 'image/png'
        elif path == '/products.json':
            with connection() as conn:
                records = conn.execute("SELECT * FROM sku_lookup WHERE match_level NOT LIKE 'N/A%' ORDER BY CASE WHEN mapping_rule_id='LTP13_SD_2' THEN 0 ELSE 1 END, part_number").fetchall()
            content = json.dumps([_lookup_item(row) for row in records], ensure_ascii=False).encode()
            kind = 'application/json; charset=utf-8'
        elif path == '/':
            content = (ROOT / 'artifacts/design-preview.html').read_bytes()
            kind = 'text/html; charset=utf-8'
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', kind)
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(content)

print('Design preview: http://127.0.0.1:8013/', flush=True)
HTTPServer(('127.0.0.1', 8013), Handler).serve_forever()
