from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def test_faq_has_200_indexed_source_linked_records():
 body=client.get('/api/faq?limit=200').json()
 assert body['indexed_total']>=215
 assert body['concept_total']>=115
 assert len(body['items'])==200
 assert len(body['categories'])==12
 all_items=client.get('/api/faq?limit=250').json()['items']
 assert len({x['question'] for x in all_items})==len(all_items)
 assert all(x['source_url'].startswith('https://') and x['easy_answer'] and x['expert_answer'] and x['misconception'] and x['sales_tip'] for x in body['items'])

def test_faq_search_and_category_filter():
 body=client.get('/api/faq',params={'q':'MoE','category':'模型架构'}).json()
 assert body['total']>=1
 assert all(x['category']=='模型架构' for x in body['items'])

def test_faq_covers_customer_training_examples_without_context_clones():
 for term in ('MoE','统一内存','Bit','KV Cache','N1X 18 核 CPU','CUDA','Prism模拟'):
  body=client.get('/api/faq',params={'q':term,'limit':20}).json()
  assert body['total']>=2, term
 assert all('个人日常使用：' not in x['question'] for x in client.get('/api/faq?limit=200').json()['items'])

def test_faq_detail_and_missing():
 assert client.get('/api/faq/FAQ-001').status_code==200
 assert client.get('/api/faq/FAQ-999').status_code==404

def test_october_announcement_faq_has_specific_sources_and_release_status():
 body=client.get('/api/faq',params={'q':'MXC','limit':250}).json()
 assert any('Microsoft Execution Containers' in x['question'] for x in body['items'])
 assert any(x['source_url'].startswith('https://blogs.windows.com/windowsdeveloper/2026/10/07/') for x in body['items'])
 hybrid=client.get('/api/faq',params={'q':'hybrid intelligence','limit':250}).json()
 assert any('混合智能' in x['question'] for x in hybrid['items'])
 assert any('实验预览' in x['expert_answer'] for x in client.get('/api/faq',params={'q':'HydraFusion','limit':250}).json()['items'])
