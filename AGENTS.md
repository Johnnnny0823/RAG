# PatentScope AI — Shared Implementation & Handoff Contract

> **Status:** implementation specification / source of truth for coding agents  
> **Last updated:** 2026-11-09  
> **Language:** Traditional Chinese for product/UI/docs; English for code identifiers and API contracts.  
> **Consumers:** OpenAI Codex, Claude Code, human maintainers.  
> **Important:** This is a plan, not a claim that code, tests, data feeds, or integrations already exist.

## 0. Mandatory operating instructions (read first)

1. **Read this entire document**, inspect repository state (`pwd`, `git status`, tree, README, manifests), and read `docs/PROGRESS.md` and `docs/HANDOFF.md` if present **before modifying code**.
2. Treat this document as the common project contract. The latest accepted ADRs in `docs/adr/` can refine implementation decisions; if they conflict, explain the conflict and obtain approval before changing the architecture.
3. Work in **small, testable vertical slices**. Prefer a functioning end-to-end feature over speculative infrastructure. Do not implement all modules at once.
4. **Never fabricate** Taiwanese patent records, production search results, official API endpoints, data license permissions, benchmark scores, or successful tests. Clearly label fixtures and mocks as `DEMO`/`fixture`.
5. Before relying on TIPO datasets, **verify the current official catalog, access method, fields, refresh schedule, license/usage conditions, and download behavior**. Record exact dataset title, URL, retrieval date, format, and limitations in `docs/DATA_SOURCES.md`. If network access is unavailable, create a connector interface and fixtures; mark live ingestion BLOCKED rather than pretending it works.
6. **No secrets in git**. Use `.env.example`; do not commit credentials, tokens, raw confidential inventions, or personally identifying user data.
7. **No destructive operations** on real databases, files, branches, or migrations without explicit approval. Never silently reset/drop data. Use additive, reversible migrations when practical.
8. Run relevant format/lint/typecheck/tests for every change. Report commands and actual outcomes; never state “passed” unless executed.
9. Update `docs/PROGRESS.md` and `docs/HANDOFF.md` at the end of each meaningful work session. Leave the repository in a reproducible state. Follow the handoff template in §15.
10. If another agent may be working concurrently, coordinate ownership by file/module, inspect `git status`, avoid overwriting uncommitted work, and do not force-push or rewrite shared history.
11. If a task is too broad, **implement the earliest incomplete milestone** in §12, document what remains, and stop at a coherent checkpoint. Do not claim full completion prematurely.
12. Prefer deterministic, inspectable search pipelines. An LLM must not be the source of truth for patent identifiers, quotations, legal status, or citations.

## 1. Product mission and boundaries

**Product:** PatentScope AI (working name) — Taiwan-first AI patent prior-art search and research workspace.

**User story:** An inventor or R&D student describes an idea in natural Traditional Chinese; the system extracts technical features, retrieves relevant Taiwan patent publications, explains similarities/differences with exact source evidence, and saves a reproducible research session.

**Value:** Lower the terminology barrier to patent research, surface related technical disclosures, and support human review.

**Not a legal opinion:** Finding a similar patent does not prove infringement; not finding one does not establish novelty or patentability. Do not label an LLM score as infringement probability or legal clearance. Coverage is limited to indexed, accessible sources. Show corpus coverage and data freshness prominently.

**MVP in scope:**
- Official Taiwan patent data ingestion (verified sources), document/version preservation, parsing, and indexing.
- Natural-language search; editable extracted technical features and query expansion.
- Keyword + vector retrieval, fusion, reranking, metadata filters.
- Patent search results, document/claims detail, source links, evidence-backed feature comparison.
- Projects, saved searches, asynchronous search jobs, simple research history.
- Evaluation harness and reproducible baselines.

**MVP out of scope:** Global patent completeness, definitive freedom-to-operate opinions, automatic patent filing, production-grade legal-status conclusions, multi-agent autonomy, Electron packaging, real-time worldwide updates, OCR for every scan, enterprise SSO, and payments.

