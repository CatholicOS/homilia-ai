# Project To-Do List — ParishChat (MVP first, then scale)

Below is a detailed, prioritized, step-by-step to-do list to complete the whole project. It’s organized into phases: **MVP (single-tenant, no Postgres/Redis)**, then **Core product (users, multi-tenant)**, then **Scale / polish / ops**. Each item includes concrete tasks, acceptance criteria, dependencies, risks, and suggested owners.

---

# Phase A — Project Initiation & Planning
**Goal:** Agree scope, repo layout, infra decisions, secrets handling, and onboarding for contributors.

- Create GitHub repo(s) and initial branches (`main`, `dev`).
- Define environment variable strategy and secrets storage.
- Choose hosting targets for MVP (e.g., Render, Vercel + EC2, or single VPS).
- Create high-level architecture diagram and ERD.
- Set up issue tracker + milestone structure in GitHub.

---

# Phase B — MVP: Single-tenant demo (no Postgres, no Redis)
**Goal:** Deliver an end-to-end demo: upload → extract → embed → index → chat.

## B.1 Backend skeleton + infra connectors
- Create FastAPI project scaffold (`app.main`, configs).
- Install/configure SDKs & clients: Strands/OpenAI, boto3 (S3), opensearch-py.
- Create simple file storage (S3 or local folder).

## B.2 OpenSearch index setup
- Create index mapping `parish_docs` (knn_vector field, text, metadata).
- Build `opensearch_utils.py`: create_index, index_chunk, search_knn.

## B.3 Ingestion pipeline (sync)
- Implement `/api/upload` endpoint.
- Implement text extraction & chunk logic.
- Implement embedding generation call (OpenAI).
- Index chunks into OpenSearch.
- Integrate ingestion steps into `/api/upload`.

## B.4 Chat (RAG) endpoint
- Implement `/api/query` endpoint:
  1. Embed question.
  2. Vector search in OpenSearch.
  3. Construct RAG prompt.
  4. Generate answer via LLM.
  5. Return `{ answer, sources }`.
- Add fallback for low-confidence results.

## B.5 Minimal frontend
- React pages:
  - `/upload`: file input → POST `/api/upload`.
  - `/chat`: input → POST `/api/query`, show messages.
  - `/docs`: list uploaded docs via `/api/docs`.

## B.6 QA & demo
- End-to-end test: upload PDF → query → correct answer.
- Deploy demo (Render/Vercel/Fly.io).

---

# Phase C — Core Product: Users, Postgres, Multi-Tenant, Roles
**Goal:** Add persistence, auth, multi-tenancy, and admin features.

## C.1 Add Postgres and basic schema
- Provision Postgres (managed).
- Create schema: `parishes`, `users`, `documents`, `ingest_jobs`, `chat_sessions`, `chat_messages`, `feedback`.
- Implement Alembic migrations and DB connection.

## C.2 Authentication & Authorization
- Implement JWT login/signup.
- Add password hashing, tokens.
- Define roles: `superadmin`, `parish_admin`, `uploader`, `parishioner`.
- Enforce role checks via middleware/dependencies.

## C.3 Multi-tenant enforcement
- Add `parish_id` to all tables.
- Update ingestion & queries to filter by `parish_id`.
- Ensure searches are parish-specific.

## C.4 Admin UI & workflows
- Pages:
  - Parish settings
  - Upload dashboard
  - FAQ management
  - User management

## C.5 Background ingestion (Postgres queue)
- Create `ingest_jobs` table.
- Create background worker loop to process jobs.
- Update job status during processing.

---

# Phase D — Product Polish & Features
**Goal:** Improve UX, prompt design, and admin experience.

- Add feedback capture & reporting.
- Improve RAG prompt for accurate answers.
- Implement streaming responses (SSE/WebSocket).
- Add FAQ & pinned answers injection.
- Create analytics dashboard for admins.

---


# Safety, Legal & Operational Considerations
- Add terms of service and data ownership documentation.
- Implement content moderation and delete/takedown APIs.
- Ensure data deletion and GDPR compliance.

---

# Testing Matrix
- Unit tests for ingestion, embedding, indexing, query.
- Integration tests for end-to-end flow.
- Load tests for performance.
- Acceptance tests for demos.

---

# Acceptance Criteria Summary
**MVP Done:** Upload a PDF → embed → index → query → sourced answer via frontend.

**Core Product Done:** Multi-tenancy, auth, roles, admin UI, background jobs.

**Production Ready:** Scalable workers, monitoring, security, legal compliance.

---

# Risks & Mitigations
- **LLM hallucination:** enforce strict prompts, source citations.
- **Index drift:** implement versioning & soft deletes.
- **Costs:** use small models, cache results.
- **Search quality:** hybrid retrieval (BM25 + vector).
- **Complexity:** start simple, add systems gradually.

---

# Suggested Roles
- **PM:** scope, acceptance, demo coordination.
- **Tech lead:** architecture, backend.
- **Frontend dev:** React UI.
- **DevOps:** deployment, monitoring.
- **QA:** testing and validation.
- **Beta testers:** feedback and domain validation.

---

# Deliverables Checklist
- [ ] Repo + README + CI stub  
- [ ] FastAPI scaffold + health endpoint  
- [ ] S3/local upload helper  
- [ ] OpenSearch index creation script  
- [ ] Ingestion pipeline: extract → chunk → embed → index  
- [ ] `/api/upload`, `/api/query`, `/api/docs`  
- [ ] Minimal React UI  
- [ ] Demo deployment  
- [ ] Postgres schema + migrations  
- [ ] Auth & roles  
- [ ] Admin UI  
- [ ] Background job queue  
- [ ] Feedback & analytics  
- [ ] Monitoring, backups, security hardening  

---

# Summary
- **Phase A:** Setup & planning  
- **Phase B:** MVP (no Postgres/Redis)  
- **Phase C:** Core Product (multi-tenant, auth)  
- **Phase D:** Polish  
- **Phase E:** Scale & Ops  
- **Phase F:** Advanced features  

Each phase builds sequentially — MVP first, then persistence and scaling, then polish and expansion.
