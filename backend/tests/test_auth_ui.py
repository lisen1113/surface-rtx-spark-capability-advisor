from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def test_legacy_login_bookmark_redirects_to_account():
 response=client.get('/login.html', follow_redirects=False)
 assert response.status_code == 302
 assert response.headers['location'] == '/account'

def test_account_page_has_login_and_registration():
 html=client.get('/account').text
 assert '登录' in html and '注册' in html and '至少 12 位' in html
 assert '重置密码' in html and '/api/auth/password-reset/request' in html and '/api/auth/password-reset/confirm' in html
 assert '管理员动态验证码' in html and 'mfa_code' in html
 assert 'id="advisorlink" hidden' in html
 assert '进入能力顾问（请在当前标签页打开）' in html
 assert "user.role!=='admin'&&user.status==='approved'&&user.email_verified" in html
 assert "window.location.assign('/')" in html
 assert "$('#advisorlink').hidden=!user" in html
 assert '沪ICP备17029250号-4' in html and 'https://beian.miit.gov.cn/' in html

def test_admin_page_has_approval_license_and_audit():
 html=client.get('/admin').text
 assert '用户审批' in html and 'License 设置' in html and '最近审计' in html
 assert '<th>用户 ID</th><th>组织</th>' in html
 assert 'id="orgid"' in html and '请选择组织' in html
 assert 'x.organization_name' in html and 'escapeHtml(name)' in html
 assert "if(!Number.isInteger(orgId)||orgId<1)" in html
 assert '/api/admin/mfa/enroll' in html and '/api/admin/mfa/confirm' in html
 assert '${escapeHtml(x.email)}' in html and '${escapeHtml(x.action)}' in html
 assert 'id="mfasetup" hidden' in html
 assert "$('#mfasetup').hidden=d.enabled||!d.configured" in html
 assert "x.email_verified?'':" in html
 assert "x.status==='approved'?'':" in html
 assert '沪ICP备17029250号-4' in html
