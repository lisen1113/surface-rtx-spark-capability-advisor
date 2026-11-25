"""Authorized source import validation. Preview never mutates the catalog."""
from __future__ import annotations

import csv
import io
from collections import Counter
from dataclasses import dataclass, field


SKU_COLUMNS = {
    "sku",
    "product",
    "cpu_cores",
    "gpu_cores",
    "memory_gb",
    "os",
    "evidence_level",
    "source_url",
    "note",
}
EVIDENCE_LEVELS = {
    "official_tested",
    "official_claim",
    "third_party_tested",
    "engineering_estimate",
    "user_supplied_unverified",
    "unknown",
}


@dataclass
class ImportPreview:
    valid: bool
    rows_received: int
    rows_valid: int
    headers: list[str]
    errors: list[dict] = field(default_factory=list)
    warnings: list[dict] = field(default_factory=list)
    normalized_rows: list[dict] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "valid": self.valid,
            "rows_received": self.rows_received,
            "rows_valid": self.rows_valid,
            "headers": self.headers,
            "errors": self.errors,
            "warnings": self.warnings,
            "normalized_rows": self.normalized_rows,
            "mutated": False,
        }


def _integer(value: str, *, row: int, field_name: str, errors: list[dict]) -> int | None:
    if value.strip() == "":
        return None
    try:
        number = int(value)
    except ValueError:
        errors.append({"row": row, "field": field_name, "code": "invalid_integer"})
        return None
    if number < 0:
        errors.append({"row": row, "field": field_name, "code": "negative_value"})
        return None
    return number


def preview_sku_csv(content: str) -> ImportPreview:
    if content.startswith("\ufeff"):
        content = content.lstrip("\ufeff")
    reader = csv.DictReader(io.StringIO(content))
    headers = [header.strip() for header in (reader.fieldnames or []) if header]
    errors: list[dict] = []
    warnings: list[dict] = []
    missing = sorted(SKU_COLUMNS - set(headers))
    unknown = sorted(set(headers) - SKU_COLUMNS)
    if missing:
        errors.append({"row": 1, "field": "headers", "code": "missing_columns", "columns": missing})
    if unknown:
        warnings.append({"row": 1, "field": "headers", "code": "unknown_columns", "columns": unknown})

    raw_rows = list(reader)
    sku_counts = Counter((row.get("sku") or "").strip() for row in raw_rows)
    normalized: list[dict] = []
    for line_number, row in enumerate(raw_rows, start=2):
        row_errors_before = len(errors)
        sku = (row.get("sku") or "").strip()
        product = (row.get("product") or "").strip()
        operating_system = (row.get("os") or "").strip()
        evidence_level = (row.get("evidence_level") or "").strip()
        source_url = (row.get("source_url") or "").strip()
        for name, value in (("sku", sku), ("product", product), ("os", operating_system)):
            if not value:
                errors.append({"row": line_number, "field": name, "code": "required"})
        if sku and sku_counts[sku] > 1:
            errors.append({"row": line_number, "field": "sku", "code": "duplicate", "value": sku})
        if evidence_level not in EVIDENCE_LEVELS:
            errors.append({"row": line_number, "field": "evidence_level", "code": "invalid_evidence_level"})
        if source_url and not source_url.startswith("https://"):
            errors.append({"row": line_number, "field": "source_url", "code": "https_required"})
        if evidence_level != "unknown" and not source_url:
            errors.append({"row": line_number, "field": "source_url", "code": "required_for_evidence"})

        normalized_row = {
            "sku": sku,
            "product": product,
            "cpu_cores": _integer(row.get("cpu_cores") or "", row=line_number, field_name="cpu_cores", errors=errors),
            "gpu_cores": _integer(row.get("gpu_cores") or "", row=line_number, field_name="gpu_cores", errors=errors),
            "memory_gb": _integer(row.get("memory_gb") or "", row=line_number, field_name="memory_gb", errors=errors),
            "os": operating_system,
            "evidence_level": evidence_level,
            "source_url": source_url,
            "note": (row.get("note") or "").strip(),
        }
        if len(errors) == row_errors_before:
            normalized.append(normalized_row)

    return ImportPreview(
        valid=not errors,
        rows_received=len(raw_rows),
        rows_valid=len(normalized),
        headers=headers,
        errors=errors,
        warnings=warnings,
        normalized_rows=normalized,
    )
