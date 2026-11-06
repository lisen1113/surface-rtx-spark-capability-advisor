from fastapi.testclient import TestClient
from datetime import timedelta
import hashlib
import secrets
from app.main import app
from app.auth import iso, now
from app.auth_store import connection as auth_connection

client=TestClient(app)

def test_customer_report_contains_evidence_boundaries():
 skus=client.get('/api/catalog/imported-skus').json()['items']
 if not skus: return
 response=client.get(f"/api/reports/{skus[0]['part_number']}.html")
 assert response.status_code==200
 for text in ('客户能力报告','AI 模型能力','游戏能力','生产力能力','重要限制','© 2026 上海以和信息技术有限公司'):
  assert text in response.text
 assert 'ComfyUI 图像生成' in response.text
 assert 'Microsoft 365' in response.text and 'Blender 3D' in response.text
 assert '保存 PDF 报告' in response.text
 assert 'window.opener || (window.parent !== window ? window.parent : null)' in response.text
 assert skus[0]['part_number'] in response.text
 assert response.text.split('<footer>',1)[1].split('</footer>',1)[0] == '© 2026 上海以和信息技术有限公司。保留所有权利。'

def test_missing_report_is_404():
 assert client.get('/api/reports/NOT-FOUND.html').status_code==404

def test_customer_pdf_download_has_sku_filename_and_evidence():
 skus=client.get('/api/catalog/imported-skus').json()['items']
 if not skus: return
 part_number=skus[0]['part_number']
 response=client.get(f'/api/reports/{part_number}.pdf')
 assert response.status_code==200
 assert response.headers['content-type']=='application/pdf'
 assert part_number in response.headers['content-disposition']
 assert response.headers['cache-control']=='no-store'
 assert response.content.startswith(b'%PDF-')
 assert len(response.content)>1000

def test_missing_customer_pdf_is_404():
 assert client.get('/api/reports/NOT-FOUND.pdf').status_code==404


def test_mobile_pdf_ticket_is_short_lived_and_single_use(monkeypatch):
 skus=client.get('/api/catalog/imported-skus').json()['items']
 if not skus: return
 monkeypatch.setenv('CAPABILITY_REQUIRE_AUTH','1')
 now_text=iso(now())
 token=secrets.token_urlsafe(32)
 with auth_connection() as conn:
  org_id=conn.execute("INSERT INTO organizations (name,status,created_at) VALUES ('PDF 测试','approved',?)",(now_text,)).lastrowid
  user_id=conn.execute("INSERT INTO users (organization_id,email,password_hash,role,status,email_verified,created_at) VALUES (?,?,?,'owner','approved',1,?)",
                       (org_id,'pdf-'+secrets.token_hex(6)+'@example.invalid','unused',now_text)).lastrowid
  conn.execute("INSERT INTO licenses (organization_id,seats,expires_at,status,updated_at) VALUES (?,?,?,'active',?)",
               (org_id,1,iso(now()+timedelta(days=1)),now_text))
  conn.execute("INSERT INTO sessions VALUES (?,?,?,?,NULL)",
               (hashlib.sha256(token.encode()).hexdigest(),user_id,now_text,iso(now()+timedelta(hours=1))))
  conn.commit()
 part_number=skus[0]['part_number']
 issued=client.post('/api/reports/mobile-ticket',headers={'Authorization':'Bearer '+token},json={'part_number':part_number})
 assert issued.status_code==200
 ticket=issued.json()['ticket']
 assert ticket!=token and len(ticket)>20
 first=client.get('/api/reports/mobile-download/'+ticket)
 assert first.status_code==200 and first.content.startswith(b'%PDF-')
 assert part_number in first.headers['content-disposition']
 assert first.headers['cache-control']=='no-store'
 assert client.get('/api/reports/mobile-download/'+ticket).status_code==404

def test_home_offers_downloadable_pdf():
 html=client.get('/').text
 assert '下载 PDF 报告' in html
 assert 'downloadCustomerPdf()' in html
 assert 'downloadCustomerPdf(selectedPartNumber)' in html
 assert "encodeURIComponent(ticket.filename)" in html
 assert "link.download=filename" in html
 assert "showInlineReport(html)" in html
 assert "PDF 已下载" not in html
