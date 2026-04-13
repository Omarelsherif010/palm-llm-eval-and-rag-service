# Full-Stack Requirements Quality Checklist: LLM Eval Harness & RAG Service

**Purpose**: Author self-review — catch gaps in requirement completeness, clarity, and consistency before submission
**Created**: 2026-04-13
**Feature**: [spec.md](../spec.md)
**Depth**: Deep (~40 items)

## Requirement Completeness — Eval Harness

- [ ] CHK001 - Are the explicit generation rules for each synthetic test case type documented? [Completeness, Spec §FR-002]
- [ ] CHK002 - Are redaction guidelines for real-world edge cases specified (what must be removed vs. what can stay)? [Completeness, Spec §FR-002]
- [ ] CHK003 - Is the minimum number of cases per invariance group defined, or could a single-case "group" satisfy the requirement? [Clarity, Spec §FR-003]
- [ ] CHK004 - Is the minimum number of cases per perturbation group defined? [Clarity, Spec §FR-003]
- [ ] CHK005 - Are pass/fail thresholds specified for each scoring metric (exact match, regex, semantic similarity)? [Gap, Spec §FR-004]
- [ ] CHK006 - Is "semantic similarity" defined with a specific computation method, or is it left ambiguous? [Clarity, Spec §FR-004]
- [ ] CHK007 - Are requirements defined for how the harness handles a test case with neither expected_answer nor expected_pattern? [Edge Case, Data Model §TestCase]
- [ ] CHK008 - Is the behavior specified when a test case references a group_id that doesn't exist in the groups list? [Edge Case, Gap]
- [ ] CHK009 - Are requirements for the "ship first vs. later" note's structure and minimum content defined? [Completeness, Spec §US3]

## Requirement Completeness — RAG Service

- [ ] CHK010 - Are requirements for corpus snippet content quality defined (min/max length, required fields, topic diversity)? [Completeness, Spec §FR-007]
- [ ] CHK011 - Is the behavior specified when k exceeds the total number of snippets in the corpus? [Edge Case, Contract §POST /answer]
- [ ] CHK012 - Are requirements for how the LLM prompt is constructed from retrieved snippets documented? [Gap]
- [ ] CHK013 - Is the relevance threshold for "low confidence" responses defined with a specific numeric value? [Clarity, Spec §Edge Cases]
- [ ] CHK014 - Are requirements for the index comparison methodology documented (same queries, same corpus, what metrics to compare)? [Completeness, Spec §FR-009]
- [ ] CHK015 - Is the comparison report format specified (tabular, narrative, both)? [Gap, Spec §FR-009]
- [ ] CHK016 - Are requirements for corpus snippet ordering or shuffling during indexing addressed? [Gap]

## Requirement Completeness — Guardrails

- [ ] CHK017 - Is the denylist file format specified (one term per line, JSON array, regex patterns)? [Clarity, Gap]
- [ ] CHK018 - Is the matching behavior for denylist terms defined (exact match, substring, case-insensitive)? [Clarity, Gap]
- [ ] CHK019 - Are requirements for updating the denylist at runtime (hot-reload vs. restart) documented? [Gap]
- [ ] CHK020 - Is the guardrail check ordering relative to input validation specified (validate first, then guardrail, or vice versa)? [Gap]

## Requirement Completeness — Monitoring & Observability

- [ ] CHK021 - Are the specific percentile calculations for latency defined (how to compute p50/p95 — rolling window, per-session, lifetime)? [Clarity, Spec §FR-010]
- [ ] CHK022 - Is the retrieval hit-rate threshold documented (what score qualifies as a "hit")? [Clarity, Gap]
- [ ] CHK023 - Are requirements for log output destination defined (stdout, file, both)? [Gap]
- [ ] CHK024 - Is the structured log schema specified with exact field names and types? [Completeness, Gap]

## Requirement Clarity

- [ ] CHK025 - Is "naive answer" in US2 defined with specific generation constraints (e.g., max tokens, temperature, system prompt template)? [Ambiguity, Spec §US2]
- [ ] CHK026 - Is "drift magnitude" for perturbation tests quantified with a specific metric or formula? [Ambiguity, Spec §US1]
- [ ] CHK027 - Are "machine-readable output" format requirements unambiguous (JSON only, or also CSV/JSONL)? [Clarity, Spec §FR-005]
- [ ] CHK028 - Is "hand-written" for corpus snippets clarified — must the engineer author original text, or can snippets be adapted from public sources? [Ambiguity, Spec §FR-007]

## Requirement Consistency

- [ ] CHK029 - Are the AnswerRequest fields in the data model consistent with the API contract fields (k constraints, similarity_metric enum values)? [Consistency, Data Model ↔ Contract]
- [ ] CHK030 - Are environment variable names consistent between eval harness CLI contract and RAG service quickstart? [Consistency, Contract §eval-cli ↔ quickstart]
- [ ] CHK031 - Is the default k value consistent across spec (unspecified), contract (5), and quickstart (RAG_DEFAULT_K=5)? [Consistency]
- [ ] CHK032 - Does the EvalReport data model include all fields shown in the CLI contract's JSON output example? [Consistency, Data Model ↔ Contract]

## Acceptance Criteria Quality

- [ ] CHK033 - Is SC-002 ("90% detection rate") measurable given the test set size of 8–12 cases — can you meaningfully compute 90% of ~3 invariance cases? [Measurability, Spec §SC-002]
- [ ] CHK034 - Is SC-003 ("80% of test queries") achievable given the corpus size of 10–15 snippets — are there enough test queries defined? [Measurability, Spec §SC-003]
- [ ] CHK035 - Is SC-005 ("set up and run within 10 minutes") testable — does it include dependency install time? [Measurability, Spec §SC-005]
- [ ] CHK036 - Can SC-006 ("clearly shows which configuration performs better") be objectively evaluated — is "clearly" defined? [Measurability, Spec §SC-006]

## Scenario Coverage

- [ ] CHK037 - Are requirements defined for running the eval harness without an API key (e.g., dry-run mode or cached responses for testing)? [Coverage, Gap]
- [ ] CHK038 - Are requirements for concurrent requests to the RAG endpoint addressed (thread safety of in-memory index)? [Coverage, Gap]
- [ ] CHK039 - Are requirements for the RAG service startup behavior defined (what happens if corpus file is missing or malformed at boot)? [Coverage, Exception Flow]
- [ ] CHK040 - Are requirements for eval harness behavior on partial LLM failures (some cases succeed, some fail) clearly documented beyond "report partial results"? [Coverage, Spec §Edge Cases]

## Dependencies & Assumptions

- [ ] CHK041 - Is the assumption "reviewers have Python 3.11+" validated — are lower Python version requirements documented as unsupported? [Assumption, Spec §Assumptions]
- [ ] CHK042 - Are the specific pinned dependency versions documented, or only the package names? [Gap, Spec §Assumptions]
- [ ] CHK043 - Is the LLM API rate-limit handling strategy specified (retry with backoff, skip, abort)? [Dependency, Gap]

## Notes

- Check items off as completed: `[x]`
- Items marked `[Gap]` indicate requirements that may need to be added to the spec
- Items marked `[Ambiguity]` indicate terms that need sharper definitions
- Items marked `[Consistency]` require cross-referencing between documents
- Focus on gaps that a hiring reviewer would notice — prioritize CHK005, CHK012, CHK025, CHK033
