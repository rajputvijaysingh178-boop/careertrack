
from unittest.mock import Mock, call, patch

import pytest

from app.ai import llm_client


@patch("app.ai.llm_client.httpx.post")
def test_complete_sends_gemini_request(mock_post, monkeypatch):
    monkeypatch.setattr(llm_client.settings, "LLM_API_KEY", "test-key")
    monkeypatch.setattr(llm_client.settings, "LLM_MODEL", "gemini-3.8-flash")

    response = Mock()
    response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Hello from Gemini"}]
                }
            }
        ]
    }
    response.raise_for_status.return_value = None
    mock_post.return_value = response

    result = llm_client.complete(
        "Say hello",
        system="Be concise",
        max_tokens=100,
    )

    assert result == "Hello from Gemini"

    args, kwargs = mock_post.call_args
    assert "gemini-3.8-flash:generateContent" in args[0]
    assert kwargs["headers"]["x-goog-api-key"] == "test-key"
    assert kwargs["json"]["contents"][0]["parts"][0]["text"] == "Say hello"
    assert kwargs["json"]["systemInstruction"]["parts"][0]["text"] == "Be concise"
    assert kwargs["json"]["generationConfig"]["maxOutputTokens"] == 100


@patch("app.ai.llm_client.httpx.post")
def test_complete_json_parses_response(mock_post, monkeypatch):
    monkeypatch.setattr(llm_client.settings, "LLM_API_KEY", "test-key")

    response = Mock()
    response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": '```json\n{"score": 90, "skills": ["Python"]}\n```'}
                    ]
                }
            }
        ]
    }
    response.raise_for_status.return_value = None
    mock_post.return_value = response

    result = llm_client.complete_json("Return JSON")

    assert result == {"score": 90, "skills": ["Python"]}


@patch("app.ai.llm_client.httpx.post")
def test_complete_rejects_empty_candidates(mock_post, monkeypatch):
    monkeypatch.setattr(llm_client.settings, "LLM_API_KEY", "test-key")

    response = Mock()
    response.json.return_value = {"candidates": []}
    response.raise_for_status.return_value = None
    mock_post.return_value = response

    with pytest.raises(llm_client.LLMUnavailable, match="no response candidates"):
        llm_client.complete("Say hello")


