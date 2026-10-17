"""Downloadable, evidence-labeled customer PDF for one imported SKU."""

from html import escape
from io import BytesIO
import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, PageTemplate, Paragraph, Spacer,
)

from .catalog import source_sheet
from .generation import generation_guidance
from .productivity import productivity_guidance
from .spark_updates import agent_guidance, gaming_updates


_font_candidates = (
    Path(os.environ.get("CAPABILITY_PDF_FONT_PATH", "/opt/capability-advisor/fonts/NotoSansSC-VF.ttf")),
    Path("C:/Windows/Fonts/NotoSansSC-VF.ttf"),
)
_font_file = next((path for path in _font_candidates if path.is_file()), None)
if _font_file:
    FONT = "NotoSansSC"
    pdfmetrics.registerFont(TTFont(FONT, str(_font_file)))
else:
    FONT = "STSong-Light"
    pdfmetrics.registerFont(UnicodeCIDFont(FONT))
PAGE_W, PAGE_H = A4


def _text(value: object) -> str:
    return "未知/待验证" if value in (None, "") else str(value)


def build_customer_pdf(sku: dict) -> bytes:
    """Keep source and confidence labels visible; never infer missing benchmarks."""
    part_number = str(sku["part_number"])
    styles = {
        "title": ParagraphStyle("title", fontName=FONT, fontSize=19, leading=27,
                                textColor=colors.HexColor("#142b55"), spaceAfter=14),
        "heading": ParagraphStyle("heading", fontName=FONT, fontSize=12.5, leading=19,
                                  textColor=colors.HexColor("#175cd3"), spaceBefore=13, spaceAfter=6),
        "body": ParagraphStyle("body", fontName=FONT, fontSize=9.5, leading=15,
                               wordWrap="CJK", spaceAfter=5),
        "small": ParagraphStyle("small", fontName=FONT, fontSize=8.5, leading=13,
                                wordWrap="CJK", textColor=colors.HexColor("#344054"), spaceAfter=4),
        "footer": ParagraphStyle("footer", fontName=FONT, fontSize=8, leading=12,
                                 alignment=TA_CENTER, textColor=colors.HexColor("#667085")),
    }
    content = []
    logo = Path(__file__).with_name("assets") / "yihe-logo.png"
    if logo.is_file():
        content.extend((Image(str(logo), width=145, height=56, kind="proportional"), Spacer(1, 8)))
    content.extend((Paragraph("Surface Laptop Ultra 客户能力报告", styles["title"]),
                    Paragraph(f"Part Number：{escape(part_number)}", styles["body"]),
                    Paragraph("导入配置与来源", styles["heading"])))
    fields = (
        ("平台", "platform_code"), ("统一内存", "memory_gb"),
        ("存储", "storage_tb"), ("CPU", "cpu_model"),
        ("GPU", "gpu_model"), ("ERP 参考价（元）", "erp_price_cny"),
        ("操作系统", "operating_system"), ("完整配置", "raw_configuration"),
        ("数据状态", "data_status"), ("配置来源", "source_reference"),
    )
    for label, key in fields:
        content.append(Paragraph(f"<b>{escape(label)}：</b>{escape(_text(sku.get(key)))}", styles["body"]))

    direct = lambda sheet: [row for row in source_sheet(sheet) if row.get("Part Number") == part_number]
    groups = (
        ("AI 模型能力", direct("AI能力映射")),
        ("AI 官方生态更新（非本 SKU 实测）", agent_guidance(part_number, int(sku.get("memory_gb") or 0))),
        ("游戏能力", direct("游戏能力映射")),
        ("游戏官方生态更新（非本 SKU FPS）", gaming_updates(part_number)),
        ("生成式 AI", generation_guidance(part_number, int(sku.get("memory_gb") or 0), sku.get("platform_code") or "未知平台")),
        ("生产力能力", productivity_guidance(part_number, int(sku.get("memory_gb") or 0), sku.get("platform_code") or "未知平台")),
    )
    for title, records in groups:
        content.append(Paragraph(escape(title), styles["heading"]))
        if not records:
            content.append(Paragraph("该 SKU 暂无经过验证的直接映射；相关能力保持未知/待验证。", styles["body"]))
            continue
        for record in records:
            items = []
            for key, value in record.items():
                if key in ("Part Number", "source_sha256") or value in (None, ""):
                    continue
                items.append(Paragraph(f"<b>{escape(str(key))}：</b>{escape(str(value))}", styles["small"]))
            if items:
                content.extend(items)
                content.append(Spacer(1, 7))

    content.append(Paragraph("证据边界与验收", styles["heading"]))
    content.append(Paragraph(
        "官方声明、独立实测、工程估算与未知必须分别理解。平台级声明不能转换为该 SKU 的性能保证；"
        "空白 Token/s、FPS 和兼容性字段保持未知。请在目标设备验证软件/驱动、实际模型、游戏画质、"
        "业务任务正确性及持续运行稳定性。", styles["body"]))
    content.append(Paragraph("© 2026 上海以和信息技术有限公司。保留所有权利。", styles["footer"]))

    stream = BytesIO()
    document = BaseDocTemplate(stream, pagesize=A4, leftMargin=43, rightMargin=43,
                               topMargin=45, bottomMargin=45,
                               title=f"Surface Laptop Ultra 客户能力报告 - {part_number}",
                               author="上海以和信息技术有限公司")
    frame = Frame(document.leftMargin, document.bottomMargin, document.width, document.height,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)

    def page_number(canvas, doc):
        canvas.saveState()
        canvas.setFont(FONT, 8)
        canvas.setFillColor(colors.HexColor("#667085"))
        canvas.drawRightString(PAGE_W - 43, 26, f"第 {doc.page} 页")
        canvas.restoreState()

    document.addPageTemplates(PageTemplate(id="customer", frames=[frame], onPage=page_number))
    document.build(content)
    return stream.getvalue()