**Target users:** Taiwan-based inventors, students, R&D teams; UI primarily Traditional Chinese.

## 2. Architecture decisions (initial)

| Layer | Choice | Notes |
|---|---|---|
| Frontend | React + TypeScript + Vite + Tailwind CSS | Accessible responsive web UI; Electron later |
| API | Python 3.12+ + FastAPI + Pydantic | REST/OpenAPI; typed schemas |
| Database | PostgreSQL 16+ | Primary relational store, transactions, JSONB |
| Vector search | pgvector | Match dimensions to selected embedding model |
| Keyword search | Pluggable lexical retrieval | Start with documented baseline; **PostgreSQL `simple` FTS is NOT robust Traditional Chinese BM25**. Use verified Chinese segmentation + BM25 implementation/search engine when needed |
| Background jobs | Simple DB-backed jobs for PoC or Celery/RQ + Redis once justified | Avoid heavy infrastructure before needed |
| Source files | Local object-store abstraction in dev; S3-compatible in production | Store raw XML/PDF separately from DB |
| AI | Provider-agnostic embeddings, LLM and reranker adapters | Configurable models; never hardcode keys |
| Tests | pytest, integration tests, Vitest, Playwright (critical flows) | Mock external AI in deterministic CI |
| Packaging | Docker Compose for development | No Kubernetes in MVP |

**Reason for PostgreSQL:** supports SQL/joins/constraints, JSONB for irregular parsed metadata, and pgvector for semantic retrieval; reinforces SQL skills useful for internships. MongoDB is **not** a required dependency. Do not introduce a second primary database without measured need and an ADR.

**Architectural rule:** Source patent metadata and legal/document version relationships remain relational; embeddings and chunks reference immutable document/version IDs. A `session` is conversation context, **not** the sole store of search results or evidence.

## 3. High-level data flow

### Offline ingestion

`TIPO verified dataset -> downloader -> immutable raw object -> format validator -> parser -> normalized application/document/claim/section -> chunker -> lexical index + embeddings -> searchable corpus`

### Online search

`User idea -> feature extraction (editable) -> query variants -> lexical + vector retrieval -> RRF fusion -> document-level dedup -> rerank -> feature/evidence matching -> citation verification -> ranked results + research record`

Keep ingestion and query pipelines independent. Every answer should expose which data snapshot/index and model versions were used.

## 4. Taiwan patent data source contract

Primary discovery portal: `https://cloud.tipo.gov.tw/S220/opdata` (verify live before implementation). Relevant categories may include published/granted patent bibliographic data, specifications, claims, IPC classifications, and legal events; **actual downloadable datasets, formats, completeness, rights and API capabilities require verification**.

Create `docs/DATA_SOURCES.md` with columns:
- dataset_name; official_url; publisher; checked_at; coverage; format; update_frequency; license/terms; access_method; rate_limits; example_record; parser_version; known_gaps.

**Source connector interface** (do not assume a specific endpoint):
- `list_available_batches() -> list[BatchManifest]`
- `download_batch(manifest) -> RawArtifact`
- `parse_artifact(artifact) -> Iterable[ParsedPatentRecord]`
- `checkpoint(batch_id, checksum, parser_version, status)`

Ingestion requirements:
- Checksums and idempotent imports; batch provenance and error quarantine.
- Preserve raw source and parsed version; never overwrite older publication/grant document versions.
- Separate **application number** from **publication/grant document number**, including kind codes where available.
- Store IPC; do not invent CPC if unavailable. Preserve original language and text offsets/paragraph markers.
- Store applicant/inventor names and priorities as available, without assuming each field exists.
- Record partial records and parser errors rather than silently dropping them.
- Avoid scraping sources that prohibit it; observe access and licensing constraints.
- For unavailable PDFs or diagrams, display `source unavailable` and retain source link if verified.

## 5. Data model (PostgreSQL)

