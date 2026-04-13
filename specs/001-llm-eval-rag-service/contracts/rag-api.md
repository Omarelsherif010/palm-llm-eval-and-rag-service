# Contract: RAG Answering Service API

**Date**: 2026-04-13
**Type**: HTTP REST API
**Base Path**: `/`

## POST /answer

Accepts a natural-language query, retrieves relevant snippets
from the corpus, and returns a generated answer.

### Request

```json
{
  "query": "What is retrieval-augmented generation?",
  "k": 5,
  "similarity_metric": "cosine"
}
```

| Field | Type | Required | Default | Constraints |
|-------|------|----------|---------|-------------|
| query | string | yes | — | Non-empty, max 1000 characters |
| k | integer | no | 5 | 1 ≤ k ≤ 15 |
| similarity_metric | string | no | "cosine" | One of: "cosine", "dot_product" |

### Response (200 OK)

```json
{
  "query": "What is retrieval-augmented generation?",
  "snippets": [
    {
      "id": "snippet-003",
      "title": "RAG Overview",
      "content": "Retrieval-augmented generation combines...",
      "score": 0.87
    }
  ],
  "answer": "Retrieval-augmented generation is a technique that...",
  "similarity_metric": "cosine",
  "latency_ms": 1234.5,
  "retrieval_ms": 12.3
}
```

### Response (400 Bad Request) — Empty Query

```json
{
  "detail": "Query must be a non-empty string"
}
```

### Response (403 Forbidden) — Guardrail Blocked

```json
{
  "detail": "Query blocked by content policy",
  "guardrail": "topic_denylist",
  "reason": "Query contains prohibited topic: [matched term]"
}
```

### Response (503 Service Unavailable) — LLM Error

```json
{
  "detail": "LLM service unavailable",
  "retrieval_completed": true,
  "snippets": [...]
}
```

Note: If retrieval succeeds but LLM generation fails, the
response still includes retrieved snippets so the caller can
use them directly.

## GET /health

Health check endpoint.

### Response (200 OK)

```json
{
  "status": "healthy",
  "corpus_loaded": true,
  "snippet_count": 12,
  "guardrail_active": true
}
```
