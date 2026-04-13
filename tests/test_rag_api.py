import pytest
from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

from rag_service.main import app
from rag_service.guardrails import TopicDenylist
from rag_service.retriever import TFIDFRetriever
import rag_service.main as main_module


@pytest.fixture
def client():
    # Initialize state directly (bypass lifespan for testing)
    main_module._retriever = TFIDFRetriever()
    main_module._guardrail = TopicDenylist("rag_service/denylist.txt")
    main_module._http_client = httpx.AsyncClient(timeout=60.0)
    with TestClient(app) as c:
        yield c
    main_module._retriever = None
    main_module._guardrail = None
    main_module._http_client = None


class TestAnswerEndpoint:
    def test_valid_query_returns_200(self, client):
        mock = AsyncMock(return_value="A generated answer.")
        with patch("rag_service.main._generate_answer", mock):
            response = client.post("/answer", json={"query": "What is RAG?"})
        assert response.status_code == 200
        data = response.json()
        assert "snippets" in data
        assert "answer" in data
        assert "latency_ms" in data
        assert "retrieval_ms" in data
        assert data["query"] == "What is RAG?"

    def test_snippets_have_required_fields(self, client):
        mock = AsyncMock(return_value="Answer.")
        with patch("rag_service.main._generate_answer", mock):
            response = client.post("/answer", json={"query": "What is TF-IDF?"})
        assert response.status_code == 200
        for snippet in response.json()["snippets"]:
            assert "id" in snippet
            assert "title" in snippet
            assert "content" in snippet
            assert "score" in snippet

    def test_denied_topic_returns_403(self, client):
        response = client.post("/answer", json={"query": "How do I hack a system?"})
        assert response.status_code == 403
        data = response.json()
        assert data["guardrail"] == "topic_denylist"
        assert "hack" in data["reason"]

    def test_empty_query_returns_422(self, client):
        response = client.post("/answer", json={"query": ""})
        assert response.status_code == 422

    def test_k_parameter_controls_snippet_count(self, client):
        mock = AsyncMock(return_value="Answer.")
        with patch("rag_service.main._generate_answer", mock):
            response = client.post("/answer", json={"query": "embeddings", "k": 3})
        assert response.status_code == 200
        assert len(response.json()["snippets"]) == 3

    def test_similarity_metric_echoed_in_response(self, client):
        mock = AsyncMock(return_value="Answer.")
        with patch("rag_service.main._generate_answer", mock):
            response = client.post(
                "/answer",
                json={"query": "transformers", "similarity_metric": "dot_product"},
            )
        assert response.status_code == 200
        assert response.json()["similarity_metric"] == "dot_product"

    def test_llm_failure_returns_503_with_snippets(self, client):
        mock = AsyncMock(side_effect=httpx.HTTPStatusError(
            "500 Server Error", request=httpx.Request("POST", "http://test"), response=httpx.Response(500)
        ))
        with patch("rag_service.main._generate_answer", mock):
            response = client.post("/answer", json={"query": "What is RAG?"})
        assert response.status_code == 503
        data = response.json()
        assert data["retrieval_completed"] is True
        assert len(data["snippets"]) > 0


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["corpus_loaded"] is True
        assert data["snippet_count"] > 0
        assert data["guardrail_active"] is True
