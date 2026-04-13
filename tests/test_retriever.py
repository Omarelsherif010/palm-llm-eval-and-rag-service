import pytest
from rag_service.retriever import TFIDFRetriever


@pytest.fixture
def retriever():
    return TFIDFRetriever()


class TestRetrieverSearch:
    def test_returns_correct_k(self, retriever):
        results = retriever.search("What is RAG?", k=3, metric="cosine")
        assert len(results) == 3

    def test_returns_fewer_than_k_if_corpus_smaller(self, retriever):
        results = retriever.search("RAG embeddings", k=50, metric="cosine")
        assert len(results) == retriever.snippet_count

    def test_scores_between_zero_and_one_cosine(self, retriever):
        results = retriever.search("retrieval augmented generation", k=5, metric="cosine")
        for r in results:
            assert 0.0 <= r.score <= 1.0

    def test_results_sorted_descending(self, retriever):
        results = retriever.search("TF-IDF cosine similarity", k=5, metric="cosine")
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_cosine_and_dot_product_may_differ(self, retriever):
        cosine = retriever.search("temperature sampling LLM", k=3, metric="cosine")
        dot = retriever.search("temperature sampling LLM", k=3, metric="dot_product")
        cosine_ids = [r.id for r in cosine]
        dot_ids = [r.id for r in dot]
        # They may agree on some results but are not guaranteed to be identical
        # This test simply verifies both run without error and return results
        assert len(cosine_ids) == 3
        assert len(dot_ids) == 3

    def test_empty_query_returns_empty(self, retriever):
        results = retriever.search("", k=5, metric="cosine")
        assert results == []

    def test_invalid_metric_raises(self, retriever):
        with pytest.raises(ValueError, match="Unknown metric"):
            retriever.search("test query", k=3, metric="euclidean")

    def test_result_has_required_fields(self, retriever):
        results = retriever.search("hallucination in LLMs", k=1, metric="cosine")
        assert len(results) == 1
        r = results[0]
        assert r.id
        assert r.title
        assert r.content
        assert isinstance(r.score, float)
