from fastapi.testclient import TestClient
from app import catalog, report
from app.main import app


def test_full_advisor_anonymous_and_administration_protected(tmp_path, monkeypatch):
    monkeypatch.setattr(catalog, 'DB_PATH', tmp_path/'catalog.sqlite3')
    monkeypatch.setenv('CAPABILITY_REQUIRE_AUTH', '1')
    monkeypatch.setenv('CAPABILITY_PUBLIC_ADVISOR', '1')
    monkeypatch.delenv('CAPABILITY_DEPLOYMENT_MODE', raising=False)
    with catalog.connection() as conn:
        conn.execute("INSERT INTO imported_skus(part_number,product_family,raw_configuration,platform_code,memory_gb,storage_tb,erp_price_cny,source_reference,source_sha256) VALUES('PUBLIC-1','Surface Laptop Ultra','S3 128GB 1TB','S3',128,1,20000,'PRIVATE','HASH')")
        conn.commit()
    client=TestClient(app)
    assert client.get('/guest', follow_redirects=False).headers['location']=='/?advisor=public'
    listing=client.get('/api/catalog/imported-skus')
    assert listing.status_code==200 and 'PRIVATE' not in listing.text and 'HASH' not in listing.text and listing.json()['items'][0]['erp_price_cny']==20000
    for path in ['/api/catalog/advisor/PUBLIC-1', '/api/catalog/models', '/api/knowledge/frameworks',
                 '/api/faq', '/api/deployment/sku/PUBLIC-1', '/api/tco/defaults/PUBLIC-1',
                 '/api/reports/PUBLIC-1.html', '/api/reports/PUBLIC-1.pdf']:
        response=client.get(path)
        assert response.status_code==200,(path,response.text[:200])
    for path in ['/api/admin/users', '/api/catalog/sources', '/api/catalog/imports']:
        assert client.get(path).status_code==401,path
    recommendation=client.post('/api/recommendations',json={'usages':['ai'],'ai_size':'70B','budget_cny':1})
    assert recommendation.status_code==200 and recommendation.json()['items'][0]['price_cny']==20000 and recommendation.json()['items'][0]['over_budget']
    need_report=client.post('/api/reports/recommendation',json={'part_number':'PUBLIC-1','usages':['ai']})
    assert need_report.status_code==200 and '20,000' in need_report.text
    assert client.get('/api/tco/defaults/PUBLIC-1').json()['values']['purchase_price_cny']==20000
    rendered=[]
    original_builder=report.build_customer_pdf
    def capture(sku):
        rendered.append(sku)
        return original_builder(sku)
    monkeypatch.setattr(report,'build_customer_pdf',capture)
    assert client.post('/api/estimate/memory',json={'parameters_billion':8,'bits_per_weight':4}).status_code==200
    assert client.post('/api/tco/calculate',json={'purchase_price_cny':20000}).status_code==200
    ticket=client.post('/api/reports/mobile-ticket',json={'part_number':'PUBLIC-1'})
    assert ticket.status_code==200,ticket.text
    route='/api/reports/mobile-download/'+ticket.json()['ticket']
    pdf=client.get(route)
    assert pdf.status_code==200 and pdf.content.startswith(b'%PDF')
    assert rendered and rendered[-1]['erp_price_cny']==20000 and 'source_reference' not in rendered[-1]
    assert client.get(route).status_code==404
    assert client.post('/api/reports/mobile-ticket',json={'part_number':'PUBLIC-1','report_kind':'surface'}).status_code==404
    monkeypatch.setenv('CAPABILITY_PUBLIC_ADVISOR','0')
    assert client.get('/api/catalog/imported-skus').status_code==401
    assert client.get('/api/reports/PUBLIC-1.pdf').status_code==401
