from decimal import Decimal
import json

import pytest
from fastapi import HTTPException
from test_commercial import workspace, inputs, create
from test_commercial_public import configuration, selection
from app import catalog
from app.commercial import rental, store, engine
from app.commercial.models import RentalRulesInput, ResidualRates


def rules(**changes):
    return RentalRulesInput(residual_by_brand={brand:ResidualRates() for brand in rental.BRANDS},terms_reference='User supplied conventional lease example',**changes)


def item(brand='Surface',price='10000'):
    return {'part_number':'TEST','product_type':brand+' 设备','product_name':{'Surface':'Surface Pro','Apple':'Apple MacBook','Think':'ThinkPad'}[brand],'erp_price_cny':price}


@pytest.mark.parametrize('months,total,monthly,final',[(12,'6500','541.67','541.63'),(24,'9000','375','375'),(36,'11500','319.44','319.60')])
def test_document_ten_thousand_examples_and_rounding(months,total,monthly,final):
    result=rental.price(item(),rental.policy_payload(rules()),months)
    assert result['term_total']==Decimal(total)
    assert result['monthly']==Decimal(monthly)
    assert result['final_monthly']==Decimal(final)
    assert result['monthly']*(months-1)+result['final_monthly']==result['term_total']


@pytest.mark.parametrize('months,total,monthly',[(12,'12220','1018.33'),(24,'16920','705'),(36,'21620','600.56')])
def test_document_eighteen_thousand_eight_hundred_examples(months,total,monthly):
    result=rental.price(item(price='18800'),rental.policy_payload(rules()),months)
    assert result['term_total']==Decimal(total) and result['monthly']==Decimal(monthly)
    assert result['monthly']*(months-1)+result['final_monthly']==Decimal(total)


def test_brand_specific_residual_and_surface_only_cost_discount():
    data=rules(surface_erp_cost_factor='0.9')
    data.residual_by_brand['Apple']=ResidualRates(months_12='.6',months_24='.5',months_36='.4')
    data.residual_by_brand['Think']=ResidualRates(months_12='.4',months_24='.3',months_36='.2')
    policy=rental.policy_payload(data)
    surface=rental.price(item(),policy,24);apple=rental.price(item('Apple'),policy,24);think=rental.price(item('Think'),policy,24)
    assert surface['erp_cost']==10000 and surface['cost']==9000 and surface['term_total']==8100
    assert apple['cost']==10000 and apple['term_total']==8000
    assert think['cost']==10000 and think['term_total']==10000
    accessory=item();accessory['product_type']='配件'
    assert rental.price(accessory,policy,24)['residual']==0
    assert rental.price(item(price='4.23'),rental.policy_payload(rules()),12)['term_total']==Decimal('2.75')


def publish(client,auth,data=None):
    client.put('/api/commercial/admin/settings',headers=auth['admin'],json=configuration()).raise_for_status()
    result=client.put('/api/commercial/admin/rental-rules',headers=auth['admin'],json=(data or rules()).model_dump(mode='json'))
    assert result.status_code==200,result.text
    return result.json()['id']


def test_admin_rules_apply_to_public_catalog_and_quotes_and_keep_original_erp(workspace):
    client,auth=workspace
    previous=create(client,auth['org1'])
    policy_id=publish(client,auth,rules(surface_erp_cost_factor='.9'))
    with catalog.connection() as conn:
        assert conn.execute("SELECT erp_price_cny FROM sku_lookup WHERE part_number='SURFACE-A'").fetchone()[0]==12000
    public_catalog=client.get('/api/commercial/public/catalog').json()
    card=next(x for x in public_catalog['hardware'] if x['part_number']=='SURFACE-A')
    assert card['monthly']['24']=='405.00' and card['monthly']['12']=='585.00'
    assert public_catalog['budget']['lease_terms']==[12,24,36]
    s=selection();s['cloud']=[]
    for months in (12,24,36):
        s['term_months']=months
        response=client.post('/api/commercial/public/estimate',json=s)
        assert response.status_code==200,response.text
        output=response.json()
        assert sum(Decimal(p['due_cny']) for p in output['payment_schedule'])==Decimal(output['total_cny'])
        assert output['hardware'][0]['unit_monthly_cny']==card['monthly'][str(months)]
        for key in ('erp_cost_factor','effective_unit_cost_cny','residual_by_brand','term_multiplier'):
            assert key not in response.text and key not in json.dumps(public_catalog)
    quote=create(client,auth['org1'],policy_id=policy_id,term_months=12,cloud=[])
    internal=client.get('/api/commercial/admin/quotes/'+quote['id'],headers=auth['admin']).json()['internal']
    assert internal['hardware'][0]['erp_unit_cost_cny']=='12000.00'
    assert internal['hardware'][0]['effective_unit_cost_cny']=='10800.00'
    assert internal['hardware'][0]['residual_cny']=='5400.00'
    assert client.get('/api/commercial/quotes/'+previous['id'],headers=auth['org1']).json()['customer']==previous['customer']


def test_rules_protected_fixed_fields_validated_and_no_partial_publish(workspace):
    client,auth=workspace
    data=rules().model_dump(mode='json')
    assert client.get('/api/commercial/admin/rental-rules').status_code==401
    assert client.put('/api/commercial/admin/rental-rules',headers=auth['org1'],json=data).status_code==403
    # Missing settings cannot create a half-published policy.
    with store.connection() as conn:
        count=conn.execute('SELECT COUNT(*) FROM lease_policies').fetchone()[0]
    assert client.put('/api/commercial/admin/rental-rules',headers=auth['admin'],json=data).status_code==409
    with store.connection() as conn:
        assert conn.execute('SELECT COUNT(*) FROM lease_policies').fetchone()[0]==count
    for key,value in [('term_multipliers',{'12':'2'}),('annual_funding_rate','.1'),('monthly_service_cny','100'),('surface_erp_cost_factor','0'),('surface_erp_cost_factor','1.1')]:
        assert client.put('/api/commercial/admin/rental-rules',headers=auth['admin'],json={**data,key:value}).status_code==422
    del data['residual_by_brand']['Apple']
    assert client.put('/api/commercial/admin/rental-rules',headers=auth['admin'],json=data).status_code==422


def test_legacy_policies_fail_cleanly_for_new_twelve_month_term(workspace):
    client,auth=workspace
    response=client.post('/api/commercial/estimate',headers=auth['org1'],json=inputs(term_months=12))
    assert response.status_code==422
    assert '12' in response.json()['detail']
