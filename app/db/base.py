# Import all the models so that Base has them before being imported by Alembic
from app.db.session import Base
from app.models.user import User
from app.models.chat import Chat
from app.models.message import Message
from app.models.document import Document
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.quiz import Quiz
from app.models.admin import AdminLog
