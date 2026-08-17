from app.repositories.base import CRUDBase
from app.models.course import Course
from app.schemas.course import CourseCreate

class CourseRepository(CRUDBase[Course, CourseCreate, CourseCreate]):
    pass

course_repository = CourseRepository(Course)
