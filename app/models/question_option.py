from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base


class QuestionOption(Base):
    __tablename__ = "question_options"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    option_key = Column(String(4), nullable=False)
    text = Column(Text, nullable=False)
    is_correct = Column(Boolean(), nullable=False, default=False)
    sort_order = Column(Integer, nullable=False, default=0)

    question = relationship("Question", back_populates="options")