from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def test_faq_has_200_indexed_source_linked_records():
 body=client.get('/api/faq?limit=200').json()
 assert body['indexed_total']==200
 assert len(body['items'])==200
 assert len(body['categories'])==12
 assert all(x['source_url'].startswith('https://') and x['easy_answer'] and x['expert_answer'] for x in body['items'])

def test_faq_search_and_category_filter():
 body=client.get('/api/faq',params={'q':'Argon2id','category':'安全与账号'}).json()
 assert body['total']>=1
 assert all(x['category']=='安全与账号' for x in body['items'])

def test_faq_detail_and_missing():
 assert client.get('/api/faq/FAQ-001').status_code==200
 assert client.get('/api/faq/FAQ-999').status_code==404
