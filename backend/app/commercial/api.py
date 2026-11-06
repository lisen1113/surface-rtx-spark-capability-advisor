"""Authenticated tenant-scoped workflows and admin-only commercial controls."""
from datetime import date
from decimal import Decimal
import hashlib
import json
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from ..auth import current_user, require_admin, _license_check, RegisterInput, register_user
from ..auth_store import connection as identity_connection
from . import engine, store, settings, rental
from .documents import build_quote_pdf
from .models import (AzureContractInput, CloudRecommendInput, CompanyProfile, PolicyInput, PriceInput,
                     QuoteInput, RecommendInput, ReviewInput, UsageInput, SettingsInput, RentalRulesInput, ResidualRates)

router = APIRouter(prefix="/api/commercial", tags=["commercial"])

OWNER_ROLES = ("owner", "customer_owner", "admin")


@router.post("/register", status_code=201)
def register_customer(data: RegisterInput):
    store.ensure_enabled()
    return register_user(data, role="customer_owner")


def customer(user=Depends(current_user)):
    store.ensure_enabled()
    if user["status"] != "approved" or not user["email_verified"]:
        raise HTTPException(403, "账号尚未完成验证或审批")
    with identity_connection() as conn:
        _license_check(conn, user)
    if user["role"] != "admin" and not user["organization_id"]:
        raise HTTPException(403, "需要有效组织")
    return user


def admin(user=Depends(require_admin)):
    return customer(user)


def org_id(user):
    if not user.get("organization_id"):
        raise HTTPException(422, "请使用有组织归属的客户账号创建方案")
    return user["organization_id"]


def read_quote(conn, quote_id, user):
    row = conn.execute("SELECT * FROM commercial_quotes WHERE id=?", (quote_id,)).fetchone()
    if not row or (user["role"] != "admin" and row["organization_id"] != user["organization_id"]):
        raise HTTPException(404, "方案不存在")
    return dict(row)


def safe_quote(row):
    return {"id": row["id"], "state": row["state"], "customer": json.loads(row["customer_json"]),
            "profile": json.loads(row["profile_json"]) if row["profile_json"] else None,
            "created_at": row["created_at"], "snapshot_hash": row["snapshot_hash"],
            "formal_number": row["formal_number"], "reviewed_at": row["reviewed_at"],
            "issued_at": row["issued_at"], "commercial_reference": row["commercial_reference"],
            "document_sha256": row["document_sha256"]}


def quote_hash(inputs, customer_data, internal, profile=None):
    return store.digest({"input": inputs, "customer": customer_data, "internal": internal, "profile": profile})


@router.get("/products")
def products(user=Depends(customer)):
    with store.connection() as conn:
        ids = conn.execute("SELECT DISTINCT product_id FROM cloud_prices WHERE status='published' AND effective_from<=? AND (effective_to IS NULL OR effective_to>?) ORDER BY product_id",
                           (str(engine.today()), str(engine.today()))).fetchall()
        items = [store.resolve_price(conn, row["product_id"], engine.today()) for row in ids]
    # Whitelist: no partner cost or price-floor fields exist in this response.
    fields = ("product_id", "name", "kind", "monthly_usd", "seat_limit", "prerequisite", "components", "market", "price_version_id", "source_url", "source_checked_at")
    return {"items": [{k: item[k] for k in fields} for item in items],
            "note": "美元公开标准价，年度承诺年付；来源日期不等于实时官网核验日期"}


@router.get("/hardware")
def hardware(q: str = Query(default="", max_length=100), user=Depends(customer)):
    items = [x for x in engine.catalog_items() if rental.in_scope(x)
             and q.casefold() in (x["part_number"] + " " + (x["product_name"] or "") + " " + x["raw_description"]).casefold()]
    fields = ("part_number", "product_name", "raw_description", "product_type", "memory_gb", "erp_price_cny")
    # ERP is an internal cost, not returned by the new customer workflow.
    return {"items": [{k: item[k] for k in fields if k != "erp_price_cny"} for item in items[:300]], "total": len(items)}


