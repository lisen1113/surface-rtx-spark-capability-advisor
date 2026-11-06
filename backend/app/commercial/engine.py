"""Deterministic decimal pricing, separated customer and internal snapshots."""
from datetime import date
from contextlib import closing
from decimal import Decimal, ROUND_HALF_UP, localcontext
import json
import sqlite3
import re

from fastapi import HTTPException
from .. import catalog
from . import store, settings, rental

D = Decimal
CENT = D("0.01")
COST_FACTOR = D("0.85")
TEMPLATE_VERSION = "commercial-2026-11-v1"


def money(value):
    return D(value).quantize(CENT, rounding=ROUND_HALF_UP)


def cash(value):
    return format(money(value), ".2f")


def today():
    # Business dates are China time, independent of the deployment host timezone.
    from datetime import datetime, timedelta, timezone
    return datetime.now(timezone(timedelta(hours=8))).date()


def catalog_items():
    # Read only. No schema creation and no modification of the existing ERP data.
    try:
        with closing(sqlite3.connect(catalog.DB_PATH.as_uri() + "?mode=ro", uri=True)) as conn:
            conn.row_factory = sqlite3.Row
            items={r['part_number']:dict(r) for r in conn.execute("SELECT * FROM sku_lookup WHERE match_level NOT LIKE 'N/A%' ORDER BY part_number")}
            # A reviewed Part Number must exist in both datasets. ERP price and
            # original description remain from sku_lookup; specs are enriched
            # only from that exact SKU, never inferred from the platform name.
            rows=conn.execute("""SELECT l.*,s.memory_gb AS spark_memory,s.storage_tb AS spark_storage,
                s.source_sha256 AS spark_source_sha256 FROM sku_lookup l JOIN imported_skus s ON l.part_number=s.part_number
                WHERE l.original_family='Surface Laptop Ultra' AND s.product_family='Surface Laptop Ultra'
                AND l.product_type LIKE 'NVIDIA%' AND s.platform_code IN ('S2','S3')""")
            for row in rows:
                item=dict(row)
                memory=item.pop('spark_memory');storage=item.pop('spark_storage')
                item['spec_source_sha256']=item.pop('spark_source_sha256')
                item['source_product_type']=item['product_type']
                item['rental_family']='RTX Spark'
                item['product_type']='RTX Spark 设备'
                item['series_group']='Laptop Ultra（RTX Spark）'
                item['product_name']='Surface Laptop Ultra（RTX Spark）'
                if item['memory_gb'] is None:item['memory_gb']=memory
                if not item['storage_capacity'] and storage is not None:
                    matches=re.findall(r'(\d+(?:\.\d+)?)\s*(TB|TGB|GB)',item['raw_description'],re.I)
                    item['storage_capacity']=(matches[-1][0]+matches[-1][1].upper().replace('TGB','TB')) if len(matches)>1 else f'{storage:g}TB'
                items[item['part_number']]=item
            return sorted(items.values(),key=lambda x:x['part_number'])
    except sqlite3.Error as exc:
        raise HTTPException(503, "Surface 查询库尚未就绪，请先导入授权 ERP 数据") from exc


def pmt(annual_rate, months, investment, residual):
    """Positive month-end rent, month-0 investment and month-n residual."""
    with localcontext() as ctx:
        ctx.prec = 36
        rate = (D(1) + D(annual_rate)) ** (D(1) / D(12)) - 1
        if rate == 0:
            return money((investment - residual) / months), rate
        discount = (D(1) + rate) ** (-months)
        return money((investment - residual * discount) * rate / (1 - discount)), rate


