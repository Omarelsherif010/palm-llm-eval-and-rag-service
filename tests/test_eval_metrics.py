import pytest
from eval_harness.metrics import exact_match, pairwise_max_drift, regex_match, semantic_similarity


class TestExactMatch:
    def test_identical_strings(self):
        assert exact_match("Paris", "Paris") == 1.0

    def test_case_insensitive(self):
        assert exact_match("Paris", "paris") == 1.0

    def test_strips_whitespace(self):
        assert exact_match("Paris", "  Paris  ") == 1.0

    def test_different_strings(self):
        assert exact_match("Paris", "London") == 0.0

    def test_partial_match_is_zero(self):
        assert exact_match("Paris", "The capital is Paris") == 0.0


class TestRegexMatch:
    def test_matching_pattern(self):
        assert regex_match(r"(?i)\bparis\b", "The capital is Paris.") == 1.0

    def test_non_matching_pattern(self):
        assert regex_match(r"(?i)\bparis\b", "London is the capital.") == 0.0

    def test_empty_pattern(self):
        assert regex_match("", "any text") == 0.0

    def test_numeric_pattern(self):
        assert regex_match(r"150\s*(miles?)?", "150 miles") == 1.0

    def test_case_insensitive_flag(self):
        assert regex_match(r"(?i)paris", "PARIS") == 1.0


class TestSemanticSimilarity:
    def test_identical_texts_high_score(self):
        score = semantic_similarity("the cat sat on the mat", "the cat sat on the mat")
        assert score > 0.95

    def test_empty_text_returns_zero(self):
        assert semantic_similarity("", "some text") == 0.0
        assert semantic_similarity("some text", "") == 0.0

    def test_unrelated_texts_low_score(self):
        score = semantic_similarity("the capital of France is Paris", "machine learning embeddings")
        assert score < 0.3

    def test_paraphrases_higher_than_unrelated(self):
        para_score = semantic_similarity(
            "What is the capital of France?",
            "Name the capital city of France.",
        )
        unrelated_score = semantic_similarity(
            "What is the capital of France?",
            "How do neural networks learn?",
        )
        assert para_score > unrelated_score

    def test_returns_float_in_range(self):
        score = semantic_similarity("hello world", "greetings earth")
        assert 0.0 <= score <= 1.0


class TestPairwiseMaxDrift:
    def test_identical_texts_zero_drift(self):
        texts = ["Paris", "Paris", "Paris"]
        assert pairwise_max_drift(texts) < 0.05

    def test_single_text_zero_drift(self):
        assert pairwise_max_drift(["Paris"]) == 0.0

    def test_different_texts_nonzero_drift(self):
        texts = ["Python is most popular", "Java leads in enterprise", "JavaScript dominates the web"]
        drift = pairwise_max_drift(texts)
        assert drift > 0.0

    def test_drift_in_range(self):
        texts = ["foo", "bar", "baz"]
        drift = pairwise_max_drift(texts)
        assert 0.0 <= drift <= 1.0
