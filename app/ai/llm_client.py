"""OWNER: M3 - thin wrapper around the LLM API. AI is OPTIONAL; core app must work without it."""
from app.core.config import settings


def complete(prompt: str) -> str:
    raise NotImplementedError("TODO(M3): call LLM using settings.LLM_API_KEY")
