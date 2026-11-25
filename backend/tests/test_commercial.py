"""Business invariants, authorization boundaries and immutable formal documents."""
from datetime import date, timedelta
from decimal import Decimal
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import catalog
from app.auth import iso, now
from app.main import app
from app.commercial import engine, store
from app.commercial.models import PolicyInput, PriceInput, QuoteInput


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    monkeypatch.setenv("CAPABILITY_DEPLOYMENT_MODE", "local")
    monkeypatch.setenv("CAPABILITY_REQUIRE_AUTH", "0")
    monkeypatch.delenv("CAPABILITY_AUTH_DATABASE_URL", raising=False)
    monkeypatch.delenv("CAPABILITY_AUTH_SQLITE_PATH", raising=False)
    monkeypatch.delenv("CAPABILITY_COMMERCIAL_KEY", raising=False)
    monkeypatch.setenv("CAPABILITY_COMMERCIAL_PATH", str(tmp_path / "commercial.sqlite3"))
    monkeypatch.setattr(catalog, "DB_PATH", tmp_path / "catalog.sqlite3")
    credentials = {}
    with catalog.connection() as conn:
        for role, org in (("owner", 1), ("owner", 2), ("admin", 3), ("member", 1)):
            key = "admin" if role == "admin" else ("member" if role == "member" else f"org{org}")
            conn.execute("INSERT OR IGNORE INTO organizations(id,name,status,created_at) VALUES(?,?,'approved',?)", (org, f"Org {org}", iso(now())))
            uid = conn.execute("INSERT INTO users(organization_id,email,password_hash,role,status,email_verified,created_at) VALUES(?,?,?,?,'approved',1,?)", (org, key+'@example.com', 'unused-password', role, iso(now()))).lastrowid
            conn.execute("INSERT OR IGNORE INTO licenses VALUES(?,10,?,'active',?)", (org, iso(now()+timedelta(days=30)), iso(now())))
            token = 'test-token-' + key
            conn.execute("INSERT INTO sessions VALUES(?,?,?,?,NULL)", (hashlib.sha256(token.encode()).hexdigest(), uid, iso(now()), iso(now()+timedelta(hours=1))))
            credentials[key] = {"Authorization": "Bearer " + token}
        for pn, price, kind, memory in (("SURFACE-A", 12000, "Surface 设备", 16), ("SURFACE-B", 18000, "Surface 设备", 32), ("SURFACE-C", 20000, "Surface 设备", 64), ("DOCK", 1200, "配件", None), ("NO-PRICE", None, "Surface 设备", 16), ("UNKNOWN-MEMORY", 8000, "Surface 设备", None), ("SPARK", 20000, "NVIDIA 设备（数据层保留）", 128)):
            conn.execute("INSERT INTO sku_lookup(part_number,source_sheet,source_row,original_family,raw_description,product_type,series_group,product_name,memory_gb,erp_price_cny,match_level,source_sha256) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (pn,'SKU映射',2,'Surface',f'{memory}GB device',kind,'Laptop',pn,memory,price,'reviewed','source-1'))
        conn.commit()
    with store.connection() as conn:
        policy = PolicyInput(name="Test policy",annual_funding_rate="0",residual_rate_24="0.2",residual_rate_36="0.1",monthly_service_cny="0",recovery_cost_cny="0",minimum_margin="0",terms_reference="Approved test terms",approved_for_formal=True)
        conn.execute("INSERT INTO lease_policies VALUES(?,?,?,?)", ('LP-TEST',store.dumps(policy.model_dump(mode='json')),3,store.timestamp()))
        for product, kind, price, components in (("STANDARD","Base","14",[]),("COPILOT","Add-on","21",[]),("BUNDLE","Bundle","23.5",["STANDARD","COPILOT"]),("CHAT","Included/Metered","0",[])):
            data=PriceInput(product_id=product,name=product+' product',kind=kind,monthly_usd=price,effective_from=engine.today()-timedelta(days=1),seat_limit=300,source_url='https://www.microsoft.com/test',source_checked_at=engine.today(),components=components)
            pid=store.create_price(conn,data,3);store.publish_price(conn,pid,3)
    yield TestClient(app), credentials


def inputs(**changes):
    return {"title":"Test workplace", "term_months":24,"hardware":[{"part_number":"SURFACE-A","quantity":2}],
            "cloud":[{"product_id":"STANDARD","seats":10,"eligibility_confirmed":True,"eligibility_reference":"Validated tenant market and license"}],
            "policy_id":"LP-TEST","usd_cny":"7","fx_reference":"Finance test rate","fx_date":str(engine.today()),
            "cloud_tax_rate":"0","valid_until":str(engine.today()+timedelta(days=7)),**changes}


def profile():
    return {"company_name":"Example HK Limited","hk_company_name":"Example HK Limited","region":"HK","address":"Hong Kong office address","phone":"12345678","domain":"example.com","contact_name":"Owner","contact_email":"owner@example.com","bank_account_name":"Example HK Limited","bank_name":"Example Bank","bank_account":"SENSITIVE-BANK-123456789","invoice_title":"Example HK Limited","invoice_registration":"BR-1234","invoice_address":"Hong Kong invoice address","invoice_email":"invoice@example.com"}


def create(client, auth, **changes):
    response=client.post('/api/commercial/quotes',headers=auth,json=inputs(**changes))
    assert response.status_code==201,response.text
    return response.json()


def test_decimal_rent_zero_and_effective_annual_rate():
    rent, rate=engine.pmt(Decimal('0'),24,Decimal('12000'),Decimal('2400'))
    assert rent==Decimal('400.00') and rate==0
    rent, rate=engine.pmt(Decimal('0.08'),36,Decimal('12000'),Decimal('1200'))
    # Independent discounted cash-flow reconciliation, <= half cent per payment.
    pv=sum(rent/(1+rate)**m for m in range(1,37))+Decimal('1200')/(1+rate)**36
    assert abs(pv-Decimal('12000'))<Decimal('0.18')


def test_standard_price_85_percent_cost_and_cash_schedule(workspace):
    client, auth=workspace
    quote=create(client,auth['org1'],azure_requested=True,project_discount_cny='100',discount_reason='Whole project review')
    data=quote['customer']
    assert data['cloud'][0]['standard_unit_monthly_usd']=='14'
    assert data['cloud_annual_cny']=='11760.00'
    assert data['hardware_monthly_cny']=='800.00'
    assert data['total_cny']=='42620.00'
    assert data['first_payment_cny']=='11660.00'
    assert sum(Decimal(x['due_cny']) for x in data['payment_schedule'])==Decimal(data['total_cny'])
    assert [x['month'] for x in data['payment_schedule'] if Decimal(x['cloud_cny'])>0]==[0,12]
    assert data['azure_requested'] and 'Azure' in ' '.join(data['warnings'])
    internal=client.get('/api/commercial/admin/quotes/'+quote['id'],headers=auth['admin']).json()['internal']
    assert internal['software_cost_factor']=='0.85'
    assert internal['software_annual_cost_cny']=='9996.00'
    assert internal['software_annual_gross_profit_cny']=='1764.00'
    assert 'erp_unit_cost_cny' not in json.dumps(quote)
    assert 'software_cost_factor' not in json.dumps(quote)


def test_customer_costs_not_returned_and_tenant_boundaries(workspace):
    client, auth=workspace
    quote=create(client,auth['org1'])
    assert client.get('/api/commercial/products').status_code==401
    for suffix in ('','/inputs','/document.pdf'):
        assert client.get('/api/commercial/quotes/'+quote['id']+suffix,headers=auth['org2']).status_code==404
    assert client.get('/api/commercial/admin/quotes/'+quote['id'],headers=auth['org1']).status_code==403
    assert client.get('/api/commercial/admin/prices',headers=auth['org1']).status_code==403
    assert client.get('/api/commercial/admin/audit',headers=auth['org1']).status_code==403
    hw=client.get('/api/commercial/hardware',headers=auth['org1']).json()
    assert 'erp_price_cny' not in json.dumps(hw)
    assert 'SPARK' not in json.dumps(hw)
    assert client.get('/api/commercial/quotes',headers=auth['org2']).json()['items']==[]


def test_bank_profile_encrypted_and_never_in_quote_or_audit(workspace):
    client,auth=workspace
    response=client.put('/api/commercial/profile',headers=auth['org1'],json=profile());assert response.status_code==200
    with store.connection() as conn:
        raw=conn.execute('SELECT encrypted_payload FROM commercial_profiles').fetchone()[0]
        assert 'SENSITIVE-BANK' not in raw
    member=client.get('/api/commercial/profile',headers=auth['member']).json()['profile']
    assert 'bank_account' not in member
    assert client.put('/api/commercial/profile',headers=auth['member'],json=profile()).status_code==403
    assert client.get('/api/commercial/admin/profiles/1',headers=auth['org2']).status_code==403
    assert client.get('/api/commercial/admin/profiles/1',headers=auth['admin']).json()['profile']['bank_account']=='SENSITIVE-BANK-123456789'
    quote=create(client,auth['org1'])
    submitted=client.post('/api/commercial/quotes/'+quote['id']+'/submit',headers=auth['org1'])
    assert submitted.status_code==200,submitted.text
    assert 'SENSITIVE-BANK' not in submitted.text
    audit=client.get('/api/commercial/admin/audit',headers=auth['admin']).text
    assert 'SENSITIVE-BANK' not in audit


def test_formal_workflow_snapshot_price_change_and_pdf_immutability(workspace):
    client,auth=workspace
    client.put('/api/commercial/profile',headers=auth['org1'],json=profile())
    quote=create(client,auth['org1'])
    path='/api/commercial/quotes/'+quote['id']
    assert client.post(path+'/submit',headers=auth['org1']).status_code==200
    review='/api/commercial/admin/quotes/'+quote['id']
    assert client.post(review+'/issue',headers=auth['admin']).status_code==409
    assert client.post(review+'/review',headers=auth['admin'],json={'decision':'approve','reason':'Checked'}).status_code==422
    approved=client.post(review+'/review',headers=auth['admin'],json={'decision':'approve','reason':'Checked financial and licensing data','commercial_reference':'Supplier legal entity; payment and return terms; software eligibility verified; service cost and tax treatment approved'})
    assert approved.status_code==200,approved.text
    issued=client.post(review+'/issue',headers=auth['admin']);assert issued.status_code==200,issued.text
    pdf=client.get(path+'/document.pdf',headers=auth['org1']);assert pdf.content.startswith(b'%PDF')
    assert hashlib.sha256(pdf.content).hexdigest()==issued.json()['document_sha256']
    assert client.post(review+'/issue',headers=auth['admin']).status_code==409
    # ERP and public-price changes never rewrite a signed quote or signed PDF.
    with catalog.connection() as conn: conn.execute("UPDATE sku_lookup SET erp_price_cny=99000 WHERE part_number='SURFACE-A'");conn.commit()
    new_price={'product_id':'STANDARD','name':'STANDARD product','kind':'Base','monthly_usd':'20','effective_from':str(engine.today()),'seat_limit':300,'source_url':'https://www.microsoft.com/test','source_checked_at':str(engine.today())}
    added=client.post('/api/commercial/admin/prices',headers=auth['admin'],json=new_price).json()
    assert client.post('/api/commercial/admin/prices/'+added['id']+'/publish?replace=true',headers=auth['admin']).status_code==200
    assert client.get(path,headers=auth['org1']).json()['customer']==quote['customer']
    assert client.get(path+'/document.pdf',headers=auth['org1']).content==pdf.content


def test_invalid_data_bundle_overlap_and_separate_user_groups(workspace):
    client,auth=workspace
    for changes in ({'hardware':[{'part_number':'NO-PRICE','quantity':1}]},{'hardware':[{'part_number':'SPARK','quantity':1}]},
                    {'project_discount_cny':'999999','discount_reason':'Too much'}, {'usd_cny':'NaN'},
                    {'cloud':[{'product_id':'CHAT','seats':1}]},{'cloud':[{'product_id':'STANDARD','seats':301}]}):
        assert client.post('/api/commercial/estimate',headers=auth['org1'],json=inputs(**changes)).status_code in (409,422)
    overlap=[{'product_id':'BUNDLE','seats':10},{'product_id':'STANDARD','seats':10}]
    assert client.post('/api/commercial/estimate',headers=auth['org1'],json=inputs(cloud=overlap)).status_code==422
    overlap[0]['user_group']='AI trial';overlap[1]['user_group']='Office only'
    assert client.post('/api/commercial/estimate',headers=auth['org1'],json=inputs(cloud=overlap)).status_code==200
    aggregate=[{'product_id':'STANDARD','seats':200,'user_group':'A'},{'product_id':'STANDARD','seats':101,'user_group':'B'}]
    assert client.post('/api/commercial/estimate',headers=auth['org1'],json=inputs(cloud=aggregate)).status_code==422


def test_expired_license_and_disabled_deployment(workspace,monkeypatch):
    client,auth=workspace
    with catalog.connection() as conn: conn.execute("UPDATE licenses SET expires_at=? WHERE organization_id=1", (iso(now()-timedelta(days=1)),));conn.commit()
    assert client.get('/api/commercial/products',headers=auth['org1']).status_code==403
    monkeypatch.setenv('CAPABILITY_DEPLOYMENT_MODE','public')
    monkeypatch.delenv('CAPABILITY_COMMERCIAL_ENABLED',raising=False)
    # Host boundary first; direct guard verifies module cannot be enabled accidentally.
    with pytest.raises(Exception) as exc: store.ensure_enabled()
    assert exc.value.status_code==503


def test_recommendations_never_infer_unknown_memory(workspace):
    client,auth=workspace
    response=client.post('/api/commercial/recommendations',headers=auth['org1'],json={'min_memory_gb':16})
    assert response.status_code==200
    items=response.json()['items'];assert len(items)==3
    assert all(x['memory_gb']>=16 for x in items)
    assert 'UNKNOWN-MEMORY' not in response.text and 'SPARK' not in response.text


def test_unconfirmed_eligibility_cannot_issue_formal_quote(workspace):
    client,auth=workspace
    client.put('/api/commercial/profile',headers=auth['org1'],json=profile())
    quote=create(client,auth['org1'],cloud=[{'product_id':'COPILOT','seats':10}])
    assert not quote['customer']['formal_ready']
    assert client.post('/api/commercial/quotes/'+quote['id']+'/submit',headers=auth['org1']).status_code==200
    approved=client.post('/api/commercial/admin/quotes/'+quote['id']+'/review',headers=auth['admin'],json={'decision':'approve','reason':'Attempt','commercial_reference':'Reference'})
    assert approved.status_code==409


def test_price_overlaps_rejected_atomically(workspace):
    client,auth=workspace
    with store.connection() as conn:
        data=PriceInput(product_id='STANDARD',name='New standard',kind='Base',monthly_usd='15',effective_from=engine.today()-timedelta(days=1),source_url='https://www.microsoft.com/test',source_checked_at=engine.today())
        pid=store.create_price(conn,data,3)
    response=client.post('/api/commercial/admin/prices/'+pid+'/publish?replace=true',headers=auth['admin'])
    assert response.status_code==409
    with store.connection() as conn:
        assert store.resolve_price(conn,'STANDARD',engine.today())['monthly_usd']=='14'


def test_azure_requires_separate_contract_and_prevents_overlap(workspace):
    client,auth=workspace
    terms={'contract_number':'AZ-TEST','subscription_id':'sub-test','service_name':'cowork specified service','meter':'Input tokens','unit':'million tokens','unit_price_usd':'2.50','signed_on':str(engine.today()-timedelta(days=31)),'starts_on':str(engine.today()-timedelta(days=30)),'ends_on':str(engine.today()+timedelta(days=365)),'reference':'Signed separate contract record'}
    assert client.post('/api/commercial/admin/azure/1/contracts',headers=auth['org1'],json=terms).status_code==403
    response=client.post('/api/commercial/admin/azure/1/contracts',headers=auth['admin'],json=terms)
    assert response.status_code==201,response.text
    contract=response.json()['id']
    second={**terms,'meter':'Output tokens','unit_price_usd':'5.00'}
    assert client.post('/api/commercial/admin/azure/1/contracts',headers=auth['admin'],json=second).status_code==201
    assert client.post('/api/commercial/admin/azure/1/contracts',headers=auth['admin'],json=terms).status_code==409
    usage={'period_start':str(engine.today()-timedelta(days=20)),'period_end':str(engine.today()-timedelta(days=10)),'quantity':'3.125','source_reference':'Actual billing export 001'}
    response=client.post('/api/commercial/admin/azure/'+contract+'/usage',headers=auth['admin'],json=usage)
    assert response.status_code==201 and response.json()['amount_usd']=='7.81'
    assert client.post('/api/commercial/admin/azure/'+contract+'/usage',headers=auth['admin'],json=usage).status_code==409
    assert client.get('/api/commercial/azure/'+contract+'/usage',headers=auth['org2']).status_code==404
    assert client.get('/api/commercial/azure/'+contract+'/usage',headers=auth['org1']).status_code==200


def test_tampered_snapshot_blocks_signature(workspace):
    client,auth=workspace
    client.put('/api/commercial/profile',headers=auth['org1'],json=profile())
    quote=create(client,auth['org1']);client.post('/api/commercial/quotes/'+quote['id']+'/submit',headers=auth['org1'])
    with store.connection() as conn:
        internal=conn.execute('SELECT internal_json FROM commercial_quotes WHERE id=?',(quote['id'],)).fetchone()[0]
        payload=json.loads(internal);payload['software_cost_factor']='0.1'
        conn.execute('UPDATE commercial_quotes SET internal_json=? WHERE id=?',(store.dumps(payload),quote['id']))
    response=client.post('/api/commercial/admin/quotes/'+quote['id']+'/review',headers=auth['admin'],json={'decision':'approve','reason':'Checked','commercial_reference':'Reference'})
    assert response.status_code==409


def test_workplace_page_has_all_business_entry_points(workspace):
    client,_=workspace
    page=client.get('/workplace');assert page.status_code==200
    for identifier in ('feature-options','subscription-options','device-options','catalog-grid','download-budget'):
        assert identifier in page.text
    assert 'login-form' not in page.text
    admin_page=client.get('/workplace/admin')
    for identifier in ('login-form','settings-form','azure-form','price-form','policy-form','usage-form'):
        assert identifier in admin_page.text
    home=client.get('/').text
    nav=home.split('<nav class="home-entry-grid"',1)[1].split('</nav>',1)[0]
    assert 'href="/workplace"' in nav and 'Surface AI Workplace租赁及订阅' in nav
    assert '设备租赁与 Microsoft 365、Copilot 订阅' in home
    assert 'Surface 与 M365 Copilot 组合方案 · 选型、租赁与报价' not in home


def test_customer_can_read_public_erp_but_not_internal_imports(workspace, monkeypatch):
    client, auth = workspace
    monkeypatch.setenv('CAPABILITY_DEV_EXPOSE_TOKENS','1')
    response = client.post('/api/commercial/register',json={'organization_name':'External customer','email':'external@example.com','password':'Strong-external-123','accepted_terms':True,'accepted_privacy':True})
    assert response.status_code == 201
    with catalog.connection() as conn:
        registered = conn.execute("SELECT role FROM users WHERE email='external@example.com'").fetchone()
        assert registered['role'] == 'customer_owner'
        conn.execute("UPDATE users SET role='customer_owner' WHERE email='org1@example.com'")
        conn.commit()
    monkeypatch.setenv('CAPABILITY_REQUIRE_AUTH','1')
    assert client.get('/api/commercial/products',headers=auth['org1']).status_code==200
    assert client.get('/api/catalog/quick-search',headers=auth['org1']).status_code==200
    assert client.get('/api/catalog/imported-skus',headers=auth['org1']).status_code==403
    assert client.put('/api/commercial/profile',headers=auth['org1'],json=profile()).status_code==200


def test_import_preserves_source_and_never_uses_promotional_price(workspace, tmp_path):
    from openpyxl import Workbook
    workbook = Workbook()
    sheet=workbook.active;sheet.title='产品价格数据库'
    sheet.append(['ProductId','官方英文名称','产品类型','币种','官方月价','核验日期','官方来源URL','用户上限','市场基准','促销月价'])
    sheet.append(['IMPORT-TEST','Import Test','Add-on','USD',21,engine.today(),'https://www.microsoft.com/test',300,'US Public',18])
    path=tmp_path/'source.xlsx';workbook.save(path)
    spec=importlib.util.spec_from_file_location('commercial_import_test',Path(__file__).resolve().parents[2]/'scripts'/'import-cloud-prices.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert module.import_workbook(path)['count']==1
    assert module.import_workbook(path)['status']=='already_imported'
    with store.connection() as conn:
        row=conn.execute("SELECT * FROM cloud_prices WHERE product_id='IMPORT-TEST'").fetchone()
        assert row['status']=='draft'
        assert json.loads(row['payload'])['monthly_usd']=='21'
        raw=conn.execute('SELECT original_records_json FROM commercial_imports').fetchone()[0]
        assert '促销月价' in raw


def test_bundle_comparison_uses_standard_prices_and_partial_seats(workspace):
    client,auth=workspace
    with store.connection() as conn:
        for product,kind,price,components in [('M365-BIZ-STANDARD','Base','14',[]),('COPILOT-BUSINESS','Add-on','21',[]),('BUNDLE-STANDARD-COPILOT','Bundle','23.5',['M365-BIZ-STANDARD','COPILOT-BUSINESS'])]:
            data=PriceInput(product_id=product,name=product,kind=kind,monthly_usd=price,effective_from=engine.today(),source_url='https://www.microsoft.com/test',source_checked_at=engine.today(),components=components)
            pid=store.create_price(conn,data,3);store.publish_price(conn,pid,3)
    response=client.post('/api/commercial/cloud-recommendations',headers=auth['org1'],json={'users':100,'copilot_users':20})
    assert response.status_code==200
    bundle,standalone=response.json()['items']
    assert bundle['annual_usd']=='19080.00'
    assert standalone['annual_usd']=='21840.00'
    assert sum(x['seats'] for x in bundle['lines'])==100
    # Both suggested configurations must be accepted by the actual quote engine.
    for option in (bundle,standalone):
        assert client.post('/api/commercial/estimate',headers=auth['org1'],json=inputs(cloud=option['lines'])).status_code==200
    existing=client.post('/api/commercial/cloud-recommendations',headers=auth['org1'],json={'users':100,'copilot_users':20,'existing_qualifying_base':True}).json()
    assert existing['items'][0]['annual_usd']=='5040.00'
    assert len(existing['items'][0]['lines'])==1


def test_trial_policy_and_stale_erp_block_formal_approval(workspace):
    client,auth=workspace
    client.put('/api/commercial/profile',headers=auth['org1'],json=profile())
    quote=create(client,auth['org1'])
    client.post('/api/commercial/quotes/'+quote['id']+'/submit',headers=auth['org1'])
    with catalog.connection() as conn:
        conn.execute("UPDATE sku_lookup SET erp_price_cny=12500 WHERE part_number='SURFACE-A'");conn.commit()
    response=client.post('/api/commercial/admin/quotes/'+quote['id']+'/review',headers=auth['admin'],json={'decision':'approve','reason':'Checked','commercial_reference':'Reference'})
    assert response.status_code==409 and 'ERP' in response.text
    with store.connection() as conn:
        raw=conn.execute("SELECT payload FROM lease_policies WHERE id='LP-TEST'").fetchone()[0]
        payload=json.loads(raw);payload['approved_for_formal']=False
        conn.execute('INSERT INTO lease_policies VALUES(?,?,?,?)',('LP-TRIAL',store.dumps(payload),3,store.timestamp()))
    quote=create(client,auth['org1'],policy_id='LP-TRIAL')
    assert not quote['customer']['formal_ready']


def test_thirty_six_month_cashflow_tax_and_discount_reconciliation(workspace):
    client,auth=workspace
    quote=create(client,auth['org1'],term_months=36,cloud_tax_rate='0.06',service_once_cny='1000',project_discount_cny='20000',discount_reason='Project promotion')
    data=quote['customer']
    assert data['cloud_annual_cny']=='12465.60'
    assert len(data['payment_schedule'])==37
    assert [x['month'] for x in data['payment_schedule'] if Decimal(x['cloud_cny'])>0]==[0,12,24]
    assert all(Decimal(x['due_cny'])>=0 for x in data['payment_schedule'])
    assert sum(Decimal(x['discount_cny']) for x in data['payment_schedule'])==Decimal('20000')
    assert sum(Decimal(x['due_cny']) for x in data['payment_schedule'])==Decimal(data['total_cny'])


def test_customer_cannot_override_cost_and_internal_review_notes_hidden(workspace):
    client,auth=workspace
    assert client.post('/api/commercial/estimate',headers=auth['org1'],json=inputs(software_cost_factor='0.1')).status_code==422
    client.put('/api/commercial/profile',headers=auth['org1'],json=profile())
    quote=create(client,auth['org1']);client.post('/api/commercial/quotes/'+quote['id']+'/submit',headers=auth['org1'])
    response=client.post('/api/commercial/admin/quotes/'+quote['id']+'/review',headers=auth['admin'],json={'decision':'reject','reason':'INTERNAL-COST-NOTES-999'})
    assert response.status_code==200 and 'INTERNAL-COST-NOTES' not in response.text
    assert 'INTERNAL-COST-NOTES' not in client.get('/api/commercial/quotes/'+quote['id'],headers=auth['org1']).text
