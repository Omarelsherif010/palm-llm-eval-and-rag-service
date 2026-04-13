# Implementation Plan: LLM Eval Harness & RAG Service

**Branch**: `001-llm-eval-rag-service` | **Date**: 2026-04-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-llm-eval-rag-service/spec.md`

## Summary

Build two independent deliverables for the Palm Outsourcing Senior AI Engineer
trial task: (1) a prompt consistency evaluation harness with a hand-rolled test
set of 8–12 cases, invariance/perturbation tests, and multi-metric scoring; and
(2) a FastAPI RAG service backed by a 10–15 snippet corpus with a topic denylist
guardrail, cosine-vs-dot-product index comparison, and structured-log monitoring.
Both components use TF-IDF vectorization with scikit-learn to keep dependencies
minimal and avoid external model downloads.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, uvicorn, pydantic, scikit-learn, numpy, httpx
**Storage**: In-memory (TF-IDF matrices via scikit-learn, JSON files for test sets and corpus)
**Testing**: pytest for unit tests; custom eval harness script for LLM consistency scoring
**Target Platform**: macOS / Linux local development
**Project Type**: CLI tool (eval harness) + web service (RAG endpoint)
**Performance Goals**: Eval harness completes full test set in <5 min; RAG endpoint p95 <2s (excluding LLM generation time)
**Constraints**: No external vector DB, no GPU, no model downloads >100MB, single-process
**Scale/Scope**: 8–12 test cases, 10–15 corpus snippets, single-user prototype

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Evaluation-Driven Development | Test set has synthetic + real-world cases, invariance + perturbation groups, reproducible metrics, CLI-runnable with machine-readable output | PASS |
| II. Retrieval Accuracy | Corpus versioned in repo as JSON, two index configs compared (cosine vs dot-product), retrieved snippets returned alongside answer | PASS |
| III. Guardrails by Default | Topic denylist guardrail active on `POST /answer`, rationale documented, fails closed on denylist load failure | PASS |
| IV. Production-Minded Prototyping | Pydantic request/response models, config via env vars + `.env.example`, deps pinned in `requirements.txt`, single `uvicorn` command | PASS |
| V. Observability & Monitoring | Structured JSON logs with per-request latency and retrieval score; drift metric (answer-length variance) sketched | PASS |

All gates pass. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/001-llm-eval-rag-service/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── rag-api.md
│   └── eval-cli.md
└── tasks.md
```

### Source Code (repository root)

```text
eval_harness/
├── __init__.py
├── runner.py            # Main CLI entry point: loads test set, calls LLM, scores
├── metrics.py           # Scoring: exact_match, regex_match, semantic_similarity
├── models.py            # Pydantic models: TestCase, TestGroup, EvalResult
├── config.py            # Env-var loading (LLM API key, base URL, model name)
└── test_sets/
    └── default.json     # 8–12 hand-rolled test cases

rag_service/
├── __init__.py
├── main.py              # FastAPI app, POST /answer endpoint, app lifespan
├── retriever.py         # TF-IDF vectorizer + similarity search
├── guardrails.py        # Topic denylist: load, check, fail-closed
├── monitoring.py        # Structured logging: latency, hit-rate, drift
├── models.py            # Pydantic: AnswerRequest, AnswerResponse, Snippet
├── config.py            # Env-var loading (LLM key, k, similarity metric)
├── compare_indexes.py   # Cosine vs dot-product comparison script
├── denylist.txt         # Prohibited topic terms (one per line)
└── corpus/
    └── snippets.json    # 10–15 hand-written text snippets

tests/
├── test_eval_metrics.py # Unit tests for scoring functions
├── test_retriever.py    # Unit tests for retrieval logic
├── test_guardrails.py   # Unit tests for denylist guardrail
└── test_rag_api.py      # Integration tests for POST /answer

docs/
└── ship_first_vs_later.md  # Ship-first vs ship-later roadmap note

requirements.txt
.env.example
.gitignore
README.md
```

**Structure Decision**: Single project with two top-level packages (`eval_harness/`
and `rag_service/`) reflecting the two independent deliverables. No shared runtime
code between them — only shared dev dependencies. The `tests/` directory covers
both packages with clear file naming conventions.

## Complexity Tracking

No constitution violations. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
