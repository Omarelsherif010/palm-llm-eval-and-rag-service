# Research: LLM Eval Harness & RAG Service

**Date**: 2026-04-13
**Branch**: `001-llm-eval-rag-service`

## R1: Embedding / Similarity Approach

**Decision**: Use scikit-learn TF-IDF vectorization + cosine similarity
for both the eval harness (semantic similarity scoring) and the RAG
service (snippet retrieval).

**Rationale**: For a corpus of 10–15 snippets and 8–12 test cases,
neural embeddings (sentence-transformers, OpenAI embeddings) are
overkill. TF-IDF is:
- Zero external API cost (no embedding endpoint calls)
- No GPU or large model download required
- Fast enough for interactive use (<10ms for 15 snippets)
- Deterministic (same input → same vector, unlike LLM-based embeddings
  which may vary across API versions)
- Easy to inspect and debug (sparse vectors with interpretable terms)

**Alternatives considered**:
- `sentence-transformers` (all-MiniLM-L6-v2): Better semantic quality
  but adds ~400MB torch dependency. Deferred to "ship later."
- OpenAI embeddings API: Best quality but adds API cost per query
  and network latency. Deferred to "ship later."
- BM25 (rank-bm25 package): Good for keyword retrieval but no vector
  representation for similarity scoring in the eval harness. Rejected.

## R2: LLM Provider Integration

**Decision**: Use `httpx` with direct HTTP calls to an
OpenAI-compatible API. Configure via `LLM_API_KEY`, `LLM_BASE_URL`,
and `LLM_MODEL` environment variables.

**Rationale**: Using raw `httpx` instead of the `openai` or
`anthropic` SDK keeps dependencies minimal and gives explicit
control over request/response handling. The OpenAI chat completions
format (`/v1/chat/completions`) is supported by OpenAI, Anthropic
(via proxy), Azure OpenAI, and local servers (Ollama, LM Studio,
vLLM). This gives reviewers maximum flexibility to test with
whatever provider they have access to.

**Alternatives considered**:
- `openai` Python SDK: Convenient but adds a dependency and
  abstracts away the HTTP layer. Acceptable for production.
- `anthropic` Python SDK: Ties to one provider. The constitution
  suggests Anthropic as primary but the prototype benefits from
  provider flexibility.
- `litellm`: Unified interface across providers but heavy
  dependency with many transitive deps. Rejected for prototype.

## R3: Guardrail Type Selection

**Decision**: Topic denylist guardrail — a configurable list of
prohibited topic keywords/phrases checked against incoming queries
before processing.

**Rationale**: A topic denylist is the most practical first
guardrail because it:
- Runs in <1ms (string matching, no LLM call needed)
- Is fully transparent and auditable (the list is a config file)
- Catches the most common misuse pattern (off-topic or
  prohibited queries)
- Fails closed naturally: if the denylist cannot be loaded,
  no queries can be validated → reject all
- Is easy to update without code changes (just edit the list)

**Alternatives considered**:
- Per-user budget/rate limiting: Requires user identity tracking,
  adds state management. Better for production, not prototype.
- Token-length limiter: Useful but doesn't address content safety.
  Could be added as a second guardrail later.
- LLM-based content classifier: High quality but adds latency
  and cost per request. Deferred to "ship later."

## R4: Index Configuration Comparison

**Decision**: Compare cosine similarity vs dot-product similarity
on the same TF-IDF vectors, with k=5 for both.

**Rationale**: Cosine and dot-product behave differently on
unnormalized TF-IDF vectors:
- Cosine normalizes by vector magnitude → favors semantic
  relevance regardless of document length.
- Dot-product is magnitude-sensitive → longer documents with
  more term overlap score higher.

This is a meaningful architectural comparison for a retrieval system
because the choice affects whether the system prefers concise,
focused snippets (cosine) or longer, comprehensive ones (dot-product).
Holding k constant isolates the similarity metric as the variable.

**Alternatives considered**:
- k=3 vs k=5 comparison: Valid but less architecturally interesting.
  The "right k" is usually tuned empirically per corpus. Will mention
  in the ship-later notes.
- Euclidean distance vs cosine: Euclidean on TF-IDF is dominated
  by vector magnitude, making it a poor retrieval metric. Rejected.

## R5: Monitoring Approach

**Decision**: Structured JSON logs emitted via Python's `logging`
module with a custom JSON formatter. Track two metrics:
1. **Request latency** (p50, p95): Time from request receipt to
   response send, broken into retrieval_ms and generation_ms.
2. **Retrieval hit-rate**: Fraction of returned snippets with
   similarity score above a configurable threshold (default 0.1).

Drift metric (sketched, not implemented): Track answer-length
variance over a rolling window. A spike in variance may indicate
the LLM is generating inconsistent-length responses, which often
correlates with prompt drift or model updates.

**Rationale**: Structured JSON logs are the lowest-friction
monitoring approach:
- No external monitoring stack required
- Parseable by any log aggregator (ELK, CloudWatch, Datadog)
- Can be piped to `jq` for ad-hoc analysis during development
- No additional dependencies

**Alternatives considered**:
- Prometheus `/metrics` endpoint: Standard for production services
  but adds `prometheus_client` dependency and requires a scraper.
  Deferred to "ship later."
- OpenTelemetry tracing: Best for distributed systems but massive
  dependency graph. Overkill for single-process prototype.

## R6: Test Set Design Rules

**Decision**: 10 test cases total (within the 8–12 range).

**Synthetic cases (5)** — generation rules:
1. **Template substitution**: Take a base question template and
   substitute entities (e.g., "What is the capital of {country}?"
   with different countries).
2. **Numeric variation**: Change numeric values in a question
   to test if the LLM adapts (e.g., "Convert 100 USD to EUR"
   → "Convert 250 USD to EUR").
3. **Format permutation**: Same question in different formats
   (declarative, interrogative, imperative).
4. **Invariance group** (3 cases): Paraphrases of the same
   question with typos and filler words — expected answer
   MUST NOT change.
5. **Perturbation group** (2 cases): Same question with
   reordered list items or added distractors — answer MAY
   legitimately differ.

**Real-world edge cases (5)** — redacted from past work:
1. Ambiguous entity reference (multiple valid interpretations)
2. Multi-step reasoning with implicit constraints
3. Domain jargon requiring specialized knowledge
4. Contradictory context in the prompt
5. Very short query with insufficient context

**Rationale**: 10 cases balances coverage with manual curation
effort. The synthetic rules are explicit and reproducible. The
real-world cases are drawn from common LLM failure modes observed
in production systems.
