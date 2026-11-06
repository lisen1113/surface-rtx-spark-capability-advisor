import json
from decimal import Decimal
import sqlite3

from test_commercial import workspace, inputs
from app import catalog
from app.auth import hasher
from app.commercial import engine, store


def configuration(**changes):
    return dict(usd_cny='7',fx_date=str(engine.today()),fx_reference='Published test rate',cloud_tax_rate='0',software_cost_factor='0.85',active_policy_id='LP-TEST',**changes)


def publish(client,auth,data=None):
    r=client.put('/api/commercial/admin/settings',headers=auth['admin'],json=data or configuration())
    assert r.status_code==200,r.text


def selection():
    return {'term_months':24,'hardware':[{'part_number':'SURFACE-A','quantity':2}],'cloud':[{'product_id':'STANDARD','seats':10}]}


def test_public_anonymous_catalog_estimate_pdf_and_no_persistence(workspace):
    client,auth=workspace
    publish(client,auth)
    r=client.get('/api/commercial/public/catalog');assert r.status_code==200,r.text
    assert len(r.json()['cloud'])==4
    assert all(x['part_number']!='SPARK' for x in r.json()['hardware'])
    r=client.post('/api/commercial/public/estimate',json=selection());assert r.status_code==200,r.text
    assert r.json()['cloud_annual_cny']=='11760.00'
    assert r.json()['hardware_monthly_cny']=='800.00'
    for forbidden in ('erp_price_cny','cost_factor','annual_funding_rate','internal','formal_requirements'):
        assert forbidden not in r.text
        assert forbidden not in client.get('/api/commercial/public/catalog').text
    pdf=client.post('/api/commercial/public/budget.pdf',json=selection())
    assert pdf.status_code==200,pdf.text[:200] if pdf.status_code!=200 else ''
    assert pdf.content.startswith(b'%PDF')
    with store.connection() as conn:
        assert conn.execute('SELECT COUNT(*) FROM commercial_quotes').fetchone()[0]==0
        assert conn.execute('SELECT COUNT(*) FROM commercial_profiles').fetchone()[0]==0


def test_admin_parameters_change_internal_cost_only_and_public_exchange(workspace):
    client,auth=workspace
    assert client.get('/api/commercial/admin/settings').status_code==401
    assert client.put('/api/commercial/admin/settings',headers=auth['org1'],json=configuration()).status_code==403
    publish(client,auth)
    before=client.post('/api/commercial/public/estimate',json=selection()).json()
    config=configuration();config['software_cost_factor']='0.8';publish(client,auth,config)
    after=client.post('/api/commercial/public/estimate',json=selection()).json()
    assert before==after
    data=inputs()
    from app.commercial.models import QuoteInput
    with store.connection() as conn:
        _,internal=engine.calculate(conn,QuoteInput(**data))
    assert internal['software_cost_factor']=='0.8'
    config['usd_cny']='8';publish(client,auth,config)
    assert client.post('/api/commercial/public/estimate',json=selection()).json()['cloud_annual_cny']=='13440.00'
    config['active_policy_id']='missing'
    assert client.put('/api/commercial/admin/settings',headers=auth['admin'],json=config).status_code==422


def test_public_rejects_financial_override_and_invalid_selection(workspace):
    client,auth=workspace
    assert client.post('/api/commercial/public/estimate',json=selection()).status_code==503
    publish(client,auth)
    for key,value in [('usd_cny','1'),('software_cost_factor','0.1'),('project_discount_cny','100'),('policy_id','other')]:
        assert client.post('/api/commercial/public/estimate',json={**selection(),key:value}).status_code==422
    assert client.post('/api/commercial/public/estimate',json={}).status_code==422
    s=selection();s['hardware']*=2
    assert client.post('/api/commercial/public/estimate',json=s).status_code==422
    s=selection();s['hardware']=[{'part_number':'DOCK','quantity':1}]
    assert client.post('/api/commercial/public/estimate',json=s).status_code==422


def test_separate_identity_database_preserves_legacy_login(workspace,tmp_path,monkeypatch):
    client,auth=workspace
    password='Existing-test-account-123!'
    with catalog.connection() as conn:
        conn.execute('UPDATE users SET password_hash=? WHERE email=?',(hasher.hash(password),'admin@example.com'))
        conn.commit()
        with sqlite3.connect(tmp_path/'identity.sqlite3') as target:
            conn.backup(target)
    monkeypatch.setenv('CAPABILITY_AUTH_SQLITE_PATH',str(tmp_path/'identity.sqlite3'))
    # Remove identity rows from catalog: login must use the separate identity store.
    with catalog.connection() as conn:
        conn.execute('DELETE FROM sessions');conn.execute('DELETE FROM users');conn.commit()
    r=client.post('/api/auth/login',json={'email':'admin@example.com','password':password})
    assert r.status_code==200,r.text
    token={'Authorization':'Bearer '+r.json()['access_token']}
    assert client.get('/api/auth/me',headers=token).json()['role']=='admin'
    assert client.get('/api/commercial/admin/settings',headers=token).status_code==200


def test_anonymous_budget_mobile_ticket_is_single_use_and_expires(workspace,monkeypatch):
    client,auth=workspace
    publish(client,auth)
    issued=client.post('/api/commercial/public/budget-ticket',json=selection())
    assert issued.status_code==200,issued.text
    token=issued.json()['ticket']
    assert issued.json()['filename'].startswith('Surface-Workplace-Budget-')
    path='/api/commercial/public/budget-download/'+token
    result=client.get(path)
    assert result.status_code==200 and result.content.startswith(b'%PDF')
    assert result.headers['cache-control']=='no-store'
    assert client.get(path).status_code==404
    issued=client.post('/api/commercial/public/budget-ticket',json=selection()).json()
    from app.commercial import public
    current=public.time.time()
    monkeypatch.setattr(public.time,'time',lambda:current+91)
    assert client.get('/api/commercial/public/budget-download/'+issued['ticket']).status_code==404
    assert client.get('/api/commercial/public/budget-download/not-a-valid-ticket').status_code==404
    with store.connection() as conn:
        assert conn.execute('SELECT COUNT(*) FROM commercial_quotes').fetchone()[0]==0
        assert conn.execute('SELECT COUNT(*) FROM commercial_profiles').fetchone()[0]==0
