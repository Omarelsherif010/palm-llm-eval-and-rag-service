"""
RAG Answering Service — FastAPI application.

Start with:
    uvicorn rag_service.main:app --reload

Endpoints:
    POST /answer  — query in, top-k snippets + generated answer out
    GET  /health  — corpus and guardrail status
"""

from __future__ import annotations
import time
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from rag_service import config
from rag_service.guardrails import TopicDenylist
from rag_service.models import AnswerRequest, AnswerResponse, HealthResponse
from rag_service.monitoring import log_request
from rag_service.retriever import TFIDFRetriever

# ---------------------------------------------------------------------------
# Application state (populated at startup via lifespan)
# ---------------------------------------------------------------------------

_retriever: TFIDFRetriever | None = None
_guardrail: TopicDenylist | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _retriever, _guardrail
    _retriever = TFIDFRetriever()
    _guardrail = TopicDenylist(config.RAG_DENYLIST_PATH)
    yield
    _retriever = None
    _guardrail = None


app = FastAPI(
    title="RAG Answering Service",
    description="Minimal retrieval-augmented answering endpoint with topic denylist guardrail.",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _generate_answer(query: str, snippets_text: str) -> str:
    """Single LLM call: snippets as context, query as user message, temp=0."""
    if not config.LLM_API_KEY:
        return "[LLM_API_KEY not configured — returning retrieved snippets only]"

    system_prompt = (
        "You are a helpful assistant. Answer the user's question using only the "
        "provided context. If the context does not contain enough information to "
        "answer, say so clearly. Do not add information beyond what is in the context."
    )
    messages = [
        {"role": "system", "content": f"{system_prompt}\n\nContext:\n{snippets_text}"},
        {"role": "user", "content": query},
    ]
    payload = {
        "model": config.LLM_MODEL,
        "messages": messages,
        "temperature": 0.0,
    }
    headers = {
        "Authorization": f"Bearer {config.LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    response = httpx.post(
        f"{config.LLM_BASE_URL}/chat/completions",
        json=payload,
        headers=headers,
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.post("/answer", response_model=AnswerResponse)
async def answer(request: AnswerRequest) -> AnswerResponse:
    if _retriever is None or _guardrail is None:
        return JSONResponse(status_code=503, content={"detail": "Service not initialized"})

    request_start = time.perf_counter()

    # Guardrail check
    guardrail_result = _guardrail.check_query(request.query)
    if not guardrail_result.allowed:
        log_request(
            query=request.query,
            latency_ms=(time.perf_counter() - request_start) * 1000,
            retrieval_ms=0.0,
            snippet_scores=[],
            answer_length=0,
            similarity_metric=request.similarity_metric or config.RAG_SIMILARITY_METRIC,
            hit_rate_threshold=config.RAG_HIT_RATE_THRESHOLD,
            blocked=True,
        )
        return JSONResponse(
            status_code=403,
            content={
                "detail": "Query blocked by content policy",
                "guardrail": guardrail_result.rule_triggered,
                "reason": guardrail_result.reason,
            },
        )

    k = request.k if request.k is not None else config.RAG_DEFAULT_K
    metric = request.similarity_metric or config.RAG_SIMILARITY_METRIC

    # Retrieval
    retrieval_start = time.perf_counter()
    snippets = _retriever.search(query=request.query, k=k, metric=metric)
    retrieval_ms = (time.perf_counter() - retrieval_start) * 1000

    # LLM generation
    snippets_text = "\n\n".join(
        f"[{s.id}] {s.title}\n{s.content}" for s in snippets
    )
    answer_text = "[No snippets retrieved]"
    generation_error = None
    if snippets:
        try:
            answer_text = _generate_answer(request.query, snippets_text)
        except Exception as e:
            generation_error = str(e)
            answer_text = "[LLM generation failed — see retrieved snippets]"

    total_ms = (time.perf_counter() - request_start) * 1000

    log_request(
        query=request.query,
        latency_ms=total_ms,
        retrieval_ms=retrieval_ms,
        snippet_scores=[s.score for s in snippets],
        answer_length=len(answer_text),
        similarity_metric=metric,
        hit_rate_threshold=config.RAG_HIT_RATE_THRESHOLD,
        blocked=False,
        error=generation_error,
    )

    if generation_error:
        return JSONResponse(
            status_code=503,
            content={
                "detail": "LLM service unavailable",
                "retrieval_completed": True,
                "snippets": [s.model_dump() for s in snippets],
            },
        )

    return AnswerResponse(
        query=request.query,
        snippets=snippets,
        answer=answer_text,
        similarity_metric=metric,
        latency_ms=round(total_ms, 2),
        retrieval_ms=round(retrieval_ms, 2),
    )


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        corpus_loaded=_retriever is not None,
        snippet_count=_retriever.snippet_count if _retriever else 0,
        guardrail_active=_guardrail is not None and _guardrail.active,
    )
