from app.repositories.base import CRUDBase
from app.models.quiz import Quiz
from app.schemas.quiz import QuizCreate

class QuizRepository(CRUDBase[Quiz, QuizCreate, QuizCreate]):
    pass

quiz_repository = QuizRepository(Quiz)
