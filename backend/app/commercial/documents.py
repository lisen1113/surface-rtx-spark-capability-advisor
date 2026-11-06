"""Customer-safe PDF output generated only from the customer snapshot."""
from html import escape
from datetime import datetime, timedelta, timezone
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from ..report_pdf import FONT


def display_time(value):
    return datetime.fromisoformat(value).astimezone(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S 北京时间")


def build_quote_pdf(quote):
    data = quote["customer"]
    formal = quote.get("state") == "issued"
    output = BytesIO()
    body = ParagraphStyle("commercial-body", fontName=FONT, fontSize=9, leading=14, wordWrap="CJK", spaceAfter=6)
    title = ParagraphStyle("commercial-title", parent=body, fontSize=18, leading=26, spaceAfter=14)
    heading = ParagraphStyle("commercial-heading", parent=body, fontSize=12, leading=18, spaceBefore=10)
    def p(text, style=body):
        return Paragraph(escape(str(text)), style)
    def table(rows, widths):
        result = Table([[p(value) for value in row] for row in rows], colWidths=widths, repeatRows=1, hAlign="LEFT")
        result.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e9eef5")),
            ("GRID", (0, 0), (-1, -1), .5, colors.HexColor("#d9d9d9")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        return result
    story = [p("Surface 与 M365 Copilot 正式报价" if formal else "Surface 与 M365 Copilot 预算方案", title),
             p(data["title"]), p("报价编号：" + (quote.get("formal_number") or quote["id"])),
             p(f"有效期至 {data['valid_until']}　测算期 {data['term_months']} 个月　金额币种 CNY")]
    profile = quote.get("profile") or {}
    for label, key in (("使用公司", "company_name"), ("签约公司", "contracting_company"),
                       ("地址", "address"), ("联系人", "contact_name"), ("邮箱", "contact_email")):
        if profile.get(key):
            story.append(p(label + "：" + profile[key]))
    if data.get("personas"):
        story += [p("项目需求", heading), p(data["personas"])]
    if data["hardware"]:
        story.append(p("设备与租赁", heading))
        rows = [["产品与配置", "数量", "单台月租", "月租小计"]]
        for item in data["hardware"]:
            rows.append([f"{item['part_number']} {item['name']}\n{item['configuration']}", item["quantity"], item["unit_monthly_cny"], item["monthly_cny"]])
        story.append(table(rows, [275, 42, 78, 78]))
    if data["cloud"]:
        story.append(p("软件订阅", heading))
        rows = [["产品", "席位", "USD 每人月均", "CNY 年付含税"]]
        for item in data["cloud"]:
            rows.append([item.get("user_group", "全体用户") + " " + item["name"], item["seats"], item["standard_unit_monthly_usd"], item["annual_due_cny"]])
        story.append(table(rows, [255, 42, 88, 88]))
    story += [p("项目费用", heading),
              table([["项目", "金额 CNY"], ["优惠前总额", data["before_discount_cny"]],
                     ["整体项目优惠", data["project_discount_cny"]], ["合同期间预计总额", data["total_cny"]],
                     ["月均预算", data["average_monthly_cny"]], ["初始付款", data["first_payment_cny"]]], [335, 138]),
              p("月均预算仅用于比较；实际付款按下列计划。"), p("付款计划", heading)]
    rows = [["月份", "设备", "软件", "服务", "优惠", "应付 CNY"]]
    for item in data["payment_schedule"]:
        if item["due_cny"] != "0.00" or item["discount_cny"] != "0.00":
            rows.append([item[k] for k in ("month", "hardware_cny", "cloud_cny", "service_cny", "discount_cny", "due_cny")])
    story.append(table(rows, [40, 82, 95, 80, 78, 98]))
    story += [p("价格与商务说明", heading),
              p(f"软件 USD/CNY 汇率 {data['fx']['usd_cny']}，日期 {data['fx']['date']}，依据 {data['fx']['reference']}。"),
              p(f"软件税率 {data['tax']['cloud_rate']}。{data['tax']['hardware']}。")]
    for warning in data["warnings"]:
        story.append(p(warning))
    if data.get("discount_reason"):
        story.append(p("项目优惠说明：" + data["discount_reason"]))
    if formal:
        story += [p("正式商务条款：" + quote["commercial_reference"]),
                  p(f"签发时间：{display_time(quote['issued_at'])}　审批时间：{display_time(quote['reviewed_at'])}"),
                  p("供应方法定信息及适用合同条款以本报价引用的商务文件为准。"),
                  Spacer(1, 18), p("客户确认签字盖章：________________　供应方签字盖章：________________")]
    else:
        story.append(p("预算报价，仅供方案讨论，不构成正式价格、供货、授信或金融承诺。"))
    story += [p("快照校验：" + quote["snapshot_hash"]), p("模板版本：" + data["template_version"])]
    def page(canvas, doc):
        canvas.saveState()
        if not formal:
            canvas.setFillColor(colors.HexColor("#e6e8ec"))
            canvas.setFont(FONT, 44)
            canvas.translate(180, 380)
            canvas.rotate(35)
            canvas.drawString(0, 0, "预算报价")
        canvas.restoreState()
        canvas.saveState()
        canvas.setFont(FONT, 8)
        canvas.drawString(36, 24, "© 2026 上海以和信息技术有限公司。保留所有权利。")
        canvas.drawRightString(A4[0]-36, 24, str(doc.page))
        canvas.restoreState()
    SimpleDocTemplate(output, pagesize=A4, leftMargin=60, rightMargin=60, topMargin=40, bottomMargin=42,
                      title=data["title"], author="上海以和信息技术有限公司").build(story, onFirstPage=page, onLaterPages=page)
    return output.getvalue()
