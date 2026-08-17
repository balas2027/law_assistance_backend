from typing import List
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class MessageBase(BaseModel):
    content: str
    role: str

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int
    created_at: datetime
    chat_id: int

    model_config = ConfigDict(from_attributes=True)

class ChatBase(BaseModel):
    title: str

class ChatCreate(ChatBase):
    pass

class Chat(ChatBase):
    id: int
    user_id: int
    messages: List[Message] = []

    model_config = ConfigDict(from_attributes=True)
