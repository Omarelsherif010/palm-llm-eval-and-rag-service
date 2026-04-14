import os
import logging
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

LLM_API_KEY: str = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL: str = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL: str = os.environ.get("LLM_MODEL", "gpt-5.4-nano-2026-03-17")
RAG_SIMILARITY_METRIC: str = os.environ.get("RAG_SIMILARITY_METRIC", "cosine")
RAG_DENYLIST_PATH: str = os.environ.get("RAG_DENYLIST_PATH", "rag_service/denylist.txt")


def _safe_int(key: str, default: int) -> int:
    raw = os.environ.get(key, "")
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        log.warning("Invalid %s=%r, using default %d", key, raw, default)
        return default


def _safe_float(key: str, default: float) -> float:
    raw = os.environ.get(key, "")
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        log.warning("Invalid %s=%r, using default %f", key, raw, default)
        return default


RAG_DEFAULT_K: int = _safe_int("RAG_DEFAULT_K", 5)
RAG_HIT_RATE_THRESHOLD: float = _safe_float("RAG_HIT_RATE_THRESHOLD", 0.1)
