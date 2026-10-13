"""Local-first catalog with explicit provenance. Seed data are illustrative, not benchmarks."""
from pathlib import Path
import json
import sqlite3
from fastapi import APIRouter, Query

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

@router.get("/skus")
def skus(): return {"items":rows("skus"),"note":"待导入完整官方 SKU 数据"}

@router.get("/models")
def models(): return {"items":rows("models"),"note":"家族占位，不可作为性能基准"}

@router.get("/sources")
def sources(): return {"items":rows("evidence")}
