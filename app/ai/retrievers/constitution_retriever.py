from typing import List

from app.ai.embeddings import embed_text
from app.ai.vector_store import RetrievedDocument, vector_store


def retrieve_constitution(query: str, top_k: int = 5) -> List[RetrievedDocument]:
    if not isinstance(query, str):
        raise ValueError("Query must be a string.")
    if not query.strip():
        raise ValueError("Query cannot be empty.")

    query_embedding = embed_text(query)
    return vector_store.query_documents(
        query_embedding=query_embedding,
        n_results=top_k,
        source_type="constitution",
    )


class ConstitutionRetriever:
    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievedDocument]:
        return retrieve_constitution(query=query, top_k=top_k)