Use UUID primary keys internally and UNIQUE constraints on verified external identifiers. All timestamps UTC (`timestamptz`); dates as `date` when only calendar date is known. Use Alembic migrations. Do not use patent title as an identifier.

### Core patent tables

1. `source_datasets(id, name, publisher, official_url, license_notes, checked_at, ...)`
2. `ingestion_batches(id, dataset_id, batch_key, checksum, parser_version, status, counts_jsonb, started_at, finished_at, error_log, ...)`
3. `patent_applications(id, jurisdiction, application_no, filing_date, metadata_jsonb, ...)` — unique `(jurisdiction, application_no)` when valid.
4. `patent_documents(id, application_id, publication_no, kind_code, document_stage, publication_date, title_zh, title_en, abstract_zh, abstract_en, raw_object_key, source_url, source_hash, parser_version, ...)` — unique key must account for official identifier/version semantics; validate against actual source.
5. `patent_parties(id, normalized_name, original_name, ...)`, `document_parties(document_id, party_id, role, sequence)`.
6. `patent_classifications(id, document_id, scheme, code, version, ...)` — IPC and optional CPC.
7. `patent_priorities(id, application_id, jurisdiction, priority_no, priority_date, ...)`.
8. `patent_sections(id, document_id, section_type, ordinal, original_text, source_locator_jsonb, ...)`.
9. `patent_claims(id, document_id, claim_number, text, independent_flag_nullable, source_locator_jsonb, ...)`.
10. `claim_dependencies(child_claim_id, parent_claim_id)` — verify parent exists in same document; guard against cycles.
11. `patent_chunks(id, document_id, section_id_nullable, claim_id_nullable, chunk_order, text_for_search, exact_source_text, source_locator_jsonb, content_hash, tokenizer_version, ...)`.
12. `embedding_models(id, provider, model_name, model_version, dimensions, ...)` and `chunk_embeddings(chunk_id, model_id, embedding, created_at)` — dimension/DDL and index must match chosen model; migrations needed for model changes.
13. `patent_legal_events(id, application_id, source_dataset_id, event_type, event_date, source_reference, ...)` — only when verified and with freshness disclaimers.
14. `document_assets(id, document_id, asset_type, object_key, checksum, mime_type, ...)`.

### User/research tables

15. `users(id, email, password_hash, created_at, ...)` (or trusted auth provider, with ADR).
16. `projects(id, owner_user_id, name, description, created_at, ...)`.
17. `project_members(project_id, user_id, role)` if collaboration is actually in scope; otherwise defer.
18. `sessions(id, project_id, title, created_at, ...)`, `messages(id, session_id, role, content, created_at, ...)`.
19. `search_runs(id, project_id, query_text, parsed_features_jsonb, filters_jsonb, search_config_jsonb, corpus_snapshot_id, status, error, created_at, completed_at, ...)`.
20. `search_candidates(id, search_run_id, document_id, lexical_rank, vector_rank, fusion_score, rerank_score, final_rank, explanation_jsonb, ...)`.
21. `feature_matches(id, search_run_id, document_id, feature_key, verdict, rationale, model_version, ...)`.
22. `evidence_spans(id, feature_match_id, chunk_id, start_offset, end_offset, exact_quote, verification_status, ...)`.
23. `saved_patents(project_id, document_id, note, created_at, ...)`.
24. `reports(id, project_id, search_run_id, object_key, status, created_at, ...)`.
25. `corpus_snapshots(id, ingestion_cutoff, index_version, embedding_model_id, created_at, ...)`.

**Constraints and indexes:** FK/unique/check constraints; indexes on document number, application number, publication date, IPC, project owner, search run status; GIN on selected JSONB where justified; ANN index for pgvector after empirical tests. Query plans must be measured using `EXPLAIN (ANALYZE, BUFFERS)` on representative data.

**Privacy:** Private invention ideas, queries, chats, and reports are user-scoped; enforce authorization in every API query, not only in the UI. Use minimal retention and a deletion workflow.

