from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, field_validator


class AnswerRequest(BaseModel):
    query: str
    k: Optional[int] = None
    similarity_metric: Optional[str] = None

    @field_validator("query")
    @classmethod
    def query_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Query must be a non-empty string")
        if len(v) > 1000:
            raise ValueError("Query must not exceed 1000 characters")
        return v

    @field_validator("k")
    @classmethod
    def k_in_range(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1 <= v <= 15):
            raise ValueError("k must be between 1 and 15")
        return v

    @field_validator("similarity_metric")
    @classmethod
    def valid_metric(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("cosine", "dot_product"):
            raise ValueError("similarity_metric must be 'cosine' or 'dot_product'")
        return v


class RetrievedSnippet(BaseModel):
    id: str
    title: str
    content: str
    score: float


class AnswerResponse(BaseModel):
    query: str
    snippets: list[RetrievedSnippet]
    answer: str
    similarity_metric: str
    latency_ms: float
    retrieval_ms: float


class HealthResponse(BaseModel):
    status: str
    corpus_loaded: bool
    snippet_count: int
    guardrail_active: bool
