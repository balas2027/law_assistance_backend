from typing import List

class EmbeddingsClient:
    def get_embedding(self, text: str) -> List[float]:
        # Placeholder for embeddings generation (e.g. 1536 dimensions)
        return [0.0] * 1536

embeddings_client = EmbeddingsClient()
