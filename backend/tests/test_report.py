from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def test_customer_report_contains_evidence_boundaries():
 skus=client.get('/api/catalog/imported-skus').json()['items']
 if not skus: return
 response=client.get(f"/api/reports/{skus[0]['part_number']}.html")
 assert response.status_code==200
 for text in ('客户能力报告','AI 模型能力','游戏能力','生产力能力','重要限制','© 2026 上海以和信息技术有限公司'):
  assert text in response.text
 assert 'ComfyUI 图像生成' in response.text

def test_missing_report_is_404():
 assert client.get('/api/reports/NOT-FOUND.html').status_code==404
