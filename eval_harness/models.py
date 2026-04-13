from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class TestCase(BaseModel):
    id: str
    prompt: str
    expected_answer: Optional[str] = None
    expected_pattern: Optional[str] = None
    test_type: str  # "standard" | "invariance" | "perturbation"
    group_id: Optional[str] = None
    source: str  # "synthetic" | "real_world"
    generation_rule: Optional[str] = None
    metadata: Optional[dict] = None


class TestGroup(BaseModel):
    group_id: str
    group_type: str  # "invariance" | "perturbation"
    description: str
    expected_behavior: str  # "identical" | "may_drift"


class TestSetMetadata(BaseModel):
    name: str
    version: str
    created: str
    total_cases: int
    synthetic_count: int
    real_world_count: int


class TestSet(BaseModel):
    metadata: TestSetMetadata
    groups: list[TestGroup]
    cases: list[TestCase]


class EvalResult(BaseModel):
    test_case_id: str
    llm_response: str
    scores: dict[str, float]
    passed: bool
    latency_ms: float
    error: Optional[str] = None


class GroupResult(BaseModel):
    group_id: str
    group_type: str
    consistency_score: float  # 1.0 = all identical (invariance) or low drift (perturbation)
    all_identical: bool
    max_drift: float  # max pairwise semantic distance within group
    cases: list[str]


class EvalReport(BaseModel):
    timestamp: str
    test_set_name: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    error_cases: int
    mean_exact_match: float
    mean_regex_match: float
    mean_semantic_similarity: float
    group_results: list[GroupResult]
    results: list[EvalResult]
