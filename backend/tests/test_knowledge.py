from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def test_framework_matrix_preserves_unknowns_and_sources():
    body=client.get('/api/knowledge/frameworks').json()
    assert len(body['items'])==6
    assert all(x['source_url'].startswith('https://') and x['version'] for x in body['items'])
    sglang=next(x for x in body['items'] if x['project']=='SGLang')
    assert sglang['native_windows_arm64']=='unknown'
    vllm=next(x for x in body['items'] if x['project']=='vLLM')
    assert vllm['native_windows_arm64']=='not_supported_natively'
