from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    role = Column(String, nullable=False) # 'user' or 'assistant'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    chat_id = Column(Integer, ForeignKey("chats.id"))

    chat = relationship("Chat")
