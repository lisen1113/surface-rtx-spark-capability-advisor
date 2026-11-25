"""Verify the deployed Surface catalog using the server runtime and its read-only catalog."""
import json
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, '/opt/capability-advisor/backend')
from app.catalog import quick_search, quick_search_detail
from app.surface_pdf import build_surface_pdf
from app.ui import surface_index, index
from fastapi import Response

def search(**kwargs):
    parameters = dict(q='', product_type=None, series=None, memory_gb=None,
                      max_erp_price_cny=None, limit=300, offset=0, include_excluded=False,
                      processor=None, storage_capacity=None, screen_size=None, network=None)
    parameters.update(kwargs)
    return quick_search(**parameters)

db = Path('/opt/capability-advisor/data/capability.sqlite3')
with sqlite3.connect(db.as_uri() + '?mode=ro', uri=True) as conn:
    assert conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    assert conn.execute('SELECT COUNT(*) FROM sku_lookup').fetchone()[0] == 237
    legacy = conn.execute('SELECT COUNT(*) FROM imported_skus').fetchone()[0]
assert search()['total'] == 226
assert search(processor='Intel')['total'] == 80
assert search(processor='Snapdragon')['total'] == 111
assert search(product_type='配件', q='NO_MATCH', processor='Intel', memory_gb=128,
              storage_capacity='1TB', screen_size='12', network='5g')['total'] == 17
assert search(product_type='延保', q='NO_MATCH', network='5g')['total'] == 18
for size in ('12', '13', '13.8', '15'):
    result = search(screen_size=size)
    assert result['total'] > 0
    assert all(item['display'].startswith(size + ' 英寸') for item in result['items'])
for network in ('wifi', '5g'):
    assert search(network=network)['total'] > 0
item = quick_search_detail('EP2-31034')['item']
assert item['erp_price_cny'] == 1458
assert item['service_details']['中文服务名称'] == '商业 Microsoft Complete'
pdf = build_surface_pdf(quick_search_detail('EP2-77145')['item'])
assert pdf.startswith(b'%PDF-') and len(pdf) > 1000
surface = surface_index(Response())
home = index(Response())
assert 'id="quick-network"' in surface and 'id="quick-screen"' in surface
assert 'id="needform"' not in surface and 'id="quick-lookup"' not in home
assert 'href="/surface"' in home
print(json.dumps({'status': 'passed', 'searchable': 226, 'intel': 80, 'snapdragon': 111,
                  'accessories': 17, 'warranties': 18, 'legacy_skus': legacy,
                  'screen_and_network_filters': 'passed', 'pdf_bytes': len(pdf)}, indent=2))
