import os
from dotenv import load_dotenv

load_dotenv()

LLM_API_KEY: str = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL: str = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL: str = os.environ.get("LLM_MODEL", "gpt-3.5-turbo")
