from typing import List, Dict, Any

class VectorStore:
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        pass

    def similarity_search(self, query_embedding: List[float], k: int = 4) -> List[Dict[str, Any]]:
        return []

vector_store = VectorStore()
