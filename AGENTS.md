# Codex development instructions — Capability Advisor V3.0
Product: Surface / RTX Spark PC Capability Advisor V3.0.
Owner/copyright notice: © 2026 上海以和信息技术有限公司。保留所有权利。Commercial identity: 微软商用 Surface 授权 ADR（须在发布前核实授权与商标使用）。
Canonical source documents (ChatGPT Library, not automatically accessible from repository):
- Surface_RTX_Spark_PC_Capability_Advisor_V3_PRD_升级母版.docx (2026-10-09)
- Surface_RTX_Spark_PC_Capability_Database_V3_2.xlsx (2026-10-11)
Do not claim that these source files are present in GitHub. Request secure import or implement documented schema and CSV importers until actual files are available.
Goals:
1. SKU-driven AI model / gaming / productivity advisor using one explainable Capability Engine.
2. Local AI framework deployment guides (Ollama, llama.cpp, LM Studio, TensorRT-LLM, vLLM, SGLang; validate OS/architecture support). Strata must identify exact project/version.
3. AI FAQ initially targeting 200 indexed questions, with plain-language and engineering answers, linked sources, SKU/model/framework relevance.
4. Token savings / TCO / ROI with user-editable assumptions.
5. Registration, email verification, admin approval, password login, tenant RBAC, server-enforced License expiration and seats, audit logs. No default shared production admin password.
6. Windows 11 local execution including ARM64 vs x64 dependency checks; SQLite quickstart; PostgreSQL production option.
7. Chinese-first accessible UI and exportable evidence-backed customer report.
Accuracy: official evidence, independent benchmark, engineering estimate, unknown must remain distinct. Never invent game FPS or model tok/s. A platform-level claim is not a per-SKU benchmark. Track source URL, test configuration, date, confidence and limitations.
Security: secrets only in env, password Argon2id, rate limiting, secure sessions, CSRF where needed, admin MFA, least privilege. Do not commit proprietary or licensed files without permission.
Delivery: small testable pull requests; lint, typecheck, unit/API/e2e tests; Windows PowerShell quickstart; update README and changelog; do not merge untested code into main.
