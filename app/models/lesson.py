from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base

class Lesson(Base):
    __tablename__ = "lessons"

    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String, index=True, nullable=False)
    content     = Column(Text, nullable=True)
    course_id   = Column(Integer, ForeignKey("courses.id"))
    status      = Column(String(16), nullable=False, default="draft")
    author_name = Column(String(255), nullable=True)
    updated_at  = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    course = relationship("Course", back_populates="lessons")

