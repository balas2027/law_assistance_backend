from sqlalchemy import Column, Integer, String
from app.db.session import Base

class AdminLog(Base):
    __tablename__ = "admin_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String, nullable=False)
    details = Column(String, nullable=True)