## 6. RAG and retrieval contract

### 6.1 Chunking
- Index title, abstract, description sections, claims separately with type/position metadata.
- Preserve each claim and its dependencies; if long, split into child chunks but retain full-claim reconstruction and source offsets.
- Store both normalized search text and exact source text; evidence quotes must use exact original text.
- Never join content from different document versions into one evidence span.

### 6.2 Query understanding
- Extract structured technical features: `feature_id`, `description_zh`, `keywords_zh`, `keywords_en`, `must_have`, `confidence`, `ipc_candidates` (only candidate classifications).
- Show features to user for review/edit before search; maintain original query.
- Expand with synonyms cautiously; avoid semantic drift. Keep original and expanded queries in run metadata.

### 6.3 Candidate retrieval
- Lexical baseline: exact patent numbers, metadata filters, Chinese tokenization, BM25 or documented equivalent. **Do not claim default PostgreSQL `to_tsvector('simple', ...)` equals Chinese BM25.**
- Semantic: embedding model with evaluated Traditional Chinese support; pgvector cosine/inner-product consistent with normalization and model docs.
- Merge via reciprocal rank fusion (RRF): `sum(1 / (k + rank))`, initial `k=60` as tunable hypothesis, not a truth.
- Deduplicate at document level; optionally group related applications/families with verified identifiers.
- Rerank top candidates with a cross-encoder or model adapter; store raw scores and model metadata.
- Initial tuning suggestions: lexical top 100, vector top 100, rerank top 50, feature-compare top 10, display top 20. Benchmark and adjust.

### 6.4 Feature matching and citation verification
- Verdict enum: `supported`, `partially_supported`, `not_found_in_checked_content`, `uncertain`.
- Every supported/partially supported judgment must include verifiable evidence (document ID, version, section/claim number, exact quote, offsets/locator).
- Verify source text substring or canonical offset after normalization; reject invented quotations and invalid document IDs.
- `not_found_in_checked_content` is NOT a claim of absence in the patent universe.
- Relevance score is NOT a probability of infringement or patentability.
- If insufficient evidence, show uncertainty and the inspected scope.

### 6.5 Model adapters
- Interfaces: `EmbeddingProvider`, `QueryAnalyzer`, `Reranker`, `FeatureMatcher`, `ReportWriter`.
- Provider and model versions configurable via environment; no provider-specific model IDs embedded in business logic.
- Deterministic fixture/mocked adapters for tests; capture token use, latency, errors and per-search estimated cost.
- Add request budgets, timeouts, retries with backoff, cancellation, and rate limiting.
- LLM/agent never executes arbitrary SQL; only allowlisted typed tools.

## 7. API contract (`/api/v1`)

Use Pydantic schemas and FastAPI-generated OpenAPI. JSON responses should have stable IDs, timestamps, pagination and machine-readable error codes. Validate authorization server-side. Async operations return HTTP 202 and a task/run ID.

| Method | Route | Purpose |
|---|---|---|
| POST | `/auth/register` | register (defer if using provider) |
| POST | `/auth/login` | login |
| GET | `/me` | current user |
| POST/GET | `/projects` | create/list projects |
| GET/PATCH/DELETE | `/projects/{project_id}` | project CRUD |
| POST | `/queries/analyze` | structured technical feature extraction |
| POST | `/search-runs` | start async search |
| GET | `/search-runs/{run_id}` | status, progress, configuration |
| GET | `/search-runs/{run_id}/results` | paginated results, filters, scores |
| POST | `/search-runs/{run_id}/cancel` | best-effort cancellation |
| GET | `/patents/{document_id}` | document metadata, provenance |
| GET | `/patents/{document_id}/claims` | ordered claims and dependencies |
| GET | `/patents/{document_id}/assets` | source assets and authorized links |
| POST | `/comparisons` | create comparison task |
| GET | `/comparisons/{comparison_id}` | feature/evidence matrix |
| POST/GET | `/sessions` | session create/list |
| POST/GET | `/sessions/{session_id}/messages` | session messages |
| POST | `/reports` | create report task |
| GET | `/reports/{report_id}` | status and secure download URL |
| GET | `/health` | liveness |
| GET | `/ready` | readiness (DB + critical dependencies) |

