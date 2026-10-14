import pytest

from bee_issues import llm
from bee_issues.config import Settings
from bee_issues.llm import LLMError


class FakeResponse:
    def __init__(self, status_code, data):
        self.status_code = status_code
        self._data = data
        self.text = str(data)

    def json(self):
        return self._data


def test_deepseek_uses_chat_completions_in_json_mode(monkeypatch):
    calls = []

    def fake_post(url, headers=None, json=None, timeout=None):
        calls.append({"url": url, "headers": headers, "json": json})
        return FakeResponse(200, {"choices": [{"message": {"content": '{"issues": []}'}}]})

    monkeypatch.setattr(llm.requests, "post", fake_post)
    settings = Settings(llm_provider="deepseek", deepseek_api_key="key")
    assert llm.complete("sys", "user", settings) == '{"issues": []}'
    call = calls[0]
    assert call["url"] == "https://api.deepseek.com/chat/completions"
    assert call["headers"]["Authorization"] == "Bearer key"
    assert call["json"]["model"] == "deepseek-chat"
    assert call["json"]["response_format"] == {"type": "json_object"}
    assert call["json"]["messages"][0] == {"role": "system", "content": "sys"}
    assert llm.model_name(settings) == "deepseek-chat"


def test_deepseek_errors(monkeypatch):
    with pytest.raises(LLMError, match="DEEPSEEK_API_KEY"):
        llm.complete("s", "u", Settings(llm_provider="deepseek"))
    monkeypatch.setattr(llm.requests, "post", lambda *a, **k: FakeResponse(401, {"error": "bad key"}))
    with pytest.raises(LLMError, match="401"):
        llm.complete("s", "u", Settings(llm_provider="deepseek", deepseek_api_key="k"))


def test_retries_network_errors_and_server_errors(monkeypatch):
    replies = [
        llm.requests.ConnectionError("reset"),
        FakeResponse(503, {"error": "busy"}),
        FakeResponse(200, {"choices": [{"message": {"content": "ok"}}]}),
    ]

    def fake_post(url, **kwargs):
        reply = replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply

    monkeypatch.setattr(llm.requests, "post", fake_post)
    monkeypatch.setattr(llm.time, "sleep", lambda seconds: None)
    assert llm.complete("s", "u", Settings(llm_provider="deepseek", deepseek_api_key="k")) == "ok"


def test_network_error_after_retries_is_llm_error(monkeypatch):
    def fake_post(url, **kwargs):
        raise llm.requests.Timeout("slow")

    monkeypatch.setattr(llm.requests, "post", fake_post)
    monkeypatch.setattr(llm.time, "sleep", lambda seconds: None)
    with pytest.raises(LLMError, match="Network error"):
        llm.complete("s", "u", Settings(llm_provider="deepseek", deepseek_api_key="k"))
