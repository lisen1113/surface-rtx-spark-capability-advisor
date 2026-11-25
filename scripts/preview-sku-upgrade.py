"""Create an isolated catalog preview and serve the upgraded advisor locally."""
import argparse
import os
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

parser = argparse.ArgumentParser()
parser.add_argument("workbook", type=Path)
parser.add_argument("--port", type=int, default=8012)
parser.add_argument("--verify-only", action="store_true")
args = parser.parse_args()
preview = ROOT / "data" / "sku-preview.sqlite3"
preview.parent.mkdir(exist_ok=True)
if not preview.exists():
    with sqlite3.connect(ROOT / "data" / "capability.sqlite3") as original:
        with sqlite3.connect(preview) as destination:
            original.backup(destination)
os.environ["CAPABILITY_CATALOG_PATH"] = str(preview)
os.environ["CAPABILITY_DEPLOYMENT_MODE"] = "local"
from app.xlsx_import import import_workbook
from app.catalog import connection

result = import_workbook(args.workbook)
with connection() as conn:
    count = conn.execute("SELECT COUNT(*) FROM sku_lookup").fetchone()[0]
    searchable = conn.execute("SELECT COUNT(*) FROM sku_lookup WHERE match_level NOT LIKE 'N/A%'").fetchone()[0]
    legacy = conn.execute("SELECT COUNT(*) FROM imported_skus").fetchone()[0]
assert count == 237 and searchable == 226, (count, searchable)
print({"lookup": count, "searchable": searchable, "legacy_advisor": legacy, "database": str(preview)}, flush=True)
if not args.verify_only:
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=args.port)
