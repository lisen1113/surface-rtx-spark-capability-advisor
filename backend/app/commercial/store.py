"""Separate transactional store; never rewrites the ERP catalog or identity DB."""
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import sqlite3
import uuid

from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[3]
SCHEMA = """
CREATE TABLE IF NOT EXISTS commercial_schema (version INTEGER PRIMARY KEY);
CREATE TABLE IF NOT EXISTS public_budget_tickets (
 ticket_hash TEXT PRIMARY KEY, content BLOB NOT NULL, filename TEXT NOT NULL, expires_at INTEGER NOT NULL
);
INSERT OR IGNORE INTO commercial_schema VALUES (1);
CREATE TABLE IF NOT EXISTS commercial_settings (
 id TEXT PRIMARY KEY, payload TEXT NOT NULL, created_by INTEGER NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS commercial_imports (
 source_sha256 TEXT PRIMARY KEY, source_name TEXT NOT NULL, imported_at TEXT NOT NULL,
 original_records_json TEXT NOT NULL, price_ids_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cloud_prices (
 id TEXT PRIMARY KEY, product_id TEXT NOT NULL, status TEXT NOT NULL,
 effective_from TEXT NOT NULL, effective_to TEXT, payload TEXT NOT NULL,
 created_by INTEGER, created_at TEXT NOT NULL, published_by INTEGER, published_at TEXT
);
CREATE INDEX IF NOT EXISTS cloud_price_resolution ON cloud_prices(product_id,status,effective_from);
CREATE TABLE IF NOT EXISTS lease_policies (
 id TEXT PRIMARY KEY, payload TEXT NOT NULL, created_by INTEGER, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS commercial_profiles (
 organization_id INTEGER PRIMARY KEY, encrypted_payload TEXT NOT NULL,
 updated_by INTEGER NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS commercial_quotes (
 id TEXT PRIMARY KEY, organization_id INTEGER NOT NULL, created_by INTEGER NOT NULL,
 state TEXT NOT NULL, input_json TEXT NOT NULL, customer_json TEXT NOT NULL,
 internal_json TEXT NOT NULL, profile_json TEXT, snapshot_hash TEXT NOT NULL,
 valid_until TEXT NOT NULL, created_at TEXT NOT NULL,
 reviewed_by INTEGER, reviewed_at TEXT, review_reason TEXT, commercial_reference TEXT,
 issued_by INTEGER, issued_at TEXT, formal_number TEXT UNIQUE, document_sha256 TEXT
);
CREATE INDEX IF NOT EXISTS commercial_quote_org ON commercial_quotes(organization_id,created_at);
CREATE TABLE IF NOT EXISTS commercial_documents (
 quote_id TEXT NOT NULL, kind TEXT NOT NULL, content BLOB NOT NULL,
 sha256 TEXT NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY(quote_id,kind)
);
CREATE TABLE IF NOT EXISTS azure_contracts (
 id TEXT PRIMARY KEY, organization_id INTEGER NOT NULL, contract_number TEXT NOT NULL,
 meter_key TEXT NOT NULL, payload TEXT NOT NULL, created_by INTEGER NOT NULL, created_at TEXT NOT NULL,
 UNIQUE(organization_id,contract_number,meter_key)
);
CREATE TABLE IF NOT EXISTS azure_usage (
 id TEXT PRIMARY KEY, contract_id TEXT NOT NULL REFERENCES azure_contracts(id),
 period_start TEXT NOT NULL, period_end TEXT NOT NULL, payload TEXT NOT NULL,
 created_by INTEGER NOT NULL, created_at TEXT NOT NULL,
 UNIQUE(contract_id,period_start,period_end)
);
CREATE TABLE IF NOT EXISTS commercial_audit (
 id INTEGER PRIMARY KEY AUTOINCREMENT, occurred_at TEXT NOT NULL,
 actor INTEGER NOT NULL, organization_id INTEGER, action TEXT NOT NULL,
 target_id TEXT NOT NULL, details_json TEXT NOT NULL
);
"""


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def identifier(prefix):
    return prefix + "-" + uuid.uuid4().hex


