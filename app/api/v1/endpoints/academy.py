from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_admin
from app.models.user import User
from app.repositories.course_repository import course_repository
from app.repositories.lesson_repository import lesson_repository
from app.schemas.course import Course, CourseCreate, CourseUpdate
from app.schemas.lesson import Lesson, LessonCreate, LessonUpdate

router = APIRouter()

# ── Courses ───────────────────────────────────────────────────────────────────

@router.get("/courses", response_model=List[Course])
def list_courses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list:
    """List all courses (public)."""
    return course_repository.get_multi(db, skip=skip, limit=limit)


@router.post("/courses", response_model=Course)
def create_course(
    payload: CourseCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> Course:
    """Create a new course (admin only)."""
    return course_repository.create(db, obj_in=payload)


@router.get("/courses/{course_id}", response_model=Course)
def get_course(course_id: int, db: Session = Depends(get_db)) -> Course:
    """Get a single course by ID."""
    course = course_repository.get(db, id=course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.put("/courses/{course_id}", response_model=Course)
def update_course(
    course_id: int,
    payload: CourseUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> Course:
    """Update a course (admin only)."""
    course = course_repository.get(db, id=course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course_repository.update(db, db_obj=course, obj_in=payload)


@router.delete("/courses/{course_id}")
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> dict:
    """Delete a course (admin only)."""
    course = course_repository.get(db, id=course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    course_repository.remove(db, id=course_id)
    return {"ok": True}


# ── Lessons ───────────────────────────────────────────────────────────────────

@router.get("/lessons", response_model=List[Lesson])
def list_lessons(
    course_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list:
    """List all lessons, optionally filtered by course_id (public)."""
    if course_id is not None:
        return lesson_repository.get_by_course(db, course_id=course_id)
    return lesson_repository.get_multi(db, skip=skip, limit=limit)


@router.post("/lessons", response_model=Lesson)
def create_lesson(
    payload: LessonCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> Lesson:
    """Create a new lesson (admin only)."""
    # Validate course exists
    if not course_repository.get(db, id=payload.course_id):
        raise HTTPException(status_code=404, detail="Course not found")
    return lesson_repository.create(db, obj_in=payload)


@router.get("/lessons/{lesson_id}", response_model=Lesson)
def get_lesson(lesson_id: int, db: Session = Depends(get_db)) -> Lesson:
    """Get a single lesson by ID."""
    lesson = lesson_repository.get(db, id=lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@router.put("/lessons/{lesson_id}", response_model=Lesson)
def update_lesson(
    lesson_id: int,
    payload: LessonUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> Lesson:
    """Update a lesson (admin only)."""
    lesson = lesson_repository.get(db, id=lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson_repository.update(db, db_obj=lesson, obj_in=payload)


@router.delete("/lessons/{lesson_id}")
def delete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> dict:
    """Delete a lesson (admin only)."""
    lesson = lesson_repository.get(db, id=lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    lesson_repository.remove(db, id=lesson_id)
    return {"ok": True}

