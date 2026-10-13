# Source-material import
The PRD and spreadsheet live in ChatGPT Library, not in this GitHub repository. No raw source has been committed. Before building data fixtures, use the user's authorized copies and verify whether redistribution is allowed.
Original source document names:
- Surface_RTX_Spark_PC_Capability_Advisor_V3_PRD_升级母版.docx
- Surface_RTX_Spark_PC_Capability_Database_V3_2.xlsx
Importer must retain column names, source URLs, test restrictions and provenance. Never silently fill missing benchmarks with fabricated numbers.

## Capability Engine output contract

Memory capacity, runtime compatibility, startup viability, and practical usability are separate fields. The engine returns `unknown` whenever evidence is missing. Its memory estimate includes model weights, configurable quantization overhead, KV cache, runtime reserve, and OS reserve. It never derives throughput or FPS from capacity or platform peak specifications.