def dumps(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def digest(value):
    return hashlib.sha256(dumps(value).encode("utf-8")).hexdigest()


def db_path():
    return Path(os.getenv("CAPABILITY_COMMERCIAL_PATH", str(ROOT / "data" / "commercial-local.sqlite3"))).resolve()


def ensure_enabled():
    if os.getenv("CAPABILITY_DEPLOYMENT_MODE", "local") != "local" and os.getenv("CAPABILITY_COMMERCIAL_ENABLED") != "1":
        raise HTTPException(503, "商业模块尚未在此部署启用")


@contextmanager
def connection():
    ensure_enabled()
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=15)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.executescript(SCHEMA)
        # Serializes approval, price publication and billing overlap checks.
        conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


def audit(conn, user, action, target, *, organization_id=None, details=None):
    # Never place customer bank details, tokens or complete profile payloads here.
    conn.execute("INSERT INTO commercial_audit(occurred_at,actor,organization_id,action,target_id,details_json) VALUES(?,?,?,?,?,?)",
                 (timestamp(), user["id"], organization_id, action, target, dumps(details or {})))


def cipher():
    from cryptography.fernet import Fernet
    key = os.getenv("CAPABILITY_COMMERCIAL_KEY")
    if not key and os.getenv("CAPABILITY_DEPLOYMENT_MODE", "local") == "local":
        path = db_path().with_suffix(".key")
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("xb") as output:
                output.write(Fernet.generate_key())
            path.chmod(0o600)
        except FileExistsError:
            pass
        key = path.read_bytes()
    if not key:
        raise HTTPException(503, "客户资料加密密钥尚未配置")
    try:
        return Fernet(key)
    except (ValueError, TypeError) as exc:
        raise HTTPException(503, "客户资料加密密钥无效") from exc


def encrypt(payload):
    return cipher().encrypt(dumps(payload).encode("utf-8")).decode("ascii")


def decrypt(payload):
    from cryptography.fernet import InvalidToken
    try:
        return json.loads(cipher().decrypt(payload.encode("ascii")))
    except InvalidToken as exc:
        raise HTTPException(503, "客户资料解密失败，请检查原密钥") from exc


def resolve_price(conn, product_id, on):
    rows = conn.execute("SELECT * FROM cloud_prices WHERE product_id=? AND status='published' AND effective_from<=? AND (effective_to IS NULL OR effective_to>?)",
                        (product_id, str(on), str(on))).fetchall()
    if not rows:
        raise HTTPException(409, f"{product_id} 没有已发布的有效标准价")
    if len(rows) != 1:
        raise HTTPException(409, f"{product_id} 存在重叠价格版本")
    row = dict(rows[0])
    return {**json.loads(row["payload"]), "price_version_id": row["id"]}


def create_price(conn, data, actor):
    price_id = identifier("PV")
    conn.execute("INSERT INTO cloud_prices(id,product_id,status,effective_from,effective_to,payload,created_by,created_at) VALUES(?,?,'draft',?,?,?,?,?)",
                 (price_id, data.product_id, str(data.effective_from), str(data.effective_to) if data.effective_to else None,
                  dumps(data.model_dump(mode="json")), actor, timestamp()))
    return price_id


def publish_price(conn, price_id, actor):
    row = conn.execute("SELECT * FROM cloud_prices WHERE id=?", (price_id,)).fetchone()
    if not row or row["status"] != "draft":
        raise HTTPException(409, "只能发布草稿价格")
    overlaps = conn.execute("SELECT id FROM cloud_prices WHERE product_id=? AND status='published' AND (effective_to IS NULL OR effective_to>?) AND (? IS NULL OR effective_from<?)",
                            (row["product_id"], row["effective_from"], row["effective_to"], row["effective_to"])).fetchall()
    if overlaps:
        raise HTTPException(409, "价格有效期重叠，请通过替换操作结束旧版本")
    conn.execute("UPDATE cloud_prices SET status='published',published_by=?,published_at=? WHERE id=?", (actor, timestamp(), price_id))


def replace_price(conn, price_id, actor):
    row = conn.execute("SELECT * FROM cloud_prices WHERE id=? AND status='draft'", (price_id,)).fetchone()
    if not row:
        raise HTTPException(409, "只能替换为草稿价格")
    # Close only earlier active intervals. Never delete/rewrite historical values.
    conn.execute("UPDATE cloud_prices SET effective_to=? WHERE product_id=? AND status='published' AND effective_from<? AND (effective_to IS NULL OR effective_to>?)",
                 (row["effective_from"], row["product_id"], row["effective_from"], row["effective_from"]))
    publish_price(conn, price_id, actor)
