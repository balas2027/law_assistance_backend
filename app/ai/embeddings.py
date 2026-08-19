import logging
import os
from typing import List, Optional

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"


class EmbeddingServiceError(RuntimeError):
    """Raised when the embedding service fails to initialize or infer."""


class EmbeddingsService:
    """Lazy-loading singleton wrapper around SentenceTransformer embeddings."""

    def __init__(self, model_name: Optional[str] = None) -> None:
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL_NAME", DEFAULT_EMBEDDING_MODEL)
        self._model: Optional[SentenceTransformer] = None

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            try:
                self._model = SentenceTransformer(self.model_name)
            except Exception as exc:
                logger.exception("Failed to load embedding model.")
                raise EmbeddingServiceError("Embedding model initialization failed.") from exc
        return self._model

    def embed_text(self, text: str) -> List[float]:
        if not isinstance(text, str):
            raise ValueError("Query must be a string.")
        if not text.strip():
            raise ValueError("Query cannot be empty.")

        try:
            vector = self._get_model().encode([text])[0]
            return vector.tolist()
        except ValueError:
            raise
        except Exception as exc:
            logger.exception("Embedding generation failed.")
            raise EmbeddingServiceError("Embedding generation failed.") from exc


embeddings_service = EmbeddingsService()


def embed_text(text: str) -> List[float]:
    """Generate a single embedding vector for the supplied text."""
    return embeddings_service.embed_text(text)
