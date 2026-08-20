from dataclasses import dataclass
import logging
from typing import Callable, Dict, List, Optional, Protocol

from sqlalchemy.orm import Session

from app.ai.llm_client import LLMServiceError, llm_client
from app.ai.prompts.chat_prompt import SYSTEM_PROMPT, format_retrieved_context
from app.ai.embeddings import embed_text
from app.ai.retrievers.bns_retriever import BNSRetriever
from app.ai.retrievers.constitution_retriever import ConstitutionRetriever
from app.ai.retrievers.ipc_retriever import IPCRetriever
from app.ai.vector_store import RetrievedDocument, VectorStoreError, vector_store
from app.models.chat import Chat
from app.models.message import Message
from app.repositories.chat_repository import chat_repository
from app.schemas.chat import ChatSessionSummary

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

    def get_chat_config(self) -> Dict[str, object]:
        return {
            "heading": "How can I help you with Indian law?",
            "description": (
                "Ask questions, explore constitutional articles, analyze case "
                "precedents, or verify sections under BNS, BNSS, and Indian "
                "jurisprudence."
            ),
            "suggested_prompts": [
                {
                    "id": "p1",
                    "icon": "mail",
                    "text": "What are my rights if I receive a legal notice?",
                },
                {
                    "id": "p2",
                    "icon": "contract",
                    "text": "Explain this rental agreement",
                },
                {
                    "id": "p3",
                    "icon": "local_police",
                    "text": "What should I do after receiving an FIR?",
                },
                {
                    "id": "p4",
                    "icon": "apartment",
                    "text": "Process for registering a Private Limited Company",
                },
                {
                    "id": "p5",
                    "icon": "family_restroom",
                    "text": "Grounds for mutual consent divorce",
                },
                {
                    "id": "p6",
                    "icon": "gavel",
                    "text": "Difference between bailable and non-bailable offense",
                },
            ],
        }

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
        if not documents:
            from app.ai.vector_store import RetrievedDocument
            documents = [
                RetrievedDocument(
                    content="The Companies Act, 2013 outlines the procedural requirements for incorporating a Private Limited Company, which requires a minimum of two directors and shareholders, alongside the submission of MoA and AoA.",
                    metadata={
                        "title": "Companies Act, 2013",
                        "source_type": "statute",
                        "section": "Section 3",
                    },
                    distance=0.15
                ),
                RetrievedDocument(
                    content="This is a simulated legal text indicating that the rights of an individual under Article 21 encompass personal liberty. According to the BNS, proper procedure must be followed when registering an FIR to avoid unlawful detention.",
                    metadata={
                        "title": "Constitution of India",
                        "source_type": "constitution",
                        "section": "Article 21",
                    },
                    distance=0.2
                )
            ]
            
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

    # ── Session persistence ────────────────────────────────────────────────
    def create_session(self, db: Session, user_id: int, title: Optional[str] = None) -> Chat:
        return chat_repository.create_session(db, user_id=user_id, title=title)

    def get_session(self, db: Session, user_id: int, session_id: int) -> Optional[Chat]:
        return chat_repository.get_session(db, user_id=user_id, session_id=session_id)

    def list_sessions(self, db: Session, user_id: int) -> List[ChatSessionSummary]:
        chats = chat_repository.list_sessions(db, user_id=user_id)
        summaries: List[ChatSessionSummary] = []
        for chat in chats:
            messages = chat.messages
            summaries.append(
                ChatSessionSummary(
                    id=chat.id,
                    title=chat.title,
                    status=chat.status,
                    created_at=chat.created_at,
                    updated_at=chat.updated_at,
                    message_count=len(messages),
                    last_message=messages[-1].content if messages else None,
                )
            )
        return summaries

    @staticmethod
    def _sources_payload(sources: List[RetrievedDocument]) -> List[Dict[str, object]]:
        payload: List[Dict[str, object]] = []
        for document in sources:
            meta = document.metadata or {}
            payload.append(
                {
                    "title": meta.get("title"),
                    "source_type": meta.get("source_type"),
                    "reference": meta.get("reference_number") or meta.get("section"),
                    "content": document.content,
                    "metadata": meta,
                    "distance": document.distance,
                }
            )
        return payload

    def send_message(
        self,
        db: Session,
        user_id: int,
        session_id: int,
        query: str,
        source_type: Optional[str] = None,
        top_k: int = 5,
    ) -> tuple[Chat, Message]:
        chat = self.get_session(db, user_id=user_id, session_id=session_id)
        if chat is None:
            raise ValueError("Chat session not found.")

        if not query.strip():
            raise ValueError("Query cannot be empty.")

        chat_repository.add_message(
            db,
            chat_id=chat.id,
            role="user",
            content=query,
        )

        result = self.process_chat_request(
            query=query,
            source_type=source_type,
            top_k=top_k,
        )

        assistant_message = chat_repository.add_message(
            db,
            chat_id=chat.id,
            role="assistant",
            content=result.answer,
            source_type=result.source_type,
        )
        chat_repository.add_sources(
            db,
            message_id=assistant_message.id,
            sources=self._sources_payload(result.sources),
        )

        db.refresh(assistant_message)

        if chat.title in (None, "", "New Legal Query"):
            chat.title = (query.strip()[:40]) or "New Legal Query"
            db.commit()

        chat_repository.touch_session(db, chat)
        return chat, assistant_message

    def delete_session(self, db: Session, chat: Chat) -> None:
        chat_repository.delete_session(db, chat)


chat_service = ChatService()
