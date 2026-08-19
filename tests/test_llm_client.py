import pytest

from app.ai.llm_client import GroqLLMClient, LLMServiceError


def test_generate_answer_builds_expected_payload(monkeypatch):
    client = GroqLLMClient(api_key="x", model="m")
    captured_messages = {}

    def _fake_create_chat_completion(messages):
        captured_messages["messages"] = messages
        return {"choices": [{"message": {"content": "generated"}}]}

    monkeypatch.setattr(client, "_create_chat_completion", _fake_create_chat_completion)

    answer = client.generate_answer(
        user_query="What is Article 21?",
        context="context block",
        system_prompt="system prompt",
    )

    assert answer == "generated"
    assert captured_messages["messages"][0]["role"] == "system"
    assert "context block" in captured_messages["messages"][1]["content"]


def test_generate_answer_raises_service_error_on_provider_failure(monkeypatch):
    client = GroqLLMClient(api_key="x")

    def _broken_create_chat_completion(messages):
        raise LLMServiceError("LLM request failed.")

    monkeypatch.setattr(client, "_create_chat_completion", _broken_create_chat_completion)

    with pytest.raises(LLMServiceError):
        client.generate_answer("q", "ctx", "sys")