@patch("app.ai.llm_client.httpx.post")
def test_complete_rejects_empty_text(mock_post, monkeypatch):
    monkeypatch.setattr(llm_client.settings, "LLM_API_KEY", "test-key")
    response = Mock()
    response.json.return_value = {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": "  "}]}}]}
    response.raise_for_status.return_value = None
    mock_post.return_value = response
    with pytest.raises(llm_client.LLMUnavailable, match="empty response"):
        llm_client.complete("Say hello")


@patch("app.ai.llm_client.httpx.post")
def test_complete_reports_prompt_block(mock_post, monkeypatch):
    monkeypatch.setattr(llm_client.settings, "LLM_API_KEY", "test-key")
    response = Mock()
    response.json.return_value = {"candidates": [], "promptFeedback": {"blockReason": "SAFETY"}}
    response.raise_for_status.return_value = None
    mock_post.return_value = response
    with pytest.raises(llm_client.LLMUnavailable, match=r"blocked the prompt \(SAFETY\)"):
        llm_client.complete("blocked")


@patch("app.ai.llm_client.httpx.post")
def test_complete_rejects_truncated_output(mock_post, monkeypatch):
    monkeypatch.setattr(llm_client.settings, "LLM_API_KEY", "test-key")
    response = Mock()
    response.json.return_value = {"candidates": [{"finishReason": "MAX_TOKENS"}]}
    response.raise_for_status.return_value = None
    mock_post.return_value = response
    with pytest.raises(llm_client.LLMUnavailable, match="finished with MAX_TOKENS"):
        llm_client.complete("truncated")


@patch("app.ai.llm_client.httpx.post")
def test_complete_http_error_is_useful_and_redacts_key(mock_post, monkeypatch):
    monkeypatch.setattr(llm_client.settings, "LLM_API_KEY", "secret-test-key")
    response = Mock()
    response.status_code = 429
    response.json.return_value = {"error": {"message": "Quota exceeded for secret-test-key"}}
    error = llm_client.httpx.HTTPStatusError("failed", request=Mock(), response=response)
    response.raise_for_status.side_effect = error
    mock_post.return_value = response
    with pytest.raises(llm_client.LLMUnavailable) as exc_info:
        llm_client.complete("quota")
    assert "HTTP 429" in str(exc_info.value)
    assert "Quota exceeded" in str(exc_info.value)
    assert "secret-test-key" not in str(exc_info.value)


@patch("app.ai.llm_client.complete")
def test_complete_json_rejects_malformed_json(mock_complete):
    mock_complete.return_value = '{"skills": [}'
    with pytest.raises(llm_client.LLMUnavailable, match="invalid JSON"):
        llm_client.complete_json("Return JSON")


def test_complete_requires_api_key(monkeypatch):
    monkeypatch.setattr(llm_client.settings, "LLM_API_KEY", "")

    with pytest.raises(llm_client.LLMUnavailable, match="API_KEY is not set"):
        llm_client.complete("Say hello")


@patch("app.ai.llm_client.httpx.post")
def test_complete_hides_request_error_details(mock_post, monkeypatch):
    monkeypatch.setattr(llm_client.settings, "LLM_API_KEY", "test-key")
    mock_post.side_effect = RuntimeError("example failure")

    with pytest.raises(llm_client.LLMUnavailable) as exc_info:
        llm_client.complete("Say hello")

    assert "RuntimeError" in str(exc_info.value)
    assert "test-key" not in str(exc_info.value)


def _http_error(status_code, message):
    response = Mock()
    response.status_code = status_code
    response.json.return_value = {"error": {"message": message}}
    return llm_client.httpx.HTTPStatusError(
        "mock status", request=Mock(), response=response
    )


@pytest.mark.parametrize("status_code", [429, 503])
def test_complete_retries_transient_http_status_then_succeeds(status_code, monkeypatch):
    monkeypatch.setattr(llm_client.settings, "LLM_API_KEY", "test-key")
    response = Mock()
    response.json.return_value = {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}
    response.raise_for_status.return_value = None
    with patch("app.ai.llm_client.httpx.post", side_effect=[_http_error(status_code, "temporary"), response]) as post, \
            patch("app.ai.llm_client.time.sleep") as sleep:
        assert llm_client.complete("hello") == "ok"
    assert post.call_count == 2
    sleep.assert_called_once_with(llm_client.RETRY_BACKOFF_SECONDS)


def test_complete_retries_timeout_twice_then_succeeds(monkeypatch):
    monkeypatch.setattr(llm_client.settings, "LLM_API_KEY", "test-key")
    response = Mock()
    response.json.return_value = {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}
    response.raise_for_status.return_value = None
    timeout = llm_client.httpx.ReadTimeout("temporary read timeout")
    with patch("app.ai.llm_client.httpx.post", side_effect=[timeout, timeout, response]) as post, \
            patch("app.ai.llm_client.time.sleep") as sleep:
        assert llm_client.complete("hello") == "ok"
    assert post.call_count == 3
    assert sleep.call_args_list == [
        call(llm_client.RETRY_BACKOFF_SECONDS),
        call(llm_client.RETRY_BACKOFF_SECONDS * 2),
    ]


def test_complete_stops_after_two_retries(monkeypatch):
    monkeypatch.setattr(llm_client.settings, "LLM_API_KEY", "test-key")
    with patch("app.ai.llm_client.httpx.post", side_effect=llm_client.httpx.ReadTimeout("timeout")) as post, \
            patch("app.ai.llm_client.time.sleep") as sleep:
        with pytest.raises(llm_client.LLMUnavailable, match="ReadTimeout"):
            llm_client.complete("hello")
    assert post.call_count == 3
    assert sleep.call_count == 2
