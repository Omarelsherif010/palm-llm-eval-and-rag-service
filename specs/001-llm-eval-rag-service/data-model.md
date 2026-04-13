# Data Model: LLM Eval Harness & RAG Service

**Date**: 2026-04-13
**Branch**: `001-llm-eval-rag-service`

## Eval Harness Entities

### TestCase

A single evaluation item in the test set.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | yes | Unique identifier (e.g., "SYN-001", "RW-003") |
| prompt | string | yes | The query to send to the LLM |
| expected_answer | string | no | Expected answer for exact/regex matching (null for open-ended) |
| expected_pattern | string | no | Regex pattern the answer must match |
| test_type | enum | yes | One of: "standard", "invariance", "perturbation" |
| group_id | string | no | Links cases in the same invariance/perturbation group |
| source | enum | yes | One of: "synthetic", "real_world" |
| generation_rule | string | no | For synthetic: which rule generated this case |
| metadata | object | no | Freeform metadata (redaction notes, domain, etc.) |

### TestGroup

A collection of related test cases sharing a group_id.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| group_id | string | yes | Matches TestCase.group_id |
| group_type | enum | yes | One of: "invariance", "perturbation" |
| description | string | yes | What this group tests |
| expected_behavior | string | yes | "identical" for invariance, "may_drift" for perturbation |

### EvalResult

Scoring output for a single test case.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| test_case_id | string | yes | References TestCase.id |
| llm_response | string | yes | Raw LLM output |
| scores | object | yes | Map of metric_name → score_value (0.0–1.0) |
| passed | boolean | yes | Whether all applicable thresholds met |
| latency_ms | float | yes | Time to get LLM response |
| error | string | no | Error message if LLM call failed |

### EvalReport

Aggregate results across all test cases.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| timestamp | string | yes | ISO 8601 run timestamp |
| total_cases | int | yes | Number of test cases run |
| passed_cases | int | yes | Number passing all thresholds |
| failed_cases | int | yes | Number failing at least one threshold |
| error_cases | int | yes | Number with LLM call errors |
| group_results | list | yes | Per-group consistency scores |
| mean_exact_match | float | yes | Average exact match score |
| mean_semantic_similarity | float | yes | Average semantic similarity |
| results | list | yes | List of EvalResult objects |

## RAG Service Entities

### CorpusSnippet

A text passage in the knowledge base.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | yes | Unique identifier (e.g., "snippet-001") |
| title | string | yes | Short descriptive title |
| content | string | yes | The text passage (typically 2–5 sentences) |
| topic | string | yes | Topic category for the snippet |
| metadata | object | no | Optional metadata (source, date, tags) |

### AnswerRequest

Incoming query to the RAG endpoint.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| query | string | yes | Natural-language question |
| k | int | no | Number of snippets to retrieve (default from config) |
| similarity_metric | string | no | Override: "cosine" or "dot_product" (default from config) |

### RetrievedSnippet

A single snippet returned by retrieval.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | yes | References CorpusSnippet.id |
| title | string | yes | Snippet title |
| content | string | yes | Snippet text |
| score | float | yes | Similarity score (0.0–1.0 for cosine) |

### AnswerResponse

Full response from the RAG endpoint.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| query | string | yes | Echo of the input query |
| snippets | list | yes | List of RetrievedSnippet objects |
| answer | string | yes | LLM-generated answer grounded in snippets |
| similarity_metric | string | yes | Which metric was used |
| latency_ms | float | yes | Total request processing time |
| retrieval_ms | float | yes | Time spent on retrieval only |

### GuardrailResult

Output of a guardrail check (internal, not exposed in API).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| allowed | boolean | yes | Whether the request passed |
| rule_triggered | string | no | Which rule blocked it (null if allowed) |
| reason | string | no | Human-readable explanation |

## Relationships

- TestCase (many) → TestGroup (one) via group_id (optional)
- EvalResult (one) → TestCase (one) via test_case_id
- EvalReport (one) → EvalResult (many) via results list
- AnswerRequest → RetrievedSnippet (many) via retrieval
- AnswerResponse → RetrievedSnippet (many) via snippets list
- AnswerRequest → GuardrailResult (one) via pre-processing check

## State Transitions

Neither component maintains persistent state. All data flows
are request-scoped:
- Eval harness: load test set → iterate cases → call LLM → score → aggregate → output report
- RAG service: receive request → guardrail check → retrieve snippets → generate answer → respond
