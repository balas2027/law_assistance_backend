from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.lesson import Lesson
from app.models.course import Course
from app.models.lesson_completion import LessonCompletion
from app.models.user_stat import UserStat
from app.models.user_streak import UserStreak
from app.repositories.lesson_completion_repository import lesson_completion_repository
from app.services.quiz_service import quiz_service


class ProgressService:
    def mark_lesson_completed(self, db: Session, *, user_id: int, lesson_id: int) -> LessonCompletion:
        lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        existing = lesson_completion_repository.get_by_user_lesson(db, user_id=user_id, lesson_id=lesson_id)
        if existing:
            return existing
        record = LessonCompletion(
            user_id=user_id,
            lesson_id=lesson_id,
            course_id=lesson.course_id,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        quiz_service._update_streak(db, user_id=user_id)
        return record

    def unmark_lesson_completed(self, db: Session, *, user_id: int, lesson_id: int) -> None:
        record = lesson_completion_repository.get_by_user_lesson(db, user_id=user_id, lesson_id=lesson_id)
        if record:
            db.delete(record)
            db.commit()

    def is_lesson_completed(self, db: Session, *, user_id: int, lesson_id: int) -> Optional[dict]:
        record = lesson_completion_repository.get_by_user_lesson(db, user_id=user_id, lesson_id=lesson_id)
        if not record:
            return {"completed": False, "completed_at": None}
        return {
            "completed": True,
            "completed_at": record.completed_at,
            "lesson_id": record.lesson_id,
            "course_id": record.course_id,
        }

    def get_academy_stats(self, db: Session, *, user_id: int) -> dict:
        courses = db.query(Course).filter(Course.status == "published").order_by(Course.id).all()
        lessons_by_course = {}
        total_lessons = 0
        for course in courses:
            lessons = [l for l in course.lessons if l.status == "published"]
            lessons_by_course[course.id] = lessons
            total_lessons += len(lessons)

        completions = lesson_completion_repository.list_for_user(db, user_id=user_id)
        completed_by_lesson = {c.lesson_id for c in completions}
        completed_lessons = len(completed_by_lesson)

        course_stats = []
        for course in courses:
            lessons = lessons_by_course.get(course.id, [])
            done_ids = [l.id for l in lessons if l.id in completed_by_lesson]
            course_stats.append({
                "id": course.id,
                "title": course.title,
                "lessons_total": len(lessons),
                "lessons_completed": len(done_ids),
                "completed_lesson_ids": done_ids,
                "progress_pct": round(len(done_ids) / len(lessons) * 100, 2) if lessons else 0.0,
            })

        completion_pct = round(completed_lessons / total_lessons * 100, 2) if total_lessons else 0.0

        today = datetime.now(timezone.utc).date()
        since = today - timedelta(days=364)
        rows = db.query(
            func.date(LessonCompletion.completed_at).label("day"),
            func.count(LessonCompletion.id),
        ).filter(
            LessonCompletion.user_id == user_id,
            LessonCompletion.completed_at >= datetime(since.year, since.month, since.day, tzinfo=timezone.utc),
        ).group_by("day").all()
        count_by_day = {str(day): cnt for day, cnt in rows}

        calendar = []
        active_days = 0
        for i in range(365):
            day = since + timedelta(days=i)
            key = day.isoformat()
            count = count_by_day.get(key, 0)
            if count:
                active_days += 1
            calendar.append({"date": key, "count": count})

        stat = db.query(UserStat).filter(UserStat.user_id == user_id).first()
        streak = db.query(UserStreak).filter(UserStreak.user_id == user_id).first()

        return {
            "total_courses": len(courses),
            "total_lessons": total_lessons,
            "completed_lessons": completed_lessons,
            "completion_pct": completion_pct,
            "courses": course_stats,
            "total_xp": stat.total_xp if stat else 0,
            "level": stat.level if stat else 1,
            "quizzes_taken": stat.quizzes_taken if stat else 0,
            "quizzes_passed": stat.quizzes_passed if stat else 0,
            "current_streak": streak.current_streak if streak else 0,
            "longest_streak": streak.longest_streak if streak else 0,
            "calendar": calendar,
            "active_days": active_days,
        }


progress_service = ProgressService()