from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base

class Course(Base):
    __tablename__ = "courses"

    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    status      = Column(String(16), nullable=False, default="draft")
    updated_at  = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    lessons = relationship("Lesson", back_populates="course")

