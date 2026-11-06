from decimal import Decimal
import pytest
from test_commercial import workspace
from test_commercial_public import configuration
from app.commercial import engine,store
from app.commercial.models import PriceInput


@pytest.fixture
def subscriptions(workspace):
    client,auth=workspace
    products=[('M365-BIZ-BASIC','Base','7',[]),('M365-BIZ-STANDARD','Base','14',[]),('M365-BIZ-PREMIUM','Base','22',[]),('COPILOT-BUSINESS','Add-on','21',[]),('BUNDLE-STANDARD-COPILOT','Bundle','23.5',['M365-BIZ-STANDARD','COPILOT-BUSINESS']),('BUNDLE-PREMIUM-COPILOT','Bundle','32',['M365-BIZ-PREMIUM','COPILOT-BUSINESS'])]
    with store.connection() as conn:
        for product,kind,price,components in products:
            value=PriceInput(product_id=product,name=product,kind=kind,monthly_usd=price,components=components,seat_limit=300,effective_from=engine.today(),source_checked_at=engine.today(),source_url='https://www.microsoft.com/test')
            identifier=store.create_price(conn,value,3);store.publish_price(conn,identifier,3)
    client.put('/api/commercial/admin/settings',headers=auth['admin'],json=configuration()).raise_for_status()
    return client,auth


def recommendations(client,**changes):
    response=client.post('/api/commercial/public/recommendations',json={'users':10,'copilot_users':3,**changes})
    assert response.status_code==200,response.text
    return response.json()['items']


@pytest.mark.parametrize('desktop,security,monthly,base,bundle,saving',[(True,False,'168.50','M365-BIZ-STANDARD','BUNDLE-STANDARD-COPILOT','414.00'),(False,False,'119.50','M365-BIZ-BASIC','BUNDLE-STANDARD-COPILOT','162.00'),(True,True,'250.00','M365-BIZ-PREMIUM','BUNDLE-PREMIUM-COPILOT','396.00')])
def test_lowest_matching_price_partial_ai_and_executable_plans(subscriptions,desktop,security,monthly,base,bundle,saving):
    client,_=subscriptions
    items=recommendations(client,desktop_office=desktop,security_management=security)
    best=items[0]
    assert best['is_recommended'] and best['monthly_average_usd']==monthly and best['annual_saving_usd']==saving
    assert [(x['product_id'],x['seats']) for x in best['breakdown']]==[(base,7),(bundle,3)]
    assert best['copilot_users']==3 and best['ordinary_users']==7
    assert sum(x['is_recommended'] for x in items)==1
    assert [Decimal(x['annual_usd']) for x in items]==sorted(Decimal(x['annual_usd']) for x in items)
    for option in items:
        result=client.post('/api/commercial/public/estimate',json={'cloud':option['lines']})
        assert result.status_code==200,result.text
        assert sum(Decimal(p['monthly_usd']) for p in option['breakdown'])==Decimal(option['monthly_average_usd'])
    if security:
        assert all('BUNDLE-STANDARD-COPILOT' not in [x['product_id'] for x in p['lines']] for p in items)
    elif desktop:
        premium=next(x for x in items if x['route']=='bundle' and x['tier']==2)
        assert premium['optional_upgrade'] and premium['annual_extra_usd']=='306.00'


def test_no_ai_only_base_all_ai_only_bundle_and_existing_base_only_addon(subscriptions):
    client,_=subscriptions
    no_ai=recommendations(client,copilot_users=0)
    assert len(no_ai)==1 and no_ai[0]['monthly_average_usd']=='140.00'
    assert no_ai[0]['route']=='base'
    all_ai=recommendations(client,copilot_users=10)[0]
    assert len(all_ai['lines'])==1 and all_ai['monthly_average_usd']=='235.00'
    existing=recommendations(client,existing_qualifying_base=True)
    assert len(existing)==1 and existing[0]['monthly_average_usd']=='63.00'
    assert [p['product_id'] for p in existing[0]['lines']]==['COPILOT-BUSINESS']
    assert recommendations(client,existing_qualifying_base=True,copilot_users=0)==[]


def test_do_not_force_bundle_when_standard_prices_change(subscriptions):
    client,_=subscriptions
    with store.connection() as conn:
        row=conn.execute("SELECT id,payload FROM cloud_prices WHERE product_id='BUNDLE-STANDARD-COPILOT'").fetchone()
        import json
        payload=json.loads(row['payload']);payload['monthly_usd']='60'
        conn.execute('UPDATE cloud_prices SET payload=? WHERE id=?',(store.dumps(payload),row['id']))
        row=conn.execute("SELECT id,payload FROM cloud_prices WHERE product_id='BUNDLE-PREMIUM-COPILOT'").fetchone()
        payload=json.loads(row['payload']);payload['monthly_usd']='70'
        conn.execute('UPDATE cloud_prices SET payload=? WHERE id=?',(store.dumps(payload),row['id']))
    best=recommendations(client)[0]
    assert best['route']=='standalone' and best['monthly_average_usd']=='203.00'
    standard=next(p for p in best['breakdown'] if p['product_id']=='M365-BIZ-STANDARD')
    assert standard['seats']==10  # merged display, not two repeated product names


def test_business_cap_and_invalid_ai_count(subscriptions):
    client,_=subscriptions
    assert recommendations(client,users=301)==[]
    assert client.post('/api/commercial/public/recommendations',json={'users':10,'copilot_users':11}).status_code==422
