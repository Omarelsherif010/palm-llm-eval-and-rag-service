import os
from dotenv import load_dotenv

load_dotenv()

LLM_API_KEY: str = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL: str = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL: str = os.environ.get("LLM_MODEL", "gpt-3.5-turbo")
RAG_DEFAULT_K: int = int(os.environ.get("RAG_DEFAULT_K", "5"))
RAG_SIMILARITY_METRIC: str = os.environ.get("RAG_SIMILARITY_METRIC", "cosine")
RAG_DENYLIST_PATH: str = os.environ.get("RAG_DENYLIST_PATH", "rag_service/denylist.txt")
RAG_HIT_RATE_THRESHOLD: float = float(os.environ.get("RAG_HIT_RATE_THRESHOLD", "0.1"))
