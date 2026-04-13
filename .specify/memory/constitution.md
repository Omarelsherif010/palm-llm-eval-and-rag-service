<!--
Sync Impact Report
===================
Version change: 0.0.0 → 1.0.0
Bump rationale: MAJOR — initial constitution ratification, all principles new.

Modified principles: N/A (first version)

Added sections:
  - Core Principles (5 principles)
  - Technology Stack & Constraints
  - Development & Delivery Workflow
  - Governance

Removed sections: N/A (first version)

Templates requiring updates:
  - .specify/templates/plan-template.md — ✅ no updates needed
    (Constitution Check section is dynamically filled from this file)
  - .specify/templates/spec-template.md — ✅ no updates needed
    (User stories & requirements structure aligns with principles)
  - .specify/templates/tasks-template.md — ✅ no updates needed
    (Phase structure accommodates evaluation and observability tasks)

Follow-up TODOs: none
-->

# Palm LLM Eval & RAG Service Constitution

## Core Principles

### I. Evaluation-Driven Development

Every LLM interaction MUST be testable and scored for consistency
before it is considered production-ready.

- Test sets MUST contain both synthetic and real-world edge cases.
- Each test set MUST include at least one invariance test
  (paraphrases, typos, noise that MUST NOT change the answer)
  and one perturbation test (reordering, distractors that MAY
  change the answer).
- Scoring MUST use explicit, reproducible metrics
  (exact match, regex, or semantic similarity). No subjective
  "looks good" assessments.
- Evaluation scripts MUST be runnable from the command line
  with a single command and MUST produce machine-readable output.

### II. Retrieval Accuracy

The RAG pipeline MUST prioritize retrieval precision and expose
configuration knobs that are empirically compared.

- The text corpus MUST be curated, versioned, and small enough
  to reason about manually (10–15 snippets for the prototype).
- At least two index configurations (e.g., cosine vs dot-product,
  or k=3 vs k=5) MUST be compared with documented justification
  for the chosen default.
- Retrieved context MUST be returned alongside the generated
  answer so reviewers can inspect grounding.

### III. Guardrails by Default

Safety and cost controls MUST be embedded in every endpoint
from day one — not bolted on after incidents.

- At least one guardrail (denylist, budget cap, token limit,
  or content filter) MUST be active on every user-facing
  endpoint.
- Guardrail rationale MUST be documented: what attack or
  failure mode it mitigates and why it is practical at this
  scale.
- Guardrails MUST fail closed: if the check cannot execute,
  the request MUST be rejected rather than allowed through.

### IV. Production-Minded Prototyping

Code MUST be scrappy but structured so it can migrate to
production without a rewrite.

- FastAPI endpoints MUST follow standard request/response
  schemas (Pydantic models, not raw dicts).
- Configuration (API keys, model names, thresholds) MUST
  live in environment variables or config files, never
  hardcoded.
- Dependencies MUST be pinned in a requirements file.
- The prototype MUST start with a single `uvicorn` or
  `python -m` command documented in the README.

### V. Observability & Monitoring

Every component MUST expose lightweight monitoring metrics
so degradation is detected before users report it.

- At minimum, track request latency (p50, p95) and retrieval
  hit-rate per query.
- Suggest at least one drift-detection metric (e.g., embedding
  distribution shift, answer-length variance over time).
- Metrics MUST be collectible via structured logs or a
  `/metrics` endpoint — no proprietary dashboards required
  for the prototype.

## Technology Stack & Constraints

- **Language**: Python 3.11+
- **Web Framework**: FastAPI
- **LLM Provider**: Anthropic Claude API (or OpenAI-compatible
  for evaluation harness — configurable via environment variable)
- **Embeddings / Vector Search**: lightweight in-process library
  (e.g., scikit-learn, numpy, or FAISS). No external vector DB
  required for the prototype.
- **Testing**: pytest for unit/integration tests; custom eval
  harness script for LLM consistency scoring.
- **Dependency Management**: `requirements.txt` with pinned
  versions.
- **Target Platform**: Local development / single-server
  deployment. Containerization is a nice-to-have, not required.

## Development & Delivery Workflow

- **Ship incrementally**: Question 1 (eval harness) is
  deliverable independently of Question 2 (RAG service).
  Each MUST work standalone.
- **README-first**: Every deliverable MUST have a README
  section explaining how to run it, what it does, and what
  decisions were made.
- **Git discipline**: Atomic commits with descriptive messages.
  One logical change per commit.
- **No secrets in repo**: API keys MUST come from environment
  variables. `.env` files MUST be git-ignored.
- **Code review mindset**: Write code as if a reviewer will
  read it in 5 minutes. Prefer clarity over cleverness.

## Governance

This constitution governs all development within the
palm-llm-eval-and-rag-service repository.

- **Precedence**: This constitution supersedes ad-hoc practices.
  When in doubt, follow the principles above.
- **Amendments**: Any change to a principle MUST be documented
  with rationale, versioned per semantic versioning (MAJOR for
  principle removal/redefinition, MINOR for additions, PATCH
  for clarifications), and reflected in the Sync Impact Report.
- **Compliance**: All pull requests and code reviews MUST verify
  alignment with active principles. Violations MUST be justified
  in the PR description if intentional.
- **Complexity justification**: Adding dependencies, abstractions,
  or infrastructure beyond what a principle requires MUST be
  justified against the "Production-Minded Prototyping" principle.

**Version**: 1.0.0 | **Ratified**: 2026-04-13 | **Last Amended**: 2026-04-13
