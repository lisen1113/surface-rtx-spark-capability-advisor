"""Import an authorized V3 workbook while retaining every populated source row."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any

from openpyxl import load_workbook

from .catalog import connection


SKU_SHEET = "SKU主数据"
EVIDENCE_SHEET = "官方数据与来源"


def _json_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _records(sheet) -> list[tuple[int, dict[str, Any]]]:
    values = sheet.iter_rows(values_only=True)
    headers = [str(value).strip() if value is not None else "" for value in next(values)]
    records = []
    for row_number, row in enumerate(values, start=2):
        record = {header: _json_value(value) for header, value in zip(headers, row) if header}
        if any(value not in (None, "") for value in record.values()):
            records.append((row_number, record))
    return records


def import_workbook(path: str | Path, *, db: sqlite3.Connection | None = None) -> dict:
    source_path = Path(path)
    digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
    workbook = load_workbook(source_path, read_only=True, data_only=False)
    own_connection = db is None
    conn = db or connection()
    all_records: dict[str, list[tuple[int, dict[str, Any]]]] = {
        sheet.title: _records(sheet) for sheet in workbook.worksheets
    }
    record_count = sum(len(records) for records in all_records.values())
    version = "V3.4" if "V3_4" in source_path.name else "unknown"

    try:
        conn.execute("BEGIN")
        conn.execute("DELETE FROM source_records WHERE source_sha256 = ?", (digest,))
        for sheet_name, records in all_records.items():
            conn.executemany(
                "INSERT INTO source_records VALUES (?,?,?,?)",
                [(digest, sheet_name, row_number, json.dumps(record, ensure_ascii=False)) for row_number, record in records],
            )
        conn.execute(
            "INSERT OR REPLACE INTO source_imports VALUES (?,?,?,?,?,?)",
            (digest, source_path.name, version, datetime.now(timezone.utc).isoformat(), len(all_records), record_count),
        )

        if SKU_SHEET in all_records:
            conn.execute("DELETE FROM imported_skus")
            for _, r in all_records[SKU_SHEET]:
                conn.execute(
                    "INSERT INTO imported_skus VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        r.get("Part Number"), r.get("产品系列"), r.get("原始配置描述"), r.get("平台标识（原文）"),
                        r.get("内存容量_GB"), r.get("存储容量_TB"), r.get("颜色（原文）"), r.get("10月ERP含税价"),
                        r.get("价格币种"), r.get("CPU型号"), r.get("GPU型号"), r.get("GPU显存_GB"),
                        r.get("内存类型/带宽"), r.get("NPU参数"), r.get("功耗/散热信息"), r.get("操作系统"),
                        r.get("产品规格来源"), r.get("配置数据状态"), r.get("备注"), digest,
                    ),
                )

        if EVIDENCE_SHEET in all_records:
            conn.execute("DELETE FROM imported_evidence")
            for _, r in all_records[EVIDENCE_SHEET]:
                conn.execute(
                    "INSERT INTO imported_evidence VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        r.get("ID"), r.get("类别"), r.get("官方发布主体"), r.get("数据/结论"), r.get("数值/范围"),
                        r.get("适用范围"), r.get("证据等级"), r.get("测试条件/限制"), r.get("官方来源标题"),
                        r.get("官方URL"), r.get("发布日期/页面时间"), r.get("数据库处理规则"), digest,
                    ),
                )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        workbook.close()
        if own_connection:
            conn.close()

    return {
        "source_name": source_path.name,
        "source_sha256": digest,
        "version": version,
        "sheet_count": len(all_records),
        "record_count": record_count,
        "sku_count": len(all_records.get(SKU_SHEET, [])),
        "evidence_count": len(all_records.get(EVIDENCE_SHEET, [])),
    }
