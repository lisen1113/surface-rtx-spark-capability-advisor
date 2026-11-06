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
LOOKUP_SHEET = "SKU映射"


def _json_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _records(sheet) -> list[tuple[int, dict[str, Any]]]:
    values = list(sheet.iter_rows(values_only=True))
    header_index = None
    for index, row in enumerate(values):
        labels = {str(value).strip() for value in row if value not in (None, "")}
        if "Part Number" in labels or len(labels) >= 2:
            header_index = index
            break
    if header_index is None:
        return []
    headers = [str(value).strip() if value is not None else "" for value in values[header_index]]
    records = []
    for row_number, row in enumerate(values[header_index + 1 :], start=header_index + 2):
        record = {header: _json_value(value) for header, value in zip(headers, row) if header}
        if any(value not in (None, "") for value in record.values()):
            records.append((row_number, record))
    return records


def _series_group(record: dict[str, Any]) -> str:
    product_type = str(record.get("产品类型") or "").strip()
    product_name = str(record.get("映射产品名称（设备为微软中国官网名称）") or "").strip()
    original_family = str(record.get("原系列") or "").strip()
    if product_type == "配件":
        return "配件"
    if product_type == "延保":
        return "延保"
    if product_type.startswith("NVIDIA"):
        return "NVIDIA（暂不纳入）"
    for label in ("Surface Pro", "Surface Laptop", "Surface Go"):
        if label in product_name:
            return label
    return original_family or "其他 Surface"


def _lookup_row(record: dict[str, Any], *, source_sha256: str) -> dict[str, Any]:
    return {
        "part_number": record.get("Part Number"),
        "source_sheet": record.get("原工作表") or "",
        "source_row": record.get("原行号") or 0,
        "original_family": record.get("原系列") or "",
        "raw_description": record.get("原始描述/配置") or "",
        "product_type": record.get("产品类型") or "",
        "series_group": _series_group(record),
        "mapping_rule_id": record.get("映射规则 ID"),
        "product_name": record.get("映射产品名称（设备为微软中国官网名称）"),
        "platform": record.get("平台"),
        "cpu_raw": record.get("CPU 原始标识"),
        "cpu_official": record.get("CPU 官方名称"),
        "memory_gb": record.get("内存 (GB)"),
        "storage_capacity": record.get("存储容量"),
        "color": record.get("颜色"),
        "connectivity": record.get("联网"),
        "power_supply": record.get("电源"),
        "display": record.get("屏幕/面板"),
        "resolution": record.get("分辨率"),
        "refresh_rate": record.get("刷新率"),
        "npu": record.get("NPU"),
        "gpu": record.get("GPU"),
        "weight": record.get("重量"),
        "battery": record.get("电池使用时间"),
        "operating_system": record.get("操作系统"),
        "erp_price_cny": record.get("ERP 含税价"),
        "adr_price_cny": record.get("ADR Price"),
        "official_source_url": record.get("官方来源 URL"),
        "source_checked_at": record.get("来源访问日期"),
        "match_level": record.get("匹配级别") or "",
        "pn_visible": record.get("PN 官网可见"),
        "unknown_fields": record.get("未知字段"),
        "exception_note": record.get("异常/复核说明"),
        "review_status": record.get("复核状态"),
        "source_sha256": source_sha256,
    }


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
    version = "V3.1" if LOOKUP_SHEET in all_records else "V3.4" if "V3_4" in source_path.name else "unknown"

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

        if LOOKUP_SHEET in all_records:
            conn.execute("DELETE FROM sku_lookup")
            lookup_columns = tuple(_lookup_row({}, source_sha256=digest).keys())
            placeholders = ",".join("?" for _ in lookup_columns)
            column_sql = ",".join(lookup_columns)
            for _, record in all_records[LOOKUP_SHEET]:
                normalized = _lookup_row(record, source_sha256=digest)
                if not normalized["part_number"]:
                    continue
                conn.execute(
                    f"INSERT INTO sku_lookup ({column_sql}) VALUES ({placeholders})",
                    tuple(normalized[column] for column in lookup_columns),
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
        "lookup_count": len(all_records.get(LOOKUP_SHEET, [])),
        "evidence_count": len(all_records.get(EVIDENCE_SHEET, [])),
    }
