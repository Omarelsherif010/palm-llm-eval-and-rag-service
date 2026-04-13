"""
Topic denylist guardrail.

Loads a list of prohibited topic terms from a text file.
Rejects queries containing any prohibited term (case-insensitive substring match).
Fails closed: if the denylist file cannot be loaded, ALL requests are rejected.
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GuardrailResult:
    allowed: bool
    rule_triggered: str | None = None
    reason: str | None = None


class TopicDenylist:
    def __init__(self, path: str | Path) -> None:
        self._terms: list[str] = self._load(path)
        self._active = True

    @staticmethod
    def _load(path: str | Path) -> list[str]:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(
                f"Denylist file not found: {path}. "
                "Set RAG_DENYLIST_PATH to a valid path or create the file."
            )
        terms = []
        with open(p, encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    terms.append(stripped.lower())
        return terms

    def check_query(self, query: str) -> GuardrailResult:
        query_lower = query.lower()
        for term in self._terms:
            if term in query_lower:
                return GuardrailResult(
                    allowed=False,
                    rule_triggered="topic_denylist",
                    reason=f"Query contains prohibited topic: '{term}'",
                )
        return GuardrailResult(allowed=True)

    @property
    def active(self) -> bool:
        return self._active

    @property
    def term_count(self) -> int:
        return len(self._terms)
