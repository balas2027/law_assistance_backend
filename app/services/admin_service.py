from typing import List
from datetime import date, datetime, timedelta
from sqlalchemy import func, distinct
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.user_type import UserType
from app.models.lesson import Lesson
from app.models.course import Course
from app.models.quiz import Quiz
from app.models.question import Question
from app.models.quiz_attempt import QuizAttempt
from app.models.quiz_answer import QuizAnswer
from app.models.user_topic_progress import UserTopicProgress
from app.schemas.admin_stats import AdminStats
from app.schemas.analytics import QuizAnalyticsOut, TopicAnalyticsOut


class AdminService:
    def get_dashboard_stats(self, db: Session) -> AdminStats:
        total_users   = db.query(User).count()
        total_lessons = db.query(Lesson).count()
        total_courses = db.query(Course).count()
        total_quizzes = db.query(Quiz).count()
        published_quizzes = db.query(Quiz).filter(Quiz.status == "published").count()
        total_attempts = db.query(QuizAttempt).count()
        attendees = db.query(func.count(distinct(QuizAttempt.user_id))).scalar() or 0

        # Breakdown by type
        user_types    = db.query(UserType).all()
        users_by_type = {}
        for ut in user_types:
            count = db.query(User).filter(User.user_type_id == ut.id).count()
            if count > 0:
                users_by_type[ut.name] = count

        return AdminStats(
            total_users=total_users,
            total_lessons=total_lessons,
            total_courses=total_courses,
            total_quizzes=total_quizzes,
            published_quizzes=published_quizzes,
            total_attempts=total_attempts,
            attendees=attendees,
            users_by_type=users_by_type,
        )

    def get_user_signups(self, db: Session, *, from_date: str, to_date: str) -> List[dict]:
        start = date.fromisoformat(from_date)
        end = date.fromisoformat(to_date)
        rows = db.query(
            func.date(User.created_at).label("day"),
            func.count(User.id),
        ).filter(
            User.created_at >= datetime(start.year, start.month, start.day),
            User.created_at < datetime(end.year, end.month, end.day) + timedelta(days=1),
        ).group_by("day").all()
        counts = {str(day): cnt for day, cnt in rows}
        result = []
        cur = start
        while cur <= end:
            result.append({"date": cur.isoformat(), "count": counts.get(cur.isoformat(), 0)})
            cur += timedelta(days=1)
        return result

    def get_quiz_analytics(self, db: Session, *, quiz_id: int) -> QuizAnalyticsOut:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise ValueError("Quiz not found")
        attempts = db.query(QuizAttempt).filter(
            QuizAttempt.quiz_id == quiz_id, QuizAttempt.status == "completed"
        ).all()
        total = len(attempts)
        attendees = len({a.user_id for a in attempts})
        avg_score = round(sum(a.score for a in attempts) / total, 2) if total else None
        avg_acc = round(sum(float(a.accuracy_pct or 0) for a in attempts) / total, 2) if total else None
        avg_time = round(sum((a.time_taken_sec or 0) for a in attempts) / total, 2) if total else None
        passed = sum(1 for a in attempts if a.accuracy_pct is not None and a.accuracy_pct >= 60)
        pass_rate = round(passed / total * 100, 2) if total else None

        per_question = []
        questions = db.query(Question).filter(Question.quiz_id == quiz_id).order_by(Question.sort_order).all()
        for q in questions:
            correct = db.query(QuizAnswer).join(QuizAttempt).filter(
                QuizAnswer.question_id == q.id,
                QuizAnswer.is_correct.is_(True),
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.status == "completed",
            ).count()
            per_question.append({
                "question_id": q.id,
                "scenario": q.scenario,
                "correct_count": correct,
                "total_attempts": total,
                "correct_rate_pct": round(correct / total * 100, 2) if total else None,
            })

        return QuizAnalyticsOut(
            quiz_id=quiz.id,
            quiz_title=quiz.title,
            total_attempts=total,
            attendees=attendees,
            completions=total,
            avg_score=avg_score,
            avg_accuracy_pct=avg_acc,
            avg_time_sec=avg_time,
            pass_rate_pct=pass_rate,
            per_question=per_question,
        )

    def get_topic_analytics(self, db: Session, *, topic_id: int) -> TopicAnalyticsOut:
        from app.models.topic import Topic
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            raise ValueError("Topic not found")
        quizzes = db.query(Quiz).filter(Quiz.topic_id == topic_id).all()
        quiz_ids = [q.id for q in quizzes]
        attempts = []
        if quiz_ids:
            attempts = db.query(QuizAttempt).filter(
                QuizAttempt.quiz_id.in_(quiz_ids), QuizAttempt.status == "completed"
            ).all()
        total = len(attempts)
        attendees = len({a.user_id for a in attempts})
        avg_acc = round(sum(float(a.accuracy_pct or 0) for a in attempts) / total, 2) if total else None
        return TopicAnalyticsOut(
            topic_id=topic.id,
            topic_name=topic.name,
            total_quizzes=len(quizzes),
            published_quizzes=sum(1 for q in quizzes if q.status == "published"),
            total_attempts=total,
            attendees=attendees,
            avg_accuracy_pct=avg_acc,
        )


admin_service = AdminService()