from dataclasses import dataclass
import logging
import os
from typing import Any, Dict, List, Optional

import chromadb

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = "combined_db"
DEFAULT_COLLECTION_NAME = "legal_assistant"


class VectorStoreError(RuntimeError):
    """Raised when vector store operations fail."""


@dataclass
class RetrievedDocument:
    content: str
    metadata: Dict[str, Any]
    distance: Optional[float] = None


class ChromaVectorStore:
    def __init__(self, db_path: Optional[str] = None, collection_name: Optional[str] = None) -> None:
        self.db_path = db_path or os.getenv("CHROMA_DB_PATH", DEFAULT_DB_PATH)
        self.collection_name = collection_name or os.getenv("CHROMA_COLLECTION_NAME", DEFAULT_COLLECTION_NAME)
        self._client: Optional[Any] = None
        self._collection: Optional[Any] = None

    def _get_collection(self) -> Any:
        if self._collection is None:
            try:
                self._client = chromadb.PersistentClient(path=self.db_path)
                self._collection = self._client.get_or_create_collection(self.collection_name)
            except Exception as exc:
                logger.exception("Failed to initialize ChromaDB collection.")
                return None
        return self._collection

    @staticmethod
    def _normalize_item(document: str, metadata: Dict[str, Any], distance: Optional[float]) -> RetrievedDocument:
        normalized_metadata = dict(metadata or {})
        if "source_type" not in normalized_metadata and "source" in normalized_metadata:
            normalized_metadata["source_type"] = normalized_metadata.get("source")

        return RetrievedDocument(
            content=document,
            metadata=normalized_metadata,
            distance=distance,
        )

    def query_documents(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        source_type: Optional[str] = None,
    ) -> List[RetrievedDocument]:
        if not query_embedding:
            raise ValueError("query_embedding cannot be empty.")
        if n_results < 1:
            raise ValueError("n_results must be at least 1.")

        collection = self._get_collection()
        if collection is None or collection.count() == 0:
            return []

        where: Optional[Dict[str, Any]] = None
        if source_type:
            where = {"source_type": source_type}

        try:
            raw_results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results * 2,
                where=where,
            )
        except ValueError:
            raise
        except Exception as exc:
            logger.exception("Vector similarity query failed.")
            return []


        documents = (raw_results.get("documents") or [[]])[0]
        metadatas = (raw_results.get("metadatas") or [[]])[0]
        distances = (raw_results.get("distances") or [[]])[0]

        if source_type and not documents:
            try:
                fallback_results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results * 2,
                )
                documents = (fallback_results.get("documents") or [[]])[0]
                metadatas = (fallback_results.get("metadatas") or [[]])[0]
                distances = (fallback_results.get("distances") or [[]])[0]
            except Exception:
                pass

        normalized: List[RetrievedDocument] = []
        seen_sections: set[tuple[str, str]] = set()

        for document, metadata, distance in zip(documents, metadatas, distances):
            normalized_doc = self._normalize_item(document=document, metadata=metadata or {}, distance=distance)
            if source_type and str(normalized_doc.metadata.get("source_type", "")).lower() != source_type:
                continue
            source = str(normalized_doc.metadata.get("source_type", ""))
            reference = str(normalized_doc.metadata.get("reference_number") or normalized_doc.metadata.get("section_number") or normalized_doc.metadata.get("article_number") or normalized_doc.metadata.get("chunk_id") or "")
            dedupe_key = (source, reference)

            if reference and dedupe_key in seen_sections:
                continue

            if reference:
                seen_sections.add(dedupe_key)

            normalized.append(normalized_doc)
            if len(normalized) >= n_results:
                break

        return normalized


vector_store = ChromaVectorStore()
