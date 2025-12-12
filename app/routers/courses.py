from fastapi import APIRouter, Depends
from pymongo.database import Database
from qdrant_client import QdrantClient

from app.database import get_database
from app.dependencies import require_student, require_professor, get_qdrant_client
from app.exceptions import CourseNotFoundError
from app.models.user import UserResponse
from app.models.course import CourseResponse, CourseCreate, CourseUpdate, CourseDelete
from app.services import course as course_service
from app.services.log import log_event


router = APIRouter(prefix="/courses")


@router.get("")
async def get_courses(
    code: str | None = None,
    current_user: UserResponse = Depends(require_student),
    db: Database = Depends(get_database)
) -> list[CourseResponse]:
    if code:
        course = course_service.get_course_by_code(code, db)
        if course is None:
            raise CourseNotFoundError(f"Course with code {code} not found")
        return [course]
    return course_service.get_all_courses(db)


@router.post("")
async def create_course(
    course_data: CourseCreate,
    current_user: UserResponse = Depends(require_professor),
    db: Database = Depends(get_database)
) -> CourseResponse:
    course = course_service.create_course(
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
async def update_course(
    course_data: CourseUpdate,
    current_user: UserResponse = Depends(require_professor),
    db: Database = Depends(get_database)
) -> CourseResponse:
    course = course_service.update_course(
        course_data.code,
        db,
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
async def delete_course(
    course_data: CourseDelete,
    current_user: UserResponse = Depends(require_professor),
    db: Database = Depends(get_database),
    qdrant_client: QdrantClient = Depends(get_qdrant_client)
) -> dict[str, str]:
    course_service.delete_course(course_data.code, db, qdrant_client)
    log_event(
        "course_deleted",
        level="info",
        user_email=current_user.email,
        details={"course_code": course_data.code}
    )
    return {"message": "Course deleted successfully"}
