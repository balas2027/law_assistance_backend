from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.db.session import Base


class LessonCompletion(Base):
    __tablename__ = "lesson_completions"
    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="uq_lesson_completions_user_lesson"),
    )

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id    = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    course_id    = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    completed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
