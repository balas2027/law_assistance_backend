from dataclasses import dataclass
import logging
from typing import Callable, Dict, List, Optional, Protocol

from app.ai.llm_client import LLMServiceError, llm_client
from app.ai.prompts.chat_prompt import SYSTEM_PROMPT, format_retrieved_context
from app.ai.embeddings import embed_text
from app.ai.retrievers.bns_retriever import BNSRetriever
from app.ai.retrievers.constitution_retriever import ConstitutionRetriever
from app.ai.retrievers.ipc_retriever import IPCRetriever
from app.ai.vector_store import RetrievedDocument, VectorStoreError, vector_store

logger = logging.getLogger(__name__)

SUPPORTED_SOURCE_TYPES = {"constitution", "bns", "ipc"}


class RetrieverProtocol(Protocol):
    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievedDocument]:
        ...


@dataclass
class ChatResult:
    answer: str
    source_type: Optional[str]
    sources: List[RetrievedDocument]


class ChatServiceError(RuntimeError):
    pass


class UnsupportedSourceTypeError(ChatServiceError):
    pass


class RetrievalError(ChatServiceError):
    pass


class GenerationError(ChatServiceError):
    pass


class ChatService:
    def __init__(
        self,
        retrievers: Optional[Dict[str, RetrieverProtocol]] = None,
        llm_generate_fn: Optional[Callable[[str, str, str], str]] = None,
    ) -> None:
        self.retrievers = retrievers or {
            "constitution": ConstitutionRetriever(),
            "bns": BNSRetriever(),
            "ipc": IPCRetriever(),
        }
        self.llm_generate_fn = llm_generate_fn or llm_client.generate_answer

    def _normalize_source_type(self, source_type: Optional[str]) -> Optional[str]:
        if source_type is None:
            return None
        normalized = source_type.strip().lower()
        if not normalized:
            return None
        if normalized not in SUPPORTED_SOURCE_TYPES:
            raise UnsupportedSourceTypeError(
                "Unsupported source_type. Expected one of: constitution, bns, ipc."
            )
        return normalized

    def _retrieve_documents(
        self,
        query: str,
        source_type: Optional[str],
        top_k: int,
    ) -> tuple[Optional[str], List[RetrievedDocument]]:
        if source_type is not None:
            retriever = self.retrievers[source_type]
            return source_type, retriever.retrieve(query=query, top_k=top_k)

        query_embedding = embed_text(query)
        documents = vector_store.query_documents(
            query_embedding=query_embedding,
            n_results=top_k,
            source_type=None,
        )
        resolved_source_type = None
        if documents:
            resolved_source_type = str(documents[0].metadata.get("source_type") or "") or None
        return resolved_source_type, documents

    def process_chat_request(
        self,
        query: str,
        source_type: Optional[str] = None,
        top_k: int = 5,
    ) -> ChatResult:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query cannot be empty.")
        if top_k < 1:
            raise ValueError("top_k must be at least 1.")

        normalized_source_type = self._normalize_source_type(source_type)

        try:
            resolved_source_type, retrieved_documents = self._retrieve_documents(
                query=query,
                source_type=normalized_source_type,
                top_k=top_k,
            )
        except ValueError:
            raise
        except VectorStoreError as exc:
            logger.exception("Vector store retrieval failed.")
            raise RetrievalError("Vector store retrieval failed.") from exc
        except Exception as exc:
            logger.exception("Unexpected retrieval failure.")
            raise RetrievalError("Retrieval failed.") from exc

        context = format_retrieved_context(retrieved_documents)

        try:
            answer = self.llm_generate_fn(
                user_query=query,
                context=context,
                system_prompt=SYSTEM_PROMPT,
            )
        except ValueError:
            raise
        except LLMServiceError as exc:
            logger.exception("LLM generation failed.")
            raise GenerationError("LLM generation failed.") from exc
        except Exception as exc:
            logger.exception("Unexpected LLM failure.")
            raise GenerationError("LLM generation failed.") from exc

        return ChatResult(
            answer=answer,
            source_type=resolved_source_type,
            sources=retrieved_documents,
        )


chat_service = ChatService()
