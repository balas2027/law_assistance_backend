from fastapi import APIRouter, HTTPException, status

from app.api.v1.endpoints.chat_models import ChatRequest, ChatResponse, SourceDocument
from app.services.chat_service import (
    GenerationError,
    RetrievalError,
    UnsupportedSourceTypeError,
    chat_service,
)

router = APIRouter()


@router.get("")
def get_chats() -> dict:
    return {"message": "Get chats"}


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
