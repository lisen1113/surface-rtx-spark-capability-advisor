# V3.0 Codex implementation backlog
## Milestone M0 — Runnable local foundation (P0)
- Scaffold frontend Next.js + TS and backend FastAPI with Python 3.12; pin/test compatible ARM64 and x64 dependencies.
- Local SQLite dev database, Alembic migrations, sample seed data and `scripts/start-local.ps1` with prerequisite checks.
- /health API and Chinese UI shell; copyright notice on login, footer, about and exported report.
- Test Windows local startup, health endpoint and shutdown. Document Windows ARM64 limitations rather than silently using incompatible wheels.
## M1 — Product data and Capability Engine (P0)
- Normalized SKU, hardware, AI model/version, quantization, runtime, games, applications, benchmarks, citations and evidence_level entities.
- Import path from source spreadsheet with preview, validation, duplicate detection, audit trail; retain raw source provenance.
- Capacity estimation: weights + quantization overhead + KV cache + runtime + OS reserve. Separate fits-in-memory, can-start, compatible, usable.
- Never convert peak 300 GB/s or platform max specs into actual tok/s; never infer game FPS from a marketing 100 FPS statement.
## M2 — Advisors (P0/P1)
- SKU selection/search; AI advisor with context, quantization, concurrent users; gaming by title/resolution/settings/API; productivity by app/version/OS.
- Confidence labels: official tested / third-party tested / engineering estimate / unknown.
- Customer report and explanations.
## M3 — Knowledge and local deployment (P1)
- 200 FAQ records across 12 categories with easy/expert answers and reviewed references.
- Deployment guides with compatibility matrix for native Windows ARM64, WSL2, containers and external server.
- Framework catalog: Ollama, LM Studio, llama.cpp, vLLM, SGLang, TensorRT-LLM, PyTorch, Strata (disambiguate).
## M4 — Security and licensing (P0)
- Registration, email verification, admin approval, password reset, login/logout, session invalidation.
- Multi-tenant organization/roles, permissions, license seats/expiry; protected server API enforcement; audit.
- Auth integration tests: unauthorized, expired license, cross-tenant access, password reset expiry, throttling.
## M5 — TCO and release quality (P1)
- Editable local-vs-cloud assumptions, pricing in CNY, electricity, amortization, utilization, token volume, ROI.
- Packaging, Windows setup guide, CI checks, privacy/security checklist and acceptance report.
## Definition of done
- Local Windows 11 documented install and launch, DB seed + migrations, no cloud dependency for core browsing.
- Real APIs with authorization; no hardcoded secrets; all numbers show provenance and test conditions.
- Automated tests pass and core workflows manually checked. Pull request reviewed prior to merge.
