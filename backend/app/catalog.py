"""Local-first catalog with explicit provenance. Seed data are illustrative, not benchmarks."""
from pathlib import Path
import json
import sqlite3
from fastapi import APIRouter, Body

from .importer import preview_sku_csv

router = APIRouter(prefix="/api/catalog", tags=["catalog"])
DB_PATH = Path(__file__).resolve().parents[2] / "data" / "capability.sqlite3"

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
 return {"items": rows("imported_skus"), "note": "来自授权工作簿；原始记录按工作表逐行保留"}

@router.get("/imports")
def imports(): return {"items": rows("source_imports")}

@router.get("/advisor/{part_number}")
def advisor(part_number: str):
 with connection() as conn:
  sku_row = conn.execute("SELECT * FROM imported_skus WHERE part_number=?", (part_number,)).fetchone()
 if not sku_row:
  from fastapi import HTTPException
  raise HTTPException(status_code=404, detail="未找到该 Part Number")
 def direct(sheet):
  return [item for item in source_sheet(sheet) if item.get("Part Number") == part_number]
 def recommended(sheet):
  return [item for item in source_sheet(sheet) if part_number in str(item.get("适用SKU", item.get("适用SKU内存档", "")))]
 return {
  "sku": dict(sku_row), "ai": direct("AI能力映射"), "gaming": direct("游戏能力映射"),
  "generation": direct("生成能力映射"), "productivity": direct("生产力能力映射"),
  "ai_recommendations": recommended("AI经验推荐矩阵"),
  "gaming_recommendations": recommended("游戏经验推荐矩阵"),
  "disclaimer": "官方声明、实测、经验推荐和未知数据保持分离；空白性能字段不作推断。",
 }

@router.post("/import/skus/preview")
def preview_skus(content: str = Body(media_type="text/csv")):
 return preview_sku_csv(content).as_dict()
