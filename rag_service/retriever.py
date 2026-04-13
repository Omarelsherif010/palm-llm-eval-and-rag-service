"""
TF-IDF retriever with cosine and dot-product similarity options.

Loads the text corpus at startup and builds an in-memory TF-IDF index.
Supports two similarity metrics:
  - cosine:      sklearn cosine_similarity (magnitude-normalized, length-invariant)
  - dot_product: raw numpy dot product on TF-IDF vectors (magnitude-sensitive)
"""

from __future__ import annotations
import json
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from rag_service.models import RetrievedSnippet

CORPUS_PATH = Path(__file__).parent / "corpus" / "snippets.json"


class TFIDFRetriever:
    def __init__(self, corpus_path: str | Path = CORPUS_PATH) -> None:
        self._snippets: list[dict] = self._load_corpus(corpus_path)
        # norm=None disables L2 normalization so cosine and dot-product
        # produce meaningfully different rankings. With the default norm='l2',
        # all vectors have unit length and both metrics are equivalent.
        self._vectorizer = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b", norm=None)
        corpus_texts = [s["content"] for s in self._snippets]
        self._tfidf_matrix = self._vectorizer.fit_transform(corpus_texts)

    @staticmethod
    def _load_corpus(path: str | Path) -> list[dict]:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Corpus file not found: {path}")
        with open(p, encoding="utf-8") as f:
            snippets = json.load(f)
        if not snippets:
            raise ValueError("Corpus is empty. Add snippets to the corpus file.")
        return snippets

    def search(
        self,
        query: str,
        k: int,
        metric: str = "cosine",
    ) -> list[RetrievedSnippet]:
        """Return top-k snippets sorted by similarity score (descending)."""
        if not query or not query.strip():
            return []

        k = min(k, len(self._snippets))
        query_vec = self._vectorizer.transform([query])

        if metric == "cosine":
            scores = cosine_similarity(query_vec, self._tfidf_matrix)[0]
        elif metric == "dot_product":
            scores = np.asarray(query_vec.dot(self._tfidf_matrix.T).todense())[0]
        else:
            raise ValueError(f"Unknown metric: {metric}. Use 'cosine' or 'dot_product'.")

        top_k_indices = np.argsort(scores)[::-1][:k]

        results = []
        for idx in top_k_indices:
            s = self._snippets[idx]
            results.append(
                RetrievedSnippet(
                    id=s["id"],
                    title=s["title"],
                    content=s["content"],
                    score=round(float(scores[idx]), 6),
                )
            )
        return results

    @property
    def snippet_count(self) -> int:
        return len(self._snippets)
