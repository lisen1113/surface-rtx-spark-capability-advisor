'use strict';
const $ = selector => document.querySelector(selector);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const cny = value => '¥' + Number(value).toLocaleString('zh-CN', {minimumFractionDigits:2, maximumFractionDigits:2});
const displayTime = value => new Intl.DateTimeFormat('zh-CN',{timeZone:'Asia/Shanghai',dateStyle:'short',timeStyle:'short'}).format(new Date(value));
const states = {draft:'预算草稿',pending:'等待内部审核',approved:'已批准，待签发',rejected:'已退回',issued:'已签发正式报价'};
let me = null, hardware = [], products = [], hardwareLines = [], cloudLines = [], activeQuote = null, builderRevision = 0;
let subscriptionOptions = [];
const profileFields = [
 ['company_name','使用公司名称',true],['hk_company_name','香港公司名称（优先提供）',false],['region','注册国家或地区',true],
 ['address','公司地址',true],['phone','公司电话',true],['domain','公司域名',true],['contact_name','负责人姓名',true],
 ['contact_email','负责人邮箱',true],['contracting_company','签约公司（与使用公司相同时可空）',false],
 ['paying_company','付款公司（与使用公司相同时可空）',false],['bank_account_name','公司银行账户名称',true],
 ['bank_name','开户银行',true],['bank_account','公司银行账号',true],['bank_code','银行识别码（如适用）',false],
 ['invoice_title','开票抬头',true],['invoice_registration','税务或商业登记信息',true],['invoice_address','开票地址',true],['invoice_email','收票邮箱',true]
];

function message(text, error=false) {
 $('#message').hidden = false;
 $('#message').className = 'notice ' + (error ? 'error' : 'success');
 $('#message').textContent = text;
 const status=$('#login-status');
 if(status){status.hidden=!error||$('#login-panel').hidden;status.textContent=error?text:'';}
}
async function api(path, options={}) {
 const token = sessionStorage.getItem('cap_token');
 const response = await fetch('/api/' + path, {...options, headers:{...(options.body ? {'Content-Type':'application/json'} : {}), ...(options.headers || {}), ...(token ? {Authorization:'Bearer ' + token} : {})}});
 if (!response.ok) {
  let data; try { data = await response.json(); } catch { data = {}; }
  const detail = typeof data.detail === 'string' ? data.detail : (Array.isArray(data.detail) ? data.detail.map(x => x.loc.slice(1).join('.') + '：' + x.msg).join('\n') : '请求未完成');
  if (response.status === 401) { $('#login-panel').hidden = false; }
  throw Error(detail);
 }
 return response;
}
async function json(path, options={}) { const response=await api(path,options);return response.status===204?{}:response.json(); }
function post(path, body={}) { return json(path, {method:'POST',body:JSON.stringify(body)}); }
function formObject(form) { return Object.fromEntries(new FormData(form)); }
function busy(handler) {
 return async event => {
  event?.preventDefault();
  const button = event?.submitter || (event?.currentTarget?.tagName === 'BUTTON' ? event.currentTarget : null);
  if (button) button.disabled = true;
  try { await handler(event); } catch (error) { message(error.message, true); }
  finally { if (button) button.disabled = false; }
 };
}
const localDate = (days=0) => {
 const parts = new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date());
 const value = Object.fromEntries(parts.map(x => [x.type,x.value]));
 const date = new Date(`${value.year}-${value.month}-${value.day}T00:00:00Z`);
 date.setUTCDate(date.getUTCDate()+days); return date.toISOString().slice(0,10);
};

