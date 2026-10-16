"""Chinese-first local advisor UI backed by the imported V3.4 workbook."""
from fastapi import APIRouter, Response
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def index(response: Response):
 response.headers["Cache-Control"] = "no-store"
 return r'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Surface / RTX Spark PC Capability Advisor V3.0</title><style>
:root{--ink:#101828;--muted:#667085;--line:#e4e7ec;--blue:#175cd3;--pale:#eff4ff;--amber:#b54708}*{box-sizing:border-box}body{margin:0;background:#f7f8fa;color:var(--ink);font:15px/1.55 system-ui,'Microsoft YaHei',sans-serif}.top{background:#0b1220;color:white;padding:34px 24px}.wrap{max-width:1180px;margin:auto}.eyebrow{color:#9db7ff;font-weight:700;letter-spacing:.08em}h1{margin:.3rem 0;font-size:clamp(25px,4vw,38px)}h2{font-size:22px;margin:0 0 14px}h3{font-size:17px;margin:14px 0 8px}.sub{color:#cbd5e1;max-width:820px}.bar{background:white;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:2}.bar .wrap{display:flex;gap:12px;align-items:center;padding:14px 24px}.bar label{font-weight:700}.bar select{flex:1;max-width:650px;padding:11px;border:1px solid #98a2b3;border-radius:8px;background:white}main{padding:24px}.panel{background:white;border:1px solid var(--line);border-radius:14px;padding:20px;margin-bottom:18px;box-shadow:0 1px 2px #1018280a}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin:12px 0}.grid[hidden]{display:none}.metric{background:#f9fafb;border-radius:10px;padding:14px}.metric b{display:block;font-size:17px}.tabs{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}.tabs button{padding:9px 14px;border:1px solid #b2c5e8;border-radius:999px;background:white;color:#1849a9;cursor:pointer}.tabs button.active{background:var(--blue);color:white;border-color:var(--blue)}.card{border:1px solid var(--line);border-radius:10px;padding:14px;margin:10px 0}.card p{margin:5px 0}.tag{display:inline-block;background:var(--pale);color:#1849a9;padding:2px 8px;border-radius:999px;margin:2px 5px 2px 0;font-size:12px}.warn{color:var(--amber)}.empty{padding:28px;text-align:center;color:var(--muted);border:1px dashed #b9c1cc;border-radius:10px}.status{color:var(--muted)}footer{text-align:center;color:var(--muted);padding:30px}@media(max-width:650px){.bar .wrap{align-items:stretch;flex-direction:column}.bar select{max-width:none}main{padding:14px}}
</style><style>.bar #tco-shortcut{background:#175cd3;color:white;border:0;border-radius:8px;padding:10px 14px;font-weight:700;cursor:pointer;white-space:nowrap}@media(max-width:650px){.bar #tco-shortcut{width:100%}}.print-only{display:none}@media print{body.printing-tco{background:white;color:#111;font-size:10pt}body.printing-tco .top,body.printing-tco .bar,body.printing-tco footer,body.printing-tco main>.panel:not(#tco-panel),body.printing-tco #tco-panel .tabs,body.printing-tco #tco-panel button,body.printing-tco #tco-fields,body.printing-tco .print-hint{display:none!important}body.printing-tco main{padding:0;max-width:none}body.printing-tco #tco-panel,body.printing-tco #tco-panel .card{border:0;box-shadow:none;padding:0;margin:0}body.printing-tco .print-only{display:block}body.printing-tco .metric{break-inside:avoid}body.printing-tco a{color:#111}@page{size:A4;margin:16mm}}</style></head><body><header class="top"><div class="wrap"><div class="eyebrow">V3.0 本地能力顾问</div><h1>Surface Laptop Ultra 能力映射</h1><div class="sub">按真实 Part Number 查看配置、AI 模型、游戏、生成式 AI 与生产力映射。所有结论保留证据等级和限制，不把平台宣传转换为 SKU 实测。</div></div></header>
<div class="bar"><div class="wrap"><label for="sku">选择产品配置</label><select id="sku"><option>正在载入 V3.4 数据…</option></select><span id="load" class="status"></span></div></div><main class="wrap"><section class="panel"><h2>按使用需求推荐产品</h2><p class="status">先选用途，也可以用自己的话描述。系统会合并已识别的需求，给出可比较的 Surface Laptop Ultra 候选；具体软件、游戏和模型仍需验证。</p><form id="needform"><fieldset><legend>主要用途（可多选）</legend><label><input type="checkbox" name="usage" value="ai"> 本地 AI 模型</label>　<label><input type="checkbox" name="usage" value="gaming"> 游戏</label>　<label><input type="checkbox" name="usage" value="generation"> 图像/视频生成</label>　<label><input type="checkbox" name="usage" value="productivity"> 生产力</label></fieldset><div id="need-ai-fields" class="grid" hidden><label>模型名称（可选）<input id="need-model-name" maxlength="120" placeholder="例如 Qwen3"></label><label>模型规模<select id="need-ai"><option value="unsure">尚不确定</option><option>8B</option><option>32B</option><option>70B</option><option>120B</option></select></label></div><div id="need-game-fields" class="grid" hidden><label>具体游戏（可多款）<input id="need-game-titles" maxlength="240" placeholder="例如 CS2、赛博朋克 2077"></label><label>游戏类型<select id="need-game"><option value="unsure">尚不确定</option><option value="esports">电竞/网游</option><option value="aaa">3A 大型游戏</option></select></label><label>目标分辨率<select id="need-resolution"><option value="unsure">尚不确定</option><option>1080p</option><option>1440p</option><option>4K</option></select></label><label>目标 FPS<input id="need-fps" type="number" min="1" max="500" placeholder="例如 60"></label></div><div id="need-work-fields" class="grid" hidden><label>软件名称与版本（可选）<input id="need-software" maxlength="120" placeholder="例如 Premiere Pro"></label><label>生产力工作负载<select id="need-work"><option value="unsure">尚不确定</option><option value="office">日常办公</option><option value="coding">编程开发</option><option value="video">视频剪辑</option><option value="cad">CAD / 3D</option></select></label></div><div class="grid"><label>预算上限（元，可留空）<input id="need-budget" type="number" min="1" step="1" placeholder="例如 40000"></label></div><p><label for="need-description">自由描述</label><br><textarea id="need-description" rows="3" maxlength="2000" style="width:100%;padding:10px;border:1px solid #98a2b3;border-radius:8px" placeholder="例如：要玩 3A 游戏，也希望本地运行 70B 模型，用于编程和客户演示"></textarea></p><button type="submit">查找合适配置</button></form><div id="need-result" aria-live="polite"></div></section><section class="panel"><h2 id="product">产品概览</h2><p><a href="#" onclick="openCustomerReport();return false">打开可打印客户报告</a></p><div id="metrics" class="grid"></div></section>
<section class="panel" id="tco-panel"><div class="tabs" id="tabs"><button data-tab="ai" class="active">AI 模型</button><button data-tab="gaming">游戏</button><button data-tab="generation">生成式 AI</button><button data-tab="productivity">生产力</button><button data-tab="deployment">模型部署</button><button data-tab="faq">AI FAQ</button><button data-tab="tco">TCO 成本</button><button data-tab="evidence">证据与限制</button></div><div id="content"></div></section>
<section class="panel"><h2>数据说明</h2><p>当前页面读取授权 V3.4 工作簿。空白 Token/s、FPS 或实测字段保持未知；经验推荐不会显示为官方测试。</p><p><a href="/account">账号注册与登录</a> · <a href="/admin">管理员控制台</a> · <a href="/docs">API 文档</a> · <a href="/api/catalog/imported-skus">SKU 数据</a> · <a href="/api/catalog/sources">来源台账</a></p></section></main><footer>© 2026 上海以和信息技术有限公司。保留所有权利。<br><small>Microsoft、Surface、NVIDIA、RTX 等商标归各自权利人所有。微软商用 Surface 授权 ADR 身份发布前核实。</small></footer>
<style>
.top .wrap::before,body>footer::before{content:"";display:block;width:min(270px,78vw);height:90px;background:#fff url('/assets/yihe-logo.png') center/contain no-repeat;border-radius:8px;margin:0 0 18px}
body>footer::before{width:165px;height:55px;margin:0 auto 12px}
.tco-brandmark{background:#fff url('/assets/yihe-logo.png') center/contain no-repeat!important;width:160px!important;height:58px!important;border-radius:0!important;font-size:0!important}
.tco-report-footer::before,.tco-report-footer strong{display:none!important}
.spec-scroll{overflow-x:auto;margin:14px 0}.spec-table{width:100%;border-collapse:collapse;min-width:760px;font-size:14px;line-height:1.5}.spec-table th,.spec-table td{border:1px solid var(--line);padding:11px 12px;text-align:left;vertical-align:top}.spec-table thead th{background:#eaf1fb;color:#1849a9}.spec-table tbody th{background:#f9fafb;width:15%}.spec-table td{width:28%}.spec-table tr:hover td{background:#fbfcff}.spec-table .status{font-weight:400}
@media print{.tco-brandmark{width:130px!important;height:48px!important}}
</style><script>
const $=s=>document.querySelector(s);let data=null,tab='ai';const text=v=>(v===null||v===undefined||v==='')?'未知':String(v);const escapeHtml=v=>text(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));const metric=(k,v)=>`<div class="metric"><span class="status">${k}</span><b>${text(v)}</b></div>`;
const fetch=(url,options={})=>{const token=sessionStorage.getItem('cap_token');return window.fetch(url,{...options,headers:{...(options.headers||{}),...(token?{Authorization:'Bearer '+token}:{})}})};
async function openCustomerReport(){
 if(!data)return;
 const reportWindow=window.open('','_blank');
 if(!reportWindow){alert('浏览器拦截了报告窗口，请允许本站打开新窗口。');return}
 reportWindow.document.title='正在生成客户报告';
 try{
  const response=await fetch('/api/reports/'+encodeURIComponent(data.sku.part_number)+'.html');
  if(!response.ok)throw Error(response.status===401?'请先在账号页登录':response.status===403?'请确认组织 License 有效':'报告生成失败');
  reportWindow.document.open();reportWindow.document.write(await response.text());reportWindow.document.close();
 }catch(error){reportWindow.document.body.textContent=error.message}
}
// The TCO tab retains its own print action; the duplicate selector-bar shortcut was removed.
let lastNeedBody=null;
async function findProducts(event){
 event.preventDefault();
 const budget=$('#need-budget').value;
 const body={usages:[...document.querySelectorAll('input[name="usage"]:checked')].map(x=>x.value),ai_size:$('#need-ai').value,game_need:$('#need-game').value,work_need:$('#need-work').value,generation_need:$('#need-generation').value,model_name:$('#need-model-name').value,game_titles:$('#need-game-titles').value,target_resolution:$('#need-resolution').value,target_fps:$('#need-fps').value?Number($('#need-fps').value):null,software_name:$('#need-software').value,budget_cny:budget?Number(budget):null,prefer_lower_price:$('#need-priority').value==='price',description:$('#need-description').value};
 const target=$('#need-result');lastNeedBody=null;target.innerHTML='<p class="status">正在匹配已导入产品…</p>';
 try{
  const r=await fetch('/api/recommendations',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}),d=await r.json();
  if(!r.ok)throw Error(d.detail||'推荐请求失败');
  if(d.status==='needs_input'){target.innerHTML=`<p class="warn">${escapeHtml(d.message)}</p>`;return}
  lastNeedBody=body;
  const interpreted=d.interpreted_need;
  const labels={ai:'本地 AI 模型',gaming:'游戏',generation:'生成式 AI',productivity:'生产力'};
  target.innerHTML=`<h3>需求档案</h3><p>用途：${escapeHtml(interpreted.usages.map(x=>labels[x]||x).join(' + '))}；模型：${escapeHtml(interpreted.ai_size)}；工程筛选内存档：${escapeHtml(interpreted.minimum_memory_tier_gb)} GB</p>`+d.reasoning.map(x=>`<p class="status">${escapeHtml(x)}</p>`).join('')+d.needs_confirmation.map(x=>`<p class="warn">待确认：${escapeHtml(x)}</p>`).join('')+`<h3>产品候选（${d.items.length}）</h3>`+(d.items.length?d.items.map(x=>`<article class="card"><h3>${escapeHtml(x.part_number)} · ${escapeHtml(x.platform_code)} · ${escapeHtml(x.memory_gb)}GB</h3><p>存储 ${escapeHtml(x.storage_tb)}TB · 导入价格 ${x.price_cny===null?'未知':'¥'+Number(x.price_cny).toLocaleString()} ${x.over_budget?'· 超出预算':''}</p><p>${escapeHtml(x.reason)}</p><span class="tag">${escapeHtml(x.evidence_level)}</span><p><button type="button" data-pn="${escapeHtml(x.part_number)}">查看此配置的详细能力并生成报告</button></p></article>`).join(''):'<div class="empty">当前导入产品中没有匹配候选。</div>')+`<p class="status">${escapeHtml(d.limitations||'')}</p><div id="need-report-output" aria-live="polite"></div>`;
 }catch(e){target.innerHTML=`<p class="warn">${escapeHtml(e.message)}</p>`}
}
const generationFields=document.createElement('div');generationFields.id='need-generation-fields';generationFields.className='grid';generationFields.hidden=true;generationFields.innerHTML='<label>生成工作流<select id="need-generation"><option value="unsure">尚不确定</option><option value="image">图像生成</option><option value="video">视频生成</option></select></label>';$('#needform').insertBefore(generationFields,$('#need-budget').parentElement.parentElement);
const priorityField=document.createElement('label');priorityField.innerHTML='推荐排序<select id="need-priority"><option value="price">优先控制采购价</option><option value="capacity">优先更大内存</option></select>';$('#need-budget').parentElement.parentElement.appendChild(priorityField);
function updateNeedFields(){let chosen=new Set([...document.querySelectorAll('input[name="usage"]:checked')].map(x=>x.value));$('#need-ai-fields').hidden=!chosen.has('ai');$('#need-game-fields').hidden=!chosen.has('gaming');$('#need-work-fields').hidden=!chosen.has('productivity');$('#need-generation-fields').hidden=!chosen.has('generation');if(!chosen.has('ai')){$('#need-ai').value='unsure';$('#need-model-name').value=''}if(!chosen.has('gaming')){$('#need-game').value='unsure';$('#need-game-titles').value='';$('#need-resolution').value='unsure';$('#need-fps').value=''}if(!chosen.has('productivity')){$('#need-work').value='unsure';$('#need-software').value=''}if(!chosen.has('generation'))$('#need-generation').value='unsure'}
document.querySelectorAll('input[name="usage"]').forEach(x=>x.addEventListener('change',updateNeedFields));$('#needform').addEventListener('submit',findProducts);
let activeNeedReportHtml='',activeNeedReportName='';
function openNeedReportPrintWindow(){
 if(!activeNeedReportHtml)return;
 const reportWindow=window.open('','_blank');
 if(!reportWindow){alert('浏览器拦截了报告窗口。请允许本站打开新窗口后重试。');return}
 reportWindow.document.open();reportWindow.document.write(activeNeedReportHtml);reportWindow.document.close();
 reportWindow.document.title=activeNeedReportName;
 reportWindow.focus();
}
async function showNeedReport(partNumber){
 const output=$('#need-report-output');if(!output||!lastNeedBody)return;
 output.innerHTML='<p class="status">正在生成此配置与本次需求的完整报告…</p>';
 try{
  const r=await fetch('/api/reports/recommendation',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...lastNeedBody,part_number:partNumber})});
  if(!r.ok){const error=await r.json();throw Error(typeof error.detail==='string'?error.detail:'报告生成失败')}
  const html=await r.text();
  $('#sku').value=partNumber;await choose(partNumber);
  const reportName='按描述需求配置报告-'+String(partNumber).replace(/[^A-Za-z0-9-]/g,'-');
  activeNeedReportHtml=html;activeNeedReportName=reportName;
  output.innerHTML='<h3>此配置与本次需求的匹配报告</h3><p><button type="button" id="need-report-print">打开独立报告页并打印／另存为 PDF</button></p><p class="status">独立报告页的 PDF 文件名：'+escapeHtml(reportName)+'.pdf（保存时可按需修改）</p>';
  const frame=document.createElement('iframe');frame.title=reportName;frame.style.cssText='width:100%;min-height:900px;border:1px solid #d0d5dd;border-radius:10px;background:white';
  frame.addEventListener('load',()=>{try{frame.style.height=Math.max(900,frame.contentDocument.documentElement.scrollHeight+30)+'px'}catch(_){}});
  output.appendChild(frame);frame.srcdoc=html;
  $('#need-report-print').addEventListener('click',openNeedReportPrintWindow);
  output.scrollIntoView({behavior:'smooth',block:'start'});
 }catch(e){output.textContent='无法生成报告：'+e.message}
}
$('#need-result').addEventListener('click',e=>{const button=e.target.closest('button[data-pn]');if(button)showNeedReport(button.dataset.pn)});
function cards(items){
 if(!items||!items.length)return '<div class="empty">该 SKU 暂无已验证的直接映射；请查看经验推荐与证据限制。</div>';
 return items.map(x=>{
  let title=x['目标模型/场景']||x['游戏名称']||x['推荐模型/工作负载名称']||x['软件/工作负载']||x['推荐定位']||x['推荐游戏类型']||'能力记录';
  let e=x['证据等级']||x['证据类型']||x['数据类型（官方/实测/估算）']||'未知';
  let result=x['本地运行判断']||x['兼容性状态']||x['经验推荐与我的判断']||x['实测结果']||x['内存适配判断']||x['推荐等级']||'待验证';
  let official=x['官方能力/平台声明']||'';
  let engineering=x['经验推荐与我的判断']||'';
  let perf=x['预计输出速度_Token/s']||x['平均FPS']||x['官方基准结果']||x['性能指标'];
  let note=x['备注']||x['依据与限制']||x['兼容性风险与销售话术']||x['兼容性/风险']||'';
  let source=x['官方来源URL']||x['来源/链接']||x['Benchmark来源/链接']||'';
  return `<article class="card"><h3>${text(title)}</h3><span class="tag">${text(e)}</span><span class="tag">${text(x['数据状态']||'数据记录')}</span><p><b>判断：</b>${text(result)}</p>${official?`<p><b>官方资料：</b>${text(official)}</p>`:''}${engineering&&engineering!==result?`<p><b>工程建议：</b>${text(engineering)}</p>`:''}${perf?`<p><b>性能：</b>${text(perf)}</p>`:''}${note?`<p class="status"><b>限制：</b>${text(note)}</p>`:''}${source?`<p><a href="${source.split(' ; ')[0]}" target="_blank" rel="noopener">查看官方来源</a></p>`:''}</article>`
 }).join('')
}
function tcoForm(s){return `<style id="tco-report-style">@media print{
body.printing-tco{font-family:system-ui,'Microsoft YaHei',sans-serif;font-size:10pt;line-height:1.5;-webkit-print-color-adjust:exact;print-color-adjust:exact}
body.printing-tco #tco-panel .card{max-width:none;padding-bottom:18mm}
body.printing-tco .tco-screen-title,body.printing-tco .tco-screen-intro,body.printing-tco #tco-status,body.printing-tco .tco-screen-source{display:none!important}
body.printing-tco .tco-report-header{display:flex!important;align-items:center;gap:14px;border-bottom:2px solid #175cd3;padding:0 0 14px;margin-bottom:22px}
body.printing-tco .tco-brandmark{width:52px;height:52px;border-radius:12px;background:#142b55;color:#fff;font-size:20px;font-weight:800;display:grid;place-items:center;flex:none}
body.printing-tco .tco-report-header h2{font-size:22pt;line-height:1.2;margin:4px 0}body.printing-tco .tco-report-header p{margin:2px 0;color:#475467}
body.printing-tco .tco-report-section{display:block!important;margin:18px 0 8px;font-size:13pt;font-weight:700;color:#173f87;break-after:avoid}
body.printing-tco #tcoresult>.grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
body.printing-tco #tcoresult .metric,body.printing-tco #tco-print-values .metric{background:#f0f5fd;border:1px solid #cfddf4;border-radius:8px;padding:10px;min-height:58px}
body.printing-tco #tcoresult .metric b{font-size:14pt;color:#0f2e66}body.printing-tco #tcoresult>p{margin-top:14px;color:#344054}
body.printing-tco #tco-print-values>.grid{grid-template-columns:repeat(3,minmax(0,1fr));gap:6px}
body.printing-tco #tco-print-values .metric{background:#fff;min-height:48px;padding:7px}body.printing-tco #tco-print-values .metric b{font-size:10pt}
body.printing-tco .tco-report-note{display:block!important;margin-top:15px;padding:10px 12px;background:#fff8ed;border-left:3px solid #b54708;color:#5d3b16}
body.printing-tco .tco-report-footer{display:flex!important;position:fixed;bottom:0;left:0;right:0;align-items:center;justify-content:space-between;border-top:1px solid #9aaec9;background:white;padding:7px 0 0;color:#344054;font-size:8pt}
body.printing-tco .tco-report-footer strong{color:#173f87;font-size:10pt}body.printing-tco .tco-report-footer span{white-space:nowrap}
@page{size:A4;margin:16mm 16mm 24mm}}
</style><div class="card"><div class="print-only tco-report-header"><div class="tco-brandmark">以和</div><div><small>上海以和信息技术有限公司 · 客户方案测算</small><h2>Surface Laptop Ultra TCO 成本报告</h2><p>Part Number：${escapeHtml(s.part_number)}　·　生成日期：<span id="tco-print-date"></span></p></div></div><h3 class="tco-screen-title">Surface Laptop Ultra TCO 报告 · ${escapeHtml(s.part_number)}</h3><p class="tco-screen-intro">SKU 导入价自动填入；其余仅是可编辑的预算示例，不是设备吞吐、官方功耗或云端报价。请用客户实际账单和目标设备 PoC 替换。</p><p><button id="tco-print" onclick="printTcoReport()" disabled>打印报告／另存为 PDF</button> <button id="tco-calc" onclick="calcTco()" disabled>重新计算</button></p><p id="tco-filename" class="status print-hint">建议 PDF 文件名：Surface-Laptop-Ultra-TCO-${escapeHtml(s.part_number)}.pdf</p><div id="tco-status" class="status">正在读取此 SKU 的初始值…</div><div id="tco-fields" class="grid"></div><div class="print-only tco-report-section">成本结论</div><div id="tcoresult" aria-live="polite"></div><div id="tco-print-values" class="print-only"></div><p class="print-only tco-report-note">本报告为可编辑参数形成的情景估算，不是节省承诺。SKU 参考价来自授权导入数据；其他默认值须以客户实际合同、用量和目标设备 PoC 替换。未验证 Token/s 或业务承载能力。</p><p class="status tco-screen-source"><a href="https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/pricing-calculator" target="_blank" rel="noopener">云端报价应参考供应商定价工具和企业合同</a>；若输入/输出单价不同，请按真实 Token 占比换算混合单价。</p><div class="print-only tco-report-footer"><strong>以和 · 上海以和信息技术有限公司</strong><span>© 2026 上海以和信息技术有限公司。保留所有权利。</span></div></div>`}
const tcoFields=[['years','计算年限','年'],['purchase_price_cny','设备采购价','元'],['device_cost_allocation_ratio','计入 AI 场景的设备成本比例','0–1'],['residual_value_cny','期末残值','元'],['annual_maintenance_cny','每年维护与支持','元'],['power_watts','AI 使用时平均功率','W'],['hours_per_day','每日 AI 使用时间','小时'],['days_per_year','每年 AI 使用天数','天'],['electricity_cny_per_kwh','电价','元/kWh'],['monthly_tokens_million','每月业务量','百万 Token'],['cloud_cny_per_million_tokens','云端综合单价','元/百万 Token'],['hybrid_cloud_share','混合方案保留云端比例','0–1']];
const advisorTitle=document.title;
function tcoReportTitle(){return 'Surface-Laptop-Ultra-TCO-'+data.sku.part_number.replace(/[^A-Za-z0-9-]/g,'-')}
async function printTcoReport(){if(tab!=='tco'||!data)return;if(!await calcTco())return;$('#tco-print-date').textContent=new Date().toLocaleDateString('zh-CN');document.title=tcoReportTitle();document.body.classList.add('printing-tco');window.print()}
window.addEventListener('afterprint',()=>{document.body.classList.remove('printing-tco');document.title=advisorTitle});
async function loadTcoDefaults(s){let r=await fetch('/api/tco/defaults/'+encodeURIComponent(s.part_number)),d=await r.json();if(tab!=='tco'||!data||data.sku.part_number!==s.part_number)return;if(!r.ok){$('#tco-status').textContent=d.detail||'无法读取默认值';return}$('#tco-fields').innerHTML=tcoFields.map(([id,label,unit])=>`<label>${label}（${unit}）<input id="tco-${id}" type="number" min="0" step="any" value="${d.values[id]}"></label>`).join('');$('#tco-status').textContent=d.warning+' 参考价来源：'+(d.source_reference||'导入工作簿')+'；示例月业务量 '+d.values.monthly_tokens_million+' 百万 Token 并非此 SKU 的处理能力。默认 100% 云端保留，完成 PoC 后再修改。';$('#tco-calc').disabled=false;$('#tco-print').disabled=false;$('#tco-filename').textContent='建议 PDF 文件名：'+tcoReportTitle()+'.pdf';$('#tco-fields').addEventListener('change',calcTco);calcTco()}
async function calcTco(){let body={};for(let [id] of tcoFields)body[id]=Number($('#tco-'+id).value);let target=$('#tcoresult');try{let r=await fetch('/api/tco/calculate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}),d=await r.json();if(!r.ok)throw Error(typeof d.detail==='string'?d.detail:'请检查输入值');let money=n=>'¥'+Number(n).toLocaleString(),threshold=d.break_even_monthly_tokens_million_within_period;let payback=d.payback_status==='no_cloud_price'?'云端单价为 0；无节省可抵扣设备成本':d.payback_status==='no_monthly_savings'?'当前用量下不回本':d.payback_status==='beyond_period'?`${d.payback_months} 个月（超过 ${d.period_years} 年测算期）`:`${d.payback_months} 个月`;target.innerHTML='<div class="grid">'+metric('本地全量承担方案',money(d.local_tco_cny))+metric('云端全量方案',money(d.cloud_tco_cny))+metric('混合方案',money(d.hybrid_tco_cny))+metric('本地相对云端的情景差额',money(d.local_vs_cloud_savings_cny))+metric('简化回本结论',payback)+metric('每月云端费－本地运营费',money(d.cloud_minus_local_operating_monthly_cny))+'</div>'+`<p class="status">${threshold===null?'云端单价为 0，无法给出有限的回本业务量阈值。':`按当前云端单价，若要在 ${d.period_years} 年内回本，月业务量需至少约 ${threshold} 百万 Token（当前输入 ${body.monthly_tokens_million}）。`}设备净成本计入 ${money(d.breakdown.purchase_net_residual_allocated)}；电费 ${money(d.breakdown.electricity)}；维护 ${money(d.breakdown.maintenance)}。仅在本地模型通过目标任务 PoC 且能承接该业务量时，差额才有决策意义。</p>`;$('#tco-print-values').innerHTML='<h4>本次测算输入</h4><div class="grid">'+tcoFields.map(([id,label,unit])=>metric(escapeHtml(label),escapeHtml(body[id])+' '+escapeHtml(unit))).join('')+'</div>';return true}catch(e){target.innerHTML=`<p class="warn">${escapeHtml(e.message)}</p>`;return false}}
function faqForm(){return `<div class="card"><h3>AI 与 RTX Spark 销售培训知识库</h3><p>涵盖模型、内存、量化、硬件、Windows、部署、安全、MXC 与混合智能。知识点及问答总数以搜索结果为准。</p><div class="grid"><label>关键词<input id="faqquery" placeholder="例如：MoE、统一内存、MXC、混合智能"></label><label>分类<select id="faqcategory"><option value="">全部分类</option></select></label></div><p><button onclick="searchFaq()">搜索知识库</button></p><div id="faqresult" class="status">输入关键词或直接浏览前 20 条。</div></div>`}
const microsoftSpecsUrl='https://www.microsoftstore.com.cn/surface/surface-laptop-ultra-for-business';
function renderProductDetails(s){
 let host=$('#product-details');if(!host){host=document.createElement('div');host.id='product-details';$('#metrics').after(host)}
 $('#metrics').hidden=true;
 const known=v=>v!==null&&v!==undefined&&v!=='';
 const sku=v=>known(v)?String(v):'未提供';
 const color=String(s.color||'').toUpperCase();
 const colorNote=color&& !['PLATINUM','NIGHTFALL','亮铂金','夜幕色'].includes(color)?'导入颜色名称与中国微软商城的亮铂金/夜幕色不同；不能自动认定同色，须核对料号':'颜色需核对具体料号';
 const storage=known(s.storage_tb)?Number(s.storage_tb)+' TB':'未提供';
 const ssdGeneration=Number(s.storage_tb)===0.5?'第 4 代 SSD':([1,2].includes(Number(s.storage_tb))?'第 5 代 SSD':'代际待核对');
 const rows=[
  ['识别','产品与料号',sku(s.product_family)+' · '+sku(s.part_number),'Surface Laptop Ultra 商用版','料号来自导入；官网技术规格为系列级'],
  ['识别','原始配置描述',sku(s.raw_configuration),'按处理器、内存、SSD、颜色组合销售','保留导入原文；不自动扩展简写'],
  ['核心硬件','处理器',sku(s.cpu_model),'NVIDIA RTX Spark N1X：18 核 CPU / 5120 核 GPU，或 20 核 CPU / 6144 核 GPU','导入映射；官网列出两种系列选项，料号对应仍需核对'],
  ['核心硬件','图形处理器',sku(s.gpu_model),'NVIDIA Blackwell RTX 5120 核或 6144 核 GPU','导入映射；不推导游戏 FPS'],
  ['核心硬件','NPU',sku(s.npu_spec),'NVIDIA NPU','官网为系列规格；未提供逐料号 NPU 型号或算力'],
  ['核心硬件','统一内存',known(s.memory_gb)?s.memory_gb+' GB LPDDR5x 统一内存':'未提供','可选 24 / 32 / 48 / 64 / 128 GB LPDDR5x 统一内存','容量取导入、类型按官网补充；导入带宽未获官网此页逐料号核实；非全部可用 GPU 显存'],
  ['核心硬件','GPU 专用显存',known(s.gpu_memory_gb)?s.gpu_memory_gb+' GB':'未提供','CPU/GPU 共享统一内存；GPU 可寻址量小于总内存','官网未提供独立显存数值；不得填成统一内存容量'],
  ['核心硬件','SSD',known(s.storage_tb)?storage+' 可拆卸式 '+ssdGeneration:'未提供','512 GB 为第 4 代 SSD；1 / 2 TB 为第 5 代 SSD','容量取导入，代际按中国官网容量规则补充；实机核验'],
  ['核心硬件','散热',sku(s.thermal_spec),'新散热系统；微软称散热能力相较 Surface Laptop 第 8 代提升 2.5 倍','系列官方声明，非该 SKU 温度或持续性能实测'],
  ['显示','屏幕与分辨率','未逐料号导入','15 英寸 PixelSense Ultra Mini-LED 触控；3270 × 2180，262 PPI，3:2','系列官方规格'],
  ['显示','刷新率与色彩','未逐料号导入','动态刷新率最高 120 Hz；DCI-P3 100%；10 点触控；Dolby Vision IQ','系列官方规格；笔输入不受支持'],
  ['显示','亮度与防眩光','未逐料号导入','SDR 最高 1000 尼特（典型）；HDR 10% 窗口峰值 2000 尼特；防反射','系列官方规格；实际亮度依内容和设置变化'],
  ['连接','USB 与充电','未逐料号导入','2 × USB-C/USB4 + 1 × USB-C/USB4 Magnetic Connect；最高 40 Gbps；USB-C 支持 140W 充电','充电器随市场和配置变化；至少 115W 充电器支持快充'],
  ['连接','其他接口','未逐料号导入','HDMI 2.1b、USB-A 3.1、SD 读卡器、3.5 mm 耳机孔','系列官方规格'],
  ['连接','无线','未逐料号导入','Wi-Fi 7、Bluetooth 5.4','Wi-Fi 6 GHz 频段依地区而定'],
  ['系统与安全','操作系统',sku(s.operating_system),'Windows 11 专业版；Windows on Arm','中国官网确认系列系统；导入仍保留原始表述'],
  ['系统与安全','安全与登录','未逐料号导入','Secured-core PC、TPM 2.0、BitLocker 支持、Windows Hello 人脸识别','系列官方规格；企业策略与授权另行确认'],
  ['影音','摄像头与音频','未逐料号导入','1080p 前置摄像头、双 Studio 麦克风、四 Omnisonic 扬声器','系列官方规格'],
  ['机身','颜色',sku(s.color),'亮铂金 / 夜幕色（中国官网选项）',colorNote],
  ['机身','尺寸与重量','未逐料号导入','328.8 × 238.7 × 17.99 mm（不含脚垫）；含脚垫 19.16 mm；约 2.0 kg','重量随配置与制造工艺变化'],
  ['机身','电池与续航','未逐料号导入','标称 92 Wh；本地视频最长 15 小时，主动网页最长 12 小时','续航测试用预生产 6144 核 GPU / 64GB / 1TB，非此料号实测'],
  ['机身','键盘与触控板','未逐料号导入','背光机械键盘、F1–F12 功能键、精准触觉触控板','中国官网系列规格；键盘布局以实际销售配置为准'],
  ['机身','传感器','未逐料号导入','氛围颜色传感器、加速度计、陀螺仪','中国官网系列规格'],
  ['服务','可维修组件','未逐料号导入','显示组件、键盘、触控板、SSD、电池、主板、风扇等可更换','官网列出组件；维修须遵循授权流程'],
  ['服务','包装清单','未逐料号导入','设备、USB-C Magnetic Connect 连接线、快速入门指南、安全及保修文档','140 W 电源适配器仅特定市场/配置提供，不能承诺此 SKU 随附'],
  ['服务','中国市场保修','未逐料号导入','Surface 主机 3 年有限硬件保修（自发票日期起）','按中国微软商城页面；具体服务条款及配件保修另核对'],
  ['采购','ERP 参考价',known(s.erp_price_cny)?'¥'+Number(s.erp_price_cny).toLocaleString():'未提供','官网页面非此料号 ERP 报价','仅取授权导入价格；'+sku(s.currency_note)],
  ['溯源','数据状态',sku(s.data_status),'系列技术参数以中国微软商城为基准','官网不证明导入 Part Number 与颜色/配置一一对应'],
 ];
 const tr=([group,name,selected,official,note])=>{
  const missing=selected==='未逐料号导入'||selected==='未提供';
  const cannotFill=name==='GPU 专用显存'||name==='ERP 参考价';
  const value=missing&&!cannotFill?official:selected;
  const origin=missing&&!cannotFill?'中国微软商城 · 系列规格':missing?'尚无逐料号数值':'授权 V3.4 导入'+(name==='SSD'?' + 中国官网容量规则':name==='统一内存'?' + 中国官网内存类型':'');
  return `<tr><th scope="row">${escapeHtml(group)}<br><span class="status">${escapeHtml(name)}</span></th><td><b>${escapeHtml(value)}</b></td><td>${escapeHtml(origin)}</td><td>${escapeHtml(note)}</td></tr>`;
 };
 host.innerHTML='<h3>产品技术规格 · '+escapeHtml(s.part_number)+'</h3><p class="status">以授权导入的 SKU 值为主；未导入的系列通用项目用中国微软商城技术规格补充。每行标明来源，不能确定逐料号数值的字段保留待核对。</p><div class="spec-scroll"><table class="spec-table"><thead><tr><th scope="col">类别 / 参数</th><th scope="col">合并后的规格值</th><th scope="col">数据来源</th><th scope="col">限制与核对事项</th></tr></thead><tbody>'+rows.map(tr).join('')+'</tbody></table></div><p class="status">导入来源：'+escapeHtml(s.source_reference||'未提供')+'；原始备注：'+escapeHtml(s.note||'无')+'</p><p><a href="'+microsoftSpecsUrl+'" target="_blank" rel="noopener">查看中国微软商城完整技术规格与脚注</a></p>';
}
async function searchFaq(){let q=$('#faqquery').value,c=$('#faqcategory').value,r=await fetch('/api/faq?limit=20&q='+encodeURIComponent(q)+'&category='+encodeURIComponent(c)),d=await r.json();if($('#faqcategory').options.length===1){d.categories.forEach(x=>$('#faqcategory').add(new Option(x,x)))}$('#faqresult').innerHTML=`<p>找到 ${d.total} 条；知识库共 ${d.concept_total} 个独立概念、${d.indexed_total} 条问答。</p>`+d.items.map(x=>`<article class="card"><h3>${x.question}</h3><span class="tag">${x.category}</span><p>${x.easy_answer}</p><p class="status"><b>工程说明：</b>${x.expert_answer}</p><p class="warn"><b>常见误区：</b>${x.misconception}</p><p><b>销售提示：</b>${x.sales_tip}</p><p><a href="${x.source_url}" target="_blank" rel="noopener">查看来源</a></p></article>`).join('')}
function render(){if(!data)return;let s=data.sku;$('#product').textContent=`${s.product_family} · ${s.part_number}`;$('#metrics').innerHTML=metric('平台',s.platform_code)+metric('统一内存',s.memory_gb+' GB')+metric('存储',s.storage_tb+' TB')+metric('ERP 含税价',s.erp_price_cny?'¥'+Number(s.erp_price_cny).toLocaleString():'未知')+metric('CPU',s.cpu_model)+metric('GPU',s.gpu_model)+metric('颜色',s.color)+metric('操作系统',s.operating_system);renderProductDetails(s);let html='';if(tab==='ai')html=cards(data.ai)+'<h3>同档经验推荐</h3>'+cards(data.ai_recommendations);else if(tab==='gaming')html=cards(data.gaming)+'<h3>同档经验推荐</h3>'+cards(data.gaming_recommendations);else if(tab==='generation')html=cards(data.generation);else if(tab==='productivity')html=cards(data.productivity);else if(tab==='deployment')html=`<div class="card"><h3>本机模型部署与企业私有知识</h3><p>针对当前 ${escapeHtml(s.part_number)} 配置，逐步核对系统架构、模型许可、运行后端、真实任务与数据安全；包含个人试用、开发集成、多人服务、RAG 和微调的选择与验收。</p><p><a href="/deployment?sku=${encodeURIComponent(s.part_number)}">打开此配置的详细部署指南 →</a></p><p class="warn">指南是工程操作建议；模型是否能运行、GPU 加速和速度均需在目标设备实测。</p></div>`;else if(tab==='faq')html=faqForm();else if(tab==='tco')html=tcoForm(s);else html=`<div class="card"><h3>数据边界</h3><p>${data.disclaimer}</p><p class="warn">平台级 1440p / 100 FPS、120B+ 或理论峰值不能转换为本 SKU 的 FPS、Token/s 或稳定运行承诺。</p><p><b>配置状态：</b>${text(s.data_status)}</p><p><b>来源：</b>${text(s.source_reference)}</p><p><b>备注：</b>${text(s.note)}</p></div>`;$('#content').innerHTML=html;if(tab==='faq')searchFaq();if(tab==='tco')loadTcoDefaults(s)}
async function choose(p){$('#load').textContent='载入中…';try{let r=await fetch('/api/catalog/advisor/'+encodeURIComponent(p));if(!r.ok)throw Error('读取失败');data=await r.json();render();$('#load').textContent=''}catch(e){$('#load').textContent=e.message}}
async function init(){try{let r=await fetch('/api/catalog/imported-skus');if(r.status===401||r.status===403){$('#load').textContent='请先登录并确认 License 有效';$('#content').innerHTML='<div class="empty">此部署已启用访问保护。请前往 <a href="/account">账号页登录</a>，再刷新本页。</div>';return}if(!r.ok)throw Error('产品数据请求失败');let j=await r.json(),sel=$('#sku');if(!j.items.length){sel.innerHTML='<option>尚未导入 V3.4 工作簿</option>';$('#content').innerHTML='<div class="empty">请先运行授权工作簿导入。</div>';return}j.items.sort((a,b)=>{let ap=Number(a.erp_price_cny),bp=Number(b.erp_price_cny);return (a.erp_price_cny==null?Infinity:ap)-(b.erp_price_cny==null?Infinity:bp)||String(a.part_number).localeCompare(String(b.part_number))});sel.innerHTML=j.items.map(x=>`<option value="${escapeHtml(x.part_number)}">${escapeHtml(x.part_number)} · ${escapeHtml(x.platform_code)} · ${escapeHtml(x.memory_gb)}GB / ${escapeHtml(x.storage_tb)}TB · ${x.erp_price_cny==null?'价格待确认':'¥'+Number(x.erp_price_cny).toLocaleString()}</option>`).join('');sel.onchange=()=>choose(sel.value);choose(sel.value)}catch(error){$('#load').textContent='载入失败';$('#content').textContent=error.message}}
$('#tabs').onclick=e=>{if(e.target.tagName!=='BUTTON')return;document.querySelectorAll('.tabs button').forEach(b=>b.classList.remove('active'));e.target.classList.add('active');tab=e.target.dataset.tab;render()};init();
</script></body></html>'''
