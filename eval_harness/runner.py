"""
Eval harness runner.

Usage:
    python -m eval_harness.runner [--test-set PATH] [--output PATH] [--format json|human|both]

Exit codes:
    0 — all cases passed
    1 — one or more cases failed
    2 — configuration error (missing API key, invalid test set)
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

from eval_harness import config
from eval_harness.metrics import (
    exact_match,
    pairwise_max_drift,
    regex_match,
    semantic_similarity,
)
from eval_harness.models import (
    EvalReport,
    EvalResult,
    GroupResult,
    TestSet,
)

DEFAULT_TEST_SET = Path(__file__).parent / "test_sets" / "default.json"
PASS_THRESHOLD_SEMANTIC = 0.4  # minimum semantic similarity to consider a scored case "passed"


def load_test_set(path: Path) -> TestSet:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return TestSet.model_validate(data)


def call_llm(prompt: str) -> tuple[str, float]:
    """
    Call OpenAI-compatible chat completions endpoint.
    Returns (response_text, latency_ms).
    """
    if not config.LLM_API_KEY:
        raise ValueError("LLM_API_KEY is not set. Export it or add it to .env")

    payload = {
        "model": config.LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
    }
    headers = {
        "Authorization": f"Bearer {config.LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    start = time.perf_counter()
    response = httpx.post(
        f"{config.LLM_BASE_URL}/chat/completions",
        json=payload,
        headers=headers,
        timeout=60.0,
    )
    latency_ms = (time.perf_counter() - start) * 1000

    response.raise_for_status()
    text = response.json()["choices"][0]["message"]["content"].strip()
    return text, latency_ms


def score_result(case, llm_response: str) -> dict[str, float]:
    scores: dict[str, float] = {}

    if case.expected_answer is not None:
        scores["exact_match"] = exact_match(case.expected_answer, llm_response)
        scores["semantic_similarity"] = semantic_similarity(case.expected_answer, llm_response)

    if case.expected_pattern is not None:
        scores["regex_match"] = regex_match(case.expected_pattern, llm_response)

    if not scores:
        # Open-ended case — only semantic check (against prompt as loose proxy)
        scores["semantic_similarity"] = semantic_similarity(case.prompt, llm_response)

    return scores


def is_passed(scores: dict[str, float], case) -> bool:
    """
    A case passes if:
    - regex_match == 1.0 (when a pattern is defined), OR
    - semantic_similarity >= threshold (when expected answer is defined), OR
    - for open-ended cases (no expected_answer, no expected_pattern): always passes
    """
    # Open-ended cases have no ground truth to check against
    if case.expected_answer is None and case.expected_pattern is None:
        return True
    if "regex_match" in scores and case.expected_pattern:
        return scores["regex_match"] == 1.0
    if case.expected_answer is not None:
        return scores.get("semantic_similarity", 0.0) >= PASS_THRESHOLD_SEMANTIC
    return True


def compute_group_results(test_set: TestSet, results_map: dict[str, EvalResult]) -> list[GroupResult]:
    group_results = []
    for group in test_set.groups:
        member_cases = [c for c in test_set.cases if c.group_id == group.group_id]
        member_ids = [c.id for c in member_cases]
        responses = []
        for case_id in member_ids:
            r = results_map.get(case_id)
            if r and not r.error:
                responses.append(r.llm_response)

        if not responses:
            group_results.append(GroupResult(
                group_id=group.group_id,
                group_type=group.group_type,
                consistency_score=0.0,
                all_identical=False,
                max_drift=0.0,
                cases=member_ids,
            ))
            continue

        all_identical = len(set(r.strip().lower() for r in responses)) == 1

        if group.group_type == "invariance":
            # Consistency = fraction of responses semantically close to the first
            reference = responses[0]
            sims = [semantic_similarity(reference, r) for r in responses[1:]]
            consistency = (sum(sims) / len(sims)) if sims else 1.0
            max_drift = pairwise_max_drift(responses)
        else:
            # Perturbation: measure drift magnitude
            max_drift = pairwise_max_drift(responses)
            consistency = 1.0 - max_drift

        group_results.append(GroupResult(
            group_id=group.group_id,
            group_type=group.group_type,
            consistency_score=round(consistency, 4),
            all_identical=all_identical,
            max_drift=round(max_drift, 4),
            cases=member_ids,
        ))
    return group_results


def run_evaluation(test_set: TestSet) -> EvalReport:
    results: list[EvalResult] = []
    results_map: dict[str, EvalResult] = {}

    for case in test_set.cases:
        try:
            llm_response, latency_ms = call_llm(case.prompt)
            scores = score_result(case, llm_response)
            passed = is_passed(scores, case)
            result = EvalResult(
                test_case_id=case.id,
                llm_response=llm_response,
                scores=scores,
                passed=passed,
                latency_ms=round(latency_ms, 2),
            )
        except Exception as e:
            result = EvalResult(
                test_case_id=case.id,
                llm_response="",
                scores={},
                passed=False,
                latency_ms=0.0,
                error=str(e),
            )

        results.append(result)
        results_map[case.id] = result
        status = "PASS" if result.passed else ("ERROR" if result.error else "FAIL")
        print(f"  [{status}] {case.id}", file=sys.stderr)

    group_results = compute_group_results(test_set, results_map)

    passed = sum(1 for r in results if r.passed and not r.error)
    errors = sum(1 for r in results if r.error)
    failed = len(results) - passed - errors

    exact_scores = [r.scores.get("exact_match", 0.0) for r in results if "exact_match" in r.scores]
    regex_scores = [r.scores.get("regex_match", 0.0) for r in results if "regex_match" in r.scores]
    sem_scores = [r.scores.get("semantic_similarity", 0.0) for r in results if "semantic_similarity" in r.scores]

    return EvalReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        test_set_name=test_set.metadata.name,
        total_cases=len(results),
        passed_cases=passed,
        failed_cases=failed,
        error_cases=errors,
        mean_exact_match=round(sum(exact_scores) / len(exact_scores), 4) if exact_scores else 0.0,
        mean_regex_match=round(sum(regex_scores) / len(regex_scores), 4) if regex_scores else 0.0,
        mean_semantic_similarity=round(sum(sem_scores) / len(sem_scores), 4) if sem_scores else 0.0,
        group_results=group_results,
        results=results,
    )


def format_human(report: EvalReport) -> str:
    lines = [
        "=== LLM Consistency Evaluation Report ===",
        f"Run:       {report.timestamp}",
        f"Test set:  {report.test_set_name} ({report.total_cases} cases)",
        "",
        f"RESULTS: {report.passed_cases} passed | {report.failed_cases} failed | {report.error_cases} errors",
        "",
    ]

    for gr in report.group_results:
        lines.append(f"GROUP: {gr.group_id} ({gr.group_type}) — consistency: {gr.consistency_score:.0%}  max_drift: {gr.max_drift:.3f}")
        for case_id in gr.cases:
            r = next((x for x in report.results if x.test_case_id == case_id), None)
            if r:
                score_str = "  ".join(f"{k}={v:.2f}" for k, v in r.scores.items())
                status = "PASS" if r.passed else ("ERROR" if r.error else "FAIL")
                lines.append(f"  {case_id}: {status} ({score_str})")
        lines.append("")

    lines += [
        "AGGREGATE METRICS:",
        f"  Mean exact match:          {report.mean_exact_match:.4f}",
        f"  Mean regex match:          {report.mean_regex_match:.4f}",
        f"  Mean semantic similarity:  {report.mean_semantic_similarity:.4f}",
        "",
    ]

    # Non-group cases
    group_case_ids = {cid for gr in report.group_results for cid in gr.cases}
    standalone = [r for r in report.results if r.test_case_id not in group_case_ids]
    if standalone:
        lines.append("STANDALONE CASES:")
        for r in standalone:
            score_str = "  ".join(f"{k}={v:.2f}" for k, v in r.scores.items()) if r.scores else "no scores"
            status = "PASS" if r.passed else ("ERROR" if r.error else "FAIL")
            err = f"  !! {r.error}" if r.error else ""
            lines.append(f"  {r.test_case_id}: {status} ({score_str}){err}")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run LLM prompt consistency evaluation",
        prog="python -m eval_harness.runner",
    )
    parser.add_argument(
        "--test-set",
        type=Path,
        default=DEFAULT_TEST_SET,
        help=f"Path to test set JSON file (default: {DEFAULT_TEST_SET})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path to write JSON results (default: stdout)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "human", "both"],
        default="both",
        help="Output format (default: both)",
    )
    args = parser.parse_args()

    if not args.test_set.exists():
        print(f"Error: test set not found: {args.test_set}", file=sys.stderr)
        return 2

    if not config.LLM_API_KEY:
        print("Error: LLM_API_KEY not set. Copy .env.example to .env and set your key.", file=sys.stderr)
        return 2

    print(f"Running evaluation: {args.test_set}", file=sys.stderr)
    try:
        test_set = load_test_set(args.test_set)
    except (json.JSONDecodeError, Exception) as e:
        print(f"Error: invalid test set: {e}", file=sys.stderr)
        return 2
    n = len(test_set.cases)

    if n < 8 or n > 12:
        print(f"Warning: test set has {n} cases (expected 8–12)", file=sys.stderr)

    report = run_evaluation(test_set)

    json_output = report.model_dump_json(indent=2)

    if args.format in ("json", "both"):
        if args.output:
            args.output.write_text(json_output, encoding="utf-8")
            print(f"JSON results written to {args.output}", file=sys.stderr)
        else:
            print(json_output)

    if args.format in ("human", "both"):
        human_output = format_human(report)
        if args.format == "human" and args.output:
            args.output.write_text(human_output, encoding="utf-8")
        else:
            print(human_output, file=sys.stderr if args.format == "both" else sys.stdout)

    return 0 if report.failed_cases == 0 and report.error_cases == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
