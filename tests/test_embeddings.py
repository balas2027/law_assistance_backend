import pytest

from app.ai.embeddings import EmbeddingsService


class _FakeModel:
    def encode(self, texts):
        assert texts == ["hello"]
        return [[0.1, 0.2, 0.3]]


def test_embed_text_valid(monkeypatch):
    service = EmbeddingsService(model_name="dummy")
    monkeypatch.setattr(service, "_get_model", lambda: _FakeModel())

    vector = service.embed_text("hello")

    assert vector == [0.1, 0.2, 0.3]


def test_embed_text_empty_input_rejected():
    service = EmbeddingsService(model_name="dummy")

    with pytest.raises(ValueError):
        service.embed_text("   ")


def test_model_is_initialized_once(monkeypatch):
    calls = {"count": 0}

    class _TrackedModel:
        def encode(self, texts):
            return [[0.9, 0.8]]

    def _factory(_model_name):
        calls["count"] += 1
        return _TrackedModel()

    monkeypatch.setattr("app.ai.embeddings.SentenceTransformer", _factory)
    service = EmbeddingsService(model_name="dummy")

    service.embed_text("hello")
    service.embed_text("hello")

    assert calls["count"] == 1
