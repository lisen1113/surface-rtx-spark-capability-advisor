from decimal import Decimal
import json
import pytest
from test_commercial import workspace,inputs,create
from test_commercial_public import configuration
from test_rental_rules import rules
from app import catalog
from app.commercial import engine,store


@pytest.fixture
def spark(workspace):
    client,auth=workspace
    with catalog.connection() as conn:
        conn.execute("INSERT INTO sku_lookup(part_number,source_sheet,source_row,original_family,raw_description,product_type,series_group,memory_gb,erp_price_cny,match_level,source_sha256) VALUES('ULTRA-1','SKU映射',100,'Surface Laptop Ultra','S3 128GB 1TB DARK STEEL','NVIDIA 设备（暂不纳入）','NVIDIA',NULL,20000,'N/A 不在本轮设备规格范围','erp-source')")
        conn.execute("INSERT INTO imported_skus(part_number,product_family,raw_configuration,platform_code,memory_gb,storage_tb,erp_price_cny,source_sha256) VALUES('ULTRA-1','Surface Laptop Ultra','S3 128GB 1TB DARK STEEL','S3',128,1,99999,'spec-source')")
        conn.commit()
    client.put('/api/commercial/admin/settings',headers=auth['admin'],json=configuration()).raise_for_status()
    return client,auth


def publish(client,auth,explicit=False):
    data=rules(surface_erp_cost_factor='.8',approved_for_formal=True).model_dump(mode='json')
    if explicit:
        data['residual_by_brand']['RTX Spark']['months_24']='.1'
    else:
        data['residual_by_brand'].pop('RTX Spark')
    r=client.put('/api/commercial/admin/rental-rules',headers=auth['admin'],json=data)
    assert r.status_code==200,r.text
    return r.json()['id']


def test_exact_sku_join_read_only_specs_and_original_erp(spark):
    client,auth=spark
    before=next(x for x in engine.catalog_items() if x['part_number']=='SURFACE-A')
    publish(client,auth)
    r=client.get('/api/commercial/public/catalog')
    assert r.status_code==200,r.text
    item=next(x for x in r.json()['hardware'] if x['part_number']=='ULTRA-1')
    assert item['is_device'] and item['brand']=='RTX Spark'
    assert item['memory_gb']==128 and item['storage_capacity']=='1TB'
    assert item['cpu_official'] is None
    assert item['monthly']['24']=='750.00'  # ERP 20000, not imported price 99999 or Surface 80% factor
    assert all(x['part_number']!='SPARK' for x in r.json()['hardware'])  # no broad NVIDIA inclusion
    assert next(x for x in engine.catalog_items() if x['part_number']=='SURFACE-A')==before
    assert 'erp_price_cny' not in r.text and 'source_product_type' not in r.text
    with catalog.connection() as conn:
        row=conn.execute("SELECT erp_price_cny,memory_gb,product_type,match_level FROM sku_lookup WHERE part_number='ULTRA-1'").fetchone()
        assert row['erp_price_cny']==20000 and row['memory_gb'] is None and row['match_level'].startswith('N/A')
    search=client.get('/api/commercial/hardware?q=ULTRA-1',headers=auth['org1'])
    assert search.status_code==200 and search.json()['total']==1


def test_spark_can_be_sole_device_three_terms_and_independent_residual(spark):
    client,auth=spark
    policy=publish(client,auth)
    for months in (12,24,36):
        r=client.post('/api/commercial/public/estimate',json={'term_months':months,'hardware':[{'part_number':'ULTRA-1','quantity':2}]})
        assert r.status_code==200,r.text
        data=r.json()
        assert sum(Decimal(x['due_cny']) for x in data['payment_schedule'])==Decimal(data['total_cny'])
        assert any('RTX Spark' in w for w in data['warnings'])
    quote=create(client,auth['org1'],policy_id=policy,hardware=[{'part_number':'ULTRA-1','quantity':1}],cloud=[])
    assert not quote['customer']['formal_ready']
    policy=publish(client,auth,True)
    quote=create(client,auth['org1'],policy_id=policy,hardware=[{'part_number':'ULTRA-1','quantity':1}],cloud=[])
    assert quote['customer']['formal_ready'] and quote['customer']['hardware_monthly_cny']=='1000.00'
    internal=client.get('/api/commercial/admin/quotes/'+quote['id'],headers=auth['admin']).json()['internal']['hardware'][0]
    assert internal['erp_unit_cost_cny']=='20000.00' and internal['effective_unit_cost_cny']=='20000.00'
    assert internal['brand']=='RTX Spark' and internal['erp_cost_factor']=='1'
    pdf=client.post('/api/commercial/public/budget.pdf',json={'hardware':[{'part_number':'ULTRA-1','quantity':1}]})
    assert pdf.status_code==200 and pdf.content.startswith(b'%PDF')


def test_spark_rejects_legacy_policy(spark):
    client,auth=spark
    r=client.post('/api/commercial/estimate',headers=auth['org1'],json=inputs(hardware=[{'part_number':'ULTRA-1','quantity':1}]))
    assert r.status_code==422 and 'RTX Spark' in r.json()['detail']
