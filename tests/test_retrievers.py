from app.ai.retrievers import bns_retriever, constitution_retriever, ipc_retriever
from app.ai.vector_store import RetrievedDocument


def _mock_docs():
    return [
        RetrievedDocument(
            content="text",
            metadata={"source_type": "constitution", "reference_number": "21"},
            distance=0.1,
        )
    ]


def test_retrieve_constitution_uses_source_filter(monkeypatch):
    captured = {}

    monkeypatch.setattr(constitution_retriever, "embed_text", lambda _q: [0.1])

    def _query_documents(**kwargs):
        captured.update(kwargs)
        return _mock_docs()

    monkeypatch.setattr(constitution_retriever.vector_store, "query_documents", _query_documents)

    result = constitution_retriever.retrieve_constitution("article 21", top_k=3)

    assert len(result) == 1
    assert captured["source_type"] == "constitution"
    assert captured["n_results"] == 3


def test_retrieve_bns_uses_source_filter(monkeypatch):
    captured = {}

    monkeypatch.setattr(bns_retriever, "embed_text", lambda _q: [0.2])

    def _query_documents(**kwargs):
        captured.update(kwargs)
        return _mock_docs()

    monkeypatch.setattr(bns_retriever.vector_store, "query_documents", _query_documents)

    bns_retriever.retrieve_bns("bns", top_k=2)

    assert captured["source_type"] == "bns"


def test_retrieve_ipc_uses_source_filter(monkeypatch):
    captured = {}

    monkeypatch.setattr(ipc_retriever, "embed_text", lambda _q: [0.3])

    def _query_documents(**kwargs):
        captured.update(kwargs)
        return _mock_docs()

    monkeypatch.setattr(ipc_retriever.vector_store, "query_documents", _query_documents)

    ipc_retriever.retrieve_ipc("ipc", top_k=4)

    assert captured["source_type"] == "ipc"
