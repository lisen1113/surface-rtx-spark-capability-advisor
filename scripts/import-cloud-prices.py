"""Read the supplied workbook into local draft versions with source provenance."""
import argparse
from datetime import date, datetime
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.commercial.models import PriceInput
from app.commercial import store

COMPONENTS = {
    "BUNDLE-STANDARD-COPILOT": ["M365-BIZ-STANDARD", "COPILOT-BUSINESS"],
    "BUNDLE-PREMIUM-COPILOT": ["M365-BIZ-PREMIUM", "COPILOT-BUSINESS"],
    "M365-E7": ["M365-E5", "COPILOT-ENTERPRISE", "AGENT-365", "ENTRA-SUITE"],
}


def import_workbook(path):
    if os.getenv("CAPABILITY_DEPLOYMENT_MODE", "local") != "local":
        raise RuntimeError("This importer is local-only; production imports need a separate reviewed release")
    from openpyxl import load_workbook
    path = Path(path)
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    workbook = load_workbook(path, read_only=True, data_only=False)
    try:
        originals = {sheet.title: [list(row) for row in sheet.iter_rows(values_only=True)] for sheet in workbook}
        sheet = workbook["产品价格数据库"]
        rows = list(sheet.iter_rows(values_only=True))
        headers = rows[0]
        required = {"ProductId", "官方英文名称", "产品类型", "币种", "官方月价", "核验日期", "官方来源URL"}
        if not required.issubset(set(headers)):
            raise ValueError("Workbook headers do not match the reviewed import format")
        records = []
        for row_number, values in enumerate(rows[1:], 2):
            row = dict(zip(headers, values))
            if not row["ProductId"]:
                continue
            if row["币种"] != "USD":
                raise ValueError(f"Row {row_number}: expected USD source price; no implicit RMB conversion")
            value = row["官方月价"]
            if value is None or isinstance(value, str) and value.startswith("="):
                raise ValueError(f"Row {row_number}: standard monthly price must be a source number")
            checked = row["核验日期"]
            if isinstance(checked, datetime):
                checked = checked.date()
            elif not isinstance(checked, date):
                checked = date.fromisoformat(str(checked)[:10])
            limit = row.get("用户上限")
            records.append(PriceInput(
                product_id=row["ProductId"], name=row["官方英文名称"], kind=row["产品类型"],
                monthly_usd=Decimal(str(value)), effective_from=checked, source_checked_at=checked,
                seat_limit=int(limit) if isinstance(limit, (int, float)) else None,
                prerequisite=str(row.get("许可前置条件") or ""), market=str(row.get("市场基准") or ""),
                components=COMPONENTS.get(row["ProductId"], []), source_url=row["官方来源URL"],
                source_reference=f"{path.name} / 产品价格数据库 / row {row_number} / sha256 {sha}; 用户成本规则为标准公开价×85%；原表促销不用于对客报价"))
        if not records or len({r.product_id for r in records}) != len(records):
            raise ValueError("No records or duplicate ProductId values")
        with store.connection() as conn:
            previous = conn.execute("SELECT price_ids_json FROM commercial_imports WHERE source_sha256=?", (sha,)).fetchone()
            if previous:
                return {"status": "already_imported", "count": len(json.loads(previous[0])), "source_sha256": sha}
            ids = [store.create_price(conn, record, 0) for record in records]
            conn.execute("INSERT INTO commercial_imports VALUES(?,?,?,?,?)", (sha, path.name, store.timestamp(), store.dumps(originals), store.dumps(ids)))
            store.audit(conn, {"id": 0}, "source.imported_as_draft", sha, details={"record_count": len(ids), "source_name": path.name})
        return {"status": "draft", "count": len(ids), "source_sha256": sha, "note": "Original source preserved; no prices published, promotions applied or catalog data changed"}
    finally:
        workbook.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--database", type=Path, required=True, help="Separate local commercial database")
    args = parser.parse_args()
    os.environ["CAPABILITY_COMMERCIAL_PATH"] = str(args.database.resolve())
    print(json.dumps(import_workbook(args.workbook), ensure_ascii=False))
