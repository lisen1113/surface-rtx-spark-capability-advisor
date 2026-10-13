"""Minimal local UI; future Next.js frontend will replace this starter."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
router = APIRouter()
@router.get("/", response_class=HTMLResponse)
def index():
 return """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
 <title>Surface / RTX Spark PC Capability Advisor V3.0</title>
 <style>body{font:16px system-ui,'Microsoft YaHei',sans-serif;background:#f5f7fb;color:#172033;margin:0}
 main{max-width:920px;margin:48px auto;padding:24px}header,section{background:white;border:1px solid #e3e8ef;border-radius:16px;padding:24px;margin-bottom:18px}
 h1{font-size:27px}a{color:#1764bc}button{background:#1758b5;color:white;border:0;padding:11px 18px;border-radius:8px;cursor:pointer}
 input{padding:10px;border:1px solid #aebaca;border-radius:8px;width:120px}small{color:#64748b}footer{text-align:center;color:#64748b;padding:25px}
 .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}.tile{padding:16px;background:#f4f7fc;border-radius:12px}</style></head>
 <body><main><header><small>本地开发预览 · V3.0</small><h1>Surface / RTX Spark PC Capability Advisor</h1>
 <p>Surface Laptop Ultra · AI 本地模型 · 游戏 · 生产力 · 部署指导</p>
 <small>当前仅开放演示查询；用户登录和授权功能尚未完成，不应部署至公网。</small></header>
 <section><h2>能力顾问</h2><div class="grid"><div class="tile">AI 模型推荐<br><small>开发中</small></div>
 <div class="tile">游戏能力<br><small>待导入验证数据</small></div><div class="tile">生产力软件<br><small>开发中</small></div>
 <div class="tile">部署与 AI 知识库<br><small>开发中</small></div></div></section>
 <section><h2>模型权重内存估算</h2><p><label>参数 B <input id="params" type="number" min="1" value="70"></label>
 <label>量化 bit <input id="bits" type="number" min="1" value="4"></label></p>
 <button onclick="estimate()">计算理论容量</button><p id="result" role="status"></p>
 <small>工程估算：不含量化元数据、KV Cache、运行时开销；不能保证模型可运行或 Token/s。</small></section>
 <section><h2>本地 API 与数据</h2><p><a href="/docs">API 文档</a> · <a href="/api/catalog/skus">SKU 列表</a> ·
 <a href="/api/catalog/sources">官方来源台账</a></p></section>
 <footer>© 2026 上海以和信息技术有限公司。保留所有权利。<br>
 <small>Microsoft、Surface、NVIDIA、RTX 商标归各自权利人所有。</small></footer></main>
 <script>async function estimate(){let el=document.getElementById('result');el.textContent='计算中…';
 try{let r=await fetch('/api/estimate/memory',{method:'POST',headers:{'Content-Type':'application/json'},
 body:JSON.stringify({parameters_billion:Number(document.getElementById('params').value),bits_per_weight:Number(document.getElementById('bits').value)})});
 if(!r.ok)throw Error('参数不正确');let d=await r.json();el.textContent='理论权重 '+d.estimated_weight_gb+' GB；剩余预算 '+d.available_budget_gb+' GB（仅供估算）'}
 catch(e){el.textContent='计算失败：'+e.message}}</script></body></html>"""
