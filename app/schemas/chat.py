from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class MessageSourceOut(BaseModel):
    position: int = 0
    title: Optional[str] = None
    source_type: Optional[str] = None
    reference: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    distance: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class MessageOut(BaseModel):
    id: int
    content: str
    role: str
    source_type: Optional[str] = None
    is_error: bool = False
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    sources: List[MessageSourceOut] = []

    model_config = ConfigDict(from_attributes=True)


class ChatSessionSummary(BaseModel):
    id: int
    title: str
    status: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    last_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ChatSessionCreate(BaseModel):
    title: Optional[str] = None


class ChatSessionOut(BaseModel):
    id: int
    title: str
    status: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageOut] = []

    model_config = ConfigDict(from_attributes=True)


class ChatMessageRequest(BaseModel):
    query: str
    source_type: Optional[str] = None
    top_k: int = 5


class ChatSendResponse(BaseModel):
    message: MessageOut
    session: ChatSessionOut


class ChatSessionList(BaseModel):
    sessions: List[ChatSessionSummary]