"""Validate an enabled public deployment without changing live customer records."""
from decimal import Decimal
import json
from fastapi.testclient import TestClient
from app.main import app
from app.commercial import store


def verify():
    with TestClient(app,base_url='https://surfacedmp.com') as client:
        assert client.get('/health').status_code==200
        home=client.get('/').text
        assert 'home-entry-grid' in home and 'Surface AI Workplace' in home
        assert client.get('/workplace').status_code==200
        assert client.get('/workplace/admin').status_code==200
        assert client.get('/api/commercial/admin/settings').status_code==401
        assert client.get('/api/catalog/imported-skus').status_code==401
        catalog=client.get('/api/commercial/public/catalog')
        assert catalog.status_code==200,catalog.text
        data=catalog.json()
        assert len(data['cloud'])==14 and len(data['hardware'])==226
        assert data['budget']['lease_terms']==[12,24,36]
        for field in ('erp_price_cny','software_cost_factor','residual_by_brand'):
            assert field not in catalog.text
        selected=next(x for x in data['hardware'] if x['is_device'] and x['monthly'].get('12'))
        inputs={'term_months':12,'hardware':[{'part_number':selected['part_number'],'quantity':2}],
                'cloud':[{'product_id':'BUNDLE-STANDARD-COPILOT','seats':3}]}
        estimate=client.post('/api/commercial/public/estimate',json=inputs)
        assert estimate.status_code==200,estimate.text
        result=estimate.json()
        assert sum(Decimal(x['due_cny']) for x in result['payment_schedule'])==Decimal(result['total_cny'])
        assert result['hardware'][0]['unit_monthly_cny']==selected['monthly']['12']
        assert 'erp_unit_cost_cny' not in estimate.text
        plans=client.post('/api/commercial/public/recommendations',json={'users':10,'copilot_users':3}).json()
        assert plans['items'][0]['monthly_average_usd']=='168.50'
        ticket=client.post('/api/commercial/public/budget-ticket',json=inputs)
        assert ticket.status_code==200,ticket.text
        route='/api/commercial/public/budget-download/'+ticket.json()['ticket']
        pdf=client.get(route)
        assert pdf.status_code==200 and pdf.content.startswith(b'%PDF')
        assert client.get(route).status_code==404
    print(json.dumps({'status':'passed','hardware':226,'cloud':14,'protected_admin':True,'public_estimate':True,'mobile_pdf_single_use':True}))


if __name__=='__main__':
    verify()
