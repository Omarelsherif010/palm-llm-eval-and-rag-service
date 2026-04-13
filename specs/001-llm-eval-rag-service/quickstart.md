# Quickstart: LLM Eval Harness & RAG Service

**Prerequisites**: Python 3.11+, an OpenAI-compatible API key

## Setup

```bash
# Clone and enter the project
cd palm-llm-eval-and-rag-service

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set your LLM_API_KEY
```

## Question 1: Eval Harness

```bash
# Run the evaluation against the default test set
python -m eval_harness.runner

# Run with specific test set and JSON output
python -m eval_harness.runner --test-set eval_harness/test_sets/default.json --format json

# Save results to file
python -m eval_harness.runner --output results.json
```

Expected output: A scored report showing per-case results and
aggregate consistency metrics. Invariance groups flag when
answers diverge; perturbation groups quantify drift.

## Question 2: RAG Service

```bash
# Start the service
uvicorn rag_service.main:app --reload

# In another terminal, send a test query
curl -X POST http://localhost:8000/answer \
  -H "Content-Type: application/json" \
  -d '{"query": "What is retrieval-augmented generation?"}'

# Test the guardrail (should be blocked)
curl -X POST http://localhost:8000/answer \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I hack into a system?"}'

# Health check
curl http://localhost:8000/health

# Compare index configurations
curl -X POST http://localhost:8000/answer \
  -H "Content-Type: application/json" \
  -d '{"query": "What is TF-IDF?", "similarity_metric": "cosine"}'

curl -X POST http://localhost:8000/answer \
  -H "Content-Type: application/json" \
  -d '{"query": "What is TF-IDF?", "similarity_metric": "dot_product"}'
```

## Running Tests

```bash
pytest tests/ -v
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| LLM_API_KEY | yes | — | API key for OpenAI-compatible provider |
| LLM_BASE_URL | no | https://api.openai.com/v1 | API base URL |
| LLM_MODEL | no | gpt-3.5-turbo | Model to use |
| RAG_DEFAULT_K | no | 5 | Default number of snippets to retrieve |
| RAG_SIMILARITY_METRIC | no | cosine | Default similarity metric |
| RAG_DENYLIST_PATH | no | rag_service/denylist.txt | Path to topic denylist |
