from app.ai.vector_store import ChromaVectorStore


class _FakeCollection:
    def __init__(self):
        self.calls = []

    def query(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "documents": [["doc-a", "doc-a-dup", "doc-b"]],
            "metadatas": [[
                {"source_type": "constitution", "reference_number": "21", "title": "Life"},
                {"source_type": "constitution", "reference_number": "21", "title": "Life"},
                {"source_type": "ipc", "reference_number": "302", "title": "Murder"},
            ]],
            "distances": [[0.1, 0.11, 0.2]],
        }


class _EmptyCollection:
    def query(self, **_kwargs):
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}


def test_query_documents_passes_filter_and_normalizes():
    store = ChromaVectorStore(db_path="x", collection_name="y")
    fake_collection = _FakeCollection()
    store._collection = fake_collection

    result = store.query_documents(query_embedding=[0.1, 0.2], n_results=2, source_type="constitution")

    assert len(result) == 1
    assert result[0].content == "doc-a"
    assert result[0].metadata["source_type"] == "constitution"
    assert fake_collection.calls[0]["where"] == {"source_type": "constitution"}


def test_query_documents_handles_empty_result():
    store = ChromaVectorStore(db_path="x", collection_name="y")
    store._collection = _EmptyCollection()

    result = store.query_documents(query_embedding=[0.1], n_results=5, source_type="ipc")

    assert result == []
