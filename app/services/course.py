from pymongo.database import Database

from app.exceptions import CourseNotFoundError, CourseAlreadyExistsError
from app.models.course import CourseResponse


def get_course_by_code(code: str, db: Database) -> CourseResponse | None:
    course_doc = db.courses.find_one({"code": code})
    if course_doc is None:
        return None
    return CourseResponse(
        code=course_doc["code"],
        name=course_doc["name"],
        description=course_doc.get("description")
    )


def get_all_courses(db: Database) -> list[CourseResponse]:
    courses = []
    for course_doc in db.courses.find():
        courses.append(CourseResponse(
            code=course_doc["code"],
            name=course_doc["name"],
            description=course_doc.get("description")
        ))
    return courses


def create_course(code: str, name: str, description: str | None, db: Database) -> CourseResponse:
    existing_course = db.courses.find_one({"code": code})
    if existing_course is not None:
        raise CourseAlreadyExistsError(f"Course with code {code} already exists")

    course_doc = {
        "code": code,
        "name": name,
        "description": description
    }
    db.courses.insert_one(course_doc)

    return CourseResponse(
        code=code,
        name=name,
        description=description
    )


def update_course(
    code: str,
    db: Database,
    new_code: str | None = None,
    name: str | None = None,
    description: str | None = None
) -> CourseResponse:
    course_doc = db.courses.find_one({"code": code})
    if course_doc is None:
        raise CourseNotFoundError(f"Course with code {code} not found")

    if new_code is not None and new_code != code:
        existing_course = db.courses.find_one({"code": new_code})
        if existing_course is not None:
            raise CourseAlreadyExistsError(f"Course with code {new_code} already exists")

    update_data = {}
    if new_code is not None:
        update_data["code"] = new_code
    if name is not None:
        update_data["name"] = name
    if description is not None:
        update_data["description"] = description

    if update_data:
        db.courses.update_one({"code": code}, {"$set": update_data})
        course_doc.update(update_data)

    return CourseResponse(
        code=course_doc["code"],
        name=course_doc["name"],
        description=course_doc.get("description")
    )


def delete_course(code: str, db: Database) -> None:
    result = db.courses.delete_one({"code": code})
    if result.deleted_count == 0:
        raise CourseNotFoundError(f"Course with code {code} not found")