**Example search request (illustrative):**
```json
{
  "project_id": "<uuid>",
  "query": "利用影像辨識植物病害並自動控制灌溉",
  "features": [{"feature_id": "f1", "description_zh": "辨識植物病害", "must_have": true}],
  "filters": {"jurisdictions": ["TW"], "published_from": "2015-01-01"},
  "options": {"mode": "hybrid", "top_k": 20, "rerank": true}
}
```

**Example accepted response:**
```json
{"search_run_id": "<uuid>", "status": "queued", "status_url": "/api/v1/search-runs/<uuid>"}
```

**Example result item fields:** `document_id`, `publication_no`, `title`, `publication_date`, `rank`, `lexical_rank`, `vector_rank`, `fusion_score`, `rerank_score`, `matched_features[]`, `evidence[]`, `source_url`, `corpus_snapshot_id`. Never present raw model scores as calibrated percentages.

**Error contract:** `{"error":{"code":"DATA_SOURCE_UNAVAILABLE","message":"...","request_id":"..."}}`; distinguish validation 422, auth 401/403, not found 404, rate limit 429, unavailable 503.

## 8. Frontend functional spec

**Navigation:** Dashboard, AI Search, Results, Patent Detail, Comparison, Research Workspace, Reports, Settings; Admin ingestion dashboard restricted to authorized users.

### AI Search (P0)
- Large Traditional Chinese free-text field; optional patent number input; filters (publication date, document kind, IPC, applicant where available).
- AI feature extraction with editable feature chips; mark must-have/optional; show query variants.
- Explain coverage and that search is non-exhaustive.
- Submit async search; show progress, errors, cancellation and retry.

### Results (P0)
- List of ranked **real indexed** documents; number, title, applicant, dates, abstract excerpt, relevant features, evidence preview.
- Facets, pagination, sorting, saved items, explain why retrieved.
- Group versions/families only when relationships are verified; distinguish publication vs grant.
- Clearly show data freshness and `no results` vs `source unavailable` vs `search failed`.

### Patent detail (P0)
- Metadata, abstract, claims tree, IPC, original source URL, source/version provenance.
- Original-text pane with evidence highlighting and navigable claim/paragraph references; PDF preview only when available and permitted.

### Comparison (P0)
- Feature-by-document matrix, four verdicts, expandable exact evidence, editable human notes.
- Explicit caveat that it is research assistance, not legal determination.

### Workspace (P1)
- Projects, sessions, saved patents, saved runs, notes, reproducibility metadata.

### Reports (P1)
- Export with query, filters, corpus date, methods, ranked patents, feature/evidence table, citations, limitations and timestamp.

**UX:** responsive desktop-first, accessible keyboard navigation, loading/empty/error states, WCAG-minded contrast and labels; no fake confidence percentages or fabricated results. Use Traditional Chinese UI text.

## 9. Security, privacy, legal safeguards

- User inventions may be confidential. Treat prompts, files and research notes as private; document model-provider data handling and retention.
- Validate upload MIME/size, sanitize filenames, scan if infrastructure available; limit decompression and XML entity expansion (XXE/billion laughs).
- Never render untrusted patent HTML unsanitized. Guard prompt injection from patent content; treat it as evidence, not instructions.
- Authentication, object-level authorization, rate limits, audit logs, secure signed asset URLs, CSRF/CORS policy as appropriate.
- Use least-privilege DB roles; parameterized queries/ORM; TLS in deployment.
- Allow data deletion/export; prevent cross-tenant retrieval in vector/keyword search.
- Cite official patent source and distinguish patent publication from legal status. Verify source licensing and robots/terms before bulk retrieval.
- No automatic definitive legal opinion, infringement determination, or guarantee of patentability.

