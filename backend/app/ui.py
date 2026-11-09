"""Chinese-first local advisor UI backed by the imported V3.4 workbook."""
from fastapi import APIRouter, Response
from fastapi.responses import HTMLResponse
from .branding import apply_theme
import os

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def index(response: Response):
 from .home_intro import render
 page=apply_theme(render(_commercial_link(_render_page(response))))
 page=page.replace('</head>','<link rel="stylesheet" href="/assets/home-hero.css?v=20261106"></head>',1)
 switch='<nav class="wrap" aria-label="语言 / Language" style="text-align:right;padding:0 0 10px"><a lang="zh-CN" href="/" aria-current="page" style="color:#fff">中文</a> <span aria-hidden="true"> | </span> <a lang="en" href="/en" style="color:#fff">English</a></nav>'
 return page.replace('</header>',switch+'</header>',1)

@router.get('/en', response_class=HTMLResponse)
def index_en(response: Response):
 from .ui_en import translate_advisor
 return translate_advisor(index(response))

@router.get('/surface', response_class=HTMLResponse)
def surface_index(response: Response):
 return apply_theme(_commercial_link(_render_page(response, surface=True)))

@router.get('/en/surface', response_class=HTMLResponse)
def surface_index_en(response: Response):
 from .ui_en import translate_surface
 return translate_surface(surface_index(response))

def _commercial_link(page):
 if os.getenv('CAPABILITY_DEPLOYMENT_MODE', 'local') == 'local' or os.getenv('CAPABILITY_COMMERCIAL_ENABLED') == '1':
  return page.replace('<a href="/">RTX Spark 能力顾问</a></nav>', '<a href="/">RTX Spark 能力顾问</a>　·　<a href="/workplace">Surface AI Workplace租赁及订阅</a></nav>', 1)
 return page

def _render_page(response: Response, surface=False):
 response.headers["Cache-Control"] = "no-store"
 page = r'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Surface AI Workplace及RTX Spark能力与选型顾问</title><style>
