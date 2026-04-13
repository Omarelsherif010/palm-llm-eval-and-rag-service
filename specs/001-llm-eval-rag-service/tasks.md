# Tasks: LLM Eval Harness & RAG Service

**Input**: Design documents from `/specs/001-llm-eval-rag-service/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Included — plan.md defines test files in project structure and constitution requires testability.

**Organization**: Tasks grouped by user story. US1 (eval harness) and US2 (RAG service) are fully independent and can be implemented in parallel.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup

**Purpose**: Project initialization and shared infrastructure

- [x] T001 Create project directory structure per plan.md: `eval_harness/`, `eval_harness/test_sets/`, `rag_service/`, `rag_service/corpus/`, `tests/`
- [x] T002 [P] Create `requirements.txt` with pinned dependencies: fastapi, uvicorn, pydantic, scikit-learn, numpy, httpx, pytest, python-dotenv
- [x] T003 [P] Create `.env.example` with all environment variables: LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, RAG_DEFAULT_K, RAG_SIMILARITY_METRIC, RAG_DENYLIST_PATH
- [x] T004 [P] Create `.gitignore` excluding .env, __pycache__/, .venv/, *.pyc, results.json

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared configuration modules that both deliverables depend on

- [x] T005 [P] Create `eval_harness/__init__.py` and `eval_harness/config.py` — load LLM_API_KEY, LLM_BASE_URL (default `https://api.openai.com/v1`), LLM_MODEL (default `gpt-3.5-turbo`) from environment using python-dotenv
- [x] T006 [P] Create `rag_service/__init__.py` and `rag_service/config.py` — load LLM env vars plus RAG_DEFAULT_K (default 5), RAG_SIMILARITY_METRIC (default `cosine`), RAG_DENYLIST_PATH (default `rag_service/denylist.txt`) from environment

**Checkpoint**: Foundation ready — user story implementation can begin. US1 and US2 can proceed in parallel.

---

## Phase 3: User Story 1 — Run Prompt Consistency Evaluation (Priority: P1)

**Goal**: Engineer can run `python -m eval_harness.runner` and get a scored consistency report with per-case results and aggregate metrics.

**Independent Test**: Run `python -m eval_harness.runner --test-set eval_harness/test_sets/default.json --format both` and verify JSON output matches contract in `contracts/eval-cli.md`. Verify invariance group flags divergent answers; perturbation group quantifies drift.

### Implementation for User Story 1

