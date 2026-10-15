"""Printable evidence-backed customer report."""
from html import escape
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import Field
from .auth import require_entitled_user
from .catalog import connection, rows, source_sheet
from .generation import generation_guidance
from .productivity import productivity_guidance
from .recommendation import RecommendationInput, recommend

router=APIRouter(prefix="/api/reports",tags=["reports"])

USAGE_LABELS = {"ai": "本地 AI 模型", "gaming": "游戏", "generation": "生成式 AI", "productivity": "生产力"}


class NeedReportInput(RecommendationInput):
    part_number: str = Field(min_length=1, max_length=80)


def detail_section(title: str, items: list[dict]) -> str:
    """Show the source record, without turning a screening suggestion into a benchmark."""
    if not items:
        return f"<section><h2>{escape(title)}</h2><p>当前料号没有可直接引用的记录；相关能力保持待验证。</p></section>"
    cards = []
    for item in items:
        fields = []
        for key, raw in item.items():
            if key in {"Part Number", "产品系列", "适用SKU", "适用SKU内存档", "source_sha256"} or raw in (None, ""):
                continue
            fields.append(f"<dt>{escape(str(key))}</dt><dd>{escape(str(raw))}</dd>")
        cards.append(f"<article class='record'><dl>{''.join(fields)}</dl></article>")
    return f"<section><h2>{escape(title)}</h2>{''.join(cards)}</section>"


def related_records(items: list[dict], key: str, terms: tuple[str, ...]) -> list[dict]:
    """Keep scenario guidance relevant to the user's selected workload."""
    if not terms:
        return items
    return [item for item in items if any(term.casefold() in str(item.get(key, "")).casefold() for term in terms)]


