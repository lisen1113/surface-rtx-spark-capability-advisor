"""Local-first catalog with explicit provenance. Seed data are illustrative, not benchmarks."""
from pathlib import Path
import json
import os
import sqlite3
from fastapi import APIRouter, Body, HTTPException, Query
from .advisor_access import public_product

from .importer import preview_sku_csv
from .generation import generation_guidance
from .productivity import productivity_guidance
from .spark_updates import agent_guidance, gaming_updates

router = APIRouter(prefix="/api/catalog", tags=["catalog"])
DB_PATH = Path(os.getenv("CAPABILITY_CATALOG_PATH", str(Path(__file__).resolve().parents[2] / "data" / "capability.sqlite3"))).resolve()

SCHEMA = """
CREATE TABLE IF NOT EXISTS skus (
 sku TEXT PRIMARY KEY, product TEXT NOT NULL, cpu_cores INTEGER, gpu_cores INTEGER,
 memory_gb INTEGER, os TEXT NOT NULL, evidence_level TEXT NOT NULL, note TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS models (
 model_id TEXT PRIMARY KEY, name TEXT NOT NULL, params_b REAL NOT NULL,
 kind TEXT NOT NULL, evidence_level TEXT NOT NULL, note TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS evidence (
 id TEXT PRIMARY KEY, title TEXT NOT NULL, source_url TEXT NOT NULL,
 evidence_level TEXT NOT NULL, scope TEXT NOT NULL, limitations TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS import_audit (
 id INTEGER PRIMARY KEY AUTOINCREMENT, source_name TEXT NOT NULL,
 source_sha256 TEXT NOT NULL, imported_at TEXT NOT NULL, imported_by TEXT NOT NULL,
 rows_received INTEGER NOT NULL, rows_imported INTEGER NOT NULL,
 status TEXT NOT NULL, details_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS source_imports (
 source_sha256 TEXT PRIMARY KEY, source_name TEXT NOT NULL, source_version TEXT NOT NULL,
 imported_at TEXT NOT NULL, sheet_count INTEGER NOT NULL, record_count INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS source_records (
 source_sha256 TEXT NOT NULL, sheet_name TEXT NOT NULL, row_number INTEGER NOT NULL,
 record_json TEXT NOT NULL, PRIMARY KEY (source_sha256, sheet_name, row_number)
);
CREATE TABLE IF NOT EXISTS imported_skus (
 part_number TEXT PRIMARY KEY, product_family TEXT NOT NULL, raw_configuration TEXT NOT NULL,
 platform_code TEXT NOT NULL, memory_gb INTEGER, storage_tb REAL, color TEXT,
 erp_price_cny REAL, currency_note TEXT, cpu_model TEXT, gpu_model TEXT,
 gpu_memory_gb REAL, memory_spec TEXT, npu_spec TEXT, thermal_spec TEXT,
 operating_system TEXT, source_reference TEXT, data_status TEXT, note TEXT,
 source_sha256 TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sku_lookup (
 part_number TEXT PRIMARY KEY,
 source_sheet TEXT NOT NULL,
 source_row INTEGER NOT NULL,
 original_family TEXT NOT NULL,
 raw_description TEXT NOT NULL,
 product_type TEXT NOT NULL,
 series_group TEXT NOT NULL,
 mapping_rule_id TEXT,
 product_name TEXT,
 platform TEXT,
 cpu_raw TEXT,
 cpu_official TEXT,
 memory_gb INTEGER,
 storage_capacity TEXT,
 color TEXT,
 connectivity TEXT,
 power_supply TEXT,
 display TEXT,
 resolution TEXT,
 refresh_rate TEXT,
 npu TEXT,
 gpu TEXT,
 weight TEXT,
 battery TEXT,
 operating_system TEXT,
 erp_price_cny REAL,
 adr_price_cny REAL,
 official_source_url TEXT,
 source_checked_at TEXT,
 match_level TEXT NOT NULL,
 pn_visible TEXT,
 unknown_fields TEXT,
 exception_note TEXT,
 review_status TEXT,
 source_sha256 TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sku_lookup_type_series ON sku_lookup(product_type, series_group);
CREATE INDEX IF NOT EXISTS idx_sku_lookup_memory_price ON sku_lookup(memory_gb, erp_price_cny);
CREATE TABLE IF NOT EXISTS imported_evidence (
 evidence_id TEXT PRIMARY KEY, category TEXT, publisher TEXT, claim TEXT,
 value_range TEXT, scope TEXT, evidence_level TEXT, limitations TEXT,
 source_title TEXT, source_url TEXT, published_at TEXT, handling_rule TEXT,
 source_sha256 TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS organizations (
 id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY AUTOINCREMENT, organization_id INTEGER, email TEXT NOT NULL UNIQUE,
 password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'member', status TEXT NOT NULL DEFAULT 'pending',
 email_verified INTEGER NOT NULL DEFAULT 0, failed_login_count INTEGER NOT NULL DEFAULT 0,
 locked_until TEXT, created_at TEXT NOT NULL, approved_at TEXT
);
CREATE TABLE IF NOT EXISTS licenses (
 organization_id INTEGER PRIMARY KEY, seats INTEGER NOT NULL, expires_at TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'active', updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
 token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL, created_at TEXT NOT NULL,
 expires_at TEXT NOT NULL, revoked_at TEXT
);
CREATE TABLE IF NOT EXISTS remember_sessions (
 token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL, created_at TEXT NOT NULL,
 expires_at TEXT NOT NULL, revoked_at TEXT
);
CREATE TABLE IF NOT EXISTS pdf_download_tickets (
 token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL, part_number TEXT NOT NULL,
 expires_at TEXT NOT NULL, used_at TEXT
);
CREATE TABLE IF NOT EXISTS admin_mfa (
 user_id INTEGER PRIMARY KEY, enabled_at TEXT NOT NULL, last_counter INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS password_reset_tokens (
 token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL, created_at TEXT NOT NULL,
 expires_at TEXT NOT NULL, used_at TEXT
);
CREATE TABLE IF NOT EXISTS email_verification_tokens (
 token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL, created_at TEXT NOT NULL,
 expires_at TEXT NOT NULL, used_at TEXT
);
CREATE TABLE IF NOT EXISTS audit_logs (
 id INTEGER PRIMARY KEY AUTOINCREMENT, occurred_at TEXT NOT NULL, actor_user_id INTEGER,
 organization_id INTEGER, action TEXT NOT NULL, target_type TEXT, target_id TEXT,
 details_json TEXT NOT NULL
);
"""
SEED_SKUS = [
 ("S2","Surface Laptop Ultra",18,5120,None,"Windows 11 Pro","user_supplied_unverified","GPU/CPU mapping from project discussion; exact SKU and memory must be checked against official product listing."),
 ("S3","Surface Laptop Ultra",20,6144,None,"Windows 11 Pro","user_supplied_unverified","GPU/CPU mapping from project discussion; exact SKU and memory must be checked against official product listing.")
]
SEED_MODELS = [
 ("qwen-family","Qwen (具体版本待导入)",0,"family","unknown","模型家族占位，不能用于性能计算"),
 ("deepseek-family","DeepSeek (具体版本待导入)",0,"family","unknown","模型家族占位，不能用于性能计算")
]
SEED_EVIDENCE = [
 ("SRC-001","NVIDIA RTX Spark platform specifications","https://www.nvidia.com/en-us/products/rtx-spark/","official_claim","RTX Spark platform","Maximum configuration is not necessarily a specific Surface SKU."),
 ("SRC-002","NVIDIA RTX Spark Porting Guide","https://docs.nvidia.com/rtx-spark/rtx-spark-porting-guide/latest/overview.html","official_claim","RTX Spark Windows on Arm platform","Peak bandwidth is not sustained inference bandwidth."),
 ("SRC-004","Building Windows for hybrid intelligence","https://blogs.windows.com/windowsexperience/2026/10/07/building-windows-for-hybrid-intelligence/","official_tested","Specified preproduction benchmark","Relative performance only; no absolute tok/s or TTFT.")
]

