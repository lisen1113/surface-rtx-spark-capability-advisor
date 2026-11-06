"""Anonymous discovery and stateless budgets; customer data stays authenticated."""
from datetime import timedelta
from decimal import Decimal
import json
import os
import hashlib
import secrets
import time

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import ValidationError
from ..request_limit import limiter, source_address
from . import api, engine, settings, store, rental
from .documents import build_quote_pdf
from .models import CloudRecommendInput, PublicEstimateInput, QuoteInput

router = APIRouter(prefix="/api/commercial/public", tags=["public-workplace"])

FEATURES = {
 "M365-BIZ-BASIC": ["网页与移动办公", "企业邮箱", "Teams 协作", "云存储"],
 "M365-BIZ-STANDARD": ["桌面 Office", "企业邮箱", "Teams 协作", "云存储"],
 "M365-BIZ-PREMIUM": ["桌面 Office", "企业邮箱", "Teams 协作", "设备管理", "身份与安全"],
 "COPILOT-BUSINESS": ["Office 内 AI", "工作数据问答"],
 "BUNDLE-STANDARD-COPILOT": ["桌面 Office", "企业邮箱", "Teams 协作", "Office 内 AI"],
 "BUNDLE-PREMIUM-COPILOT": ["桌面 Office", "企业邮箱", "设备管理", "身份与安全", "Office 内 AI"],
 "COPILOT-CHAT": ["AI 聊天", "部分功能按量计费"],
 "COPILOT-ENTERPRISE": ["企业 AI", "合格基础许可前提"],
 "M365-E3": ["企业办公", "设备管理", "安全与合规", "Teams 协作"],
 "M365-E3-NOTEAMS": ["企业办公", "设备管理", "安全与合规", "不含 Teams"],
 "M365-E5": ["企业办公", "高级安全与合规", "Teams 协作"],
 "M365-E5-NOTEAMS": ["企业办公", "高级安全与合规", "不含 Teams"],
 "M365-E7": ["企业办公", "Copilot", "智能体治理", "身份与安全"],
 "AGENT-365": ["智能体治理", "合格基础许可前提"],
}


def limit(request: Request):
    store.ensure_enabled()
    # Public-mode POSTs are already limited by the application's middleware.
    if request.method == "POST" and os.getenv("CAPABILITY_DEPLOYMENT_MODE") == "public":
        return
    peer = request.client.host if request.client else "unknown"
    path=request.url.path
    if path.startswith('/api/commercial/public/budget-download/'):
        path='/api/commercial/public/budget-download'
    retry = limiter.check(source_address(peer, request.headers.get("x-forwarded-for")), path)
    if retry:
        raise HTTPException(429, "操作较频繁，请稍后再试", headers={"Retry-After": str(retry)})


router.dependencies.append(Depends(limit))


def config(conn):
    data = settings.current(conn)
    if not data:
        raise HTTPException(503, "预算参数尚未发布，请联系管理员设置汇率与租赁政策")
    return data


def public_result(data):
    # Internal approval conditions are not customer selection criteria.
    return {key: value for key, value in data.items() if key not in ("formal_ready", "formal_requirements")}


def calculate(conn, data):
    active = config(conn)
    try:
        inputs = QuoteInput(title=data.title, term_months=data.term_months, hardware=data.hardware, cloud=data.cloud,
                            policy_id=active["active_policy_id"], usd_cny=active["usd_cny"],
                            fx_date=active["fx_date"], fx_reference=active["fx_reference"], cloud_tax_rate=active["cloud_tax_rate"],
                            azure_requested=data.azure_requested, valid_until=engine.today()+timedelta(days=7), personas=data.personas)
    except ValidationError as exc:
        raise HTTPException(422, "请选择设备或订阅，相同产品请合并数量") from exc
    customer, _ = engine.calculate(conn, inputs)
    customer['warnings'].append('本方案为预算参考，不构成正式报价；整体优惠及交付条款另行确认。')
    if data.hardware:
        row = conn.execute('SELECT payload FROM lease_policies WHERE id=?', (active['active_policy_id'],)).fetchone()
        if row and not json.loads(row[0])['approved_for_formal']:
            customer['warnings'].append('当前设备租赁采用试算政策，正式订购前需确认。')
    return public_result(customer)


