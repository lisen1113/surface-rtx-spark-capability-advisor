# Source-material import
The PRD and spreadsheet live in ChatGPT Library, not in this GitHub repository. No raw source has been committed. Before building data fixtures, use the user's authorized copies and verify whether redistribution is allowed.
Original source document names:
- Surface_RTX_Spark_PC_Capability_Advisor_V3_PRD_升级母版.docx
- Surface_RTX_Spark_PC_Capability_Database_V3_2.xlsx
Importer must retain column names, source URLs, test restrictions and provenance. Never silently fill missing benchmarks with fabricated numbers.

## Capability Engine output contract

Memory capacity, runtime compatibility, startup viability, and practical usability are separate fields. The engine returns `unknown` whenever evidence is missing. Its memory estimate includes model weights, configurable quantization overhead, KV cache, runtime reserve, and OS reserve. It never derives throughput or FPS from capacity or platform peak specifications.

## Authorized import workflow

1. Export an authorized worksheet to UTF-8 CSV without changing the original file.
2. Send it to `POST /api/catalog/import/skus/preview` with `Content-Type: text/csv`.
3. Resolve missing required fields, duplicate SKU identifiers, invalid numeric values, evidence labels, and provenance URLs.
4. Review normalized rows before any database mutation. The preview endpoint is intentionally read-only (`mutated: false`).
5. A commit endpoint must remain disabled until authentication, tenant authorization, license enforcement, and import-audit identity are implemented.

Required SKU columns are `sku`, `product`, `cpu_cores`, `gpu_cores`, `memory_gb`, `os`, `evidence_level`, `source_url`, and `note`. Non-unknown evidence requires an HTTPS source URL.

## V3.4 workbook import

The authorized V3.4 workbook is imported locally with `scripts/import-v3-workbook.py`. The source file itself is not copied into Git. Every populated row from every worksheet is retained in `source_records` with its original Chinese headers, sheet name, row number, and the workbook SHA-256. `SKU主数据` and `官方数据与来源` are additionally normalized for API queries. Re-importing the identical file is idempotent.

## V3.1 Surface SKU mapping import

The same local import command accepts the reviewed V3.1 mapping workbook when it contains a `SKU映射` sheet:

```powershell
.\backend\.venv\Scripts\python.exe .\scripts\import-v3-workbook.py "<authorized V3.1 xlsx path>"
```

The importer detects the table header below the workbook title rows and normalizes all `SKU映射` records into `sku_lookup`. This lookup table is separate from `imported_skus`: importing the Surface mapping must not replace the existing RTX Spark V3.4 advisor records. The protected API exposes `/api/catalog/quick-search`, `/api/catalog/quick-search/options`, and `/api/catalog/quick-search/{part_number}`.

By default the quick-search API excludes records whose match level is `N/A`; these retained NVIDIA rows are not deleted. ERP and ADR prices are copied from the authorized workbook and are never replaced with public-store prices. The browser's optional quote factor is a presentation calculation only and does not mutate stored prices. The workbook itself remains local and ignored by Git.