def connection():
 if os.getenv("CAPABILITY_DEPLOYMENT_MODE") == "public":
  conn = sqlite3.connect(DB_PATH.as_uri() + "?mode=ro", uri=True)
  conn.row_factory = sqlite3.Row
  return conn
 DB_PATH.parent.mkdir(parents=True, exist_ok=True)
 conn = sqlite3.connect(DB_PATH)
 conn.row_factory = sqlite3.Row
 conn.executescript(SCHEMA)
 conn.executemany("INSERT OR IGNORE INTO skus VALUES (?,?,?,?,?,?,?,?)",SEED_SKUS)
 conn.executemany("INSERT OR IGNORE INTO models VALUES (?,?,?,?,?,?)",SEED_MODELS)
 conn.executemany("INSERT OR IGNORE INTO evidence VALUES (?,?,?,?,?,?)",SEED_EVIDENCE)
 conn.commit()
 return conn

def rows(table):
 with connection() as conn:
  return [dict(r) for r in conn.execute(f"SELECT * FROM {table} ORDER BY 1")]

def source_sheet(sheet_name):
 with connection() as conn:
  return [json.loads(r["record_json"]) for r in conn.execute(
   "SELECT record_json FROM source_records WHERE sheet_name=? ORDER BY row_number", (sheet_name,)
  )]

