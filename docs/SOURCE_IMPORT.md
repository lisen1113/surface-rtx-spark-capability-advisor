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
