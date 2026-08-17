from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    difficulty = Column(String(16), nullable=False, default="beginner")
    xp_per_question = Column(Integer, nullable=False, default=10)
    max_lives = Column(Integer, nullable=False, default=3)
    time_limit_sec = Column(Integer, nullable=True)
    status = Column(String(16), nullable=False, default="draft")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    topic = relationship("Topic", back_populates="quizzes")
    questions = relationship(
        "Question",
        back_populates="quiz",
        cascade="all, delete-orphan",
        order_by="Question.sort_order",
    )