def financial_metrics(flows, monthly_rate):
    """IRR is solved on periodic month-end cash flows, not accounting profit."""
    def npv(rate):
        return sum((v / ((1 + rate) ** t) for t, v in enumerate(flows)), D(0))
    irr = None
    if flows[0] < 0 and any(v > 0 for v in flows[1:]):
        low, high = D("-0.9"), D("1")
        # Only a conventional single-sign-change flow is unambiguous.
        signs = [v > 0 for v in flows if v != 0]
        changes = sum(a != b for a, b in zip(signs, signs[1:]))
        if changes == 1 and npv(low) * npv(high) <= 0:
            for _ in range(160):
                mid = (low + high) / 2
                if npv(mid) > 0:
                    low = mid
                else:
                    high = mid
            irr = str((((1 + (low + high) / 2) ** 12) - 1).quantize(D("0.000001")))
    running = D(0)
    maximum = D(0)
    payback = None
    for month, value in enumerate(flows):
        running += value
        maximum = max(maximum, -running)
        if month > 0 and running >= 0 and payback is None:
            # Do not call a temporary positive balance a durable payback.
            if all(sum(flows[:i + 1], D(0)) >= 0 for i in range(month, len(flows))):
                payback = month
    return {"npv_cny": cash(npv(monthly_rate)), "annual_irr": irr,
            "maximum_funding_cny": cash(maximum), "payback_month": payback,
            "cashflows_cny": [cash(v) for v in flows]}