@router.get("/skus")
def skus(): return {"items":rows("skus"),"note":"待导入完整官方 SKU 数据"}

@router.get("/models")
def models(): return {"items":rows("models"),"note":"家族占位，不可作为性能基准"}

@router.get("/sources")
def sources():
 imported = rows("imported_evidence")
 return {"items": imported or rows("evidence"), "source": "v3_import" if imported else "bootstrap_seed"}

@router.get("/imported-skus")
def imported_skus():
 from .advisor_access import public_advisor_enabled
 items = rows("imported_skus")
 if public_advisor_enabled():
  keys = {"part_number", "product_family", "platform_code", "memory_gb", "storage_tb", "erp_price_cny", "cpu_model", "gpu_model", "operating_system"}
  items = [{k: v for k, v in item.items() if k in keys} for item in items]
 return {"items": items, "note": "产品配置与参考价；实际能力按证据级别及实机验证"}


def _lookup_filters(*, q: str, product_type: str | None, series: str | None,
                    memory_gb: int | None, max_erp_price_cny: float | None,
                    include_excluded: bool) -> tuple[str, list]:
 conditions = []
 params: list = []
 if not include_excluded:
  conditions.append("match_level NOT LIKE 'N/A%'")
 if q:
  like = f"%{q.strip()}%"
  columns = (
   "part_number", "original_family", "raw_description", "product_name", "platform",
   "cpu_raw", "cpu_official", "storage_capacity", "color", "connectivity",
   "mapping_rule_id", "review_status",
  )
  conditions.append("(" + " OR ".join(f"COALESCE({column}, '') LIKE ? COLLATE NOCASE" for column in columns) + ")")
  params.extend([like] * len(columns))
 if product_type:
  conditions.append("product_type = ?")
  params.append(product_type)
 if series:
  conditions.append("series_group = ?")
  params.append(series)
 if memory_gb is not None:
  conditions.append("memory_gb = ?")
  params.append(memory_gb)
 if max_erp_price_cny is not None:
  conditions.append("erp_price_cny IS NOT NULL AND erp_price_cny <= ?")
  params.append(max_erp_price_cny)
 return (" WHERE " + " AND ".join(conditions)) if conditions else "", params


