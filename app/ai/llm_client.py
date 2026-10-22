
"""Optional Gemini LLM access with rule-based fallback support."""

import json
import re
import time

import httpx

from app.core.config import settings

DEFAULT_MODEL = "gemini-3.8-flash"
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
MAX_RETRIES = 2
RETRY_BACKOFF_SECONDS = 0.2
REQUEST_TIMEOUT_SECONDS = 90


class LLMUnavailable(Exception):
    """AI is disabled or the call failed."""


def is_enabled() -> bool:
    return bool(settings.LLM_API_KEY.strip())


def complete(
    prompt: str,
    system: str = "",
    max_tokens: int = 3000,
) -> str:
    if not is_enabled():
        raise LLMUnavailable("LLM_API_KEY is not set")

    model = settings.LLM_MODEL.strip() or DEFAULT_MODEL
    url = API_URL.format(model=model)

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
        },
    }

    if system.strip():
        payload["systemInstruction"] = {
            "parts": [{"text": system}],
        }

    response = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = httpx.post(
                url,
                headers={
                    "x-goog-api-key": settings.LLM_API_KEY,
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            break
        except (httpx.TimeoutException, httpx.HTTPStatusError) as exc:
            status = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
            retryable = isinstance(exc, httpx.TimeoutException) or status in (429, 503)
            if retryable and attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * (2 ** attempt))
                continue
            if isinstance(exc, httpx.HTTPStatusError):
                try:
                    details = exc.response.json().get("error", {}).get("message", "")
                except (ValueError, AttributeError):
                    details = ""
                details = str(details)
                if settings.LLM_API_KEY:
                    details = details.replace(settings.LLM_API_KEY, "[REDACTED]")
                raise LLMUnavailable(
                    f"Gemini API HTTP {status}: {details[:300]}"
                ) from None
            raise LLMUnavailable(
                f"Gemini request failed ({type(exc).__name__})"
            ) from None
        except Exception as exc:
            raise LLMUnavailable(
                f"Gemini request failed ({type(exc).__name__})"
            ) from None

    try:
        # `response` is populated on successful status; exhausted errors raise above.
        data = response.json()

        candidates = data.get("candidates", [])
        if not candidates:
            feedback = data.get("promptFeedback") or {}
            reason = feedback.get("blockReason") if isinstance(feedback, dict) else None
            if reason:
                raise LLMUnavailable(f"Gemini blocked the prompt ({reason})")
            raise LLMUnavailable("Gemini returned no response candidates")

        candidate = candidates[0]
        if not isinstance(candidate, dict):
            raise LLMUnavailable("Gemini returned an invalid response candidate")
        finish = candidate.get("finishReason")
        if finish and finish != "STOP":
            message = candidate.get("finishMessage")
            detail = f": {message[:160]}" if isinstance(message, str) and message else ""
            raise LLMUnavailable(f"Gemini response finished with {finish}{detail}")

        content = candidate.get("content") or {}
        parts = content.get("parts", []) if isinstance(content, dict) else []
        result = "".join(
            part.get("text", "")
            for part in parts
            if isinstance(part.get("text"), str)
        )

        if not result.strip():
            raise LLMUnavailable("Gemini returned an empty response")

        return result

    except LLMUnavailable:
        raise
    except Exception as exc:
        raise LLMUnavailable(
            f"Gemini request failed ({type(exc).__name__})"
        ) from exc

def complete_json(
    prompt: str,
    system: str = "",
    max_tokens: int = 3000,
) -> dict:
    raw = complete(prompt, system, max_tokens)
    raw = raw.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", raw, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        raw = fenced.group(1).strip()

    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        raise LLMUnavailable("LLM did not return JSON")

    try:
        result = json.loads(raw[start : end + 1])
    except json.JSONDecodeError as exc:
        raise LLMUnavailable("LLM returned invalid JSON") from exc

    if not isinstance(result, dict):
        raise LLMUnavailable("LLM returned JSON that is not an object")

    return result
