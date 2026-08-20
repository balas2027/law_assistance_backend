from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    role = Column(String(16), nullable=False)  # 'user' or 'assistant'
    source_type = Column(String(32))
    is_error = Column(Boolean, default=False, nullable=False)
    metadata_json = Column("metadata", JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)

    chat = relationship("Chat", back_populates="messages")
    sources = relationship(
        "MessageSource",
        back_populates="message",
        cascade="all, delete-orphan",
        order_by="MessageSource.position",
    )