"""
Structured JSON logging for the RAG service.

Tracks per-request metrics:
  - latency_ms:     total request processing time
  - retrieval_ms:   time spent on TF-IDF retrieval only
  - hit_rate:       fraction of retrieved snippets above similarity threshold
  - answer_length:  length of generated answer (proxy for drift detection)

Drift metric (sketched):
  Track answer_length variance over a rolling window. A spike in variance
  may indicate the LLM is generating inconsistent-length responses,
  which often correlates with prompt drift or model API changes.
"""

from __future__ import annotations
import json
import logging
import sys
from typing import Optional


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = record.__dict__.get("json_payload", {})
        payload["level"] = record.levelname
        return json.dumps(payload)


def _build_logger() -> logging.Logger:
    logger = logging.getLogger("rag_service.monitoring")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


_logger = _build_logger()


def log_request(
    query: str,
    latency_ms: float,
    retrieval_ms: float,
    snippet_scores: list[float],
    answer_length: int,
    similarity_metric: str,
    hit_rate_threshold: float,
    blocked: bool = False,
    error: Optional[str] = None,
) -> None:
    hit_rate = (
        sum(1 for s in snippet_scores if s >= hit_rate_threshold) / len(snippet_scores)
        if snippet_scores
        else 0.0
    )

    payload = {
        "event": "rag_request",
        "query_length": len(query),
        "latency_ms": round(latency_ms, 2),
        "retrieval_ms": round(retrieval_ms, 2),
        "generation_ms": round(latency_ms - retrieval_ms, 2),
        "snippet_count": len(snippet_scores),
        "hit_rate": round(hit_rate, 4),
        "answer_length": answer_length,
        "similarity_metric": similarity_metric,
        "blocked": blocked,
    }
    if error:
        payload["error"] = error

    record = logging.LogRecord(
        name="rag_service.monitoring",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="",
        args=(),
        exc_info=None,
    )
    record.json_payload = payload
    _logger.handle(record)
