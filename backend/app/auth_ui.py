"""Chinese account and administrator screens for the local application."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()
STYLE = """body{font:15px/1.55 system-ui,'Microsoft YaHei';background:#f7f8fa;color:#101828;margin:0}.wrap{max-width:920px;margin:40px auto;padding:20px}.panel{background:white;border:1px solid #e4e7ec;border-radius:14px;padding:22px;margin:14px 0}label{display:block;font-weight:650;margin:10px 0}input{display:block;width:100%;padding:10px;border:1px solid #98a2b3;border-radius:8px}button{padding:10px 16px;background:#175cd3;color:white;border:0;border-radius:8px;cursor:pointer;margin:5px}.muted{color:#667085}.ok{color:#067647}.err{color:#b42318}table{width:100%;border-collapse:collapse}th,td{border:1px solid #d0d5dd;padding:7px;text-align:left}th{background:#eaf1fb}a{color:#175cd3}pre{white-space:pre-wrap}"""


def page(title: str, body: str, script: str) -> str:
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{STYLE}</style></head><body><main class="wrap">{body}</main><script>{script}</script></body></html>'''


@router.get("/account", response_class=HTMLResponse)
def account_page():
    body = '''<h1>Capability Advisor 账号</h1><p><a href="/">返回能力顾问</a></p>
<section class="panel"><h2>登录</h2><label>邮箱<input id="lemail" type="email" autocomplete="email"></label><label>密码<input id="lpassword" type="password" autocomplete="current-password"></label><button onclick="login()">登录</button><button onclick="logout()">退出</button><p id="loginstatus" class="muted"></p></section>
<section class="panel"><h2>注册</h2><label>组织名称<input id="org"></label><label>邮箱<input id="remail" type="email" autocomplete="email"></label><label>密码（至少 12 位）<input id="rpassword" type="password" autocomplete="new-password"></label><button onclick="register()">提交注册</button><p id="registerstatus" class="muted"></p></section>
<section class="panel"><h2>重置密码</h2><p class="muted">申请后请从已配置的邮件通道获取 30 分钟有效的一次性令牌。本地开发仅在显式开启开发令牌时显示令牌。</p><label>登记邮箱<input id="resetemail" type="email"></label><button onclick="requestReset()">申请重置</button><label>重置令牌<input id="resettoken"></label><label>新密码（至少 12 位）<input id="newpassword" type="password" autocomplete="new-password"></label><button onclick="confirmReset()">更新密码并撤销旧会话</button><p id="resetstatus" class="muted"></p></section>
<section class="panel"><h2>当前账号</h2><pre id="me">尚未登录</pre><p><a href="/admin">管理员控制台</a></p></section>'''
    script = r'''const $=s=>document.querySelector(s),token=()=>sessionStorage.getItem('cap_token'),headers=()=>({Authorization:'Bearer '+token()});
async function result(r){let d=await r.json().catch(()=>({}));return [d,d.detail||d.message||'请求失败']}
async function login(){let r=await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:$('#lemail').value,password:$('#lpassword').value})}),[d,m]=await result(r);if(r.ok){sessionStorage.setItem('cap_token',d.access_token);$('#loginstatus').className='ok';$('#loginstatus').textContent='登录成功';me()}else{$('#loginstatus').className='err';$('#loginstatus').textContent=m}}
async function register(){let r=await fetch('/api/auth/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({organization_name:$('#org').value,email:$('#remail').value,password:$('#rpassword').value})}),[d,m]=await result(r);$('#registerstatus').className=r.ok?'ok':'err';$('#registerstatus').textContent=r.ok?'注册成功，等待邮箱验证、管理员审批与 License 授权':m}
async function requestReset(){let r=await fetch('/api/auth/password-reset/request',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:$('#resetemail').value})}),[d,m]=await result(r);$('#resetstatus').className=r.ok?'ok':'err';$('#resetstatus').textContent=r.ok?m+(d.development_token?'；开发令牌：'+d.development_token:''):m;if(d.development_token)$('#resettoken').value=d.development_token}
async function confirmReset(){let r=await fetch('/api/auth/password-reset/confirm',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:$('#resettoken').value,new_password:$('#newpassword').value})}),[d,m]=await result(r);$('#resetstatus').className=r.ok?'ok':'err';$('#resetstatus').textContent=r.ok?'密码已更新，所有旧会话已撤销，请重新登录':m;if(r.ok)sessionStorage.removeItem('cap_token')}
async function me(){if(!token())return;let r=await fetch('/api/auth/me',{headers:headers()});$('#me').textContent=r.ok?JSON.stringify(await r.json(),null,2):'会话无效'}
async function logout(){if(token())await fetch('/api/auth/logout',{method:'POST',headers:headers()});sessionStorage.removeItem('cap_token');$('#me').textContent='尚未登录';$('#loginstatus').textContent='已退出'}me();'''
    return page("账号与登录", body, script)


@router.get("/admin", response_class=HTMLResponse)
def admin_page():
    body = '''<h1>管理员控制台</h1><p><a href="/account">账号页</a> · <a href="/">能力顾问</a></p><p id="status" class="muted">使用账号页登录管理员后刷新。</p><section class="panel"><h2>用户审批</h2><div id="users"></div></section><section class="panel"><h2>License 设置</h2><label>组织 ID<input id="orgid" type="number"></label><label>席位<input id="seats" type="number" value="5"></label><label>到期时间<input id="expiry" type="datetime-local"></label><button onclick="saveLicense()">保存 License</button></section><section class="panel"><h2>最近审计</h2><div id="audit"></div></section>'''
    script = r'''const $=s=>document.querySelector(s),token=()=>sessionStorage.getItem('cap_token'),h=()=>({Authorization:'Bearer '+token(),'Content-Type':'application/json'});
async function action(id,type){let r=await fetch('/api/admin/users/'+id+'/'+type,{method:'POST',headers:h()});if(!r.ok)alert((await r.json()).detail);load()}
async function saveLicense(){let exp=new Date($('#expiry').value);if(Number.isNaN(exp.valueOf())){alert('请选择有效到期时间');return}let r=await fetch('/api/admin/licenses',{method:'PUT',headers:h(),body:JSON.stringify({organization_id:Number($('#orgid').value),seats:Number($('#seats').value),expires_at:exp.toISOString()})});alert(r.ok?'License 已保存':(await r.json()).detail);load()}
async function load(){let u=await fetch('/api/admin/users',{headers:h()});if(!u.ok){$('#status').className='err';$('#status').textContent='需要管理员登录';return}let users=(await u.json()).items;$('#status').className='ok';$('#status').textContent='管理员会话有效';$('#users').innerHTML='<table><tr><th>ID</th><th>组织</th><th>邮箱</th><th>状态</th><th>操作</th></tr>'+users.map(x=>`<tr><td>${x.id}</td><td>${x.organization_id||'-'}</td><td>${x.email}</td><td>${x.email_verified?'邮箱已验证':'待验证'} / ${x.status}</td><td><button onclick="action(${x.id},\'verify-email\')">验证邮箱</button><button onclick="action(${x.id},\'approve\')">批准</button></td></tr>`).join('')+'</table>';let a=await fetch('/api/admin/audit?limit=30',{headers:h()}),logs=(await a.json()).items;$('#audit').innerHTML='<table><tr><th>时间</th><th>动作</th><th>对象</th></tr>'+logs.map(x=>`<tr><td>${x.occurred_at}</td><td>${x.action}</td><td>${x.target_type||''} ${x.target_id||''}</td></tr>`).join('')+'</table>'}load();'''
    return page("管理员控制台", body, script)
