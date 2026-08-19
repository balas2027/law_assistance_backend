from app.ai.vector_store import RetrievedDocument
import app.services.chat_service as chat_service_module


def test_get_chats(client) -> None:
    response = client.get("/api/v1/chat")
    assert response.status_code == 200


def test_post_chat_valid_request(client, monkeypatch) -> None:
    def _mock_process_chat_request(**_kwargs):
        return chat_service_module.ChatResult(
            answer="Article 21 protects life and liberty.",
            source_type="constitution",
            sources=[
                RetrievedDocument(
                    content="Article 21 text",
                    metadata={"source_type": "constitution", "reference_number": "21"},
                    distance=0.1,
                )
            ],
        )

    monkeypatch.setattr(chat_service_module.chat_service, "process_chat_request", _mock_process_chat_request)

    response = client.post(
        "/api/v1/chat",
        json={"query": "Explain Article 21", "source_type": "constitution", "top_k": 5},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"]
    assert body["source_type"] == "constitution"
    assert len(body["sources"]) == 1


def test_post_chat_empty_query_rejected(client) -> None:
    response = client.post("/api/v1/chat", json={"query": "   "})
    assert response.status_code == 400


def test_post_chat_invalid_source_type(client) -> None:
    response = client.post("/api/v1/chat", json={"query": "test", "source_type": "invalid"})
    assert response.status_code == 400
    assert "Unsupported source_type" in response.json()["detail"]


def test_post_chat_no_results(client, monkeypatch) -> None:
    def _mock_process_chat_request(**_kwargs):
        return chat_service_module.ChatResult(answer="No direct provision found.", source_type=None, sources=[])

    monkeypatch.setattr(chat_service_module.chat_service, "process_chat_request", _mock_process_chat_request)

    response = client.post("/api/v1/chat", json={"query": "unknown question"})
    assert response.status_code == 200
    assert response.json()["sources"] == []


def test_post_chat_vector_store_failure(client, monkeypatch) -> None:
    def _mock_process_chat_request(**_kwargs):
        raise chat_service_module.RetrievalError("Vector store retrieval failed.")

    monkeypatch.setattr(chat_service_module.chat_service, "process_chat_request", _mock_process_chat_request)

    response = client.post("/api/v1/chat", json={"query": "test"})
    assert response.status_code == 503


def test_post_chat_llm_failure(client, monkeypatch) -> None:
    def _mock_process_chat_request(**_kwargs):
        raise chat_service_module.GenerationError("LLM generation failed.")

    monkeypatch.setattr(chat_service_module.chat_service, "process_chat_request", _mock_process_chat_request)

    response = client.post("/api/v1/chat", json={"query": "test"})
    assert response.status_code == 502
