from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.api.v1.endpoints.chat_models import (
    ChatConfigResponse,
    ChatRequest,
    ChatResponse,
    SourceDocument,
)
from app.models.user import User
from app.models.chat import Chat
from app.models.message import Message
from app.schemas.chat import (
    ChatMessageRequest,
    ChatSendResponse,
    ChatSessionCreate,
    ChatSessionList,
    ChatSessionOut,
    MessageOut,
    MessageSourceOut,
)
from app.services.chat_service import (
    GenerationError,
    RetrievalError,
    UnsupportedSourceTypeError,
    chat_service,
)

router = APIRouter()


def _source_out(source) -> MessageSourceOut:
    return MessageSourceOut(
        position=source.position,
        title=source.title,
        source_type=source.source_type,
        reference=source.reference,
        content=source.content,
        metadata=source.metadata_json,
        distance=source.distance,
    )


def _message_out(message: Message) -> MessageOut:
    return MessageOut(
        id=message.id,
        content=message.content,
        role=message.role,
        source_type=message.source_type,
        is_error=message.is_error,
        metadata=message.metadata_json,
        created_at=message.created_at,
        sources=[_source_out(s) for s in message.sources],
    )


def _session_out(chat: Chat) -> ChatSessionOut:
    return ChatSessionOut(
        id=chat.id,
        title=chat.title,
        status=chat.status,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        messages=[_message_out(m) for m in chat.messages],
    )


@router.get("/config", response_model=ChatConfigResponse)
def get_chat_config() -> ChatConfigResponse:
    return ChatConfigResponse(**chat_service.get_chat_config())


@router.get("/sessions", response_model=ChatSessionList)
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatSessionList:
    sessions = chat_service.list_sessions(db, user_id=current_user.id)
    return ChatSessionList(sessions=sessions)


@router.post("/sessions", response_model=ChatSessionOut, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatSessionOut:
    chat = chat_service.create_session(db, user_id=current_user.id, title=payload.title)
    return _session_out(chat)


@router.get("/sessions/{session_id}", response_model=ChatSessionOut)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatSessionOut:
    chat = chat_service.get_session(db, user_id=current_user.id, session_id=session_id)
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat session not found.")
    return _session_out(chat)


@router.post("/sessions/{session_id}/messages", response_model=ChatSendResponse)
def send_session_message(
    session_id: int,
    payload: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatSendResponse:
    try:
        chat, assistant_message = chat_service.send_message(
            db,
            user_id=current_user.id,
            session_id=session_id,
            query=payload.query,
            source_type=payload.source_type,
            top_k=payload.top_k,
        )
    except UnsupportedSourceTypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RetrievalError as exc:
        raise HTTPException(
            status_code=503, detail="Vector store is currently unavailable."
        ) from exc
    except GenerationError as exc:
        raise HTTPException(
            status_code=502, detail="LLM provider is currently unavailable."
        ) from exc

    return ChatSendResponse(
        message=_message_out(assistant_message),
        session=_session_out(chat),
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    chat = chat_service.get_session(db, user_id=current_user.id, session_id=session_id)
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat session not found.")
    chat_service.delete_session(db, chat)


@router.post("", response_model=ChatResponse)
def post_chat(payload: ChatRequest) -> ChatResponse:
    try:
        result = chat_service.process_chat_request(
            query=payload.query,
            source_type=payload.source_type,
            top_k=payload.top_k,
        )
    except UnsupportedSourceTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except RetrievalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector store is currently unavailable.",
        ) from exc
    except GenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM provider is currently unavailable.",
        ) from exc

    return ChatResponse(
        answer=result.answer,
        source_type=result.source_type,
        sources=[
            SourceDocument(
                content=document.content,
                metadata=document.metadata,
                distance=document.distance,
            )
            for document in result.sources
        ],
    )