## 10. Repository layout

```text
patentscope-ai/
├── AGENTS.md                 # this canonical contract
├── CLAUDE.md                 # short pointer to AGENTS.md
├── README.md
├── .env.example
├── docker-compose.yml
├── apps/
│   └── web/                  # React + TS + Vite
├── services/
│   ├── api/                  # FastAPI routes/schemas/auth
│   ├── ingestion/            # TIPO connector/parser/workers
│   └── retrieval/            # query, lexical, vector, fusion, rerank, evidence
├── database/
│   ├── migrations/           # Alembic
│   └── seeds/                # clearly labeled DEMO fixtures
├── evaluation/
│   ├── datasets/             # labeled relevance judgments
│   ├── baselines/
│   └── metrics/
├── tests/
├── docs/
│   ├── DATA_SOURCES.md
│   ├── PROGRESS.md
│   ├── HANDOFF.md
│   ├── API.md
│   └── adr/
└── scripts/
```

Keep package/import paths coherent; prefer one working monorepo over prematurely splitting microservices. Define `make`/scripts commands for bootstrap, migrate, seed-demo, test, lint, typecheck and run.

## 11. Acceptance criteria / definition of done

A milestone is **done only if**:
1. Code is present and reviewable, with docs/config examples.
2. DB migration succeeds from clean environment; existing migrations do not destroy data.
3. Tests relevant to change are run and reported with command + result.
4. Frontend displays genuine backend states (or prominently marked demo fixture in local demo mode).
5. API schema is documented and errors handled.
6. Data provenance and citation links are correct where applicable.
7. No secrets, silent exceptions, fabricated records, or fake test claims.
8. `docs/PROGRESS.md` and `docs/HANDOFF.md` updated.

**Search evaluation:** implement lexical-only, vector-only and hybrid+rerank baselines; report Precision@10, Recall@10 relative to labeled pool, nDCG@10, MRR, citation accuracy, P50/P95 latency, cost/search. Relevance labels should be human-reviewed; don't fabricate a performance improvement. Start with a modest verified dataset and record corpus coverage.

## 12. Implementation roadmap (execute sequentially)

### M0 — Repository and contracts
- Initialize repo, `AGENTS.md`, `CLAUDE.md`, README, `.env.example`, Compose, lint/test CI, progress/handoff docs.
- Set up FastAPI health/ready endpoints, React skeleton, PostgreSQL + pgvector connection.
- **Done when:** clean checkout can boot local stack; smoke tests pass.

### M1 — Verified TIPO ingestion PoC
- Verify one official Taiwan patent source; document terms, sample files and field mapping.
- Import 100–500 **real** documents if access permits, else use clearly labeled fixtures and mark real ingestion blocked.
- Create application/document/claims/sections tables and provenance, parser tests, idempotent batch checkpoints.
- **Done when:** a real record can be traced from source artifact to DB and back; no version conflation.

### M2 — Baseline search
- Build patent metadata/detail APIs, exact patent-number search and lexical baseline with Chinese tokenization evaluation.
- Implement pgvector indexing, model adapter, vector retrieval; record embedding metadata.
- **Done when:** real indexed records can be queried through API; tests and explain plans recorded.

### M3 — Hybrid and explainability
- Query feature extraction with editable output; RRF fusion, dedup, rerank, source-grounded evidence spans.
- Implement citation verifier and search-run tracking.
- **Done when:** one query returns traceable ranked results and failed verification is visibly flagged.

### M4 — Research UI
- Search page, results filters, patent detail, comparison matrix, project/save history.
- **Done when:** end-to-end browser workflow works against backend, with empty/error/loading states.

### M5 — Evaluation, privacy, report
- Relevance test set, baseline comparison, quality/latency metrics, report export, access control tests, documentation.
- **Done when:** reproducible benchmark and demo can be run from README.

