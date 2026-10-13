from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def test_faq_has_200_indexed_source_linked_records():
 body=client.get('/api/faq?limit=200').json()
 assert body['indexed_total']==200
 assert body['concept_total']==100
 assert len(body['items'])==200
 assert len(body['categories'])==12
 assert len({x['question'] for x in body['items']})==200
 assert all(x['source_url'].startswith('https://') and x['easy_answer'] and x['expert_answer'] and x['misconception'] and x['sales_tip'] for x in body['items'])

def test_faq_search_and_category_filter():
 body=client.get('/api/faq',params={'q':'MoE','category':'模型架构'}).json()
 assert body['total']>=1
 assert all(x['category']=='模型架构' for x in body['items'])

def test_faq_covers_customer_training_examples_without_context_clones():
 for term in ('MoE','统一内存','Bit','KV Cache','S2平台','CUDA','Prism模拟'):
  body=client.get('/api/faq',params={'q':term,'limit':20}).json()
  assert body['total']>=2, term
 assert all('个人日常使用：' not in x['question'] for x in client.get('/api/faq?limit=200').json()['items'])

def test_faq_detail_and_missing():
 assert client.get('/api/faq/FAQ-001').status_code==200
 assert client.get('/api/faq/FAQ-999').status_code==404
