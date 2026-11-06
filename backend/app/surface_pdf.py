"""Product-specific Surface specification downloads."""
from html import escape
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from .report_pdf import FONT


def build_surface_pdf(item: dict) -> bytes:
    output = BytesIO()
    body = ParagraphStyle('surface-body', fontName=FONT, fontSize=10, leading=16, wordWrap='CJK', spaceAfter=7)
    title = ParagraphStyle('surface-title', parent=body, fontSize=18, leading=25, spaceAfter=16)
    fields = [
        ('Part Number', 'part_number'), ('产品名称', 'product_name'), ('产品类别', 'product_type'),
        ('原始配置', 'raw_description'), ('处理器平台', 'platform'), ('CPU', 'cpu_official'),
        ('内存 GB', 'memory_gb'), ('存储', 'storage_capacity'), ('颜色', 'color'),
        ('联网', 'connectivity'), ('电源', 'power_supply'), ('屏幕', 'display'),
        ('分辨率', 'resolution'), ('刷新率', 'refresh_rate'), ('NPU', 'npu'), ('GPU', 'gpu'),
        ('重量', 'weight'), ('续航', 'battery'), ('操作系统', 'operating_system'),
        ('ERP 含税价（元，用户原表）', 'erp_price_cny'), ('匹配级别', 'match_level'),
        ('待核对字段', 'unknown_fields'), ('复核说明', 'exception_note'),
        ('官方来源', 'official_source_url'), ('来源日期', 'source_checked_at'),
    ]
    story = [Paragraph('Surface 产品资料', title)]
    def add(label, value):
        if value is not None and value != '':
            story.append(Paragraph(escape(str(label)) + '：' + escape(str(value)), body))
    for label, key in fields:
        add(label, item.get(key))
    for key, value in item.get('service_details', {}).items():
        if key not in ('序号', '原行号', 'ERP 含税价', 'ADR Price', 'Part Number'):
            add(key, value)
    story.extend([Spacer(1, 12), Paragraph('© 2026 上海以和信息技术有限公司。保留所有权利。', body)])
    SimpleDocTemplate(output, pagesize=A4, leftMargin=42, rightMargin=42, topMargin=42, bottomMargin=42,
                      title='Surface 产品资料 - ' + item['part_number']).build(story)
    return output.getvalue()