def calculate(conn, data):
    config = settings.current(conn)
    cost_factor = D(config["software_cost_factor"]) if config else COST_FACTOR
    on = today()
    if data.valid_until < on:
        raise HTTPException(422, "报价有效期不能早于今天")
    if data.fx_date > on:
        raise HTTPException(422, "汇率日期不能晚于今天")
    n = data.term_months
    policy = None
    blockers, warnings = [], []
    if data.hardware:
        row = conn.execute("SELECT * FROM lease_policies WHERE id=?", (data.policy_id,)).fetchone()
        if not row:
            raise HTTPException(409, "请选择租赁政策，不能自动猜测资金成本和残值")
        policy = json.loads(row["payload"])
        if not policy["approved_for_formal"]:
            blockers.append("租赁政策仍为试算，需内部发布正式政策后重新报价")
    public_hw, internal_hw = [], []
    rent_total, final_rent_total, hardware_cost, residual_total = D(0), D(0), D(0), D(0)
    all_items = {x["part_number"]: x for x in catalog_items()} if data.hardware else {}
    if data.hardware and not any(rental.is_device(all_items.get(line.part_number, {})) for line in data.hardware):
        raise HTTPException(422, "配件或延保不能单独作为租赁方案，请先加入设备")
    for line in data.hardware:
        item = all_items.get(line.part_number)
        if not item or not rental.in_scope(item):
            raise HTTPException(422, f"{line.part_number} 不在已核验的设备租赁范围内")
        if item["erp_price_cny"] is None or D(str(item["erp_price_cny"])) <= 0:
            raise HTTPException(409, f"{line.part_number} 缺少有效 ERP 价格")
        price = money(str(item["erp_price_cny"]))
        original_price = price
        is_device = rental.is_device(item)
        conventional = policy.get('calculation_method') == rental.METHOD
        details = None
        if conventional:
            details = rental.price(item, policy, n)
            price, residual, rent = details['cost'], details['residual'], details['monthly']
            monthly, final_monthly, rate = rent, details['final_monthly'], D(0)
        else:
            if rental.is_rtx_spark(item):
                raise HTTPException(422,'RTX Spark 请使用常规租赁规则并单独确认残值')
            if n == 12:
                raise HTTPException(422, '旧版租赁政策不支持 12 个月，请管理员发布常规租赁规则')
            residual_rate = D(policy[f"residual_rate_{n}"]) if is_device else D(0)
            residual = max(D(0), money(price * residual_rate - (D(policy["recovery_cost_cny"]) if is_device else D(0))))
            rent, rate = pmt(policy["annual_funding_rate"], n, price, residual)
            monthly = rent + (D(policy["monthly_service_cny"]) if is_device else D(0))
            final_monthly = monthly
        total_monthly = money(monthly * line.quantity)
        final_total = money(final_monthly * line.quantity)
        rent_total += total_monthly
        final_rent_total += final_total
        hardware_cost += price * line.quantity
        residual_total += residual * line.quantity
        public_hw.append({"part_number": line.part_number, "name": item["product_name"] or item["original_family"],
                          "configuration": item["raw_description"], "quantity": line.quantity,
                          "unit_monthly_cny": cash(monthly), "monthly_cny": cash(total_monthly),
                          "final_monthly_cny": cash(final_total), "unit_final_monthly_cny": cash(final_monthly),
                          "term_total_cny": cash(total_monthly * (n-1) + final_total), "reason": "按所选硬件配置与租赁期限计算，末期调整分位尾差" if conventional else "使用所选 ERP 料号和租赁期限计算"})
        internal_hw.append({"part_number": line.part_number, "quantity": line.quantity,
                            "erp_unit_cost_cny": cash(original_price), "effective_unit_cost_cny": cash(price), "erp_tax_basis": "含税原始 ERP 价",
                            "source_sha256": item["source_sha256"], "source_row": item["source_row"],
                            "erp_snapshot_hash": store.digest(item), "residual_cny": cash(residual),
                            "base_rent_cny": cash(rent), "monthly_rate": str(rate)})
        if details:
            internal_hw[-1].update({'brand': details['brand'], 'erp_cost_factor': str(details['cost_factor']),
                                   'residual_rate': str(details['residual_rate']), 'term_multiplier': str(details['multiplier']),
                                   'priced_amount_cny': cash(details['priced_amount']), 'term_total_cny': cash(details['term_total']*line.quantity),
                                   'calculation_method': rental.METHOD})
            if details['brand']=='RTX Spark' and not details['residual_confirmed']:
                blockers.append('RTX Spark 残值尚未单独确认，请管理员保存对应规则后重新报价')
                warnings.append('RTX Spark 当前按通用残值试算，正式订购前需单独确认。')

    public_cloud, internal_cloud = [], []
    annual_sell, annual_cost, annual_tax = D(0), D(0), D(0)
    covered = {}
    product_seats = {}
    for line in data.cloud:
        price = store.resolve_price(conn, line.product_id, on)
        if price["kind"] == "Included/Metered":
            raise HTTPException(422, "Copilot Chat 不能作为零价全包订阅，计量服务需要独立合同")
        product_seats[line.product_id] = product_seats.get(line.product_id, 0) + line.seats
        if price["seat_limit"] and product_seats[line.product_id] > price["seat_limit"]:
            raise HTTPException(422, f"{price['name']} 超过当前价格记录的席位上限，需人工确认授权路径")
        components = {line.product_id, *price["components"]}
        group_coverage = covered.setdefault(line.user_group, set())
        if group_coverage & components:
            raise HTTPException(422, "选中产品与 Bundle 包含项重复，请分项目或调整组合后再报价")
        group_coverage |= components
        if not line.eligibility_confirmed or not line.eligibility_reference:
            blockers.append(f"{price['name']} 的许可资格、市场及现有订阅需内部核验")
        unit = D(price["monthly_usd"])
        net = money(unit * 12 * line.seats * data.usd_cny)
        tax = money(net * data.cloud_tax_rate)
        cost = money(unit * cost_factor * 12 * line.seats * data.usd_cny)
        annual_sell += net
        annual_cost += cost
        annual_tax += tax
        public_cloud.append({"product_id": line.product_id, "name": price["name"], "seats": line.seats, "user_group": line.user_group,
                             "standard_unit_monthly_usd": str(unit), "annual_usd": cash(unit * 12 * line.seats),
                             "annual_net_cny": cash(net), "annual_tax_cny": cash(tax), "annual_due_cny": cash(net + tax),
                             "price_version_id": price["price_version_id"], "commitment": "年度承诺，年付",
                             "source_url": price["source_url"], "source_checked_at": price["source_checked_at"],
                             "market": price["market"], "components": price["components"],
                             "eligibility_confirmed": line.eligibility_confirmed})
        internal_cloud.append({"product_id": line.product_id, "user_group": line.user_group, "price_snapshot": price,
                               "cost_factor": str(cost_factor), "annual_cost_usd": cash(unit * cost_factor * 12 * line.seats),
                               "annual_cost_cny": cash(cost), "annual_gross_profit_cny": cash(net - cost),
                               "eligibility_reference": line.eligibility_reference})
        # New formal quotes must revalidate after any known price interval closes.
        version = conn.execute("SELECT effective_to FROM cloud_prices WHERE id=?", (price["price_version_id"],)).fetchone()
        if version["effective_to"] and data.valid_until >= date.fromisoformat(version["effective_to"]):
            blockers.append(f"{price['name']} 报价有效期越过价格版本失效日期")
    years = n // 12
    if data.cloud:
        warnings.append("软件按年付款；月均预算不是月付承诺。USD 来源价为税前参考价。")
        if data.renewal == "indicative":
            warnings.append("后续年度按当前标准价估算，续订价格以届时确认结果为准。")
    if data.azure_requested:
        warnings.append("Azure / cowork 需另行签约，按 AI 实际使用量计费，不包含在本报价总额。")
    hardware_term_total = rent_total * (n-1) + final_rent_total
    gross = hardware_term_total + (annual_sell + annual_tax) * years + data.service_once_cny
    if data.project_discount_cny > gross:
        raise HTTPException(422, "整体优惠不能超过项目总额")
    discount_left = data.project_discount_cny
    schedule = []
    # Month 0: initial service and first annual software payment. Rent is in arrears.
    for month in range(n + 1):
        hw_due = (final_rent_total if month == n else rent_total) if month > 0 else D(0)
        software_due = annual_sell + annual_tax if month % 12 == 0 and month < n else D(0)
        service_due = data.service_once_cny if month == 0 else D(0)
        before_discount = hw_due + software_due + service_due
        discount = min(before_discount, discount_left)
        discount_left -= discount
        schedule.append({"month": month, "hardware_cny": cash(hw_due), "cloud_cny": cash(software_due),
                         "service_cny": cash(service_due), "discount_cny": cash(discount),
                         "due_cny": cash(before_discount - discount)})
    total = gross - data.project_discount_cny
    customer = {"template_version": TEMPLATE_VERSION, "title": data.title, "term_months": n,
                "currency": "CNY", "hardware": public_hw, "cloud": public_cloud,
                "fx": {"usd_cny": str(data.usd_cny), "date": str(data.fx_date), "reference": data.fx_reference},
                "tax": {"hardware": "按 ERP 含税价格测算，租赁税务口径以正式条款为准", "cloud_rate": str(data.cloud_tax_rate)},
                "hardware_monthly_cny": cash(rent_total), "cloud_annual_cny": cash(annual_sell + annual_tax),
                "hardware_final_monthly_cny": cash(final_rent_total), "hardware_term_total_cny": cash(hardware_term_total),
                "service_once_cny": cash(data.service_once_cny), "before_discount_cny": cash(gross),
                "project_discount_cny": cash(data.project_discount_cny), "discount_reason": data.discount_reason,
                "total_cny": cash(total), "average_monthly_cny": cash(total / n),
                "first_payment_cny": schedule[0]["due_cny"], "payment_schedule": schedule,
                "renewal": data.renewal, "renewal_reference": data.renewal_reference,
                "azure_requested": data.azure_requested, "warnings": warnings,
                "valid_until": str(data.valid_until), "personas": data.personas,
                "formal_ready": not blockers, "formal_requirements": blockers}
    flows = [D(x["due_cny"]) for x in schedule]
    flows[0] -= hardware_cost
    for month in range(0, n, 12):
        flows[month] -= annual_cost + annual_tax
    flows[-1] += residual_total
    monthly_rate = (D(1) + D(policy.get("annual_funding_rate", 0))) ** (D(1)/12) - 1 if policy else D(0)
    contribution = sum(flows, D(0))
    minimum_margin = D(policy.get("minimum_margin", 0)) if policy else D(0)
    net_revenue = total - annual_tax * years
    contribution_rate = contribution / net_revenue if net_revenue else D(0)
    internal = {"hardware": internal_hw, "cloud": internal_cloud, "policy_id": data.policy_id,
                "policy_snapshot": policy, "software_cost_factor": str(cost_factor),
                "software_annual_cost_cny": cash(annual_cost), "software_annual_gross_profit_cny": cash(annual_sell - annual_cost),
                "contribution_before_service_cost_and_hardware_tax_cny": cash(contribution),
                "contribution_rate": str(contribution_rate.quantize(D("0.000001"))),
                "below_policy_margin": contribution_rate < minimum_margin,
                "metric_basis": "现金贡献含期末净残值，未扣独立服务人工成本及设备租赁税负调整，不等同会计毛利；IRR 多重根时留空",
                "baseline": financial_metrics(flows, monthly_rate),
                "stress": financial_metrics(flows[:-1] + [flows[-1] - residual_total], monthly_rate)}
    if policy and policy.get('calculation_method') == rental.METHOD:
        internal['metric_basis'] += '；常规租赁计价系数已含资金、利润及风险因素，不再另加；NPV 使用零折现率，仅作现金合计比较。'
        warnings.append('常规月租保留两位小数，末期按租赁总额调整分位尾差。')
    return customer, internal
