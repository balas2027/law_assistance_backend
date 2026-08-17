from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from app.repositories.base import CRUDBase
from app.models.quiz import Quiz
from app.models.question import Question
from app.models.question_option import QuestionOption
from app.schemas.quiz import QuizCreate, QuizUpdate


class QuizRepository(CRUDBase[Quiz, QuizCreate, QuizUpdate]):
    def get_with_questions(self, db: Session, id: int) -> Optional[Quiz]:
        return (
            db.query(Quiz)
            .options(joinedload(Quiz.topic), joinedload(Quiz.questions).joinedload(Question.options))
            .filter(Quiz.id == id)
            .first()
        )

    def get_multi_published(self, db: Session, *, topic_id: Optional[int] = None,
                            skip: int = 0, limit: int = 100) -> List[Quiz]:
        q = db.query(Quiz).filter(Quiz.status == "published")
        if topic_id is not None:
            q = q.filter(Quiz.topic_id == topic_id)
        return q.order_by(Quiz.created_at.desc()).offset(skip).limit(limit).all()

    def create_with_questions(self, db: Session, *, obj_in: QuizCreate, created_by: int) -> Quiz:
        db_obj = Quiz(
            title=obj_in.title,
            description=obj_in.description,
            topic_id=obj_in.topic_id,
            difficulty=obj_in.difficulty,
            xp_per_question=obj_in.xp_per_question,
            max_lives=obj_in.max_lives,
            time_limit_sec=obj_in.time_limit_sec,
            status=obj_in.status,
            created_by=created_by,
        )
        if db_obj.status == "published":
            from datetime import datetime, timezone
            db_obj.published_at = datetime.now(timezone.utc)
        for idx, q in enumerate(obj_in.questions):
            question = Question(
                scenario=q.scenario,
                explanation=q.explanation,
                points=q.points,
                sort_order=q.sort_order or idx,
            )
            for oidx, opt in enumerate(q.options):
                question.options.append(QuestionOption(
                    option_key=opt.option_key,
                    text=opt.text,
                    is_correct=opt.is_correct,
                    sort_order=oidx,
                ))
            db_obj.questions.append(question)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_with_questions(self, db: Session, *, db_obj: Quiz, obj_in: QuizUpdate) -> Quiz:
        data = obj_in.model_dump(exclude_unset=True, exclude={"questions"})
        for field, value in data.items():
            setattr(db_obj, field, value)
        if "status" in data and db_obj.status == "published" and not db_obj.published_at:
            from datetime import datetime, timezone
            db_obj.published_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


quiz_repository = QuizRepository(Quiz)