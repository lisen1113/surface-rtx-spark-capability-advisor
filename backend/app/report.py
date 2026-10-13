"""Printable evidence-backed customer report."""
from html import escape
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from .catalog import connection, source_sheet

router=APIRouter(prefix="/api/reports",tags=["reports"])

def value(item,key):
 v=item.get(key)
 return "未知/待验证" if v in (None,"") else escape(str(v))

def section(title,items,title_keys,result_keys):
 rows=[]
 for item in items:
  name=next((value(item,k) for k in title_keys if item.get(k) not in (None,"")),"能力记录")
  result=next((value(item,k) for k in result_keys if item.get(k) not in (None,"")),"未知/待验证")
  evidence=value(item,"证据等级") if item.get("证据等级") else value(item,"数据类型（官方/实测/估算）")
  source=item.get("Benchmark来源/链接") or item.get("来源/链接") or item.get("官方来源URL") or "未提供独立来源"
  rows.append(f"<tr><td>{name}</td><td>{result}</td><td>{evidence}</td><td>{escape(str(source))}</td></tr>")
 if not rows: rows=["<tr><td colspan='4'>该 SKU 暂无经过验证的直接映射。</td></tr>"]
 return f"<h2>{title}</h2><table><thead><tr><th>工作负载</th><th>判断/结果</th><th>证据等级</th><th>来源</th></tr></thead><tbody>{''.join(rows)}</tbody></table>"

@router.get("/{part_number}.html",response_class=HTMLResponse)
def customer_report(part_number:str):
 with connection() as conn:
  row=conn.execute("SELECT * FROM imported_skus WHERE part_number=?",(part_number,)).fetchone()
 if not row: raise HTTPException(404,"未找到该 Part Number")
 sku=dict(row)
 direct=lambda sheet:[x for x in source_sheet(sheet) if x.get("Part Number")==part_number]
 body=section("AI 模型能力",direct("AI能力映射"),("目标模型/场景",),("本地运行判断","预计输出速度_Token/s"))
 body+=section("游戏能力",direct("游戏能力映射"),("游戏名称",),("兼容性状态","平均FPS"))
 body+=section("生成式 AI",direct("生成能力映射"),("推荐模型/工作负载名称",),("经验推荐与我的判断","官方基准结果"))
 body+=section("生产力能力",direct("生产力能力映射"),("软件/工作负载",),("兼容性状态","实测结果"))
 return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>{escape(part_number)} 客户能力报告</title><style>
body{{font:14px/1.55 system-ui,'Microsoft YaHei',sans-serif;color:#172033;max-width:1000px;margin:35px auto;padding:20px}}h1{{font-size:28px}}h2{{margin-top:28px;font-size:20px}}.meta{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}.meta div{{background:#f5f7fa;padding:10px}}table{{width:100%;border-collapse:collapse}}th,td{{border:1px solid #d0d5dd;padding:8px;text-align:left;vertical-align:top}}th{{background:#eaf1fb}}.notice{{margin-top:28px;color:#7a2e0e}}footer{{margin-top:36px;color:#667085}}@media print{{body{{margin:0}}}}
</style></head><body><h1>Surface Laptop Ultra 客户能力报告</h1><p>Part Number：<b>{escape(part_number)}</b></p><div class="meta"><div>平台<br><b>{value(sku,'platform_code')}</b></div><div>统一内存<br><b>{value(sku,'memory_gb')} GB</b></div><div>存储<br><b>{value(sku,'storage_tb')} TB</b></div><div>CPU<br><b>{value(sku,'cpu_model')}</b></div><div>GPU<br><b>{value(sku,'gpu_model')}</b></div><div>ERP 参考价<br><b>¥{value(sku,'erp_price_cny')}</b></div></div>{body}<div class="notice"><b>重要限制：</b>本报告严格区分官方声明、实测、经验推荐与未知。平台级 1440p/100 FPS、120B+ 或理论峰值不能转换为本 SKU 的性能保证；空白 Token/s、FPS 和兼容性字段保持未知。</div><footer>© 2026 上海以和信息技术有限公司。保留所有权利。Microsoft、Surface、NVIDIA、RTX 等商标归各自权利人所有。</footer></body></html>'''