:root{--ink:#101828;--muted:#667085;--line:#e4e7ec;--blue:#175cd3;--pale:#eff4ff;--amber:#b54708}*{box-sizing:border-box}body{margin:0;background:#f7f8fa;color:var(--ink);font:15px/1.55 system-ui,'Microsoft YaHei',sans-serif}.top{background:#0b1220;color:white;padding:34px 24px}.wrap{max-width:1180px;margin:auto}.eyebrow{color:#9db7ff;font-weight:700;letter-spacing:.08em}h1{margin:.3rem 0;font-size:clamp(25px,4vw,38px)}h2{font-size:22px;margin:0 0 14px}h3{font-size:17px;margin:14px 0 8px}.sub{color:#cbd5e1;max-width:820px}.bar{background:white;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:2}.bar .wrap{display:flex;gap:12px;align-items:center;padding:14px 24px}.bar label{font-weight:700}.bar select{flex:1;max-width:650px;padding:11px;border:1px solid #98a2b3;border-radius:8px;background:white}main{padding:24px}.panel{background:white;border:1px solid var(--line);border-radius:14px;padding:20px;margin-bottom:18px;box-shadow:0 1px 2px #1018280a}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin:12px 0}.grid[hidden]{display:none}.metric{background:#f9fafb;border-radius:10px;padding:14px}.metric b{display:block;font-size:17px}.tabs{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}.tabs button{padding:9px 14px;border:1px solid #b2c5e8;border-radius:999px;background:white;color:#1849a9;cursor:pointer}.tabs button.active{background:var(--blue);color:white;border-color:var(--blue)}.card{border:1px solid var(--line);border-radius:10px;padding:14px;margin:10px 0}.card p{margin:5px 0}.tag{display:inline-block;background:var(--pale);color:#1849a9;padding:2px 8px;border-radius:999px;margin:2px 5px 2px 0;font-size:12px}.warn{color:var(--amber)}.empty{padding:28px;text-align:center;color:var(--muted);border:1px dashed #b9c1cc;border-radius:10px}.status{color:var(--muted)}footer{text-align:center;color:var(--muted);padding:30px}@media(max-width:650px){.bar .wrap{align-items:stretch;flex-direction:column}.bar select{max-width:none}main{padding:14px}}
</style><style>.bar #tco-shortcut{background:#175cd3;color:white;border:0;border-radius:8px;padding:10px 14px;font-weight:700;cursor:pointer;white-space:nowrap}.quick-form{display:grid;grid-template-columns:minmax(260px,2fr) repeat(4,minmax(145px,1fr));gap:10px;align-items:end}.quick-form label{font-weight:700}.quick-form input,.quick-form select{width:100%;margin-top:5px;padding:10px;border:1px solid #98a2b3;border-radius:8px;background:white}.quick-actions{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}.quick-actions button,.quick-card button{padding:9px 13px;border:1px solid #175cd3;border-radius:8px;background:#175cd3;color:white;cursor:pointer}.quick-actions button.secondary,.quick-card button.secondary{background:white;color:#175cd3}.quick-results{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px;margin-top:14px}.quick-card{border:1px solid #ccd7ea;border-radius:12px;padding:15px;background:#fbfcff}.quick-card h3{margin-top:5px}.quick-meta{display:flex;gap:6px;flex-wrap:wrap}.quick-detail{grid-column:1/-1;background:#fff;border:2px solid #9bb6e6}.quick-detail table{width:100%;border-collapse:collapse;margin:10px 0}.quick-detail th,.quick-detail td{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}.quick-detail th{width:22%;background:#f7f9fc}.quick-price{font-size:19px;color:#173f87;font-weight:800}.quick-quote{color:#067647;font-weight:700}@media(max-width:980px){.quick-form{grid-template-columns:repeat(2,minmax(0,1fr))}.quick-form label:first-child{grid-column:1/-1}}@media(max-width:650px){.bar #tco-shortcut{width:100%}.quick-form{grid-template-columns:1fr}.quick-form label:first-child{grid-column:auto}.quick-results{grid-template-columns:1fr}}.print-only{display:none}@media print{body.printing-tco{background:white;color:#111;font-size:10pt}body.printing-tco .top,body.printing-tco .bar,body.printing-tco footer,body.printing-tco main>.panel:not(#tco-panel),body.printing-tco #tco-panel .tabs,body.printing-tco #tco-panel button,body.printing-tco #tco-fields,body.printing-tco .print-hint{display:none!important}body.printing-tco main{padding:0;max-width:none}body.printing-tco #tco-panel,body.printing-tco #tco-panel .card{border:0;box-shadow:none;padding:0;margin:0}body.printing-tco .print-only{display:block}body.printing-tco .metric{break-inside:avoid}body.printing-tco a{color:#111}@page{size:A4;margin:16mm}}</style></head><body><header class="top"><div class="wrap"><div class="eyebrow">V3.1 产品与能力顾问</div><h1>Surface AI Workplace及RTX Spark能力与选型顾问</h1><div class="sub">按真实 Part Number 快速查找 Surface 设备、配件和延保，或进入 RTX Spark 的 AI、游戏、生成式 AI 与生产力能力分析。价格以授权导入的 ERP 含税价为基础。</div></div></header>
<div class="bar"><div class="wrap"><label for="sku">RTX Spark 能力配置</label><select id="sku"><option>正在载入 V3.4 数据…</option></select><span id="load" class="status"></span></div></div><main class="wrap"><section class="panel" id="quick-lookup"><h2>Surface SKU 快速查询</h2><p class="status">可输入完整或部分 Part Number、产品名称、CPU、配置、颜色或联网方式。默认查询 Surface 设备、配件和延保，不展示暂未纳入的 NVIDIA 记录。</p><form id="quick-form"><div class="quick-form"><label>关键词／Part Number<input id="quick-query" maxlength="120" autocomplete="off" placeholder="例如 EP2-77145、Surface Pro、Ultra 5、16GB"></label><label>类别<select id="quick-type"><option value="">全部类别</option></select></label><label>大系列<select id="quick-series"><option value="">全部系列</option></select></label><label>内存<select id="quick-memory"><option value="">全部内存</option></select></label><label>ERP 价格上限<input id="quick-max-price" type="number" min="0" step="1" placeholder="例如 15000"></label></div><div class="quick-actions"><label>报价系数 <input id="quick-quote-factor" type="number" min="0" max="100" step="0.1" value="100" style="width:86px;padding:8px;border:1px solid #98a2b3;border-radius:8px">%（90% 表示九折）</label><button type="submit">立即查询</button><button type="button" class="secondary" id="quick-reset">清空条件</button></div></form><p id="quick-status" class="status" aria-live="polite">正在读取 V3.1 查询索引…</p><div id="quick-results" class="quick-results"></div></section><section class="panel"><h2>按使用需求推荐 RTX Spark 配置</h2><p class="status">先选用途，也可以用自己的话描述。系统会合并已识别的需求，给出可比较的 Surface Laptop Ultra 候选；具体软件、游戏和模型仍需验证。</p><form id="needform"><fieldset><legend>主要用途（可多选）</legend><label><input type="checkbox" name="usage" value="ai"> 本地 AI 模型</label>　<label><input type="checkbox" name="usage" value="gaming"> 游戏</label>　<label><input type="checkbox" name="usage" value="generation"> 图像/视频生成</label>　<label><input type="checkbox" name="usage" value="productivity"> 生产力</label></fieldset><div id="need-ai-fields" class="grid" hidden><label>模型名称（可选）<input id="need-model-name" maxlength="120" placeholder="例如 Qwen3"></label><label>模型规模<select id="need-ai"><option value="unsure">尚不确定</option><option>8B</option><option>32B</option><option>70B</option><option>120B</option></select></label></div><div id="need-game-fields" class="grid" hidden><label>具体游戏（可多款）<input id="need-game-titles" maxlength="240" placeholder="例如 CS2、赛博朋克 2077"></label><label>游戏类型<select id="need-game"><option value="unsure">尚不确定</option><option value="esports">电竞/网游</option><option value="aaa">3A 大型游戏</option></select></label><label>目标分辨率<select id="need-resolution"><option value="unsure">尚不确定</option><option>1080p</option><option>1440p</option><option>4K</option></select></label><label>目标 FPS<input id="need-fps" type="number" min="1" max="500" placeholder="例如 60"></label></div><div id="need-work-fields" class="grid" hidden><label>软件名称与版本（可选）<input id="need-software" maxlength="120" placeholder="例如 Premiere Pro"></label><label>生产力工作负载<select id="need-work"><option value="unsure">尚不确定</option><option value="office">日常办公</option><option value="coding">编程开发</option><option value="video">视频剪辑</option><option value="cad">CAD / 3D</option></select></label></div><div class="grid"><label>预算上限（元，可留空）<input id="need-budget" type="number" min="1" step="1" placeholder="例如 40000"></label></div><p><label for="need-description">自由描述</label><br><textarea id="need-description" rows="3" maxlength="2000" style="width:100%;padding:10px;border:1px solid #98a2b3;border-radius:8px" placeholder="例如：要玩 3A 游戏，也希望本地运行 70B 模型，用于编程和客户演示"></textarea></p><button type="submit">查找合适配置</button></form><div id="need-result" aria-live="polite"></div></section><section class="panel"><h2 id="product">RTX Spark 产品概览</h2><p><a href="#" onclick="openCustomerReport();return false">预览客户能力报告</a>　<button type="button" onclick="downloadCustomerPdf()">下载 PDF 报告</button></p><p id="pdf-status" class="status" aria-live="polite"></p><div id="metrics" class="grid"></div></section>
<section class="panel" id="tco-panel"><div class="tabs" id="tabs"><button data-tab="ai" class="active">AI 模型</button><button data-tab="gaming">游戏</button><button data-tab="generation">生成式 AI</button><button data-tab="productivity">生产力</button><button data-tab="deployment">模型部署</button><button data-tab="faq">AI FAQ</button><button data-tab="tco">TCO 成本</button><button data-tab="evidence">证据与限制</button></div><div id="content"></div></section>
<section class="panel"><h2>数据说明</h2><p>快速查询读取经审阅的 Surface SKU V3.1 映射索引；RTX Spark 能力模块继续读取授权 V3.4 工作簿。ERP 含税价以用户提供的原始表格为准。空白 Token/s、FPS 或实测字段保持未知；经验推荐不会显示为官方测试。</p><p><a href="/account">账号注册与登录</a> · <a href="/admin">管理员控制台</a> · <a href="/docs">API 文档</a> · <a href="/api/catalog/quick-search">快速查询数据</a> · <a href="/api/catalog/sources">来源台账</a></p></section></main><footer>© 2026 上海以和信息技术有限公司。保留所有权利。 · <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener noreferrer">沪ICP备17029250号-4</a><br><small>Microsoft、Surface、NVIDIA、RTX 等商标归各自权利人所有。本站供员工与内部代理商培训使用。</small></footer>
<style>
body>footer::before{content:"";display:block;width:min(270px,78vw);height:90px;background:#fff url('/assets/yihe-logo.png') center/contain no-repeat;border-radius:8px;margin:0 0 18px}
body>footer::before{width:165px;height:55px;margin:0 auto 12px}
.tco-brandmark{background:#fff url('/assets/yihe-logo.png') center/contain no-repeat!important;width:160px!important;height:58px!important;border-radius:0!important;font-size:0!important}
.tco-report-footer::before,.tco-report-footer strong{display:none!important}
.spec-scroll{overflow-x:auto;margin:14px 0}.spec-table{width:100%;border-collapse:collapse;font-size:14px;line-height:1.5}.spec-table th,.spec-table td{border:1px solid var(--line);padding:10px 12px;text-align:left;vertical-align:top}.spec-table tbody th{background:#f9fafb;width:27%;min-width:110px}.spec-table td{overflow-wrap:anywhere}.spec-table tr:hover td{background:#fbfcff}
@media print{.tco-brandmark{width:130px!important;height:48px!important}}
</style><script src="https://res.wx.qq.com/open/js/jweixin-1.6.0.js"></script><script>
const $=s=>document.querySelector(s);let data=null,tab='ai';const text=v=>(v===null||v===undefined||v==='')?'未知':String(v);const escapeHtml=v=>text(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));const metric=(k,v)=>`<div class="metric"><span class="status">${escapeHtml(k)}</span><b>${escapeHtml(v)}</b></div>`;
const platformLabel=code=>({S2:'NVIDIA RTX Spark™ N1X（18 核 CPU / 5120 核 GPU）',S3:'NVIDIA RTX Spark™ N1X（20 核 CPU / 6144 核 GPU）'})[String(code||'').toUpperCase()]||text(code);
const safeSourceUrl=value=>{try{const url=new URL(String(value).split(' ; ')[0].trim());return url.protocol==='https:'?url.href:null}catch{return null}};
const fetch=(url,options={})=>{const token=sessionStorage.getItem('cap_token');return window.fetch(url,{...options,headers:{...(options.headers||{}),...(token?{Authorization:'Bearer '+token}:{})}})};
const quickMoney=value=>value===null||value===undefined||value===''?'价格待确认':'¥'+Number(value).toLocaleString('zh-CN',{maximumFractionDigits:2});
const quickKnown=value=>value!==null&&value!==undefined&&value!=='';
const quickFacts=item=>[
 item.cpu_official,item.memory_gb?item.memory_gb+'GB':null,item.storage_capacity,item.color,item.connectivity,item.power_supply
].filter(quickKnown).join(' · ')||item.raw_description||'配置详情见完整映射';
function quickQuote(item){const factor=Number($('#quick-quote-factor').value||100);if(!quickKnown(item.erp_price_cny)||!Number.isFinite(factor))return '';return quickMoney(Number(item.erp_price_cny)*factor/100)}
function renderQuickResults(payload){
 const target=$('#quick-results');$('#quick-status').textContent=`找到 ${Number(payload.total)} 条；当前显示 ${payload.items.length} 条。价格以原表 ERP 含税价为准。`;
 if(!payload.items.length){target.innerHTML='<div class="empty">没有符合当前条件的记录。请减少筛选条件或核对 Part Number。</div>';return}
 target.innerHTML=payload.items.map(item=>{const quote=quickQuote(item),factor=Number($('#quick-quote-factor').value||100);return `<article class="quick-card"><div class="quick-meta"><span class="tag">${escapeHtml(item.product_type)}</span><span class="tag">${escapeHtml(item.series_group)}</span><span class="tag">${escapeHtml(item.match_level)}</span></div><h3>${escapeHtml(item.part_number)} · ${escapeHtml(item.product_name||item.original_family)}</h3><p>${escapeHtml(quickFacts(item))}</p><p><span class="quick-price">ERP ${escapeHtml(quickMoney(item.erp_price_cny))}</span></p><p class="status">${escapeHtml(item.review_status||'待复核')}</p><button type="button" data-quick-detail="${escapeHtml(item.part_number)}">查看完整映射</button> <button type="button" class="secondary" data-copy-pn="${escapeHtml(item.part_number)}">复制 Part Number</button></article>`}).join('');
}
async function runQuickSearch(event){
 if(event)event.preventDefault();
 const params=new URLSearchParams(),query=$('#quick-query').value.trim(),type=$('#quick-type').value,series=$('#quick-series').value,memory=$('#quick-memory').value,maxPrice=$('#quick-max-price').value;
 if(query)params.set('q',query);if(type)params.set('product_type',type);if(series)params.set('series',series);if(memory)params.set('memory_gb',memory);if(maxPrice)params.set('max_erp_price_cny',maxPrice);params.set('limit','300');
 $('#quick-status').textContent='正在查询 V3.1 映射数据库…';$('#quick-results').innerHTML='';
 try{const response=await fetch('/api/catalog/quick-search?'+params.toString()),payload=await response.json();if(!response.ok)throw Error(payload.detail||'查询失败');renderQuickResults(payload)}catch(error){$('#quick-status').textContent='查询失败';$('#quick-results').innerHTML=`<div class="empty">${escapeHtml(error.message)}</div>`}
}
async function showQuickDetail(partNumber){
 const target=$('#quick-results');
 try{const response=await fetch('/api/catalog/quick-search/'+encodeURIComponent(partNumber)),payload=await response.json();if(!response.ok)throw Error(payload.detail||'读取详情失败');const item=payload.item,source=safeSourceUrl(item.official_source_url);const fields=[['Part Number',item.part_number],['产品类别',item.product_type],['产品名称',item.product_name],['原始系列',item.original_family],['原始描述／配置',item.raw_description],['平台',item.platform],['CPU 官方名称',item.cpu_official],['内存',item.memory_gb?item.memory_gb+' GB':null],['存储',item.storage_capacity],['颜色',item.color],['联网',item.connectivity],['电源',item.power_supply],['屏幕',item.display],['分辨率／刷新率',[item.resolution,item.refresh_rate].filter(quickKnown).join(' · ')],['NPU',item.npu],['GPU',item.gpu],['重量',item.weight],['电池',item.battery],['操作系统',item.operating_system],['ERP 含税价',quickMoney(item.erp_price_cny)],['匹配级别',item.match_level],['复核状态',item.review_status],['未知字段',item.unknown_fields],['异常／复核说明',item.exception_note]].filter(([,value])=>quickKnown(value));const detail=document.createElement('article');detail.className='quick-card quick-detail';detail.id='quick-active-detail';detail.innerHTML=`<h3>完整映射 · ${escapeHtml(item.part_number)}</h3><table><tbody>${fields.map(([name,value])=>`<tr><th>${escapeHtml(name)}</th><td>${escapeHtml(value)}</td></tr>`).join('')}</tbody></table>${source?`<p><a href="${escapeHtml(source)}" target="_blank" rel="noopener noreferrer">打开微软中国官方来源</a></p>`:'<p class="status">此记录没有逐料号官方页面；映射依据与限制已保留在数据库中。</p>'}<p><button type="button" class="secondary" data-close-quick>关闭详情</button></p>`;const existing=$('#quick-active-detail');if(existing)existing.remove();if(item.service_details){const table=document.createElement('table');table.innerHTML='<tbody>'+Object.entries(item.service_details).filter(([key,value])=>quickKnown(value)&&!['序号','原行号','Part Number','ERP 含税价','ADR Price'].includes(key)).map(([key,value])=>`<tr><th>${escapeHtml(key)}</th><td>${escapeHtml(value)}</td></tr>`).join('')+'</tbody>';detail.append(table)}target.prepend(detail);detail.scrollIntoView({behavior:'smooth',block:'start'})}catch(error){$('#quick-status').textContent=error.message}
}
async function loadQuickOptions(){
 try{const response=await fetch('/api/catalog/quick-search/options'),payload=await response.json();if(!response.ok)throw Error(payload.detail||'查询索引不可用');payload.product_types.forEach(item=>$('#quick-type').add(new Option(`${item.value}（${item.count}）`,item.value)));payload.series.forEach(item=>$('#quick-series').add(new Option(`${item.value}（${item.count}）`,item.value)));payload.memory_gb.forEach(value=>$('#quick-memory').add(new Option(value+' GB',value)));$('#quick-status').textContent=`已载入 ${payload.searchable_count} 条可查询记录。`;await runQuickSearch()}catch(error){$('#quick-status').textContent=error.message;$('#quick-results').innerHTML='<div class="empty">尚未导入 V3.1 查询数据库，请先运行授权工作簿导入。</div>'}
}
function resetQuickSearch(){$('#quick-query').value='';$('#quick-type').value='';$('#quick-series').value='';$('#quick-memory').value='';$('#quick-max-price').value='';$('#quick-quote-factor').value='100';runQuickSearch()}
$('#quick-form').addEventListener('submit',runQuickSearch);$('#quick-reset').addEventListener('click',resetQuickSearch);$('#quick-quote-factor').addEventListener('change',runQuickSearch);let quickTimer;$('#quick-query').addEventListener('input',()=>{clearTimeout(quickTimer);quickTimer=setTimeout(runQuickSearch,220)});$('#quick-results').addEventListener('click',event=>{const detail=event.target.closest('[data-quick-detail]'),copy=event.target.closest('[data-copy-pn]');if(detail)showQuickDetail(detail.dataset.quickDetail);if(copy){navigator.clipboard.writeText(copy.dataset.copyPn).then(()=>{$('#quick-status').textContent='已复制 Part Number：'+copy.dataset.copyPn}).catch(()=>{$('#quick-status').textContent='无法自动复制，请手动选择 Part Number'})}if(event.target.closest('[data-close-quick]'))event.target.closest('.quick-detail').remove()});
const inWechat=/MicroMessenger/i.test(navigator.userAgent);
async function inMiniProgram(){if(!inWechat||!window.wx||!wx.miniProgram)return false;if(window.__wxjs_environment==='miniprogram')return true;return new Promise(resolve=>wx.miniProgram.getEnv(result=>resolve(Boolean(result.miniprogram))))}
function renderReportContent(target,html){const parsed=new DOMParser().parseFromString(html,'text/html');const root=target.attachShadow({mode:'open'});const styles=[...parsed.querySelectorAll('style')].map(node=>node.textContent).join('\n');root.innerHTML='<style>:host{display:block;color:#172033;background:#fff}'+styles+'</style>'+parsed.body.innerHTML;root.querySelectorAll('.actions,button[onclick*="print"],button[onclick*="Print"]').forEach(node=>node.remove())}
function showInlineReport(html){let overlay=document.createElement('div');overlay.style.cssText='position:fixed;inset:0;z-index:1000;background:white;overflow:auto';let close=document.createElement('button');close.type='button';close.textContent='关闭预览，返回能力顾问';close.style.cssText='position:sticky;top:0;z-index:1;margin:8px;padding:12px';close.onclick=()=>overlay.remove();let content=document.createElement('div');overlay.append(close,content);document.body.appendChild(overlay);renderReportContent(content,html)}
async function openCustomerReport(){
 if(!data)return;
 try{
  const response=await fetch('/api/reports/'+encodeURIComponent(data.sku.part_number)+'.html');
  if(!response.ok)throw Error(response.status===401?'请先在账号页登录':response.status===403?'请确认组织 License 有效':'报告生成失败');
  showInlineReport(await response.text());
 }catch(error){$('#pdf-status').textContent=error.message}
}
async function downloadCustomerPdf(selectedPartNumber){
 if(!data)return;
 const partNumber=String(selectedPartNumber || data.sku.part_number);
 const status=$('#pdf-status');status.textContent='正在生成 PDF…';
 try{
  if(inWechat){
   if(!await inMiniProgram())throw Error('微信内请通过小程序打开后再预览 PDF');
   const ticketResponse=await fetch('/api/reports/mobile-ticket',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({part_number:partNumber})});
   if(!ticketResponse.ok)throw Error('无法创建 PDF 预览授权，请重新登录后重试');
   const ticket=await ticketResponse.json();
   wx.miniProgram.navigateTo({url:'/pages/report/index?ticket='+encodeURIComponent(ticket.ticket)+'&filename='+encodeURIComponent(ticket.filename),fail:()=>{status.textContent='无法打开小程序 PDF 预览，请检查版本及下载域名配置'}});
   status.textContent='正在打开小程序 PDF 预览；请在预览页确认保存';return;
  }
  const response=await fetch('/api/reports/'+encodeURIComponent(partNumber)+'.pdf');
  if(!response.ok)throw Error(response.status===401?'请先在账号页登录':response.status===403?'请确认组织 License 有效':'PDF 生成失败');
  const filename='Surface-Laptop-Ultra-Capability-'+partNumber.replace(/[^A-Za-z0-9_-]/g,'-')+'.pdf';
  const url=URL.createObjectURL(await response.blob());
  const link=document.createElement('a');link.href=url;link.download=filename;document.body.appendChild(link);link.click();link.remove();
  setTimeout(()=>URL.revokeObjectURL(url),60000);status.textContent='已发起浏览器下载，请在下载记录确认：'+filename;
 }catch(error){status.textContent=error.message}
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
  target.innerHTML=`<h3>需求档案</h3><p>用途：${escapeHtml(interpreted.usages.map(x=>labels[x]||x).join(' + '))}；模型：${escapeHtml(interpreted.ai_size)}；工程筛选内存档：${escapeHtml(interpreted.minimum_memory_tier_gb)} GB</p>`+d.reasoning.map(x=>`<p class="status">${escapeHtml(x)}</p>`).join('')+d.needs_confirmation.map(x=>`<p class="warn">待确认：${escapeHtml(x)}</p>`).join('')+`<h3>产品候选（${d.items.length}）</h3>`+(d.items.length?d.items.map(x=>`<article class="card"><h3>${escapeHtml(x.part_number)} · ${escapeHtml(platformLabel(x.platform_code))} · ${escapeHtml(x.memory_gb)}GB</h3><p>存储 ${escapeHtml(x.storage_tb)}TB · 导入价格 ${x.price_cny===null?'未知':'¥'+Number(x.price_cny).toLocaleString()} ${x.over_budget?'· 超出预算':''}</p><p>${escapeHtml(x.reason)}</p><span class="tag">${escapeHtml(x.evidence_level)}</span><p><button type="button" data-pn="${escapeHtml(x.part_number)}">查看此配置的详细能力并生成报告</button></p></article>`).join(''):'<div class="empty">当前导入产品中没有匹配候选。</div>')+`<p class="status">${escapeHtml(d.limitations||'')}</p><div id="need-report-output" aria-live="polite"></div>`;
 }catch(e){target.innerHTML=`<p class="warn">${escapeHtml(e.message)}</p>`}
}
const generationFields=document.createElement('div');generationFields.id='need-generation-fields';generationFields.className='grid';generationFields.hidden=true;generationFields.innerHTML='<label>生成工作流<select id="need-generation"><option value="unsure">尚不确定</option><option value="image">图像生成</option><option value="video">视频生成</option></select></label>';$('#needform').insertBefore(generationFields,$('#need-budget').parentElement.parentElement);
const priorityField=document.createElement('label');priorityField.innerHTML='推荐排序<select id="need-priority"><option value="price">优先控制采购价</option><option value="capacity">优先更大内存</option></select>';$('#need-budget').parentElement.parentElement.appendChild(priorityField);
function updateNeedFields(){let chosen=new Set([...document.querySelectorAll('input[name="usage"]:checked')].map(x=>x.value));$('#need-ai-fields').hidden=!chosen.has('ai');$('#need-game-fields').hidden=!chosen.has('gaming');$('#need-work-fields').hidden=!chosen.has('productivity');$('#need-generation-fields').hidden=!chosen.has('generation');if(!chosen.has('ai')){$('#need-ai').value='unsure';$('#need-model-name').value=''}if(!chosen.has('gaming')){$('#need-game').value='unsure';$('#need-game-titles').value='';$('#need-resolution').value='unsure';$('#need-fps').value=''}if(!chosen.has('productivity')){$('#need-work').value='unsure';$('#need-software').value=''}if(!chosen.has('generation'))$('#need-generation').value='unsure'}
document.querySelectorAll('input[name="usage"]').forEach(x=>x.addEventListener('change',updateNeedFields));$('#needform').addEventListener('submit',findProducts);
async function showNeedReport(partNumber){
 const output=$('#need-report-output');if(!output||!lastNeedBody)return;
 output.innerHTML='<p class="status">正在生成此配置与本次需求的完整报告…</p>';
 try{
  const r=await fetch('/api/reports/recommendation',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...lastNeedBody,part_number:partNumber})});
  if(!r.ok){const error=await r.json();throw Error(typeof error.detail==='string'?error.detail:'报告生成失败')}
  const html=await r.text();
  $('#sku').value=partNumber;await choose(partNumber);
  const filename='Surface-Laptop-Ultra-Capability-'+String(partNumber).replace(/[^A-Za-z0-9_-]/g,'-')+'.pdf';
  output.innerHTML='<h3>此配置与本次需求的匹配报告</h3><p><button type="button" id="need-report-download">下载 SKU 能力 PDF</button></p><p class="status">下载文件：'+escapeHtml(filename)+'。PDF 为此 SKU 的能力资料；本次需求的匹配说明见下方预览。</p>';
  const preview=document.createElement('div');preview.className='report-preview';output.appendChild(preview);renderReportContent(preview,html);
  $('#need-report-download').addEventListener('click',()=>downloadCustomerPdf(partNumber));
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
  const sourceUrl=safeSourceUrl(source);
  return `<article class="card"><h3>${escapeHtml(title)}</h3><span class="tag">${escapeHtml(e)}</span><span class="tag">${escapeHtml(x['数据状态']||'数据记录')}</span><p><b>判断：</b>${escapeHtml(result)}</p>${official?`<p><b>官方资料：</b>${escapeHtml(official)}</p>`:''}${engineering&&engineering!==result?`<p><b>工程建议：</b>${escapeHtml(engineering)}</p>`:''}${perf?`<p><b>性能：</b>${escapeHtml(perf)}</p>`:''}${note?`<p class="status"><b>限制：</b>${escapeHtml(note)}</p>`:''}${sourceUrl?`<p><a href="${escapeHtml(sourceUrl)}" target="_blank" rel="noopener noreferrer">查看官方来源</a></p>`:''}</article>`
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
function aiStarter(s){return `<div class="card"><h3>RTX Spark AI 快速体验 · ${escapeHtml(s.part_number)}</h3><p>先选一个目标：首次 Agent 问答、办公摘要、创作辅助或开发。NVIDIA 已提供对应官方战术手册；本机安装、模型容量和速度仍需逐项验证。</p><p><a href="/deployment?sku=${encodeURIComponent(s.part_number)}">按此 SKU 打开中文上手与验收指南 →</a>　<a href="https://build.nvidia.com/rtx-spark" target="_blank" rel="noopener noreferrer">查看 NVIDIA 战术手册</a></p><p class="status">应用 MCP/CLI 让 Agent 连接工具；NVIDIA Skills 指导工作流程，不会自动授予应用权限。先用非敏感任务和只读连接试用。</p></div>`}
function faqForm(){return `<div class="card"><h3>AI 与 RTX Spark 销售培训知识库</h3><p>涵盖模型、内存、量化、硬件、Windows、部署、安全、MXC 与混合智能。选择分类即显示该分类全部内容。</p><div class="grid"><label>关键词<input id="faqquery" placeholder="例如：MoE、统一内存、MXC、混合智能"></label><label>分类<select id="faqcategory" onchange="searchFaq()"><option value="">全部分类</option></select></label></div><p><button onclick="searchFaq()">搜索知识库</button></p><div id="faqresult" class="status">输入关键词或选择分类浏览。</div></div>`}
const microsoftSpecsUrl='https://www.microsoftstore.com.cn/surface/surface-laptop-ultra-for-business';
function renderProductDetails(s){
 let host=$('#product-details');if(!host){host=document.createElement('div');host.id='product-details';$('#metrics').after(host)}
 $('#metrics').hidden=true;
 const known=v=>v!==null&&v!==undefined&&v!=='';
 const sku=v=>known(v)?String(v):'未提供';
 const platform=String(s.platform_code||'').toUpperCase();
 const cpuCores=platform==='S2'?18:platform==='S3'?20:0;
 const gpuCores=platform==='S2'?5120:platform==='S3'?6144:0;
 const cpu=cpuCores?`NVIDIA RTX Spark™ N1X（${cpuCores} 核 CPU：${cpuCores/2} 个 Cortex-X925 性能核 + ${cpuCores/2} 个 Cortex-A725 能效核）`:sku(s.cpu_model);
 const gpu=gpuCores?`NVIDIA Blackwell RTX（${gpuCores} 核 GPU）`:sku(s.gpu_model);
 const storage=known(s.storage_tb)?Number(s.storage_tb)+' TB 可拆卸式 '+(Number(s.storage_tb)===0.5?'第 4 代 SSD':([1,2].includes(Number(s.storage_tb))?'第 5 代 SSD':'SSD')):'未提供';
 const rows=[
  ['产品型号',sku(s.product_family)+' · '+sku(s.part_number)],
  ['处理器',cpu],['图形处理器',gpu],['NPU',sku(s.npu_spec)==='未提供'?'NVIDIA NPU':sku(s.npu_spec)],
  ['统一内存',known(s.memory_gb)?s.memory_gb+' GB LPDDR5x 统一内存':'未提供'],
  ['显存','共享统一内存（非独立显存；GPU 可用量小于总内存）'],
  ['内存带宽','300 GB/s（RTX Spark 平台接口规格，非此 SKU 实测吞吐）'],
  ['存储',storage],['散热',sku(s.thermal_spec)==='未提供'?'新散热系统':sku(s.thermal_spec)],
  ['显示屏','15 英寸 PixelSense™ Ultra 触控屏；3270 × 2180（262 PPI），3:2'],
  ['刷新率与色彩','最高 120 Hz 动态刷新率；DCI-P3 100%；10 点触控'],
  ['屏幕亮度','SDR 最高 1000 尼特（典型值）；HDR 10% 窗口峰值 2000 尼特'],
  ['USB-C 与充电','2 × USB-C/USB4 + 1 × USB-C/USB4 Magnetic Connect；最高 40 Gbps；支持 140 W 充电'],
  ['其他接口','HDMI 2.1b、USB-A 3.1、SD 读卡器、3.5 mm 耳机孔'],
  ['无线连接','Wi-Fi 7、蓝牙 5.4'],
  ['操作系统',sku(s.operating_system)==='未提供'?'Windows 11 专业版（ARM64）':sku(s.operating_system)],
  ['安全与登录','安全核心 PC、TPM 2.0、BitLocker 支持、Windows Hello 人脸识别'],
  ['摄像头与音频','1080p 前置摄像头、双 Studio 麦克风、四 Omnisonic 扬声器'],
  ['颜色',sku(s.color)],
  ['尺寸与重量','328.8 × 238.7 × 17.99 mm（不含脚垫）；约 2.0 kg'],
  ['续航','本地视频最长 15 小时；网页浏览最长 12 小时（官方特定测试配置）'],
  ['键盘与触控板','背光机械键盘、F1–F12 功能键、精准触觉触控板'],
  ['保修','中国市场 Surface 主机 3 年有限硬件保修'],
  ['参考价',known(s.erp_price_cny)?'¥'+Number(s.erp_price_cny).toLocaleString():'未提供'],
 ];
 host.innerHTML='<h3>产品技术规格 · '+escapeHtml(s.part_number)+'</h3><div class="spec-scroll"><table class="spec-table"><tbody>'+rows.map(([name,value])=>`<tr><th scope="row">${escapeHtml(name)}</th><td><b>${escapeHtml(value)}</b></td></tr>`).join('')+'</tbody></table></div><p class="status">系列参数按 <a href="'+microsoftSpecsUrl+'" target="_blank" rel="noopener">微软官方技术规格</a>和 <a href="https://docs.nvidia.com/rtx-spark/rtx-spark-porting-guide/latest/overview.html" target="_blank" rel="noopener">NVIDIA 平台规格</a>展示；处理器档位、内存、存储、颜色与参考价按所选 SKU 显示。实际可用 GPU 内存、续航和性能因配置及工作负载而异。</p>';
}
async function searchFaq(){let q=$('#faqquery').value,c=$('#faqcategory').value,r=await fetch('/api/faq?limit='+(c?250:20)+'&q='+encodeURIComponent(q)+'&category='+encodeURIComponent(c)),d=await r.json();if($('#faqcategory').options.length===1){d.categories.forEach(x=>$('#faqcategory').add(new Option(x,x)))}$('#faqresult').innerHTML=`<p>找到 ${Number(d.total)} 条；知识库共 ${Number(d.concept_total)} 个独立概念、${Number(d.indexed_total)} 条问答。</p>`+d.items.map(x=>{const sourceUrl=safeSourceUrl(x.source_url),comparisonUrl=safeSourceUrl(x.comparison_source_url);return `<article class="card"><h3>${escapeHtml(x.question)}</h3><span class="tag">${escapeHtml(x.category)}</span><p>${escapeHtml(x.easy_answer)}</p><p class="status"><b>工程说明：</b>${escapeHtml(x.expert_answer)}</p><p class="warn"><b>常见误区：</b>${escapeHtml(x.misconception)}</p><p><b>销售提示：</b>${escapeHtml(x.sales_tip)}</p>${sourceUrl?`<p><a href="${escapeHtml(sourceUrl)}" target="_blank" rel="noopener noreferrer">查看官方来源</a>${comparisonUrl?`　<a href="${escapeHtml(comparisonUrl)}" target="_blank" rel="noopener noreferrer">查看对比方官方规格</a>`:''}</p>`:''}</article>`}).join('')}
function render(){if(!data)return;let s=data.sku;$('#product').textContent=`${s.product_family} · ${s.part_number}`;$('#metrics').innerHTML=metric('平台',s.platform_code)+metric('统一内存',s.memory_gb+' GB')+metric('存储',s.storage_tb+' TB')+metric('ERP 含税价',s.erp_price_cny?'¥'+Number(s.erp_price_cny).toLocaleString():'未知')+metric('CPU',s.cpu_model)+metric('GPU',s.gpu_model)+metric('颜色',s.color)+metric('操作系统',s.operating_system);renderProductDetails(s);let html='';if(tab==='ai')html=aiStarter(s)+cards(data.ai)+'<h3>同档经验推荐</h3>'+cards(data.ai_recommendations)+'<h3>RTX Spark 官方生态更新（非本 SKU 实测）</h3>'+cards(data.ai_official_updates);else if(tab==='gaming')html=cards(data.gaming)+'<h3>同档经验推荐</h3>'+cards(data.gaming_recommendations)+'<h3>RTX Spark 官方生态更新（非本 SKU FPS）</h3>'+cards(data.gaming_official_updates);else if(tab==='generation')html=cards(data.generation);else if(tab==='productivity')html=cards(data.productivity);else if(tab==='deployment')html=`<div class="card"><h3>本机模型部署与企业私有知识</h3><p>针对当前 ${escapeHtml(s.part_number)} 配置，逐步核对系统架构、模型许可、运行后端、真实任务与数据安全；包含个人试用、开发集成、多人服务、RAG 和微调的选择与验收。</p><p><a href="/deployment?sku=${encodeURIComponent(s.part_number)}">打开此配置的详细部署指南 →</a></p><p class="warn">指南是工程操作建议；模型是否能运行、GPU 加速和速度均需在目标设备实测。</p></div>`;else if(tab==='faq')html=faqForm();else if(tab==='tco')html=tcoForm(s);else html=`<div class="card"><h3>数据边界</h3><p>${escapeHtml(data.disclaimer)}</p><p class="warn">平台级 1440p / 100 FPS、120B+ 或理论峰值不能转换为本 SKU 的 FPS、Token/s 或稳定运行承诺。</p><p><b>配置状态：</b>${escapeHtml(s.data_status)}</p><p><b>来源：</b>${escapeHtml(s.source_reference)}</p><p><b>备注：</b>${escapeHtml(s.note)}</p></div>`;$('#content').innerHTML=html;if(tab==='faq')searchFaq();if(tab==='tco')loadTcoDefaults(s)}
async function choose(p){$('#load').textContent='载入中…';try{let r=await fetch('/api/catalog/advisor/'+encodeURIComponent(p));if(!r.ok)throw Error('读取失败');data=await r.json();render();$('#load').textContent=''}catch(e){$('#load').textContent=e.message}}
async function init(){try{let r=await fetch('/api/catalog/imported-skus');if(r.status===401||r.status===403){$('#load').textContent='请先登录并确认 License 有效';$('#content').innerHTML='<div class="empty">此部署已启用访问保护。请前往 <a href="/account">账号页登录</a>，再刷新本页。</div>';return}if(!r.ok)throw Error('产品数据请求失败');let j=await r.json(),sel=$('#sku');if(!j.items.length){sel.innerHTML='<option>尚未导入 V3.4 工作簿</option>';$('#content').innerHTML='<div class="empty">请先运行授权工作簿导入。</div>';return}j.items.sort((a,b)=>{let ap=Number(a.erp_price_cny),bp=Number(b.erp_price_cny);return (a.erp_price_cny==null?Infinity:ap)-(b.erp_price_cny==null?Infinity:bp)||String(a.part_number).localeCompare(String(b.part_number))});sel.innerHTML=j.items.map(x=>`<option value="${escapeHtml(x.part_number)}">${escapeHtml(x.part_number)} · ${escapeHtml(platformLabel(x.platform_code))} · ${escapeHtml(x.memory_gb)}GB / ${escapeHtml(x.storage_tb)}TB · ${x.erp_price_cny==null?'价格待确认':'¥'+Number(x.erp_price_cny).toLocaleString()}</option>`).join('');sel.onchange=()=>choose(sel.value);choose(sel.value)}catch(error){$('#load').textContent='载入失败';$('#content').textContent=error.message}}
$('#tabs').onclick=e=>{if(e.target.tagName!=='BUTTON')return;document.querySelectorAll('.tabs button').forEach(b=>b.classList.remove('active'));e.target.classList.add('active');tab=e.target.dataset.tab;render()};loadQuickOptions();init();
</script></body></html>'''.replace(
  '</div></header>',
  '<p><a href="/guest" style="display:inline-block;background:#fff;color:#0b1220;font-weight:700;text-decoration:none;padding:11px 17px;border-radius:9px;margin-top:12px">游客体验 · 无需登录 →</a> <a href="/account" style="color:#fff;margin-left:14px">员工与 DMP 登录</a></p></div></header>',
  1,
 )
 import re
 quick_section = re.search(r'<section class="panel" id="quick-lookup">.*?</section>', page).group(0)
 quick_start = page.index('const quickMoney=')
 quick_end = page.index('const inWechat=')
 quick_script = page[quick_start:quick_end]
 nav = '<nav class="panel"><a href="/surface">全品类 Surface SKU 查询</a>　·　<a href="/">RTX Spark 能力顾问</a></nav>'
 if surface:
  styles = ''.join(re.findall(r'<style>.*?</style>', page, re.S))
  helpers = page[page.index('const $='):quick_start]
  quick_section = quick_section.replace('<div class="quick-actions"><label>报价系数', '<div class="quick-actions"><label hidden>报价系数')
  quick_section = quick_section.replace('<label>大系列' , '<label>处理器大类<select id="quick-platform"><option value="">全部处理器</option><option value="Intel">英特尔 Intel</option><option value="Snapdragon">高通 Snapdragon</option></select></label><label>大系列')
  quick_section = quick_section.replace('<label>ERP 价格上限', '<label>存储<select id="quick-storage"><option value="">全部存储</option></select></label><label>ERP 价格上限')
  quick_section = quick_section.replace('<label>存储', '<label>屏幕大小<select id="quick-screen"><option value="">全部尺寸</option><option value="12">12 英寸</option><option value="13">13 英寸</option><option value="13.8">13.8 英寸</option><option value="15">15 英寸</option></select></label><label>存储')
  quick_script = quick_script.replace("params.set('limit','300');", "params.set('limit','300');if($('#quick-screen').value)params.set('screen_size',$('#quick-screen').value);")
  quick_script = quick_script.replace("function resetQuickSearch(){", "function resetQuickSearch(){$('#quick-screen').value='';")
  quick_script = quick_script.replace("params.set('limit','300');", "params.set('limit','300');if($('#quick-platform').value)params.set('processor', $('#quick-platform').value);if($('#quick-storage').value)params.set('storage_capacity',$('#quick-storage').value);if(['配件','延保'].includes(type)){for(const key of ['q','series','memory_gb','max_erp_price_cny','processor','storage_capacity'])params.delete(key);}")
  quick_script = quick_script.replace('payload.memory_gb.forEach', "(payload.storage_capacity||[]).forEach(value=>$('#quick-storage').add(new Option(value,value)));payload.memory_gb.forEach")
  quick_script = quick_script.replace("function resetQuickSearch(){", "function resetQuickSearch(){$('#quick-storage').value='';")
  quick_script += "const deviceFilters=['#quick-query','#quick-series','#quick-memory','#quick-platform','#quick-storage','#quick-max-price'];function syncCategoryFilters(){const independent=['配件','延保'].includes($('#quick-type').value);deviceFilters.forEach(id=>{const element=$(id);element.disabled=independent;element.closest('label').hidden=independent});}$('#quick-type').addEventListener('change',syncCategoryFilters);$('#quick-storage').addEventListener('change',runQuickSearch);$('#quick-reset').addEventListener('click',syncCategoryFilters);"
  quick_script += "deviceFilters.push('#quick-screen');$('#quick-screen').addEventListener('change',runQuickSearch);"
  quick_section = quick_section.replace('<label>屏幕大小', '<label>联网版本<select id="quick-network"><option value="">全部版本</option><option value="wifi">Wi-Fi 版</option><option value="5g">5G 版</option></select></label><label>屏幕大小')
  quick_script = quick_script.replace("params.set('limit','300');", "params.set('limit','300');if($('#quick-network').value)params.set('network',$('#quick-network').value);")
  quick_script = quick_script.replace("function resetQuickSearch(){", "function resetQuickSearch(){$('#quick-network').value='';")
  quick_script += "deviceFilters.push('#quick-network');$('#quick-network').addEventListener('change',runQuickSearch);"
  quick_script = quick_script.replace("function resetQuickSearch(){", "function resetQuickSearch(){$('#quick-platform').value='';")
  quick_script = quick_script.replace('查看完整映射</button>', '查看完整映射</button> <button type="button" data-quick-pdf="${escapeHtml(item.part_number)}">下载 PDF 产品资料</button>')
  pdf_script = r'''async function downloadSurfacePdf(pn){try{if(/MicroMessenger/i.test(navigator.userAgent)){if(!window.wx||!wx.miniProgram)throw Error('请通过小程序重新打开查询页');const inMini=window.__wxjs_environment==='miniprogram'||await new Promise(resolve=>wx.miniProgram.getEnv(r=>resolve(r.miniprogram)));if(!inMini)throw Error('请从小程序进入查询后下载 PDF');const ticketResponse=await fetch('/api/reports/mobile-ticket',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({part_number:pn,report_kind:'surface'})});if(!ticketResponse.ok)throw Error('下载授权失败，请重新登录');const ticket=await ticketResponse.json();wx.miniProgram.navigateTo({url:'/pages/report/index?ticket='+encodeURIComponent(ticket.ticket)+'&filename='+encodeURIComponent(ticket.filename),fail:()=>{$('#quick-status').textContent='请更新小程序版本后重试'}});return;}const r=await fetch('/api/catalog/quick-search/'+encodeURIComponent(pn)+'/pdf');if(!r.ok)throw Error('PDF 下载失败，请检查登录授权');const url=URL.createObjectURL(await r.blob());const a=document.createElement('a');a.href=url;a.download='Surface-Product-'+pn.replace(/[^A-Za-z0-9_-]/g,'-')+'.pdf';a.click();setTimeout(()=>URL.revokeObjectURL(url),60000)}catch(e){$('#quick-status').textContent=e.message}}$('#quick-results').addEventListener('click',e=>{const b=e.target.closest('[data-quick-pdf]');if(b)downloadSurfacePdf(b.dataset.quickPdf)});document.querySelectorAll('#quick-type,#quick-series,#quick-memory,#quick-platform').forEach(e=>e.addEventListener('change',runQuickSearch));loadQuickOptions();'''
  return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>全品类 Surface SKU 查询</title>'+styles+'</head><body><header class="top"><div class="wrap"><h1>全品类 Surface SKU 快速查询</h1></div><div class="wrap" style="text-align:right;padding:0 0 10px"><a lang="zh-CN" href="/surface" aria-current="page" style="color:#fff">中文</a> <span aria-hidden="true"> | </span> <a lang="en" href="/en/surface" style="color:#fff">English</a></div></header><main class="wrap">'+nav+quick_section+'</main><footer>© 2026 上海以和信息技术有限公司。保留所有权利。</footer><script src="https://res.wx.qq.com/open/js/jweixin-1.6.0.js"></script><script>'+helpers+quick_script+pdf_script+'</script></body></html>'
 page = page.replace(quick_section, nav).replace(quick_script, '').replace('loadQuickOptions();init();','init();')
 return page
