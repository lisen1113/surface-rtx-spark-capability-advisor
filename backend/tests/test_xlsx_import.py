from pathlib import Path
import sqlite3

from openpyxl import Workbook

from app.catalog import SCHEMA
from app.xlsx_import import import_workbook


def test_workbook_import_preserves_all_rows_and_normalizes_core_tables(tmp_path: Path):
    workbook = Workbook()
    sku = workbook.active
    sku.title = "SKU主数据"
    sku.append(["产品系列", "Part Number", "原始配置描述", "平台标识（原文）", "内存容量_GB"])
    sku.append(["Surface Laptop Ultra", "EP2-TEST", "S3 128GB", "S3", 128])
    evidence = workbook.create_sheet("官方数据与来源")
    evidence.append(["ID", "类别", "官方发布主体", "数据/结论", "官方URL"])
    evidence.append(["SRC-TEST", "平台", "NVIDIA", "测试声明", "https://example.com"])
    extra = workbook.create_sheet("AI能力映射")
    extra.append(["Part Number", "数据状态"])
    extra.append(["EP2-TEST", "待实测"])
    path = tmp_path / "Capability_Database_V3_4.xlsx"
    workbook.save(path)

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    result = import_workbook(path, db=conn)

    assert result["version"] == "V3.4"
    assert result["sheet_count"] == 3
    assert result["record_count"] == 3
    assert conn.execute("SELECT COUNT(*) FROM source_records").fetchone()[0] == 3
    assert conn.execute("SELECT memory_gb FROM imported_skus WHERE part_number='EP2-TEST'").fetchone()[0] == 128
    assert conn.execute("SELECT source_url FROM imported_evidence WHERE evidence_id='SRC-TEST'").fetchone()[0] == "https://example.com"
