"""OWNER: M3 - OPTIONAL LLM access. The core app must keep working when this is disabled.

Enable by setting LLM_API_KEY (and optionally LLM_MODEL) in .env. Uses the Anthropic Messages API
through httpx. Any failure raises LLMUnavailable so callers can fall back to the rule-based engine.
"""
import json
import re

from app.core.config import settings

API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-5-5"


class LLMUnavailable(Exception):
    """AI is disabled or the call failed."""


def is_enabled() -> bool:
    return bool(settings.LLM_API_KEY)


def complete(prompt: str, system: str = "", max_tokens: int = 1500) -> str:
    if not is_enabled():
        raise LLMUnavailable("LLM_API_KEY is not set")
    try:
        import httpx
        resp = httpx.post(
            API_URL,
            headers={"x-api-key": settings.LLM_API_KEY, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": settings.LLM_MODEL or DEFAULT_MODEL, "max_tokens": max_tokens,
                  "system": system, "messages": [{"role": "user", "content": prompt}]},
            timeout=60,
        )
        resp.raise_for_status()
        return "".join(b.get("text", "") for b in resp.json().get("content", []) if b.get("type") == "text")
    except Exception as exc:  # network, auth, quota, parsing ...
        raise LLMUnavailable(str(exc)) from exc


def complete_json(prompt: str, system: str = "", max_tokens: int = 1500) -> dict:
    raw = complete(prompt, system, max_tokens)
    raw = re.sub(r"```(?:json)?", "", raw)
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        raise LLMUnavailable("LLM did not return JSON")
    try:
        return json.loads(raw[start:end + 1])
    except json.JSONDecodeError as exc:
        raise LLMUnavailable("LLM returned invalid JSON") from exc
