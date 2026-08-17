from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from app.db.session import Base

class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    questions = Column(JSON, nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True)