@router.get("/catalog")
def catalog():
    with store.connection() as conn:
        active = settings.current(conn)
        policy_row = conn.execute("SELECT payload FROM lease_policies WHERE id=?", (active["active_policy_id"],)).fetchone() if active else None
        policy = json.loads(policy_row[0]) if policy_row else None
        identifiers = conn.execute("SELECT DISTINCT product_id FROM cloud_prices WHERE status='published' AND effective_from<=? AND (effective_to IS NULL OR effective_to>?) ORDER BY product_id", (str(engine.today()), str(engine.today()))).fetchall()
        cloud = []
        for item in identifiers:
            price = store.resolve_price(conn, item["product_id"], engine.today())
            cloud.append({key: price[key] for key in ("product_id", "name", "kind", "monthly_usd", "seat_limit", "prerequisite", "components", "source_url", "source_checked_at")})
            cloud[-1]["features"] = FEATURES.get(price["product_id"], [])
    hardware = []
    for item in engine.catalog_items():
        if not rental.in_scope(item):
            continue
        card = {key: item[key] for key in ("part_number", "product_name", "raw_description", "product_type", "series_group", "memory_gb", "storage_capacity", "cpu_official", "color", "connectivity", "weight", "display")}
        card['brand'] = rental.brand(item)
        card['is_device'] = rental.is_device(item)
        card["monthly"] = {}
        if policy and item["erp_price_cny"] is not None and Decimal(str(item["erp_price_cny"])) > 0:
            cost = engine.money(str(item["erp_price_cny"]))
            device = rental.is_device(item)
            for months in (12, 24, 36):
                if rental.is_rtx_spark(item) and policy.get('calculation_method')!=rental.METHOD:
                    continue
                if policy.get('calculation_method') == rental.METHOD:
                    result = rental.price(item,policy,months)
                    card['monthly'][str(months)] = engine.cash(result['monthly'])
                    continue
                if months == 12:
                    continue
                residual = max(Decimal(0), engine.money(cost*Decimal(policy[f"residual_rate_{months}"])-Decimal(policy["recovery_cost_cny"]))) if device else Decimal(0)
                rent, _ = engine.pmt(policy["annual_funding_rate"], months, cost, residual)
                card["monthly"][str(months)] = engine.cash(rent+(Decimal(policy["monthly_service_cny"]) if device else Decimal(0)))
        hardware.append(card)
    return {"hardware": hardware, "cloud": cloud,
            "budget": {"available": bool(active), "lease_available": bool(policy),
                       "usd_cny": active["usd_cny"] if active else None, "fx_date": active["fx_date"] if active else None,
                       "cloud_tax_rate": active["cloud_tax_rate"] if active else None,
                       "indicative": not policy or not policy["approved_for_formal"],
                       'lease_terms': [12,24,36] if policy and policy.get('calculation_method') == rental.METHOD else [24,36]},
            "azure": {"billing": "按 AI 实际用量计费", "contract": "另行签约", "included_in_budget": False}}


@router.post("/recommendations")
def recommendations(data: CloudRecommendInput):
    return api.cloud_recommendations(data, user=None)


@router.post("/estimate")
def estimate(data: PublicEstimateInput):
    with store.connection() as conn:
        return calculate(conn, data)


@router.post("/budget.pdf")
def pdf(data: PublicEstimateInput):
    with store.connection() as conn:
        result = calculate(conn, data)
    quote = {"id": "BUDGET-"+store.digest(result)[:16].upper(), "state": "draft", "customer": result,
             "snapshot_hash": store.digest(result)}
    return Response(build_quote_pdf(quote), media_type="application/pdf", headers={"Content-Disposition": 'attachment; filename="Surface-M365-budget.pdf"', "Cache-Control": "no-store"})


@router.post('/budget-ticket')
def budget_ticket(data: PublicEstimateInput):
    with store.connection() as conn:
        result=calculate(conn,data)
        digest=store.digest(result)
        quote={'id':'BUDGET-'+digest[:16].upper(),'state':'draft','customer':result,'snapshot_hash':digest}
        content=build_quote_pdf(quote)
        now=int(time.time())
        conn.execute('DELETE FROM public_budget_tickets WHERE expires_at<=?',(now,))
        if conn.execute('SELECT COUNT(*) FROM public_budget_tickets').fetchone()[0]>=2500:
            raise HTTPException(429,'临时预算下载较多，请稍后重试')
        token=secrets.token_urlsafe(32)
        filename='Surface-Workplace-Budget-'+digest[:16]+'.pdf'
        conn.execute('INSERT INTO public_budget_tickets VALUES(?,?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),content,filename,now+90))
    return {'ticket':token,'filename':filename,'expires_in':90}


@router.get('/budget-download/{ticket}')
def budget_download(ticket: str):
    if not 30<=len(ticket)<=100:
        raise HTTPException(404,'预算下载授权已失效，请重新生成')
    hashed=hashlib.sha256(ticket.encode()).hexdigest()
    with store.connection() as conn:
        row=conn.execute('SELECT content,filename FROM public_budget_tickets WHERE ticket_hash=? AND expires_at>?',(hashed,int(time.time()))).fetchone()
        if not row:
            raise HTTPException(404,'预算下载授权已失效，请重新生成')
        conn.execute('DELETE FROM public_budget_tickets WHERE ticket_hash=?',(hashed,))
    return Response(row['content'],media_type='application/pdf',headers={'Content-Disposition':'attachment; filename="'+row['filename']+'"','Cache-Control':'no-store'})