- [x] T007 [P] [US1] Create Pydantic models in `eval_harness/models.py`: TestCase, TestGroup, TestSet (with metadata), EvalResult, GroupResult, EvalReport — per data-model.md entity definitions
- [x] T008 [P] [US1] Create scoring functions in `eval_harness/metrics.py`: `exact_match(expected, actual) -> float`, `regex_match(pattern, actual) -> float`, `semantic_similarity(expected, actual) -> float` using TF-IDF cosine from scikit-learn (per research.md R1)
- [x] T009 [P] [US1] Create hand-rolled test set in `eval_harness/test_sets/default.json` — 10 cases (mid-range of spec's 8–12): 5 synthetic (template substitution, numeric variation, format permutation) + 5 real-world edge cases (redacted). Must include invariance group INV-001 (3 paraphrase cases, group_type=invariance) and perturbation group PRT-001 (2 reordered/distractor cases, group_type=perturbation). Follow JSON schema from contracts/eval-cli.md
- [x] T010 [US1] Create main CLI runner in `eval_harness/runner.py`: argparse for --test-set, --output, --format, --help; load test set JSON; iterate cases calling LLM via httpx to OpenAI-compatible chat completions endpoint (per research.md R2); score each response; compute group consistency (invariance: all-identical check + pairwise similarity; perturbation: drift magnitude as max pairwise distance); aggregate into EvalReport; output per contract format
- [x] T011 [US1] Add human-readable output formatter to `eval_harness/runner.py` — match the human output format specified in contracts/eval-cli.md with group-level and aggregate sections; implement exit codes 0/1/2

### Tests for User Story 1

- [x] T012 [P] [US1] Create unit tests in `tests/test_eval_metrics.py`: test exact_match (identical strings → 1.0, different → 0.0), regex_match (matching pattern → 1.0, non-matching → 0.0), semantic_similarity (identical texts → 1.0, unrelated → low score, paraphrases → high score)

**Checkpoint**: User Story 1 is fully functional. Run `python -m eval_harness.runner` end-to-end.

---

## Phase 4: User Story 2 — Query the RAG Answering Service (Priority: P2)

**Goal**: Start `uvicorn rag_service.main:app` and successfully query `POST /answer` with retrieval, guardrail enforcement, and monitoring.

**Independent Test**: Start service, send valid query via curl → get snippets + answer. Send denied-topic query → get 403. Compare cosine vs dot_product on same query → verify different snippet orderings. Check structured JSON logs for latency and hit-rate fields.

### Implementation for User Story 2

- [x] T013 [P] [US2] Create Pydantic models in `rag_service/models.py`: AnswerRequest (query, optional k, optional similarity_metric), RetrievedSnippet (id, title, content, score), AnswerResponse (query, snippets, answer, similarity_metric, latency_ms, retrieval_ms), HealthResponse, GuardrailError — per data-model.md and contracts/rag-api.md
- [x] T014 [P] [US2] Create text corpus in `rag_service/corpus/snippets.json` — 12 hand-written snippets (mid-range of spec's 10–15) covering AI/ML topics (RAG, embeddings, transformers, fine-tuning, prompt engineering, etc.). Each snippet: id, title, content (2-5 sentences), topic. Ensure topic diversity for meaningful retrieval testing
- [x] T015 [P] [US2] Create topic denylist file at `rag_service/denylist.txt` — one prohibited topic per line (e.g., hacking, illegal activities, personal data extraction, jailbreaking). Include 5-8 terms
- [x] T016 [US2] Create guardrail module in `rag_service/guardrails.py`: load denylist from RAG_DENYLIST_PATH at startup; `check_query(query: str) -> GuardrailResult` does case-insensitive substring matching against all denylist terms; fail closed if denylist file cannot be loaded (raise on init, not per-request). Per research.md R3
- [x] T017 [US2] Create retriever module in `rag_service/retriever.py`: load corpus from JSON at startup; build TF-IDF matrix using scikit-learn TfidfVectorizer; `search(query, k, metric) -> list[RetrievedSnippet]` computes similarity (cosine via sklearn cosine_similarity, dot-product via numpy dot on raw TF-IDF vectors); return top-k sorted by score. Per research.md R1 and R4
- [x] T018 [US2] Create monitoring module in `rag_service/monitoring.py`: configure Python logging with JSON formatter; `log_request(query, latency_ms, retrieval_ms, snippet_scores, answer_length)` emits structured log line; compute hit_rate as fraction of snippets above threshold (default 0.1). Per research.md R5
- [x] T019 [US2] Create FastAPI application in `rag_service/main.py`: app lifespan loads corpus into retriever and denylist into guardrail at startup; `POST /answer` handler: validate request → check guardrail (return 403 if blocked) → retrieve snippets → call LLM via httpx with retrieved context as system message → return AnswerResponse; `GET /health` returns corpus and guardrail status. Per contracts/rag-api.md response formats
- [x] T020 [US2] Create index comparison script or section in `rag_service/compare_indexes.py` — run 5-8 test queries against both cosine and dot_product configs on the same corpus; output side-by-side results table showing per-query top-3 snippets and scores for each metric; write justification for default choice (cosine preferred because it normalizes by document length). Per research.md R4

### Tests for User Story 2

- [x] T021 [P] [US2] Create unit tests in `tests/test_retriever.py`: test search returns correct number of results, test cosine vs dot_product return different orderings, test empty query handling, test k > corpus size gracefully caps
- [x] T022 [P] [US2] Create unit tests in `tests/test_guardrails.py`: test denied topic is blocked, test clean query is allowed, test case-insensitive matching, test fail-closed when denylist path is invalid
- [x] T023 [US2] Create integration tests in `tests/test_rag_api.py`: test POST /answer returns 200 with valid query (check response schema), test 403 on denied topic, test 400 on empty query, test GET /health returns correct status

**Checkpoint**: User Story 2 is fully functional. Start server and run all curl commands from quickstart.md.

---

## Phase 5: User Story 3 — Review Decisions and Trade-offs (Priority: P3)

**Goal**: All written documentation is complete and covers every required decision point for reviewer assessment.

**Independent Test**: Read each document and verify it addresses the specific items listed in spec.md acceptance scenarios for US3.

### Implementation for User Story 3

- [x] T024 [P] [US3] Write ship-first-vs-later note in `docs/ship_first_vs_later.md` — identify at least 2 ship-first items (the harness itself with TF-IDF scoring; basic exact/regex metrics) and at least 2 ship-later items (neural embeddings via sentence-transformers; Prometheus /metrics endpoint; LLM-based content classifier guardrail; k-value grid search). Include rationale for each
- [x] T025 [US3] Update `README.md` with: project overview, setup instructions (venv, pip install, .env config), eval harness usage with examples, RAG service usage with curl examples, test running instructions, design decisions summary (TF-IDF choice, guardrail rationale, index comparison, monitoring approach), link to docs/

**Checkpoint**: All written deliverables ready for submission.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation and final quality pass

- [x] T026 [P] Run full eval harness end-to-end against live LLM and verify output matches contracts/eval-cli.md JSON and human formats
- [x] T027 [P] Run RAG service, execute all curl commands from quickstart.md, and verify responses match contracts/rag-api.md schemas
- [x] T028 [P] Run `pytest tests/ -v` and verify all tests pass
- [x] T029 Verify .env.example documents all required variables and README setup instructions are accurate and complete

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (directory structure exists)
- **User Story 1 (Phase 3)**: Depends on Phase 2 (config modules). No dependency on US2
- **User Story 2 (Phase 4)**: Depends on Phase 2 (config modules). No dependency on US1
- **User Story 3 (Phase 5)**: Depends on Phase 3 and Phase 4 (code deliverables complete before writing about them)
- **Polish (Phase 6)**: Depends on all previous phases

### User Story Dependencies

- **User Story 1 (P1)**: After Phase 2 — fully independent of US2
- **User Story 2 (P2)**: After Phase 2 — fully independent of US1
- **User Story 3 (P3)**: After US1 and US2 — wraps documentation around completed code

### Within Each User Story

- Models before services/retriever (T007 before T010; T013 before T017/T019)
- Corpus and denylist before retriever and guardrail (T014/T015 before T016/T017)
- Retriever and guardrail before FastAPI app (T016/T017 before T019)
- Core implementation before tests
- Tests marked [P] can run in parallel with each other

### Parallel Opportunities

```bash
# Phase 1 — all parallel:
T002, T003, T004

# Phase 2 — parallel:
T005, T006

# Phase 3 (US1) — models, metrics, test set in parallel:
T007, T008, T009
# Then sequential: T010 → T011 → T012

# Phase 4 (US2) — models, corpus, denylist in parallel:
T013, T014, T015
# Then: T016 + T017 (parallel) → T018 → T019 → T020
# Tests parallel: T021, T022, then T023

# Phase 5 (US3) — parallel:
T024, T025

# Phase 6 — mostly parallel:
T026, T027, T028 (parallel) → T029
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (eval harness)
4. **STOP and VALIDATE**: Run eval harness end-to-end
5. Demonstrates core evaluation thinking — sufficient for partial submission

### Incremental Delivery

1. Setup + Foundational → project runnable
2. User Story 1 → eval harness works standalone → validate
3. User Story 2 → RAG service works standalone → validate
4. User Story 3 → documentation complete → validate
5. Polish → everything verified end-to-end → ready to submit

### Parallel Strategy (fastest path)

Since US1 and US2 share no code:
1. Complete Setup + Foundational together
2. Work US1 and US2 in parallel (separate file trees)
3. US3 after both complete
4. Polish pass