def _lookup_item(row: sqlite3.Row) -> dict:
 item = dict(row)
 item.pop("source_sha256", None)
 item.pop("adr_price_cny", None)
 item.pop("source_reference", None)
 for key in ("source_sheet", "source_row", "mapping_rule_id", "exception_note"):
  item.pop(key, None)
 if item.get('product_type') == 'Surface 设备':
  import re
  raw = item.get('raw_description') or ''
  item['power_supply'] = '不带电源' if re.search(r'xP|No-PSU', raw, re.I) else ''
 return item


@router.get("/quick-search/options")
def quick_search_options():
 with connection() as conn:
  base = " WHERE match_level NOT LIKE 'N/A%'"
  product_types = [dict(row) for row in conn.execute(
   "SELECT product_type AS value, COUNT(*) AS count FROM sku_lookup" + base +
   " GROUP BY product_type ORDER BY CASE product_type WHEN 'Surface 设备' THEN 1 WHEN '配件' THEN 2 WHEN '延保' THEN 3 ELSE 4 END"
  )]
  series = [dict(row) for row in conn.execute(
   "SELECT series_group AS value, COUNT(*) AS count FROM sku_lookup" + base +
   " GROUP BY series_group ORDER BY CASE series_group WHEN 'Surface Pro' THEN 1 WHEN 'Surface Laptop' THEN 2 WHEN 'Surface Go' THEN 3 WHEN '配件' THEN 4 WHEN '延保' THEN 5 ELSE 6 END, series_group"
  )]
  memory = [row[0] for row in conn.execute(
   "SELECT DISTINCT memory_gb FROM sku_lookup" + base + " AND memory_gb IS NOT NULL ORDER BY memory_gb"
  )]
  storage = [row[0] for row in conn.execute("SELECT DISTINCT storage_capacity FROM sku_lookup WHERE product_type='Surface 设备' AND storage_capacity IS NOT NULL AND storage_capacity != '' ORDER BY storage_capacity")]
  price = conn.execute(
   "SELECT MIN(erp_price_cny), MAX(erp_price_cny), COUNT(*) FROM sku_lookup" + base
  ).fetchone()
 return {
  "product_types": product_types,
  "series": series,
  "memory_gb": memory,
  "storage_capacity": storage,
  "price": {"min": price[0], "max": price[1]},
  "searchable_count": price[2],
  "note": "默认不展示标记为 N/A 的 NVIDIA 记录；价格来自用户提供的原始表格。",
 }


@router.get("/quick-search")
def quick_search(
 q: str = Query(default="", max_length=120),
 product_type: str | None = Query(default=None, max_length=40),
 series: str | None = Query(default=None, max_length=80),
 memory_gb: int | None = Query(default=None, ge=1, le=1024),
 max_erp_price_cny: float | None = Query(default=None, ge=0),
 limit: int = Query(default=30, ge=1, le=300),
 offset: int = Query(default=0, ge=0),
 include_excluded: bool = False,
 processor: str | None = Query(default=None, pattern='^(Intel|Snapdragon)$'),
 storage_capacity: str | None = Query(default=None, max_length=30),
 screen_size: str | None = Query(default=None, pattern=r'^(12|13|13\.8|15)$'),
 network: str | None = Query(default=None, pattern='^(wifi|5g)$'),
):
 if product_type in ('配件', '延保'):
  q, series, memory_gb, max_erp_price_cny, processor, storage_capacity = '', None, None, None, None, None
  screen_size = None
  network = None
 where, params = _lookup_filters(
  q=q, product_type=product_type, series=series, memory_gb=memory_gb,
  max_erp_price_cny=max_erp_price_cny, include_excluded=include_excluded,
 )
 if processor:
  where += (' AND ' if where else ' WHERE ') + 'platform LIKE ?'
  params.append('%' + processor + '%')
 if storage_capacity:
  where += (' AND ' if where else ' WHERE ') + 'storage_capacity = ?'
  params.append(storage_capacity)
 if screen_size:
  where += (' AND ' if where else ' WHERE ') + "display LIKE ?"
  params.append(screen_size + ' 英寸%')
 if network:
  where += (' AND ' if where else ' WHERE ') + ("LOWER(COALESCE(connectivity,'')) LIKE '%5g%'" if network == '5g' else "LOWER(COALESCE(connectivity,'')) NOT LIKE '%5g%' AND LOWER(REPLACE(REPLACE(REPLACE(COALESCE(connectivity,''),'‑','-'),'–','-'),' ','')) LIKE '%wi-fi%'")
 with connection() as conn:
  total = conn.execute("SELECT COUNT(*) FROM sku_lookup" + where, params).fetchone()[0]
  sort_params: list = []
  order = "product_type, erp_price_cny IS NULL, erp_price_cny, part_number"
  if q.strip():
   order = "CASE WHEN part_number = ? COLLATE NOCASE THEN 0 WHEN part_number LIKE ? COLLATE NOCASE THEN 1 ELSE 2 END, " + order
   sort_params = [q.strip(), q.strip() + "%"]
  query = "SELECT * FROM sku_lookup" + where + " ORDER BY " + order + " LIMIT ? OFFSET ?"
  found = conn.execute(query, params + sort_params + [limit, offset]).fetchall()
 return {
  "items": [_lookup_item(row) for row in found], "total": total, "limit": limit, "offset": offset,
  "price_basis": "ERP 公开含税价来自已导入产品表；不含报价折扣。",
 }


