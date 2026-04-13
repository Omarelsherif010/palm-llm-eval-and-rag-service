# Palm LLM Eval & RAG Service

Two independent deliverables for the Palm Outsourcing Senior AI Engineer trial task:

1. **Eval Harness** — measures LLM response consistency across paraphrase, typo, and perturbation variants
2. **RAG Service** — FastAPI endpoint that retrieves relevant text snippets and generates grounded answers

---

## Setup

**Prerequisites**: Python 3.11+, [uv](https://docs.astral.sh/uv/), an OpenAI-compatible API key (OpenAI, Anthropic via proxy, Ollama, etc.)

```bash
# 1. Install dependencies and create venv (uv reads pyproject.toml + uv.lock)
uv sync --dev

# 2. Configure environment
cp .env.example .env
# Edit .env and set LLM_API_KEY (required for LLM calls)
```

---

## Question 1: Eval Harness

Measures LLM response consistency across a hand-rolled test set of 10 cases:
- 5 synthetic (invariance group + perturbation group + standalone)
- 5 real-world edge cases (redacted)

### Run

```bash
# Default: runs default.json, prints human report to stderr + JSON to stdout
uv run python -m eval_harness.runner

# Save JSON results to file
uv run python -m eval_harness.runner --output results.json

# Human-readable report only
uv run python -m eval_harness.runner --format human

# Custom test set
uv run python -m eval_harness.runner --test-set path/to/my_tests.json
```

### Test set design

| Group | Type | Cases | Expected behaviour |
|-------|------|-------|--------------------|
| INV-001 | invariance | SYN-001, 002, 003 | All must answer "Paris" |
| PRT-001 | perturbation | SYN-004, 005 | Ranking may vary — drift measured |
| — | standard | RW-001–005 | Real-world edge cases |

**Synthetic generation rules** (documented in `default.json` metadata):
- Template substitution: `What is the capital of {country}?` with paraphrase + typo variants
- Format permutation: Same ranking question with candidates in different order

### Scoring metrics

| Metric | Method | When used |
|--------|--------|-----------|
| `exact_match` | Case-insensitive string equality | When `expected_answer` is defined |
| `regex_match` | `re.search` with `IGNORECASE` | When `expected_pattern` is defined |
| `semantic_similarity` | TF-IDF cosine (scikit-learn) | All cases |

### Ship first vs. later

See [`docs/ship_first_vs_later.md`](docs/ship_first_vs_later.md) for a detailed breakdown of what ships now and what is deferred (neural embeddings, Prometheus metrics, async eval, etc.).

---

## Question 2: RAG Service

FastAPI endpoint that retrieves relevant snippets from a 12-snippet AI/ML corpus and generates a grounded answer.

### Run

```bash
# Start the service
uv run uvicorn rag_service.main:app --reload

# Health check
curl http://localhost:8000/health

# Query the service
curl -X POST http://localhost:8000/answer \
  -H "Content-Type: application/json" \
  -d '{"query": "What is retrieval-augmented generation?"}'

# With explicit k and metric
curl -X POST http://localhost:8000/answer \
  -H "Content-Type: application/json" \
  -d '{"query": "How does TF-IDF work?", "k": 3, "similarity_metric": "cosine"}'

# Test the guardrail (should return 403)
curl -X POST http://localhost:8000/answer \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I hack a system?"}'
```

### Index configuration comparison

```bash
# Run side-by-side comparison of cosine vs dot-product
uv run python -m rag_service.compare_indexes
```

**Verdict**: Cosine similarity is the default. It normalizes by vector magnitude, making it insensitive to document length. Dot-product inflates scores for longer documents on unnormalized TF-IDF vectors. See `compare_indexes.py` for the full justification.

### Guardrail

A topic **denylist** (`rag_service/denylist.txt`) is checked before every request:
- Matching is case-insensitive substring search
- Blocked requests return HTTP 403 with the matched term
- **Fails closed**: if the denylist file cannot be loaded at startup, the service refuses to start

**Why a denylist?** It runs in <1ms (no LLM call), is fully auditable (just a text file), and catches the most common class of misuse — prohibited topic queries. Updating the policy requires only editing the file, not redeploying code.

### Monitoring

Every request emits a structured JSON log line to stdout:

```json
{
  "event": "rag_request",
  "latency_ms": 1234.5,
  "retrieval_ms": 12.3,
  "generation_ms": 1222.2,
  "snippet_count": 5,
  "hit_rate": 0.8,
  "answer_length": 312,
  "similarity_metric": "cosine",
  "blocked": false,
  "level": "INFO"
}
```

**Tracked metrics**:
1. **Request latency** (`latency_ms`, split into `retrieval_ms` + `generation_ms`) — pipe logs to `jq` or any aggregator for p50/p95
2. **Retrieval hit-rate** (`hit_rate`) — fraction of returned snippets above similarity threshold (default 0.1); low hit-rate signals query/corpus mismatch

**Drift detection (sketched)**: Monitor `answer_length` variance over a rolling window. A spike indicates the LLM is generating inconsistent-length responses, which often correlates with prompt drift or model API changes.

---

## Run Tests

```bash
# uv run automatically uses the project venv
uv run pytest tests/ -v
```

All tests run without an API key (LLM calls are mocked in API tests).

---

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Embeddings | TF-IDF (scikit-learn) | Zero cost, no GPU, deterministic, good enough for 12 snippets |
| LLM integration | httpx + OpenAI-compatible API | Works with OpenAI, Anthropic, Ollama, Azure |
| Guardrail | Topic denylist | Sub-millisecond, auditable, fail-closed |
| Similarity metric | Cosine (default) | Length-invariant; dot-product available for comparison |
| Monitoring | Structured JSON logs | No external stack needed; parseable by any aggregator |

---

## Project Structure

```
eval_harness/          # Question 1: Prompt consistency evaluation
├── runner.py          # CLI entry point
├── metrics.py         # exact_match, regex_match, semantic_similarity
├── models.py          # Pydantic models
├── config.py          # Env-var loading
└── test_sets/
    └── default.json   # 10 hand-rolled test cases

rag_service/           # Question 2: FastAPI RAG service
├── main.py            # FastAPI app (POST /answer, GET /health)
├── retriever.py       # TF-IDF search
├── guardrails.py      # Topic denylist
├── monitoring.py      # Structured JSON logging
├── models.py          # Pydantic models
├── config.py          # Env-var loading
├── compare_indexes.py # Cosine vs dot-product comparison
├── denylist.txt       # Prohibited topics
└── corpus/
    └── snippets.json  # 12 AI/ML knowledge snippets

tests/                 # pytest suite (no API key needed)
docs/
└── ship_first_vs_later.md

pyproject.toml         # Project metadata and dependencies (canonical)
uv.lock                # Locked dependency tree (commit this)
.env.example           # Environment variable template
```
