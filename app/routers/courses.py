from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.database import get_database
from app.dependencies import get_current_user, require_student, require_professor
from app.exceptions import CourseNotFoundError
from app.models.user import UserResponse
from app.models.course import CourseResponse, CourseCreate, CourseUpdate, CourseDelete
from app.services.course import (
    get_course_by_code as get_course_by_code_service,
    get_all_courses as get_all_courses_service,
    create_course as create_course_service,
    update_course as update_course_service,
    delete_course as delete_course_service
)
from app.services.log import log_event


router = APIRouter(prefix="/courses")


@router.get("")
def get_courses(
    code: str | None = None,
    current_user: UserResponse = Depends(require_student),
    db: Database = Depends(get_database)
) -> list[CourseResponse]:
    if code:
        course = get_course_by_code_service(code, db)
        if course is None:
            raise CourseNotFoundError(f"Course with code {code} not found")
        return [course]
    return get_all_courses_service(db)


@router.post("")
def create_course_endpoint(
    course_data: CourseCreate,
    current_user: UserResponse = Depends(require_professor),
    db: Database = Depends(get_database)
) -> CourseResponse:
    course = create_course_service(
        course_data.code,
        course_data.name,
        course_data.description,
        db
    )
    log_event(
        "course_created",
        level="info",
        user_email=current_user.email,
        details={"course_code": course.code}
    )
    return course


@router.patch("")
def update_course_endpoint(
    course_data: CourseUpdate,
    current_user: UserResponse = Depends(require_professor),
    db: Database = Depends(get_database)
) -> CourseResponse:
    course = update_course_service(
        course_data.code,
        db,
        new_code=course_data.new_code,
        name=course_data.name,
        description=course_data.description
    )
    log_event(
        "course_updated",
        level="info",
        user_email=current_user.email,
        details={"course_code": course.code}
    )
    return course


@router.delete("")
def delete_course_endpoint(
    course_data: CourseDelete,
    current_user: UserResponse = Depends(require_professor),
    db: Database = Depends(get_database)
) -> dict[str, str]:
    delete_course_service(course_data.code, db)
    log_event(
        "course_deleted",
        level="info",
        user_email=current_user.email,
        details={"course_code": course_data.code}
    )
    return {"message": "Course deleted successfully"}
