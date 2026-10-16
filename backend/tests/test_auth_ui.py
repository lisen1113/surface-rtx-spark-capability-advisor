from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def test_account_page_has_login_and_registration():
 html=client.get('/account').text
 assert '登录' in html and '注册' in html and '至少 12 位' in html
 assert '重置密码' in html and '/api/auth/password-reset/request' in html and '/api/auth/password-reset/confirm' in html
 assert '管理员动态验证码' in html and 'mfa_code' in html

def test_admin_page_has_approval_license_and_audit():
 html=client.get('/admin').text
 assert '用户审批' in html and 'License 设置' in html and '最近审计' in html
 assert '/api/admin/mfa/enroll' in html and '/api/admin/mfa/confirm' in html
 assert '${escapeHtml(x.email)}' in html and '${escapeHtml(x.action)}' in html
