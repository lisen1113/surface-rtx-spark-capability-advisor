"""Prepare local public preview, preserving existing identities and source stores."""
import json
import os
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / '.commercial-local'


def insert(conn, table, values):
    columns = list(values)
    return conn.execute(f'INSERT INTO {table} ({",".join(columns)}) VALUES ({",".join("?" for _ in columns)})', list(values.values())).lastrowid


def prepare():
    identity = LOCAL / 'identity.sqlite3'
    if not identity.exists():
        staging = LOCAL / 'identity-preparing.sqlite3'
        with sqlite3.connect((ROOT / 'data/capability.sqlite3').as_uri()+'?mode=ro', uri=True) as source, sqlite3.connect(staging) as target:
            source.backup(target)
        # Keep recent preview registrations too, without changing passwords or status.
        with sqlite3.connect((LOCAL/'catalog.sqlite3').as_uri()+'?mode=ro', uri=True) as source, sqlite3.connect(staging) as target:
            source.row_factory = target.row_factory = sqlite3.Row
            organizations = {}
            for row in source.execute('SELECT * FROM users'):
                user = dict(row)
                if target.execute('SELECT 1 FROM users WHERE email=?', (user['email'],)).fetchone():
                    continue
                if source.execute('SELECT 1 FROM admin_mfa WHERE user_id=?', (user['id'],)).fetchone():
                    # MFA secrets are derived from the original user id. Never
                    # drop MFA or remap the id and pretend its old code still works.
                    raise RuntimeError('A preview-only MFA administrator needs an explicit identity migration; original accounts were not modified')
                org = user['organization_id']
                if org is not None and org not in organizations:
                    values = dict(source.execute('SELECT * FROM organizations WHERE id=?', (org,)).fetchone())
                    values.pop('id')
                    organizations[org] = insert(target, 'organizations', values)
                    license_row = source.execute('SELECT * FROM licenses WHERE organization_id=?', (org,)).fetchone()
                    if license_row:
                        license_data = dict(license_row)
                        license_data['organization_id'] = organizations[org]
                        insert(target, 'licenses', license_data)
                user.pop('id')
                user['organization_id'] = organizations.get(org)
                insert(target, 'users', user)
        staging.replace(identity)
    commercial = LOCAL/'commercial-public.sqlite3'
    os.environ['CAPABILITY_COMMERCIAL_PATH'] = str(commercial)
    os.environ['CAPABILITY_CATALOG_PATH'] = str(LOCAL/'catalog.sqlite3')
    os.environ['CAPABILITY_DEPLOYMENT_MODE'] = 'local'
    sys.path.insert(0, str(ROOT/'backend'))
    from app.commercial import store, settings, engine
    from app.commercial.models import SettingsInput
    with store.connection() as target:
        if not target.execute('SELECT 1 FROM cloud_prices LIMIT 1').fetchone():
            with sqlite3.connect((LOCAL/'commercial.sqlite3').as_uri()+'?mode=ro', uri=True) as source:
                source.row_factory = sqlite3.Row
                for table in ('cloud_prices', 'commercial_imports', 'lease_policies'):
                    for row in source.execute('SELECT * FROM '+table):
                        insert(target, table, dict(row))
        if not settings.current(target):
            policy = target.execute('SELECT id FROM lease_policies ORDER BY created_at DESC LIMIT 1').fetchone()
            settings.save(target, SettingsInput(usd_cny='7.2', fx_date=engine.today(), fx_reference='本地预览示例汇率，正式报价前核验', cloud_tax_rate='0',software_cost_factor='0.85',active_policy_id=policy[0] if policy else None), {'id':0,'role':'admin','organization_id':None})
    with sqlite3.connect(identity) as conn:
        print(json.dumps({'identity_database':str(identity),'users':conn.execute('SELECT COUNT(*) FROM users').fetchone()[0], 'commercial_database':str(commercial),'source_databases_unchanged':True}))


if __name__ == '__main__':
    prepare()