@router.post("/recommendation", response_class=HTMLResponse)
def recommendation_report(data: NeedReportInput, _user=Depends(require_entitled_user)):
    """Printable report bound to both the submitted need and selected candidate SKU."""
    all_skus = rows("imported_skus")
    sku = next((item for item in all_skus if item["part_number"] == data.part_number), None)
    if sku is None:
        raise HTTPException(404, "未找到该 Part Number")
    result = recommend(data, all_skus)
    candidate = next((item for item in result["items"] if item["part_number"] == data.part_number), None)
    if candidate is None:
        raise HTTPException(422, "该配置不在本次需求的候选结果中，请重新查找配置")
    need = result["interpreted_need"]
    usages = need["usages"]
    game_labels = {"unsure": "尚不确定", "esports": "电竞/网游", "aaa": "3A 大型游戏"}
    work_labels = {"unsure": "尚不确定", "office": "日常办公", "coding": "编程开发", "video": "视频剪辑", "cad": "CAD / 3D"}
    generation_labels = {"unsure": "尚不确定", "image": "图像生成", "video": "视频生成"}
    summary = [
        ("用途", "、".join(USAGE_LABELS[u] for u in usages)),
        ("模型", data.model_name or "未指定"), ("模型规模", need["ai_size"]),
        ("游戏", data.game_titles or "未指定"), ("游戏类型", game_labels[need["game_need"]]),
        ("目标画面", f"{data.target_resolution} / {data.target_fps or '未指定'} FPS"),
        ("软件", data.software_name or "未指定"), ("生产力负载", work_labels[need["work_need"]]),
        ("生成工作流", generation_labels[need["generation_need"]]),
        ("预算上限", f"¥{data.budget_cny:,.0f}" if data.budget_cny else "未指定"),
        ("推荐排序", "优先控制采购价" if data.prefer_lower_price else "优先更大内存"),
        ("自由描述", data.description or "未填写"),
    ]
    summary_html = "".join(f"<tr><th>{escape(key)}</th><td>{escape(str(val))}</td></tr>" for key, val in summary)
    sku_details = [
        ("完整配置描述", sku.get("raw_configuration")), ("颜色", sku.get("color")),
        ("操作系统", sku.get("operating_system")), ("内存说明", sku.get("memory_spec")),
        ("NPU", sku.get("npu_spec")), ("散热", sku.get("thermal_spec")),
        ("导入数据状态", sku.get("data_status")), ("配置来源", sku.get("source_reference")),
    ]
    sku_html = "".join(f"<tr><th>{escape(key)}</th><td>{escape(str(val)) if val not in (None, '') else '未提供/待核验'}</td></tr>" for key, val in sku_details)
    direct = lambda sheet: [item for item in source_sheet(sheet) if item.get("Part Number") == data.part_number]
    recommended = lambda sheet: [item for item in source_sheet(sheet) if data.part_number in str(item.get("适用SKU", item.get("适用SKU内存档", "")))]
    sections = []
    if "ai" in usages:
        sections.append(detail_section("本地 AI：该 SKU 的场景映射（非指定模型实测）", direct("AI能力映射")))
        sections.append(detail_section("本地 AI：经验推荐", recommended("AI经验推荐矩阵")))
    if "gaming" in usages:
        sections.append(detail_section("游戏：该 SKU 的场景映射（非逐款实测）", direct("游戏能力映射")))
        sections.append(detail_section("游戏：经验推荐", recommended("游戏经验推荐矩阵")))
    if "generation" in usages:
        generation_terms = {"image": ("图像", "3D", "创作"), "video": ("视频", "Video", "4:2:2")}.get(data.generation_need, ())
        generation_items = generation_guidance(data.part_number, int(sku.get("memory_gb") or 0), sku.get("platform_code") or "未知平台")
        sections.append(detail_section("生成式 AI：所选工作流指导", related_records(generation_items, "推荐模型/工作负载名称", generation_terms)))
    if "productivity" in usages:
        productivity_terms = {"office": ("Microsoft 365", "Copilot+", "Broadcast"), "coding": ("Visual Studio", "WSL2", "Copilot+"), "video": ("Premiere", "视频剪辑", "Photoshop"), "cad": ("CAD", "Blender")}.get(need["work_need"], ())
        productivity_items = productivity_guidance(data.part_number, int(sku.get("memory_gb") or 0), sku.get("platform_code") or "未知平台")
        specific = related_records(productivity_items, "软件/工作负载", (data.software_name,)) if data.software_name else []
        selected = specific or related_records(productivity_items, "软件/工作负载", productivity_terms)
        sections.append(detail_section("生产力：所选场景指导", selected))
    reasons = "".join(f"<li>{escape(reason)}</li>" for reason in result["reasoning"]) or "<li>尚无进一步量化筛选条件。</li>"
    confirmations = "".join(f"<li>{escape(note)}</li>" for note in result["needs_confirmation"]) or "<li>仍需以目标设备与真实业务任务验收。</li>"
    price = f"¥{float(sku['erp_price_cny']):,.0f}" if sku.get("erp_price_cny") is not None else "未知"
    filename = "按描述需求配置报告-" + "".join(c if c.isascii() and (c.isalnum() or c == "-") else "-" for c in data.part_number)
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>{escape(filename)}</title><style>
body{{font:14px/1.6 system-ui,'Microsoft YaHei',sans-serif;color:#172033;background:#f5f7fb;margin:0}}.page{{max-width:1040px;margin:25px auto;background:white;padding:32px;box-shadow:0 3px 18px #17203312}}header{{border-bottom:3px solid #175cd3;padding-bottom:15px}}header img{{width:190px;height:auto}}h1{{margin:12px 0 4px;font-size:27px}}h2{{font-size:19px;margin:0 0 10px}}section{{margin:24px 0;break-inside:avoid}}.meta{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}.meta div{{background:#eff4ff;padding:12px;border-radius:8px}}table{{width:100%;border-collapse:collapse}}th,td{{border:1px solid #d0d5dd;padding:8px;text-align:left;vertical-align:top}}th{{background:#eaf1fb;width:25%}}.record{{border:1px solid #d0d5dd;border-radius:8px;margin:10px 0;padding:10px;break-inside:avoid}}dl{{display:grid;grid-template-columns:190px 1fr;margin:0}}dt,dd{{padding:6px 8px;border-bottom:1px solid #e4e7ec;margin:0;overflow-wrap:anywhere}}dt{{font-weight:700;background:#f9fafb}}.warn{{background:#fff8ed;border-left:4px solid #b54708;padding:10px 14px}}.status{{color:#586476}}footer{{border-top:1px solid #d0d5dd;margin-top:30px;padding-top:12px;color:#586476;text-align:center}}.actions{{padding:12px 0}}button{{background:#175cd3;color:white;border:0;border-radius:7px;padding:9px 14px;cursor:pointer}}@media(max-width:650px){{.page{{padding:16px;margin:0}}.meta{{grid-template-columns:1fr}}dl{{grid-template-columns:1fr}}}}@media print{{body{{background:white}}.page{{box-shadow:none;padding:0;margin:0;max-width:none}}.actions{{display:none}}@page{{size:A4;margin:15mm}}}}
</style></head><body><div class="page"><header><img src="/assets/yihe-logo.png" alt="上海以和信息技术有限公司"><h1>Surface Laptop Ultra 需求匹配报告</h1><p>料号：<strong>{escape(data.part_number)}</strong> · 本报告只对应下述本次需求</p></header><div class="actions"><button type="button" onclick="window.print()">打印／另存为 PDF</button></div><section><h2>所选产品配置</h2><div class="meta"><div>平台<br><b>{value(sku,'platform_code')}</b></div><div>统一内存<br><b>{value(sku,'memory_gb')} GB</b></div><div>存储<br><b>{value(sku,'storage_tb')} TB</b></div><div>处理器<br><b>{value(sku,'cpu_model')}</b></div><div>图形处理器<br><b>{value(sku,'gpu_model')}</b></div><div>导入参考价<br><b>{escape(price)}</b></div></div><p class="status">配置与价格来自授权导入资料；价格口径：{value(sku,'currency_note')}。采购前须复核。</p><table>{sku_html}</table><p><a href="https://www.microsoftstore.com.cn/surface/surface-laptop-ultra-for-business" target="_blank" rel="noopener">中国微软商城系列技术规格</a>为系列资料，未逐料号核实的参数不作为本报告实测。</p></section><section><h2>本次用户需求</h2><table>{summary_html}</table></section><section><h2>为何列为候选</h2><p>{escape(candidate['reason'])}</p><ul>{reasons}</ul><p class="warn">{escape(result['limitations'])}</p>{'<p class="warn">当前候选超出输入预算。</p>' if candidate['over_budget'] else ''}</section>{''.join(sections)}<section><h2>待确认与验收</h2><ul>{confirmations}</ul><p>请在目标设备验证 Windows on Arm 软件/驱动兼容性、实际模型量化与上下文、游戏版本/画质、业务任务正确性及稳定性。未测得的 FPS、Token/s 保持未知。</p></section><footer>© 2026 上海以和信息技术有限公司。保留所有权利。</footer></div></body></html>'''

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
def customer_report(part_number:str, _user=Depends(require_entitled_user)):
 with connection() as conn:
  row=conn.execute("SELECT * FROM imported_skus WHERE part_number=?",(part_number,)).fetchone()
 if not row: raise HTTPException(404,"未找到该 Part Number")
 sku=dict(row)
 direct=lambda sheet:[x for x in source_sheet(sheet) if x.get("Part Number")==part_number]
 body=section("AI 模型能力",direct("AI能力映射"),("目标模型/场景",),("本地运行判断","预计输出速度_Token/s"))
 body+=section("游戏能力",direct("游戏能力映射"),("游戏名称",),("兼容性状态","平均FPS"))
 body+=section("生成式 AI",generation_guidance(part_number, int(sku.get("memory_gb") or 0), sku.get("platform_code") or "未知平台"),("推荐模型/工作负载名称",),("本地运行判断","经验推荐与我的判断"))
 body+=section("生产力能力",productivity_guidance(part_number, int(sku.get("memory_gb") or 0), sku.get("platform_code") or "未知平台"),("软件/工作负载",),("兼容性状态","经验推荐与我的判断"))
 return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>{escape(part_number)} 客户能力报告</title><style>
body{{font:14px/1.55 system-ui,'Microsoft YaHei',sans-serif;color:#172033;max-width:1000px;margin:35px auto;padding:20px}}h1{{font-size:28px}}h2{{margin-top:28px;font-size:20px}}.meta{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}.meta div{{background:#f5f7fa;padding:10px}}table{{width:100%;border-collapse:collapse}}th,td{{border:1px solid #d0d5dd;padding:8px;text-align:left;vertical-align:top}}th{{background:#eaf1fb}}.notice{{margin-top:28px;color:#7a2e0e}}footer{{margin-top:36px;color:#667085}}@media print{{body{{margin:0}}}}
</style></head><body><img src="/assets/yihe-logo.png" alt="上海以和信息技术有限公司" style="width:200px;height:auto;display:block;margin:0 0 20px"><h1>Surface Laptop Ultra 客户能力报告</h1><p>Part Number：<b>{escape(part_number)}</b></p><div class="meta"><div>平台<br><b>{value(sku,'platform_code')}</b></div><div>统一内存<br><b>{value(sku,'memory_gb')} GB</b></div><div>存储<br><b>{value(sku,'storage_tb')} TB</b></div><div>CPU<br><b>{value(sku,'cpu_model')}</b></div><div>GPU<br><b>{value(sku,'gpu_model')}</b></div><div>ERP 参考价<br><b>¥{value(sku,'erp_price_cny')}</b></div></div>{body}<div class="notice"><b>重要限制：</b>本报告严格区分官方声明、实测、经验推荐与未知。平台级 1440p/100 FPS、120B+ 或理论峰值不能转换为本 SKU 的性能保证；空白 Token/s、FPS 和兼容性字段保持未知。</div><footer>© 2026 上海以和信息技术有限公司。保留所有权利。</footer></body></html>'''
