from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.models.quiz import Quiz
from app.models.quiz_attempt import QuizAttempt
from app.models.quiz_answer import QuizAnswer
from app.models.user_stat import UserStat
from app.models.user_streak import UserStreak
from app.models.user_topic_progress import UserTopicProgress
from app.repositories.quiz_repository import quiz_repository
from app.schemas.quiz import QuizCreate, QuizUpdate, QuizPublic
from app.schemas.analytics import QuizCompleteOut

PASS_THRESHOLD_PCT = 60.0
XP_PER_LEVEL = 500


class QuizService:
    # ── CMS ──────────────────────────────────────────────────────────────────

    def create_quiz(self, db: Session, *, payload: QuizCreate, created_by: int) -> Quiz:
        return quiz_repository.create_with_questions(db, obj_in=payload, created_by=created_by)

    def update_quiz(self, db: Session, *, db_obj: Quiz, payload: QuizUpdate) -> Quiz:
        return quiz_repository.update_with_questions(db, db_obj=db_obj, obj_in=payload)

    def set_quiz_status(self, db: Session, *, db_obj: Quiz, status: str) -> Quiz:
        db_obj.status = status
        if status == "published" and not db_obj.published_at:
            db_obj.published_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    # ── User-facing ──────────────────────────────────────────────────────────

    def list_public_quizzes(self, db: Session, *, topic_id: Optional[int] = None,
                            skip: int = 0, limit: int = 100) -> List[QuizPublic]:
        quizzes = quiz_repository.get_multi_published(db, topic_id=topic_id, skip=skip, limit=limit)
        return [self.to_public(db, q) for q in quizzes]

    def to_public(self, db: Session, quiz: Quiz) -> QuizPublic:
        questions = []
        for q in sorted(quiz.questions, key=lambda x: x.sort_order):
            questions.append({
                "id": q.id,
                "scenario": q.scenario,
                "points": q.points,
                "options": [
                    {"id": o.id, "option_key": o.option_key, "text": o.text}
                    for o in sorted(q.options, key=lambda x: x.sort_order)
                ],
            })
        return QuizPublic(
            id=quiz.id,
            title=quiz.title,
            description=quiz.description,
            topic_id=quiz.topic_id,
            topic_name=quiz.topic.name if quiz.topic else None,
            difficulty=quiz.difficulty,
            xp_per_question=quiz.xp_per_question,
            max_lives=quiz.max_lives,
            time_limit_sec=quiz.time_limit_sec,
            questions=questions,
        )

    # ── Attempt lifecycle ────────────────────────────────────────────────────

    def start_attempt(self, db: Session, *, user_id: int, quiz_id: int) -> QuizAttempt:
        quiz = quiz_repository.get(db, id=quiz_id)
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        if quiz.status != "published":
            raise HTTPException(status_code=400, detail="Quiz is not published")
        existing = db.query(QuizAttempt).filter(
            QuizAttempt.user_id == user_id,
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.status == "in_progress",
        ).first()
        if existing:
            return existing
        attempt = QuizAttempt(user_id=user_id, quiz_id=quiz_id)
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        return attempt

    def _get_owned_attempt(self, db: Session, *, user_id: int, attempt_id: int) -> QuizAttempt:
        attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).first()
        if not attempt:
            raise HTTPException(status_code=404, detail="Attempt not found")
        if attempt.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not your attempt")
        return attempt

    def submit_answer(self, db: Session, *, user_id: int, attempt_id: int,
                      question_id: int, selected_option_id: Optional[int]) -> QuizAnswer:
        attempt = self._get_owned_attempt(db, user_id=user_id, attempt_id=attempt_id)
        if attempt.status != "in_progress":
            raise HTTPException(status_code=400, detail="Attempt already completed")
        existing = db.query(QuizAnswer).filter(
            QuizAnswer.attempt_id == attempt_id,
            QuizAnswer.question_id == question_id,
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Question already answered")

        quiz = quiz_repository.get_with_questions(db, id=attempt.quiz_id)
        question = next((q for q in quiz.questions if q.id == question_id), None)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        correct_option = next((o for o in question.options if o.is_correct), None)
        is_correct = correct_option is not None and correct_option.id == selected_option_id
        points_earned = question.points if is_correct else 0

        answer = QuizAnswer(
            attempt_id=attempt_id,
            question_id=question_id,
            selected_option_id=selected_option_id,
            is_correct=is_correct,
            points_earned=points_earned,
        )
        db.add(answer)
        attempt.score += points_earned
        if is_correct:
            attempt.correct_answers += 1
        else:
            attempt.wrong_answers += 1
        db.add(attempt)
        db.commit()
        db.refresh(answer)
        return answer

    def complete_attempt(self, db: Session, *, user_id: int, attempt_id: int,
                         time_taken_sec: Optional[int] = None) -> QuizCompleteOut:
        attempt = self._get_owned_attempt(db, user_id=user_id, attempt_id=attempt_id)
        if attempt.status == "completed":
            return self._build_complete_out(db, attempt)

        quiz = quiz_repository.get_with_questions(db, id=attempt.quiz_id)
        total = len(quiz.questions)
        if total == 0:
            raise HTTPException(status_code=400, detail="Quiz has no questions")

        attempt.status = "completed"
        attempt.completed_at = datetime.now(timezone.utc)
        attempt.time_taken_sec = time_taken_sec
        attempt.accuracy_pct = round(attempt.correct_answers / total * 100, 2)
        attempt.xp_earned = attempt.score
        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        self._update_stats(db, user_id=user_id, attempt=attempt)
        self._update_streak(db, user_id=user_id)
        self._update_topic_progress(db, user_id=user_id, quiz=quiz, attempt=attempt)

        return self._build_complete_out(db, attempt)

    def _build_complete_out(self, db: Session, attempt: QuizAttempt) -> QuizCompleteOut:
        quiz = quiz_repository.get_with_questions(db, id=attempt.quiz_id)
        total = len(quiz.questions)
        passed = attempt.accuracy_pct is not None and attempt.accuracy_pct >= PASS_THRESHOLD_PCT
        stat = db.query(UserStat).filter(UserStat.user_id == attempt.user_id).first()
        streak = db.query(UserStreak).filter(UserStreak.user_id == attempt.user_id).first()
        topic_progress = None
        if quiz.topic_id:
            tp = db.query(UserTopicProgress).filter(
                UserTopicProgress.user_id == attempt.user_id,
                UserTopicProgress.topic_id == quiz.topic_id,
            ).first()
            if tp:
                topic_progress = {
                    "topic_id": tp.topic_id,
                    "quizzes_taken": tp.quizzes_taken,
                    "avg_accuracy_pct": float(tp.avg_accuracy_pct) if tp.avg_accuracy_pct else None,
                    "mastery_level": tp.mastery_level,
                }
        return QuizCompleteOut(
            id=attempt.id,
            quiz_id=attempt.quiz_id,
            user_id=attempt.user_id,
            status=attempt.status,
            score=attempt.score,
            correct_answers=attempt.correct_answers,
            wrong_answers=attempt.wrong_answers,
            accuracy_pct=float(attempt.accuracy_pct) if attempt.accuracy_pct else None,
            xp_earned=attempt.xp_earned,
            time_taken_sec=attempt.time_taken_sec,
            started_at=attempt.started_at,
            completed_at=attempt.completed_at,
            total_questions=total,
            passed=passed,
            streak=streak.current_streak if streak else 0,
            longest_streak=streak.longest_streak if streak else 0,
            total_xp=stat.total_xp if stat else 0,
            level=stat.level if stat else 1,
            topic_mastery=topic_progress,
        )

    def _update_stats(self, db: Session, *, user_id: int, attempt: QuizAttempt) -> None:
        stat = db.query(UserStat).filter(UserStat.user_id == user_id).first()
        if not stat:
            stat = UserStat(
                user_id=user_id,
                total_xp=0, level=1, quizzes_taken=0, quizzes_passed=0,
                questions_answered=0, questions_correct=0,
            )
            db.add(stat)
        passed = attempt.accuracy_pct is not None and attempt.accuracy_pct >= PASS_THRESHOLD_PCT
        stat.total_xp += attempt.xp_earned
        stat.quizzes_taken += 1
        if passed:
            stat.quizzes_passed += 1
        stat.questions_answered += attempt.correct_answers + attempt.wrong_answers
        stat.questions_correct += attempt.correct_answers
        if stat.best_accuracy_pct is None or attempt.accuracy_pct > stat.best_accuracy_pct:
            stat.best_accuracy_pct = attempt.accuracy_pct
        stat.level = 1 + stat.total_xp // XP_PER_LEVEL
        db.add(stat)
        db.commit()

    def _update_streak(self, db: Session, *, user_id: int) -> None:
        streak = db.query(UserStreak).filter(UserStreak.user_id == user_id).first()
        if not streak:
            streak = UserStreak(user_id=user_id, current_streak=0, longest_streak=0)
            db.add(streak)
        now = datetime.now(timezone.utc)
        today = now.date()
        last = streak.last_activity_at.date() if streak.last_activity_at else None
        if last == today:
            pass
        elif last == today - timedelta(days=1):
            streak.current_streak += 1
        else:
            streak.current_streak = 1
        streak.longest_streak = max(streak.longest_streak, streak.current_streak)
        streak.last_activity_at = now
        db.add(streak)
        db.commit()

    def _update_topic_progress(self, db: Session, *, user_id: int, quiz: Quiz, attempt: QuizAttempt) -> None:
        if not quiz.topic_id:
            return
        tp = db.query(UserTopicProgress).filter(
            UserTopicProgress.user_id == user_id,
            UserTopicProgress.topic_id == quiz.topic_id,
        ).first()
        if not tp:
            tp = UserTopicProgress(
                user_id=user_id, topic_id=quiz.topic_id,
                quizzes_taken=0, avg_accuracy_pct=None, xp_earned=0, mastery_level=0,
            )
            db.add(tp)
        tp.quizzes_taken += 1
        old_total = tp.quizzes_taken - 1
        if tp.avg_accuracy_pct is None:
            tp.avg_accuracy_pct = attempt.accuracy_pct
        elif old_total > 0:
            tp.avg_accuracy_pct = round(
                (tp.avg_accuracy_pct * old_total + attempt.accuracy_pct) / tp.quizzes_taken, 2
            )
        tp.xp_earned += attempt.xp_earned
        acc = float(tp.avg_accuracy_pct or 0)
        tp.mastery_level = 5 if acc >= 90 else 4 if acc >= 80 else 3 if acc >= 70 else 2 if acc >= 60 else 1 if acc >= 50 else 0
        db.add(tp)
        db.commit()

    # ── User stats ───────────────────────────────────────────────────────────

    def get_user_stats(self, db: Session, *, user_id: int) -> dict:
        stat = db.query(UserStat).filter(UserStat.user_id == user_id).first()
        streak = db.query(UserStreak).filter(UserStreak.user_id == user_id).first()
        return {
            "user_id": user_id,
            "total_xp": stat.total_xp if stat else 0,
            "level": stat.level if stat else 1,
            "quizzes_taken": stat.quizzes_taken if stat else 0,
            "quizzes_passed": stat.quizzes_passed if stat else 0,
            "questions_answered": stat.questions_answered if stat else 0,
            "questions_correct": stat.questions_correct if stat else 0,
            "best_accuracy_pct": float(stat.best_accuracy_pct) if stat and stat.best_accuracy_pct else None,
            "current_streak": streak.current_streak if streak else 0,
            "longest_streak": streak.longest_streak if streak else 0,
        }

    def get_user_topic_progress(self, db: Session, *, user_id: int) -> List[dict]:
        rows = db.query(UserTopicProgress).filter(
            UserTopicProgress.user_id == user_id
        ).all()
        out = []
        from app.models.topic import Topic
        for tp in rows:
            topic = db.query(Topic).filter(Topic.id == tp.topic_id).first()
            out.append({
                "topic_id": tp.topic_id,
                "topic_name": topic.name if topic else f"Topic {tp.topic_id}",
                "quizzes_taken": tp.quizzes_taken,
                "avg_accuracy_pct": float(tp.avg_accuracy_pct) if tp.avg_accuracy_pct else None,
                "xp_earned": tp.xp_earned,
                "mastery_level": tp.mastery_level,
            })
        return out

    def get_user_attempts(self, db: Session, *, user_id: int, quiz_id: Optional[int] = None) -> List[dict]:
        q = db.query(QuizAttempt).filter(QuizAttempt.user_id == user_id)
        if quiz_id is not None:
            q = q.filter(QuizAttempt.quiz_id == quiz_id)
        attempts = q.order_by(QuizAttempt.started_at.desc()).limit(50).all()
        return [
            {
                "id": a.id,
                "quiz_id": a.quiz_id,
                "status": a.status,
                "score": a.score,
                "accuracy_pct": float(a.accuracy_pct) if a.accuracy_pct else None,
                "xp_earned": a.xp_earned,
                "completed_at": a.completed_at,
            }
            for a in attempts
        ]

    def get_user_quiz_progress(self, db: Session, *, user_id: int) -> List[dict]:
        rows = db.query(
            QuizAttempt.quiz_id,
            func.count(QuizAttempt.id),
            func.max(QuizAttempt.score),
            func.max(QuizAttempt.accuracy_pct),
            func.max(QuizAttempt.completed_at),
        ).filter(
            QuizAttempt.user_id == user_id,
            QuizAttempt.status == "completed",
        ).group_by(QuizAttempt.quiz_id).all()
        out = []
        for quiz_id, attempts_count, best_score, best_accuracy, last_completed in rows:
            best_acc = float(best_accuracy) if best_accuracy is not None else None
            out.append({
                "quiz_id": quiz_id,
                "attempts_count": attempts_count,
                "best_score": best_score,
                "best_accuracy_pct": best_acc,
                "passed": best_acc is not None and best_acc >= PASS_THRESHOLD_PCT,
                "last_completed_at": last_completed,
            })
        return out


quiz_service = QuizService()