function renderLines() {
 $('#hardware-lines').innerHTML = hardwareLines.map((line,index) => {
  const item = hardware.find(x => x.part_number === line.part_number);
  return `<tr><td>${esc(line.part_number)}<br>${esc(item?.raw_description || '')}</td><td><input aria-label="设备数量" type="number" min="1" max="100000" value="${line.quantity}" data-hw-qty="${index}"></td><td><button type="button" class="secondary" data-remove-hw="${index}">移除</button></td></tr>`;
 }).join('');
 $('#cloud-lines').innerHTML = cloudLines.map((line,index) => {
  const item = products.find(x => x.product_id === line.product_id);
  return `<tr><td>${esc(item?.name || line.product_id)}<br><span class="tag">${esc(line.user_group || '全体用户')}</span><br><small>USD ${esc(item?.monthly_usd)} / 人 / 月均，年付<br>${esc(item?.prerequisite)}<br>来源日期 ${esc(item?.source_checked_at)}</small></td><td><input aria-label="软件席位" type="number" min="1" max="100000" value="${line.seats}" data-cloud-qty="${index}"></td><td><label><input type="checkbox" data-cloud-confirm="${index}" ${line.eligibility_confirmed?'checked':''}>许可、市场及已有订阅已核验</label><input aria-label="资格核验依据" data-cloud-reference="${index}" value="${esc(line.eligibility_reference)}" placeholder="内部核验记录；预算阶段可空"></td><td><button type="button" class="secondary" data-remove-cloud="${index}">移除</button></td></tr>`;
 }).join('');
 builderRevision++;
}
function addHardware(partNumber, quantity=1) {
 if (!partNumber) throw Error('请先选择设备');
 const existing = hardwareLines.find(x => x.part_number === partNumber);
 if (existing) existing.quantity += quantity; else hardwareLines.push({part_number:partNumber,quantity});
 renderLines();
}
function quoteInput() {
 return {title:$('#project-title').value,term_months:Number($('#term').value),policy_id:$('#policy').value || null,
  hardware:hardwareLines,cloud:cloudLines,usd_cny:$('#fx').value,fx_date:$('#fx-date').value,fx_reference:$('#fx-reference').value,
  cloud_tax_rate:String(Number($('#tax').value)/100),service_once_cny:$('#service-once').value,
  project_discount_cny:$('#discount').value,discount_reason:$('#discount-reason').value,azure_requested:$('#azure-requested').checked,
  renewal:$('#renewal').value,renewal_reference:$('#renewal-reference').value,valid_until:$('#valid-until').value,personas:$('#personas').value};
}
function table(headers, rows) {
 return `<div class="scroll"><table><thead><tr>${headers.map(x=>`<th>${esc(x)}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${row.map(x=>`<td>${esc(x)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
}
function showResult(data, quote=null) {
 activeQuote = quote;
 $('#result-panel').hidden = false;
 $('#result-title').textContent = data.title;
 $('#result-state').textContent = quote ? `${states[quote.state]} · ${quote.formal_number || quote.id}` : '未保存的预算试算';
 $('#result-summary').innerHTML = `<div class="metrics"><div class="metric">项目预计总额<b>${cny(data.total_cny)}</b></div><div class="metric">月均预算<b>${cny(data.average_monthly_cny)}</b></div><div class="metric">设备每月租金<b>${cny(data.hardware_monthly_cny)}</b></div><div class="metric">软件年度付款<b>${cny(data.cloud_annual_cny)}</b></div></div><p>初始付款 ${cny(data.first_payment_cny)}；测算期 ${data.term_months} 个月；整体优惠 ${cny(data.project_discount_cny)}。</p><p class="notice">月均预算供比较，实际按付款计划支付。${data.warnings.map(esc).join(' ')}</p>`;
 let detail = '';
 if (data.hardware.length) detail += '<h3>设备明细</h3>' + table(['设备','配置','数量','单台月租','月租小计'],data.hardware.map(x=>[x.part_number,x.configuration,x.quantity,cny(x.unit_monthly_cny),cny(x.monthly_cny)]));
 if (data.cloud.length) detail += '<h3>订阅明细</h3>' + table(['用户组及软件','席位','USD 标准月均单价','CNY 年付含税','价格版本'],data.cloud.map(x=>[(x.user_group||'全体用户')+' · '+x.name,x.seats,x.standard_unit_monthly_usd,cny(x.annual_due_cny),x.price_version_id]));
 detail += '<details><summary>查看逐月付款计划</summary>' + table(['月份','设备','软件','服务','优惠','应付'], data.payment_schedule.map(x=>[x.month,cny(x.hardware_cny),cny(x.cloud_cny),cny(x.service_cny),cny(x.discount_cny),cny(x.due_cny)])) + '</details>';
 if (data.formal_requirements.length) detail += '<p class="notice">正式报价前需要处理：' + data.formal_requirements.map(esc).join('；') + '</p>';
 detail += `<p class="muted">汇率 ${esc(data.fx.usd_cny)}，${esc(data.fx.date)}，${esc(data.fx.reference)}。有效期至 ${esc(data.valid_until)}。</p>`;
 $('#result-details').innerHTML = detail;
 $('#quote-actions').replaceChildren();
 if (quote) {
  actionButton('下载' + (quote.state === 'issued' ? '正式报价' : '预算方案') + ' PDF', () => downloadPdf(quote));
  actionButton('复制并调整方案', () => loadInputs(quote.id));
  if (['draft','rejected'].includes(quote.state) && ['owner','customer_owner','admin'].includes(me.role)) actionButton('申请正式报价', async () => { const saved = await post(`commercial/quotes/${quote.id}/submit`); showResult(saved.customer,saved); await loadQuotes(); message('已提交内部审核'); });
 }
 $('#result-panel').scrollIntoView({behavior:'smooth',block:'start'});
}
function actionButton(label, handler) {
 const button = document.createElement('button'); button.type='button';button.className='secondary';button.textContent=label;button.addEventListener('click',busy(handler));$('#quote-actions').append(button);
}
async function downloadPdf(quote) {
 const response=await api(`commercial/quotes/${quote.id}/document.pdf`);
 const url=URL.createObjectURL(await response.blob());const link=document.createElement('a');link.href=url;link.download=(quote.formal_number||quote.id)+'.pdf';link.click();setTimeout(()=>URL.revokeObjectURL(url),30000);
}
async function loadInputs(id) {
 const {input} = await json(`commercial/quotes/${id}/inputs`);
 const mappings={title:'project-title',term_months:'term',policy_id:'policy',usd_cny:'fx',fx_date:'fx-date',fx_reference:'fx-reference',service_once_cny:'service-once',project_discount_cny:'discount',discount_reason:'discount-reason',renewal:'renewal',renewal_reference:'renewal-reference',personas:'personas'};
 Object.entries(mappings).forEach(([key,field])=>{$('#'+field).value=input[key]??'';});
 $('#tax').value=Number(input.cloud_tax_rate)*100;$('#valid-until').value=localDate(7);$('#azure-requested').checked=input.azure_requested;
 hardwareLines=input.hardware;cloudLines=input.cloud;renderLines();activeQuote=null;
 $('#builder-panel').scrollIntoView({behavior:'smooth'});message('已复制配置。再次保存将按当前有效价格创建新方案，历史方案保持原快照。');
}
async function loadQuotes() {
 const {items}=await json('commercial/quotes');
 $('#quotes-list').innerHTML=table(['项目','状态','预计总额','创建时间（北京时间）'],items.map(x=>[x.title,states[x.state],cny(x.total_cny),displayTime(x.created_at)]));
 const rows=$('#quotes-list tbody').children;
 items.forEach((item,index)=>{const button=document.createElement('button');button.textContent='打开方案';button.type='button';button.className='secondary';button.addEventListener('click',busy(async()=>{const quote=await json('commercial/quotes/'+item.id);showResult(quote.customer,quote);if(me.role==='admin')await showInternal(item.id);}));rows[index].lastElementChild.append(button);});
}
async function loadCatalog() {
 const [hw,cloud,policies]=await Promise.all([json('commercial/hardware'),json('commercial/products'),json('commercial/policies')]);
 hardware=hw.items;products=cloud.items;
 renderHardwareOptions();
 $('#cloud-select').innerHTML='<option value="">请选择软件</option>'+products.filter(x=>x.kind!=='Included/Metered').map(x=>`<option value="${esc(x.product_id)}">${esc(x.name)} · USD ${esc(x.monthly_usd)} / 月均</option>`).join('');
 $('#policy').innerHTML='<option value="">仅软件时可不选</option>'+policies.items.map(x=>`<option value="${esc(x.id)}">${esc(x.name)}${x.approved_for_formal?'':'（试算）'}</option>`).join('');
 if (!products.length) message('尚无已发布软件价格。请管理员先核验并发布导入的草稿版本。');
}
function renderHardwareOptions() {
 const q=$('#hardware-search').value.toLowerCase();
 const filtered=hardware.filter(x=>(x.part_number+' '+x.raw_description).toLowerCase().includes(q));
 const groups=[...new Set(filtered.map(x=>x.product_type))].sort((a,b)=>a==='Surface 设备'?-1:b==='Surface 设备'?1:a.localeCompare(b));
 $('#hardware-select').innerHTML='<option value="">请选择设备或配件</option>'+groups.map(group=>`<optgroup label="${esc(group)}">${filtered.filter(x=>x.product_type===group).map(x=>`<option value="${esc(x.part_number)}">${esc(x.part_number+' · '+x.raw_description)}</option>`).join('')}</optgroup>`).join('');
}
async function loadProfile() {
 $('#profile-fields').innerHTML=profileFields.map(([name,label,required])=>`<label>${esc(label)}<input name="${name}" ${required?'required':''} type="${name.includes('email')?'email':'text'}" ${name==='bank_account'?'autocomplete="off"':''}></label>`).join('');
 if (!me.organization_id) { $('#profile-panel').hidden=true; return; }
 const {profile}=await json('commercial/profile');
 if(profile)profileFields.forEach(([name])=>{$(`#profile-form [name="${name}"]`).value=profile[name]||'';});
 if(!['owner','customer_owner','admin'].includes(me.role)) { $('#profile-form button').disabled=true;$('#profile-form').querySelectorAll('input').forEach(x=>x.disabled=true); }
}
async function loadAzure() {
 const {items}=await json('commercial/azure/contracts');
 $('#azure-contracts').innerHTML='';$('#usage-contract').innerHTML='';
 for(const item of items) {
  const card=document.createElement('div');card.className='card';
  card.innerHTML=`<h3>${esc(item.service_name)}</h3><p>独立合同 ${esc(item.contract_number)} · 组织 ${item.organization_id}</p><p>${esc(item.meter)} · USD ${esc(item.unit_price_usd)} / ${esc(item.unit)}<br>${esc(item.starts_on)} 至 ${esc(item.ends_on)}</p>`;
  const {items:usage}=await json(`commercial/azure/${item.id}/usage`);
  card.insertAdjacentHTML('beforeend',table(['账期','实际用量','单位','金额 USD'],usage.map(x=>[x.period_start+' 至 '+x.period_end,x.quantity,x.unit,x.amount_usd])));
  $('#azure-contracts').append(card);$('#usage-contract').add(new Option(item.contract_number+' · '+item.meter,item.id));
 }
 if(!items.length)$('#azure-contracts').textContent='暂无已登记的独立合同。';
}
async function loadAdmin() {
 if(me.role!=='admin')return;
 $('#admin-panel').hidden=false;
 await loadRentalRules();
 const configuration=await json('commercial/admin/settings');
 const published=configuration.settings;
 const settingsPolicies=await json('commercial/admin/policies');
 $('#settings-form [name=active_policy_id]').innerHTML='<option value="">不启用设备租赁</option>'+settingsPolicies.items.map(x=>`<option value="${esc(x.id)}">${esc(x.name)}</option>`).join('');
 if(published)for(const key of ['usd_cny','fx_date','fx_reference','cloud_tax_rate','software_cost_factor','active_policy_id'])$('#settings-form').elements[key].value=published[key]??'';
 const [prices,policies,quotes]=await Promise.all([json('commercial/admin/prices'),json('commercial/admin/policies'),json('commercial/quotes')]);
 $('#prices-list').innerHTML=table(['产品','USD 标准价','生效日期','状态','版本'],prices.items.map(x=>[x.payload.name,x.payload.monthly_usd,x.effective_from,x.status,x.id]));
 prices.items.forEach((item,index)=>{
  if(item.status!=='draft')return;
  for(const [label,replace] of [['发布',false],['替换旧版本并发布',true]]) {const button=document.createElement('button');button.type='button';button.className='secondary';button.textContent=label;button.addEventListener('click',busy(async()=>{await post(`commercial/admin/prices/${item.id}/publish?replace=${replace}`);await loadAdmin();await loadCatalog();message('价格版本已发布');}));$('#prices-list tbody').children[index].lastElementChild.append(button);}
 });
 $('#policies-list').innerHTML=table(['政策','计价方式','Surface ERP 成本比例','正式用途'],policies.items.map(x=>[x.name,x.calculation_method==='fixed-term-v1'?'固定 1.15 / 1.30 / 1.45':'历史资金现值法',x.surface_erp_cost_factor??'1',x.approved_for_formal?'已确认':'仅试算']));
 $('#admin-review').innerHTML='';
 for(const quote of quotes.items.filter(x=>['pending','approved'].includes(x.state))) {
  const button=document.createElement('button');button.type='button';button.className='secondary';button.textContent=`审核 ${quote.title} · ${states[quote.state]}`;button.addEventListener('click',busy(()=>showInternal(quote.id)));$('#admin-review').append(button);
 }
}
async function loadRentalRules(){
 const data=await json('commercial/admin/rental-rules'),rules=data.active_rules||data.defaults,form=$('#rental-rules-form');
 const percent=value=>String(Number((Number(value)*100).toFixed(4)));
 form.elements.name.value=rules.name;form.elements.surface_erp_cost_percent.value=percent(rules.surface_erp_cost_factor);form.elements.terms_reference.value=rules.terms_reference;form.elements.approved_for_formal.checked=rules.approved_for_formal;
 $('#rental-brand-rows').innerHTML=[['Surface','Surface'],['Apple','苹果 Apple'],['Think','ThinkPad / ThinkBook / Think'],['RTX Spark','Laptop Ultra（RTX Spark）']].map(([key,label])=>{const rates=rules.residual_by_brand[key]||data.defaults.residual_by_brand[key];return `<tr><th>${label}</th>${[12,24,36].map(n=>`<td><input aria-label="${key} ${n} 月残值百分比" name="${key}_${n}" type="number" min="0" max="100" step="0.0001" required value="${percent(rates['months_'+n])}"></td>`).join('')}</tr>`;}).join('');
 $('#rental-rules-status').textContent=(data.active_rules?'当前已应用此规则；修改后保存将生成新版本。':'当前仍使用历史规则；保存后切换为文档中的常规租赁公式。')+(data.active_rules&&!rules.residual_by_brand['RTX Spark']?' RTX Spark 暂按通用残值试算，请核对并保存独立参数。':'');
}
async function showInternal(id) {
 const quote=await json(`commercial/admin/quotes/${id}`);const internal=quote.internal;
 const target=$('#admin-review');let card=$('#internal-active');if(card)card.remove();card=document.createElement('div');card.id='internal-active';card.className='card';
 card.innerHTML=`<h3>${esc(quote.customer.title)} · 组织 ${quote.organization_id}</h3><p>${esc(states[quote.state])} · ${esc(quote.id)}</p><p>${esc(internal.metric_basis)}</p>`;
 card.insertAdjacentHTML('beforeend',table(['内部指标','值'],[['软件成本系数',internal.software_cost_factor],['软件年度成本 CNY',internal.software_annual_cost_cny],['软件年度标准毛利 CNY',internal.software_annual_gross_profit_cny],['项目现金贡献 CNY',internal.contribution_before_service_cost_and_hardware_tax_cny],['现金贡献率',internal.contribution_rate],['低于政策门槛',internal.below_policy_margin?'是，审批需说明':'否'],['基准 NPV',internal.baseline.npv_cny],['年化项目 IRR',internal.baseline.annual_irr??'无唯一可用值'],['最大资金占用',internal.baseline.maximum_funding_cny],['回本月份',internal.baseline.payback_month??'测算期内未回本'],['零残值压力 NPV',internal.stress.npv_cny]]));
 card.insertAdjacentHTML('beforeend',table(['设备','ERP 原价','成本比例','折后采购成本','计价系数','残值比例','数量','来源行','净残值'],internal.hardware.map(x=>[x.part_number,x.erp_unit_cost_cny,x.erp_cost_factor??'1',x.effective_unit_cost_cny??x.erp_unit_cost_cny,x.term_multiplier??'历史政策',x.residual_rate??'历史政策',x.quantity,x.source_row,x.residual_cny])));
 if(quote.customer.formal_requirements.length)card.insertAdjacentHTML('beforeend','<p class="notice error">'+quote.customer.formal_requirements.map(esc).join('；')+'</p>');
 if(quote.profile)card.insertAdjacentHTML('beforeend',table(['客户资料','值'],Object.entries(quote.profile)));
 const profileButton=document.createElement('button');profileButton.type='button';profileButton.className='secondary';profileButton.textContent='核验银行及开票资料（内部）';profileButton.addEventListener('click',busy(async()=>{const {profile}=await json(`commercial/admin/profiles/${quote.organization_id}`);const values=profileFields.map(([key,label])=>[label,profile[key]||'未填写']);const detail=document.createElement('details');detail.open=true;detail.innerHTML='<summary>受限公司资料</summary>'+table(['资料','值'],values);card.append(detail);profileButton.disabled=true;}));card.append(profileButton);
 if(quote.state==='pending') {
  const form=document.createElement('form');form.innerHTML='<label>审批说明<textarea name="reason" required minlength="2"></textarea></label><label>正式商务依据<textarea name="commercial_reference" placeholder="供应方法定信息、付款与归还条款、提前终止及损坏责任、税务、软件资格、服务成本和跨年锁价依据"></textarea></label><label>决定<select name="decision"><option value="reject">退回补充</option><option value="approve">批准</option></select></label><button>提交审批</button>';
  form.addEventListener('submit',busy(async()=>{await post(`commercial/admin/quotes/${id}/review`,formObject(form));await loadQuotes();await showInternal(id);message('审批已记录');}));card.append(form);
 }
 if(quote.state==='approved'){const button=document.createElement('button');button.type='button';button.textContent='签发正式报价并固化 PDF';button.addEventListener('click',busy(async()=>{const issued=await post(`commercial/admin/quotes/${id}/issue`);showResult(issued.customer,issued);await loadQuotes();await loadAdmin();message('已签发正式报价');}));card.append(button);}
 target.append(card);$('#admin-panel').scrollIntoView({behavior:'smooth'});
}
async function start() {
 try { me=await json('auth/me'); }
 catch { $('#identity').textContent='请登录已有账号';$('#login-panel').hidden=false;$('#workspace').hidden=true;return; }
 if(me.role!=='admin') {$('#identity').textContent='此入口仅限管理员。客户选型无需登录，请进入客户页面。';$('#login-panel').hidden=false;$('#workspace').hidden=true;return;}
 $('#identity').textContent=me.email+' · 管理员';$('#admin-logout').hidden=false;
 $('#login-panel').hidden=true;$('#workspace').hidden=false;
 $('#builder-panel').hidden=true;$('#profile-panel').hidden=true;
 await loadCatalog();await loadQuotes();await loadAzure();await loadAdmin();
}
$('#admin-logout').onclick=busy(async()=>{await post('auth/logout');sessionStorage.removeItem('cap_token');location.reload();});
$('#valid-until').value=localDate(7);$('#fx-date').value=localDate();
$('#settings-form').addEventListener('submit',busy(async event=>{const payload=formObject(event.currentTarget);payload.active_policy_id=payload.active_policy_id||null;await json('commercial/admin/settings',{method:'PUT',body:JSON.stringify(payload)});message('已发布参数，客户页面的新预算会使用此配置。');}));
$('#rental-rules-form').addEventListener('submit',busy(async event=>{const form=event.currentTarget;const payload={name:form.elements.name.value,surface_erp_cost_factor:(Number(form.elements.surface_erp_cost_percent.value)/100).toFixed(6),terms_reference:form.elements.terms_reference.value,approved_for_formal:form.elements.approved_for_formal.checked,residual_by_brand:{}};for(const brand of ['Surface','Apple','Think','RTX Spark'])payload.residual_by_brand[brand]=Object.fromEntries([12,24,36].map(n=>['months_'+n,(Number(form.elements[brand+'_'+n].value)/100).toFixed(6)]));await json('commercial/admin/rental-rules',{method:'PUT',body:JSON.stringify(payload)});await loadCatalog();await loadAdmin();message('租赁规则已保存并应用，客户新预算会使用新残值与 ERP 成本折扣。');}));
$('#login-form').addEventListener('submit',busy(async event=>{const form=event.currentTarget;const payload=formObject(form);if(!payload.mfa_code)delete payload.mfa_code;const result=await post('auth/login',payload);sessionStorage.setItem('cap_token',result.access_token);form.reset();await start();message('登录成功');}));
$('#customer-register-form').addEventListener('submit',busy(async event=>{const form=event.currentTarget;const payload=formObject(form);payload.accepted_terms=form.elements.accepted_terms.checked;payload.accepted_privacy=form.elements.accepted_privacy.checked;await post('commercial/register',payload);form.reset();message('客户组织注册已提交。请在账号页完成邮箱验证，等待管理员审批及组织授权后登录。');}));
$('#hardware-search').addEventListener('input',renderHardwareOptions);
$('#add-hardware').addEventListener('click',busy(()=>addHardware($('#hardware-select').value,Number($('#hardware-quantity').value))));
$('#add-cloud').addEventListener('click',busy(()=>{const id=$('#cloud-select').value;if(!id)throw Error('请先选择软件');const group=$('#cloud-group').value.trim()||'全体用户';if(cloudLines.some(x=>x.product_id===id&&(x.user_group||'全体用户')===group))throw Error('已添加此软件，请直接修改席位数');cloudLines.push({product_id:id,user_group:group,seats:Number($('#cloud-seats').value),eligibility_confirmed:false,eligibility_reference:''});renderLines();}));
$('#builder-form').addEventListener('input',()=>builderRevision++);
$('#builder-form').addEventListener('change',event=>{
 const node=event.target;
 if(node.dataset.hwQty!==undefined)hardwareLines[Number(node.dataset.hwQty)].quantity=Number(node.value);
 if(node.dataset.cloudQty!==undefined)cloudLines[Number(node.dataset.cloudQty)].seats=Number(node.value);
 if(node.dataset.cloudConfirm!==undefined)cloudLines[Number(node.dataset.cloudConfirm)].eligibility_confirmed=node.checked;
 if(node.dataset.cloudReference!==undefined)cloudLines[Number(node.dataset.cloudReference)].eligibility_reference=node.value;
});
$('#builder-form').addEventListener('click',event=>{const hw=event.target.closest('[data-remove-hw]'),cloud=event.target.closest('[data-remove-cloud]');if(hw){hardwareLines.splice(Number(hw.dataset.removeHw),1);renderLines();}if(cloud){cloudLines.splice(Number(cloud.dataset.removeCloud),1);renderLines();}});
$('#builder-form').addEventListener('submit',busy(async()=>showResult(await post('commercial/estimate',quoteInput()))));
$('#save-quote').addEventListener('click',busy(async()=>{if(!$('#builder-form').reportValidity())return;const saved=await post('commercial/quotes',quoteInput());showResult(saved.customer,saved);await loadQuotes();message('方案已保存，报价价格快照已固定');}));
$('#recommend').addEventListener('click',busy(async()=>{const {items,note}=await post('commercial/recommendations',{min_memory_gb:Number($('#min-memory').value),product_type:$('#recommend-type').value});$('#recommend-results').innerHTML=items.map(x=>`<article class="card"><span class="tag">${esc(x.tier)}</span><h3>${esc(x.part_number)}</h3><p>${esc(x.configuration)}</p><p class="muted">${esc(x.reason)}</p><button type="button" data-candidate="${esc(x.part_number)}">加入方案</button></article>`).join('')+'<p class="muted wide">'+esc(note)+'</p>';}));
$('#recommend-results').addEventListener('click',busy(event=>{const node=event.target.closest('[data-candidate]');if(node)addHardware(node.dataset.candidate);}));
$('#compare-cloud').addEventListener('click',busy(async()=>{
 const result=await post('commercial/cloud-recommendations',{users:Number($('#software-users').value),copilot_users:Number($('#copilot-users').value),desktop_office:$('#need-desktop').checked,security_management:$('#need-security').checked,existing_qualifying_base:$('#existing-base').checked});
 subscriptionOptions=result.items;
 $('#cloud-comparison').innerHTML=result.items.map((x,index)=>`<article class="card"><h3>${esc(x.label)}</h3><p>USD ${esc(x.annual_usd)} / 年<br>USD ${esc(x.monthly_average_usd)} / 月均</p><p>${x.products.map(p=>esc(p.name)).join('<br>')}</p><p class="muted">${esc(x.qualification)}</p><button type="button" data-subscription-option="${index}">使用此组合替换软件明细</button></article>`).join('')+'<p class="muted wide">'+esc(result.note)+'</p>';
}));
$('#cloud-comparison').addEventListener('click',busy(event=>{const node=event.target.closest('[data-subscription-option]');if(node){cloudLines=subscriptionOptions[Number(node.dataset.subscriptionOption)].lines.map(x=>({...x}));renderLines();message('已更新软件组合，请核对席位及许可资格后计算预算');}}));
$('#profile-form').addEventListener('submit',busy(async event=>{await json('commercial/profile',{method:'PUT',body:JSON.stringify(formObject(event.currentTarget))});message('公司资料已加密保存');}));
$('#reload-quotes').addEventListener('click',busy(loadQuotes));$('#reload-azure').addEventListener('click',busy(loadAzure));
$('#price-form').addEventListener('submit',busy(async event=>{const payload=formObject(event.currentTarget);payload.components=payload.components.split(',').map(x=>x.trim()).filter(Boolean);payload.seat_limit=payload.seat_limit?Number(payload.seat_limit):null;payload.effective_to=payload.effective_to||null;await post('commercial/admin/prices',payload);await loadAdmin();message('草稿价格已保存，尚未发布');}));
$('#policy-form').addEventListener('submit',busy(async event=>{const payload=formObject(event.currentTarget);payload.approved_for_formal=event.currentTarget.elements.approved_for_formal.checked;await post('commercial/admin/policies',payload);await loadCatalog();await loadAdmin();message('新政策版本已保存');}));
$('#azure-form').addEventListener('submit',busy(async event=>{const payload=formObject(event.currentTarget);const org=payload.organization_id;delete payload.organization_id;await post(`commercial/admin/azure/${org}/contracts`,payload);await loadAzure();message('独立合同已登记，不会自动开通 Azure 资源');}));
$('#usage-form').addEventListener('submit',busy(async event=>{const payload=formObject(event.currentTarget);const contract=payload.contract_id;delete payload.contract_id;await post(`commercial/admin/azure/${contract}/usage`,payload);await loadAzure();message('用量已记录，USD 账单已计算');}));
$('#load-audit').addEventListener('click',busy(async()=>{const {items}=await json('commercial/admin/audit');$('#audit-list').innerHTML=table(['时间（北京时间）','操作人','组织','操作','对象'],items.map(x=>[displayTime(x.occurred_at),x.actor,x.organization_id,x.action,x.target_id]));}));
busy(start)();