@router.post("/recommendations")
def recommend(data: RecommendInput, user=Depends(customer)):
    items = [x for x in engine.catalog_items() if x["product_type"] == data.product_type and rental.in_scope(x)
             and x["memory_gb"] is not None and x["memory_gb"] >= data.min_memory_gb
             and x["erp_price_cny"] is not None and Decimal(str(x["erp_price_cny"])) > 0
             and (data.max_erp_cny is None or Decimal(str(x["erp_price_cny"])) <= data.max_erp_cny)]
    items.sort(key=lambda x: (Decimal(str(x["erp_price_cny"])), x["part_number"]))
    selected = []
    for label, index in (("经济方案", 0), ("推荐方案", len(items)//2), ("高配置候选", len(items)-1)):
        if items and items[index]["part_number"] not in {x["part_number"] for x in selected}:
            item = items[index]
            selected.append({"tier": label, "part_number": item["part_number"], "name": item["product_name"],
                             "configuration": item["raw_description"], "memory_gb": item["memory_gb"],
                             "reason": f"满足至少 {data.min_memory_gb}GB 内存及所选产品类别，按 ERP 预算档排序；不代表性能实测"})
    return {"items": selected, "note": "仅按已知字段筛选，库存、交期和软件兼容性需确认；不足三款时不补造候选"}


@router.get("/policies")
def policies(user=Depends(customer)):
    with store.connection() as conn:
        rows = conn.execute("SELECT * FROM lease_policies ORDER BY created_at DESC").fetchall()
    return {"items": [{"id": r["id"], "name": json.loads(r["payload"])["name"],
                       "approved_for_formal": json.loads(r["payload"])["approved_for_formal"]} for r in rows]}


@router.post("/cloud-recommendations")
def cloud_recommendations(data: CloudRecommendInput, user=Depends(customer)):
    from .recommendations import recommend
    return recommend(data)


@router.post("/estimate")
def estimate(data: QuoteInput, user=Depends(customer)):
    with store.connection() as conn:
        public, _internal = engine.calculate(conn, data)
    return public


@router.get("/profile")
def get_profile(user=Depends(customer)):
    with store.connection() as conn:
        row = conn.execute("SELECT * FROM commercial_profiles WHERE organization_id=?", (org_id(user),)).fetchone()
        if not row:
            return {"profile": None}
        data = store.decrypt(row["encrypted_payload"])
        if user["role"] not in OWNER_ROLES:
            for key in ("bank_account", "bank_account_name", "bank_name", "bank_code"):
                data.pop(key, None)
        store.audit(conn, user, "profile.read", str(user["organization_id"]), organization_id=user["organization_id"])
        return {"profile": data, "updated_at": row["updated_at"]}


@router.put("/profile")
def save_profile(data: CompanyProfile, user=Depends(customer)):
    if user["role"] not in OWNER_ROLES:
        raise HTTPException(403, "仅组织负责人可维护银行和开票资料")
    organization = org_id(user)
    encrypted = store.encrypt(data.model_dump(mode="json"))
    with store.connection() as conn:
        conn.execute("INSERT INTO commercial_profiles VALUES(?,?,?,?) ON CONFLICT(organization_id) DO UPDATE SET encrypted_payload=excluded.encrypted_payload,updated_by=excluded.updated_by,updated_at=excluded.updated_at",
                     (organization, encrypted, user["id"], store.timestamp()))
        store.audit(conn, user, "profile.updated", str(organization), organization_id=organization)
    return {"status": "saved"}


@router.get("/admin/profiles/{organization_id}")
def internal_profile(organization_id: int, user=Depends(admin)):
    with store.connection() as conn:
        row = conn.execute("SELECT * FROM commercial_profiles WHERE organization_id=?", (organization_id,)).fetchone()
        if not row:
            raise HTTPException(404, "组织尚未提交公司资料")
        store.audit(conn, user, "profile.internal_read", str(organization_id), organization_id=organization_id)
        return {"profile": store.decrypt(row["encrypted_payload"]), "updated_at": row["updated_at"]}


@router.post("/quotes", status_code=201)
def create_quote(data: QuoteInput, user=Depends(customer)):
    organization = org_id(user)
    with store.connection() as conn:
        public, internal = engine.calculate(conn, data)
        inputs = data.model_dump(mode="json")
        quote_id = store.identifier("Q")
        conn.execute("INSERT INTO commercial_quotes(id,organization_id,created_by,state,input_json,customer_json,internal_json,snapshot_hash,valid_until,created_at) VALUES(?,?,?,'draft',?,?,?,?,?,?)",
                     (quote_id, organization, user["id"], store.dumps(inputs), store.dumps(public), store.dumps(internal),
                      quote_hash(inputs, public, internal), str(data.valid_until), store.timestamp()))
        store.audit(conn, user, "quote.created", quote_id, organization_id=organization)
        return safe_quote(read_quote(conn, quote_id, user))


@router.get("/quotes")
def list_quotes(user=Depends(customer)):
    with store.connection() as conn:
        rows = conn.execute("SELECT id,state,customer_json,formal_number,created_at FROM commercial_quotes " +
                            ("" if user["role"] == "admin" else "WHERE organization_id=? ") + "ORDER BY created_at DESC LIMIT 200",
                            () if user["role"] == "admin" else (org_id(user),)).fetchall()
    return {"items": [{"id": r["id"], "state": r["state"], "formal_number": r["formal_number"], "created_at": r["created_at"],
                       "title": json.loads(r["customer_json"])["title"], "total_cny": json.loads(r["customer_json"])["total_cny"]} for r in rows]}


@router.get("/quotes/{quote_id}")
def get_quote(quote_id: str, user=Depends(customer)):
    with store.connection() as conn:
        return safe_quote(read_quote(conn, quote_id, user))


@router.get("/quotes/{quote_id}/inputs")
def get_inputs(quote_id: str, user=Depends(customer)):
    with store.connection() as conn:
        return {"input": json.loads(read_quote(conn, quote_id, user)["input_json"])}


@router.post("/quotes/{quote_id}/submit")
def submit_quote(quote_id: str, user=Depends(customer)):
    with store.connection() as conn:
        row = read_quote(conn, quote_id, user)
        if user["role"] not in OWNER_ROLES:
            raise HTTPException(403, "请组织负责人提交正式报价申请")
        if row["state"] not in ("draft", "rejected"):
            raise HTTPException(409, "当前状态不能提交")
        if row["valid_until"] < str(engine.today()):
            raise HTTPException(409, "预算已过期，请按新价格创建方案")
        profile = conn.execute("SELECT * FROM commercial_profiles WHERE organization_id=?", (row["organization_id"],)).fetchone()
        if not profile:
            raise HTTPException(409, "请先完善使用公司、域名、负责人、银行和开票资料")
        full = CompanyProfile.model_validate(store.decrypt(profile["encrypted_payload"])).model_dump(mode="json")
        public_profile = {key: full[key] for key in ("company_name", "hk_company_name", "region", "address", "phone", "domain", "contact_name", "contact_email", "contracting_company", "paying_company", "invoice_title", "invoice_registration", "invoice_address")}
        # Budget blockers are shown to the reviewer; only the reviewer can validate or reject.
        snapshot_hash = quote_hash(json.loads(row["input_json"]), json.loads(row["customer_json"]), json.loads(row["internal_json"]), public_profile)
        conn.execute("UPDATE commercial_quotes SET state='pending',profile_json=?,snapshot_hash=? WHERE id=?",
                     (store.dumps(public_profile), snapshot_hash, quote_id))
        store.audit(conn, user, "quote.submitted", quote_id, organization_id=row["organization_id"])
        return safe_quote(read_quote(conn, quote_id, user))


def validate_formal(conn, row):
    if row["valid_until"] < str(engine.today()):
        raise HTTPException(409, "报价已过期，请重新创建")
    if quote_hash(json.loads(row["input_json"]), json.loads(row["customer_json"]), json.loads(row["internal_json"]), json.loads(row["profile_json"]) if row["profile_json"] else None) != row["snapshot_hash"]:
        raise HTTPException(409, "报价快照校验失败")
    public = json.loads(row["customer_json"])
    if public["formal_requirements"]:
        raise HTTPException(409, "需完善后重新创建方案：" + "；".join(public["formal_requirements"]))
    internal = json.loads(row["internal_json"])
    if internal["hardware"]:
        current = {item["part_number"]: item for item in engine.catalog_items()}
        for item in internal["hardware"]:
            if item["part_number"] not in current or store.digest(current[item["part_number"]]) != item["erp_snapshot_hash"]:
                raise HTTPException(409, "设备 ERP 来源或价格已变更，请按新数据创建方案")
    for item in public["cloud"]:
        price = store.resolve_price(conn, item["product_id"], engine.today())
        if price["price_version_id"] != item["price_version_id"]:
            raise HTTPException(409, "软件价格版本已变更，请按新价格创建方案")


@router.get("/admin/quotes/{quote_id}")
def internal_quote(quote_id: str, user=Depends(admin)):
    with store.connection() as conn:
        row = read_quote(conn, quote_id, user)
        store.audit(conn, user, "quote.internal_read", quote_id, organization_id=row["organization_id"])
        return {**safe_quote(row), "internal": json.loads(row["internal_json"]), "input": json.loads(row["input_json"]),
                "organization_id": row["organization_id"], "created_by": row["created_by"], "review_reason": row["review_reason"]}


@router.post("/admin/quotes/{quote_id}/review")
def review(quote_id: str, data: ReviewInput, user=Depends(admin)):
    with store.connection() as conn:
        row = read_quote(conn, quote_id, user)
        if row["state"] != "pending":
            raise HTTPException(409, "只能审批待审核报价")
        if row["created_by"] == user["id"]:
            raise HTTPException(409, "不能审批本人创建的报价")
        if data.decision == "approve":
            validate_formal(conn, row)
            if not data.commercial_reference:
                raise HTTPException(422, "请记录供应方法定信息、付款、租赁税务、软件资格和服务成本核验及合同条款依据")
        state = "approved" if data.decision == "approve" else "rejected"
        conn.execute("UPDATE commercial_quotes SET state=?,reviewed_by=?,reviewed_at=?,review_reason=?,commercial_reference=? WHERE id=?",
                     (state, user["id"], store.timestamp(), data.reason, data.commercial_reference, quote_id))
        store.audit(conn, user, "quote." + state, quote_id, organization_id=row["organization_id"], details={"reason": data.reason})
        return safe_quote(read_quote(conn, quote_id, user))


@router.post("/admin/quotes/{quote_id}/issue")
def issue(quote_id: str, user=Depends(admin)):
    with store.connection() as conn:
        row = read_quote(conn, quote_id, user)
        if row["state"] != "approved":
            raise HTTPException(409, "只有已批准报价可以签发")
        validate_formal(conn, row)
        number = "FORMAL-" + engine.today().strftime("%Y%m%d") + "-" + quote_id[2:].upper()
        conn.execute("UPDATE commercial_quotes SET state='issued',issued_by=?,issued_at=?,formal_number=? WHERE id=?",
                     (user["id"], store.timestamp(), number, quote_id))
        document = build_quote_pdf(safe_quote(read_quote(conn, quote_id, user)))
        sha = hashlib.sha256(document).hexdigest()
        conn.execute("INSERT INTO commercial_documents VALUES(?,?,?,?,?)", (quote_id, "formal", document, sha, store.timestamp()))
        conn.execute("UPDATE commercial_quotes SET document_sha256=? WHERE id=?", (sha, quote_id))
        store.audit(conn, user, "quote.issued", quote_id, organization_id=row["organization_id"], details={"document_sha256": sha})
        return safe_quote(read_quote(conn, quote_id, user))


@router.get("/quotes/{quote_id}/document.pdf")
def download(quote_id: str, user=Depends(customer)):
    with store.connection() as conn:
        row = read_quote(conn, quote_id, user)
        kind = "formal" if row["state"] == "issued" else "budget"
        document = conn.execute("SELECT * FROM commercial_documents WHERE quote_id=? AND kind=?", (quote_id, kind)).fetchone()
        if kind == "formal":
            if not document or hashlib.sha256(document["content"]).hexdigest() != row["document_sha256"]:
                raise HTTPException(409, "正式文档校验失败")
            content = document["content"]
        else:
            # The budget may be refreshed on submission when the company snapshot is attached.
            content = build_quote_pdf(safe_quote(row))
        store.audit(conn, user, "document.download", quote_id, organization_id=row["organization_id"], details={"kind": kind})
    return Response(content, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{kind}-{quote_id}.pdf"', "Cache-Control": "no-store"})


@router.get("/admin/prices")
def prices(user=Depends(admin)):
    with store.connection() as conn:
        return {"items": [{**dict(r), "payload": json.loads(r["payload"])} for r in conn.execute("SELECT * FROM cloud_prices ORDER BY created_at DESC")]}


@router.get("/admin/settings")
def get_settings(user=Depends(admin)):
    with store.connection() as conn:
        return {"settings": settings.current(conn)}


@router.get('/admin/rental-rules')
def get_rental_rules(user=Depends(admin)):
    with store.connection() as conn:
        active = settings.current(conn)
        row = conn.execute('SELECT id,payload FROM lease_policies WHERE id=?', (active['active_policy_id'],)).fetchone() if active else None
        policy = json.loads(row['payload']) if row else None
    defaults = RentalRulesInput(residual_by_brand={b: ResidualRates() for b in rental.BRANDS}, terms_reference='硬件租赁费用计算示例表.docx；残值按品牌调整，Surface 成本按 ERP 折扣计算').model_dump(mode='json')
    return {'active_rules': policy if policy and policy.get('calculation_method') == rental.METHOD else None,
            'active_policy_id': row['id'] if row else None, 'defaults': defaults,
            'fixed_multipliers': {str(n): str(v) for n,v in rental.MULTIPLIERS.items()}}


@router.put('/admin/rental-rules')
def put_rental_rules(data: RentalRulesInput, user=Depends(admin)):
    identifier = store.identifier('LP')
    payload = rental.policy_payload(data)
    for item in engine.catalog_items():
        if not rental.in_scope(item):
            continue
        if item['erp_price_cny'] is not None and Decimal(str(item['erp_price_cny'])) > 0:
            for months in rental.MULTIPLIERS:
                rental.price(item,payload,months)
    with store.connection() as conn:
        current = settings.current(conn)
        if not current:
            raise HTTPException(409, '请先发布汇率与软件税率等预算参数')
        current.pop('settings_version', None)
        current['active_policy_id'] = identifier
        configuration = SettingsInput(**current)
        conn.execute('INSERT INTO lease_policies VALUES(?,?,?,?)', (identifier,store.dumps(payload),user['id'],store.timestamp()))
        settings.save(conn,configuration,user)
        store.audit(conn,user,'rental_rules.published',identifier,details=payload)
    return {'id':identifier,'status':'published'}


@router.put("/admin/settings")
def put_settings(data: SettingsInput, user=Depends(admin)):
    if data.fx_date > engine.today():
        raise HTTPException(422, "汇率日期不能晚于今天")
    with store.connection() as conn:
        if data.active_policy_id and not conn.execute("SELECT 1 FROM lease_policies WHERE id=?", (data.active_policy_id,)).fetchone():
            raise HTTPException(422, "所选租赁政策不存在")
        identifier = settings.save(conn, data, user)
    return {"id": identifier, "status": "published"}


@router.post("/admin/prices", status_code=201)
def add_price(data: PriceInput, user=Depends(admin)):
    with store.connection() as conn:
        price_id = store.create_price(conn, data, user["id"])
        store.audit(conn, user, "price.created", price_id, details={"product_id": data.product_id})
    return {"id": price_id, "status": "draft"}


@router.post("/admin/prices/{price_id}/publish")
def publish(price_id: str, replace: bool = False, user=Depends(admin)):
    with store.connection() as conn:
        (store.replace_price if replace else store.publish_price)(conn, price_id, user["id"])
        store.audit(conn, user, "price.published", price_id, details={"replace": replace})
    return {"status": "published"}


@router.post("/admin/policies", status_code=201)
def add_policy(data: PolicyInput, user=Depends(admin)):
    policy_id = store.identifier("LP")
    with store.connection() as conn:
        conn.execute("INSERT INTO lease_policies VALUES(?,?,?,?)", (policy_id, store.dumps(data.model_dump(mode="json")), user["id"], store.timestamp()))
        store.audit(conn, user, "policy.created", policy_id, details=data.model_dump(mode="json"))
    return {"id": policy_id}


@router.get("/admin/policies")
def internal_policies(user=Depends(admin)):
    with store.connection() as conn:
        return {"items": [{"id": r["id"], **json.loads(r["payload"])} for r in conn.execute("SELECT * FROM lease_policies ORDER BY created_at DESC")]}


@router.get("/admin/audit")
def audit_log(user=Depends(admin)):
    with store.connection() as conn:
        return {"items": [dict(r) for r in conn.execute("SELECT * FROM commercial_audit ORDER BY id DESC LIMIT 300")]}


@router.get("/azure/contracts")
def contracts(user=Depends(customer)):
    with store.connection() as conn:
        rows = conn.execute("SELECT * FROM azure_contracts " + ("" if user["role"] == "admin" else "WHERE organization_id=? ") + "ORDER BY created_at DESC",
                            () if user["role"] == "admin" else (org_id(user),)).fetchall()
        return {"items": [{"id": r["id"], "organization_id": r["organization_id"], **json.loads(r["payload"])} for r in rows]}


def contract_for(conn, contract_id, user):
    row = conn.execute("SELECT * FROM azure_contracts WHERE id=?", (contract_id,)).fetchone()
    if not row or (user["role"] != "admin" and row["organization_id"] != user["organization_id"]):
        raise HTTPException(404, "独立合同不存在")
    return row


@router.post("/admin/azure/{organization_id}/contracts", status_code=201)
def add_contract(organization_id: int, data: AzureContractInput, user=Depends(admin)):
    if data.signed_on > engine.today():
        raise HTTPException(422, "不能登记尚未签署的合同")
    with identity_connection() as identity:
        if not identity.execute("SELECT 1 FROM organizations WHERE id=?", (organization_id,)).fetchone():
            raise HTTPException(404, "组织不存在")
    with store.connection() as conn:
        contract_id = store.identifier("AZ")
        try:
            conn.execute("INSERT INTO azure_contracts VALUES(?,?,?,?,?,?,?)", (contract_id, organization_id, data.contract_number, data.meter, store.dumps(data.model_dump(mode="json")), user["id"], store.timestamp()))
        except sqlite3.IntegrityError as exc:
            raise HTTPException(409, "此组织的合同和计量项目已存在") from exc
        store.audit(conn, user, "azure.contract_registered", contract_id, organization_id=organization_id)
    return {"id": contract_id}


@router.post("/admin/azure/{contract_id}/usage", status_code=201)
def add_usage(contract_id: str, data: UsageInput, user=Depends(admin)):
    with store.connection() as conn:
        contract = contract_for(conn, contract_id, user)
        terms = json.loads(contract["payload"])
        if str(data.period_start) < terms["starts_on"] or str(data.period_end) > terms["ends_on"]:
            raise HTTPException(422, "用量账期超出合同范围")
        if data.period_end > engine.today():
            raise HTTPException(422, "不能登记未来实际用量")
        if conn.execute("SELECT 1 FROM azure_usage WHERE contract_id=? AND period_start<=? AND period_end>=?", (contract_id, str(data.period_end), str(data.period_start))).fetchone():
            raise HTTPException(409, "账期重叠，不能重复计费")
        usage_id = store.identifier("USE")
        payload = {**data.model_dump(mode="json"), "unit": terms["unit"], "meter": terms["meter"],
                   "unit_price_usd": terms["unit_price_usd"], "amount_usd": engine.cash(data.quantity * Decimal(terms["unit_price_usd"])),
                   "currency": "USD", "status": "recorded", "contract_reference": terms["reference"]}
        conn.execute("INSERT INTO azure_usage VALUES(?,?,?,?,?,?,?)", (usage_id, contract_id, str(data.period_start), str(data.period_end), store.dumps(payload), user["id"], store.timestamp()))
        store.audit(conn, user, "azure.usage_recorded", usage_id, organization_id=contract["organization_id"])
    return {"id": usage_id, **payload}


@router.get("/azure/{contract_id}/usage")
def usage(contract_id: str, user=Depends(customer)):
    with store.connection() as conn:
        contract_for(conn, contract_id, user)
        return {"items": [{"id": r["id"], **json.loads(r["payload"])} for r in conn.execute("SELECT * FROM azure_usage WHERE contract_id=? ORDER BY period_start DESC", (contract_id,))]}
