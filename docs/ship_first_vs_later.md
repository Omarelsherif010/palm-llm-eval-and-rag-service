# Ship First vs. Later — Prompt Reliability Eval Harness

## Ship First

These items are in the current build and deliver immediate value:

**1. The eval harness itself with TF-IDF scoring**
The core `eval_harness/runner.py` + `metrics.py` pipeline is ready to run against any
OpenAI-compatible API with a single command. TF-IDF cosine similarity is a deterministic,
zero-cost scoring method that works without any model download. It is not as semantically
rich as neural embeddings, but it is transparent, fast, and good enough to detect gross
consistency failures (e.g., an LLM switching from "Paris" to "France" across paraphrases).

**2. Hand-rolled test set with documented generation rules**
The 10-case test set (`eval_harness/test_sets/default.json`) ships with the code. The
invariance group (INV-001) and perturbation group (PRT-001) are explicitly labelled and
the generation rules are documented in the JSON metadata. A reviewer can understand why
each case exists without additional explanation.

**3. Multi-metric scoring (exact, regex, semantic)**
Three scoring functions cover the range from strict (exact match) to fuzzy (semantic
similarity). The harness reports all three per case, so an operator can choose the
appropriate threshold for their use case.

**4. Machine-readable JSON output**
The `--format json` flag produces a structured EvalReport that can be parsed by CI
pipelines, dashboards, or downstream analysis tools. This is the hook for future automation.

---

## Ship Later

These items are deferred to keep the prototype focused:

**1. Neural embeddings for semantic similarity**
Replace TF-IDF cosine in `metrics.py` with `sentence-transformers`
(e.g., `all-MiniLM-L6-v2`) for more accurate semantic similarity scoring, especially for
paraphrases that share few common keywords. Deferred because it adds a ~400MB dependency
and requires torch, which is overkill for a prototype demonstrating the evaluation framework.

**2. Prometheus /metrics endpoint**
Expose a `GET /metrics` endpoint (using `prometheus_client`) to track eval run latency,
pass/fail rates, and per-group consistency scores over time. Currently logged to stdout
as structured JSON; a Prometheus scraper would enable dashboarding. Deferred because it
requires an external scraper to be useful.

**3. LLM-based content classifier guardrail**
Replace the simple topic denylist with a secondary LLM call that classifies whether the
query is appropriate before processing. Higher accuracy, lower false-positive rate, but
adds latency and API cost per request. Practical at scale; overkill for a prototype with
a small, controlled corpus.

**4. k-value grid search and adaptive retrieval**
Currently k is a static config value. A production system should tune k on a validation
set by measuring retrieval precision@k. Deferred because tuning requires labeled relevance
data that does not exist in this prototype.

**5. Async LLM calls for parallel eval**
The current runner calls the LLM synchronously per test case. For large test sets (50+
cases), replacing this with `asyncio`/`httpx` async calls would reduce wall-clock eval
time significantly. Deferred because the 10-case prototype completes in under 2 minutes.

**6. deepeval / ragas for structured LLM evaluation**
deepeval provides 50+ LLM-as-a-judge metrics (G-Eval, faithfulness, hallucination detection)
and ragas provides RAG-specific metrics (context precision, context recall, answer relevancy).
Neither framework covers invariance or perturbation testing out of the box — the hand-rolled
harness was purpose-built for consistency measurement. At production scale, integrating ragas
for RAG quality evaluation and deepeval for LLM output grading would complement (not replace)
the consistency harness. Deferred because both add significant dependency weight (~100MB+)
for metrics orthogonal to the prototype's core question: "does the LLM give stable answers?"

**7. FAISS or ChromaDB for vector retrieval**
The current retriever uses in-memory sklearn TF-IDF with exact cosine similarity. For
corpora beyond a few thousand documents, FAISS (approximate nearest-neighbor with HNSW/IVF
indexes) or ChromaDB (persistent vector store with embedding management) would be necessary.
Deferred because exact search over 12 snippets is faster and simpler than any ANN index,
and adding FAISS requires a C++ extension while ChromaDB adds SQLite persistence — neither
justified at this scale.
