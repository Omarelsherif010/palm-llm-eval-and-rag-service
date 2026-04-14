# Contract: Eval Harness CLI

**Date**: 2026-04-13
**Type**: Command-line interface

## Usage

```bash
python -m eval_harness.runner [OPTIONS]
```

## Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--test-set` | path | `eval_harness/test_sets/default.json` | Path to test set JSON file |
| `--output` | path | stdout | Path to write JSON results (default: print to stdout) |
| `--format` | string | `both` | Output format: "json", "human", or "both" |
| `--help` | flag | — | Print usage and exit |

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_API_KEY` | yes | — | API key for the LLM provider |
| `LLM_BASE_URL` | no | `https://api.openai.com/v1` | Base URL for OpenAI-compatible API |
| `LLM_MODEL` | no | `gpt-5.4-nano-2026-03-17` | Model name to use |

## Test Set File Format (JSON)

```json
{
  "metadata": {
    "name": "Default consistency test set",
    "version": "1.0",
    "created": "2026-04-13",
    "total_cases": 10,
    "synthetic_count": 5,
    "real_world_count": 5
  },
  "groups": [
    {
      "group_id": "INV-001",
      "group_type": "invariance",
      "description": "Capital city paraphrases",
      "expected_behavior": "identical"
    }
  ],
  "cases": [
    {
      "id": "SYN-001",
      "prompt": "What is the capital of France?",
      "expected_answer": "Paris",
      "expected_pattern": "(?i)paris",
      "test_type": "invariance",
      "group_id": "INV-001",
      "source": "synthetic",
      "generation_rule": "template_substitution"
    }
  ]
}
```

## Output Format (JSON)

```json
{
  "timestamp": "2026-04-13T10:30:00Z",
  "total_cases": 10,
  "passed_cases": 8,
  "failed_cases": 1,
  "error_cases": 1,
  "mean_exact_match": 0.75,
  "mean_semantic_similarity": 0.89,
  "group_results": [
    {
      "group_id": "INV-001",
      "group_type": "invariance",
      "consistency_score": 0.67,
      "all_identical": false,
      "cases": ["SYN-001", "SYN-002", "SYN-003"]
    }
  ],
  "results": [
    {
      "test_case_id": "SYN-001",
      "llm_response": "The capital of France is Paris.",
      "scores": {
        "exact_match": 0.0,
        "regex_match": 1.0,
        "semantic_similarity": 0.92
      },
      "passed": true,
      "latency_ms": 450.2,
      "error": null
    }
  ]
}
```

## Human-Readable Output

```text
=== LLM Consistency Evaluation Report ===
Run: 2026-04-13T10:30:00Z
Test set: eval_harness/test_sets/default.json (10 cases)

RESULTS: 8 passed | 1 failed | 1 error

GROUP: INV-001 (invariance) — consistency: 67%
  SYN-001: PASS (exact=0.0, regex=1.0, semantic=0.92)
  SYN-002: PASS (exact=0.0, regex=1.0, semantic=0.88)
  SYN-003: FAIL (exact=0.0, regex=0.0, semantic=0.45)

AGGREGATE METRICS:
  Mean exact match:          0.75
  Mean semantic similarity:  0.89
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All test cases passed |
| 1 | One or more test cases failed |
| 2 | Configuration error (missing API key, invalid test set) |