### M6 — Optional future extensions (NOT MVP)
- Electron desktop wrapper; global patent connectors; richer multimodal parsing; agent orchestration; C#/ASP.NET module for skills development.

**Time estimates** (e.g., 10 weeks) are planning hypotheses, not commitments; prefer measured checkpoints.

## 13. Suggested commands (implement them; don't claim they exist yet)

```bash
# example target workflow after M0
cp .env.example .env
docker compose up -d --build
# API docs: http://localhost:8000/docs
# Web: http://localhost:5173
pytest -q
# front-end commands depend on package manager selected in M0
```

Create deterministic scripts for fixture seeding, data ingestion, embedding generation and evaluation. Use safe defaults (no live paid API calls during test suite).

## 14. Collaboration rules: Codex <-> Claude Code

- **One canonical instruction file:** `AGENTS.md`. `CLAUDE.md` must instruct Claude Code to read `AGENTS.md` first; do not duplicate architecture in two competing documents.
- **Ownership:** Before edits, record intended modules/files in `docs/HANDOFF.md`. If another agent has uncommitted changes in those files, do not overwrite them; request coordination.
- **Small commits:** One feature or migration per coherent commit, descriptive message, no generated secrets or bulk patent corpus committed.
- **Schema first:** If API/DB contract changes, update migrations, Pydantic schemas, frontend types and docs in the same slice.
- **Reproduce before fixing:** For bugs, add failing test where feasible, fix, rerun; log the cause and commands.
- **Do not hide blockers:** Missing source access, model credentials, license uncertainty, or unrun tests must be explicit.
- **No silent scope creep:** New stack dependencies, database swaps, major architecture changes require an ADR and human approval.
- **Cross-agent review:** Incoming agent first checks last handoff, git diff, tests and migration head. Never assume prior agent's statements are correct without verification.

## 15. Mandatory handoff template (`docs/HANDOFF.md`)

At the end of each session, replace/update with:

```markdown
# Agent Handoff
- Date/time (timezone):
- Agent: Codex | Claude Code | human
- Branch / commit SHA:
- Current milestone and status: NOT_STARTED | IN_PROGRESS | BLOCKED | DONE
- Goal of this session:
- Files changed (with purpose):
- Database migrations added/applied:
- API/Schema changes:
- Commands actually run and results:
- Tests NOT run and reason:
- Data sources checked (exact URL/date) and license/access notes:
- Known bugs / risks / blockers:
- Decisions made (ADR links):
- Uncommitted changes / file ownership warnings:
- Next 1–3 concrete actions:
- Exact reproduction steps:
```

`docs/PROGRESS.md` should maintain a milestone checklist with dated evidence and links to tests/commits; don't mark DONE without §11 criteria.

## 16. First instruction to any new coding agent

> Read `AGENTS.md` fully and inspect the repository. If no code exists, implement **M0 only**: minimal running React + FastAPI + PostgreSQL/pgvector development stack, health endpoints, Alembic setup, smoke tests, README, `.env.example`, and `docs/PROGRESS.md` / `docs/HANDOFF.md`. Run tests and record actual results. Do not claim live TIPO ingestion or AI search works yet. Then propose the exact M1 plan and blockers.

## 17. Key risks and open questions

- Official TIPO source dataset field definitions, refresh cadence, access terms, and bulk-download limits require live verification.
- Taiwanese Traditional Chinese patent retrieval quality requires a tested tokenizer/BM25 strategy; pgvector alone is not enough.
- Patent publication and granted claim versions must remain separate.
- Patent families and legal status require verified authoritative metadata; do not infer from text similarity.
- Embedding provider/model/dimensions, monthly budget and deployment environment not yet selected.
- Private invention confidentiality and model-provider retention requirements need a product decision before real user rollout.
- Human-reviewed relevance labels are needed to validate search quality.

---

**Guiding principle:** Deliver a trustworthy, reproducible Taiwan-first patent search MVP before adding complex agents, more databases, or desktop packaging.
