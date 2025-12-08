import uuid
from pymongo.database import Database

from app.exceptions import CourseNotFoundError, CourseAlreadyExistsError
from app.models.course import CourseResponse


def get_course_by_id(course_id: str, db: Database) -> CourseResponse | None:
    course_doc = db.courses.find_one({"id": course_id})
    if course_doc is None:
        return None
    return CourseResponse(
        id=course_doc["id"],
        code=course_doc["code"],
        name=course_doc["name"],
        description=course_doc.get("description")
    )


def get_all_courses(db: Database) -> list[CourseResponse]:
    courses = []
    for course_doc in db.courses.find():
        courses.append(CourseResponse(
            id=course_doc["id"],
            code=course_doc["code"],
            name=course_doc["name"],
            description=course_doc.get("description")
        ))
    return courses


def create_course(code: str, name: str, description: str | None, db: Database) -> CourseResponse:
    existing_course = db.courses.find_one({"code": code})
    if existing_course is not None:
        raise CourseAlreadyExistsError(f"Course with code {code} already exists")

    course_id = str(uuid.uuid4())
    course_doc = {
        "id": course_id,
        "code": code,
        "name": name,
        "description": description
    }
    db.courses.insert_one(course_doc)

    return CourseResponse(
        id=course_id,
        code=code,
        name=name,
        description=description
    )


def update_course(
    course_id: str,
    db: Database,
    code: str | None = None,
    name: str | None = None,
    description: str | None = None
) -> CourseResponse:
    course_doc = db.courses.find_one({"id": course_id})
    if course_doc is None:
        raise CourseNotFoundError(f"Course with id {course_id} not found")

    if code is not None and code != course_doc["code"]:
        existing_course = db.courses.find_one({"code": code, "id": {"$ne": course_id}})
        if existing_course is not None:
            raise CourseAlreadyExistsError(f"Course with code {code} already exists")

    update_data = {}
    if code is not None:
        update_data["code"] = code
    if name is not None:
        update_data["name"] = name
    if description is not None:
        update_data["description"] = description

    if update_data:
        db.courses.update_one({"id": course_id}, {"$set": update_data})
        course_doc.update(update_data)

    return CourseResponse(
        id=course_doc["id"],
        code=course_doc["code"],
        name=course_doc["name"],
        description=course_doc.get("description")
    )


def delete_course(course_id: str, db: Database) -> None:
    result = db.courses.delete_one({"id": course_id})
    if result.deleted_count == 0:
        raise CourseNotFoundError(f"Course with id {course_id} not found")
