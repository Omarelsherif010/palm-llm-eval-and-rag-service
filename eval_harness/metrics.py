"""
Scoring functions for the eval harness.

Each function returns a float in [0.0, 1.0]:
  - 1.0 = perfect match
  - 0.0 = no match
"""

import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def exact_match(expected: str, actual: str) -> float:
    """Case-insensitive exact string match after stripping whitespace."""
    return 1.0 if expected.strip().lower() == actual.strip().lower() else 0.0


def regex_match(pattern: str, actual: str) -> float:
    """Return 1.0 if actual matches the regex pattern, else 0.0."""
    if not pattern:
        return 0.0
    try:
        return 1.0 if re.search(pattern, actual, re.IGNORECASE) else 0.0
    except re.error:
        return 0.0


def semantic_similarity(text_a: str, text_b: str) -> float:
    """
    TF-IDF cosine similarity between two texts.
    Returns value in [0.0, 1.0]. Identical texts → ~1.0.
    Uses sklearn TfidfVectorizer; no external API or model download needed.
    """
    if not text_a or not text_b:
        return 0.0
    try:
        vectorizer = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
        tfidf = vectorizer.fit_transform([text_a, text_b])
        score = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
        return float(score)
    except Exception:
        return 0.0


def pairwise_max_drift(texts: list[str]) -> float:
    """
    Compute max pairwise semantic distance within a group of texts.
    Returns 0.0 if all texts are identical, up to 1.0 for maximally different.
    Used for perturbation groups to quantify drift magnitude.
    """
    if len(texts) < 2:
        return 0.0
    try:
        vectorizer = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
        tfidf = vectorizer.fit_transform(texts)
        max_dist = 0.0
        n = len(texts)
        for i in range(n):
            for j in range(i + 1, n):
                sim = cosine_similarity(tfidf[i : i + 1], tfidf[j : j + 1])[0][0]
                dist = 1.0 - float(sim)
                if dist > max_dist:
                    max_dist = dist
        return max_dist
    except Exception:
        return 0.0
