from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.db.session import Base


class MessageSource(Base):
    __tablename__ = "message_sources"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    position = Column(Integer, default=0, nullable=False)
    title = Column(String(255))
    source_type = Column(String(32))
    reference = Column(String(255))
    content = Column(String)
    metadata_json = Column("metadata", JSONB)
    distance = Column(Float)

    message = relationship("Message", back_populates="sources")