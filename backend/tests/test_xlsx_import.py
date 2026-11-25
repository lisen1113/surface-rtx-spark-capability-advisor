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


def test_v31_mapping_workbook_populates_lookup_without_replacing_existing_advisor_skus(tmp_path: Path):
    workbook = Workbook()
    mapping = workbook.active
    mapping.title = "SKU映射"
    mapping.append([])
    mapping.append(["SKU—官方技术规格映射"])
    mapping.append(["审阅版"])
    mapping.append([])
    mapping.append([
        "序号", "原工作表", "原行号", "原系列", "Part Number", "原始描述/配置", "ERP 含税价", "ADR Price",
        "产品类型", "映射规则 ID", "映射产品名称（设备为微软中国官网名称）", "平台", "CPU 原始标识", "CPU 官方名称",
        "内存 (GB)", "存储容量", "颜色", "联网", "电源", "屏幕/面板", "分辨率", "刷新率", "NPU", "GPU",
        "重量", "电池使用时间", "操作系统", "官方来源 URL", "来源访问日期", "匹配级别", "PN 官网可见",
        "未知字段", "异常/复核说明", "复核状态",
    ])
    mapping.append([
        1, "Intel、配件、延保", 2, "SrPro 13in", "EP2-FAST", "U5/16/256", 10888, 9999.99,
        "Surface 设备", "PRO13", "Surface Pro 商用版, 13 英寸", "x86 / Intel", "U5", "Intel Ultra 5",
        16, "256GB", "Platinum", "Wi-Fi", "", "13 英寸", "2880 × 1920", "120 Hz", "NPU", "GPU",
        "895 g", "17 小时", "Windows 11 专业版", "https://example.com/pro", "2026-10-27", "A1 配置一致",
        "否", "", "", "可查验",
    ])
    mapping.append([
        2, "Intel、配件、延保", 3, "配件", "ACC-FAST", "Surface mouse", 588, 500,
        "配件", "ACC_MOUSE", "Surface Arc Mouse", "", "", "", "", "", "Black", "Bluetooth", "", "", "", "", "", "", "", "", "", "", "2026-10-27", "U1 用户规则映射", "不适用", "", "", "按系列可查验",
    ])
    path = tmp_path / "Surface_mapping_V3_1.xlsx"
    workbook.save(path)

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.execute(
        "INSERT INTO imported_skus (part_number,product_family,raw_configuration,platform_code,source_sha256) VALUES (?,?,?,?,?)",
        ("RTX-EXISTING", "Surface Laptop Ultra", "S3", "S3", "old-source"),
    )
    conn.commit()
    result = import_workbook(path, db=conn)

    assert result["version"] == "V3.1"
    assert result["lookup_count"] == 2
    assert conn.execute("SELECT COUNT(*) FROM imported_skus").fetchone()[0] == 1
    row = conn.execute("SELECT * FROM sku_lookup WHERE part_number='EP2-FAST'").fetchone()
    assert row["series_group"] == "Surface Pro"
    assert row["memory_gb"] == 16
    assert row["erp_price_cny"] == 10888
    assert conn.execute("SELECT series_group FROM sku_lookup WHERE part_number='ACC-FAST'").fetchone()[0] == "配件"