@router.get("/quick-search/{part_number}")
def quick_search_detail(part_number: str):
 with connection() as conn:
  row = conn.execute("SELECT * FROM sku_lookup WHERE part_number = ? COLLATE NOCASE", (part_number,)).fetchone()
 if row is None:
  raise HTTPException(status_code=404, detail="未找到该 Part Number")
 item = _lookup_item(row)
 return {"item": item, "price_basis": "价格以用户提供的原始表格为准。"}

@router.get('/quick-search/{part_number}/pdf')
def quick_search_pdf(part_number: str):
 from .surface_pdf import build_surface_pdf
 from fastapi.responses import Response
 item = quick_search_detail(part_number)['item']
 safe = ''.join(c if c.isascii() and (c.isalnum() or c in '-_') else '-' for c in item['part_number'])
 return Response(build_surface_pdf(item), media_type='application/pdf', headers={
  'Content-Disposition': f'attachment; filename="Surface-Product-{safe}.pdf"',
  'Cache-Control': 'no-store',
 })

@router.get("/imports")
def imports(): return {"items": rows("source_imports")}

@router.get("/advisor/{part_number}")
def advisor(part_number: str):
 with connection() as conn:
  sku_row = conn.execute("SELECT * FROM imported_skus WHERE part_number=?", (part_number,)).fetchone()
 if not sku_row:
  raise HTTPException(status_code=404, detail="未找到该 Part Number")
 def direct(sheet):
  return [item for item in source_sheet(sheet) if item.get("Part Number") == part_number]
 def recommended(sheet):
  return [item for item in source_sheet(sheet) if part_number in str(item.get("适用SKU", item.get("适用SKU内存档", "")))]
 return {
  "sku": public_product(dict(sku_row)), "ai": direct("AI能力映射"), "gaming": direct("游戏能力映射"),
  "ai_official_updates": agent_guidance(part_number, int(sku_row["memory_gb"] or 0)),
  "gaming_official_updates": gaming_updates(part_number),
  "generation": generation_guidance(part_number, int(sku_row["memory_gb"] or 0), sku_row["platform_code"]),
  "generation_source_records": direct("生成能力映射"),
  "productivity": productivity_guidance(part_number, int(sku_row["memory_gb"] or 0), sku_row["platform_code"]),
  "productivity_source_records": direct("生产力能力映射"),
  "ai_recommendations": recommended("AI经验推荐矩阵"),
  "gaming_recommendations": recommended("游戏经验推荐矩阵"),
  "disclaimer": "官方声明、实测、经验推荐和未知数据保持分离；空白性能字段不作推断。",
 }

@router.post("/import/skus/preview")
def preview_skus(content: str = Body(media_type="text/csv")):
 return preview_sku_csv(content).as_dict()
