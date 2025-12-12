from pymongo.database import Database
from qdrant_client import QdrantClient

from app.exceptions import CourseNotFoundError, CourseAlreadyExistsError, DocumentDeleteError
from app.models.course import CourseResponse
from app.services.document import delete_document
from app.services.log import log_event


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
    name: str | None = None,
    description: str | None = None
) -> CourseResponse:
    course_doc = db.courses.find_one({"code": code})
    if course_doc is None:
        raise CourseNotFoundError(f"Course with code {code} not found")

    update_data = {}
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


def delete_course(code: str, db: Database, qdrant_client: QdrantClient) -> None:
    course = db.courses.find_one({"code": code})
    if course is None:
        raise CourseNotFoundError(f"Course with code {code} not found")

    documents = list(db.documents.find({"course_code": code}))

    deletion_failures = []

    for doc in documents:
        try:
            delete_document(doc["document_id"], db, qdrant_client)
        except Exception as e:
            deletion_failures.append({
                "document_id": doc["document_id"],
                "filename": doc.get("filename", "unknown"),
                "error": str(e)
            })
            log_event(
                "course_document_deletion_failed",
                level="error",
                details={
                    "course_code": code,
                    "document_id": doc["document_id"],
                    "error": str(e)
                }
            )

    if deletion_failures:
        error_summary = "; ".join([
            f"{f['filename']} ({f['document_id']}): {f['error']}"
            for f in deletion_failures
        ])
        raise DocumentDeleteError(
            f"Failed to delete {len(deletion_failures)} document(s) from course {code}. "
            f"Course deletion aborted. Failures: {error_summary}"
        )

    result = db.courses.delete_one({"code": code})
    if result.deleted_count == 0:
        raise CourseNotFoundError(f"Course with code {code} not found")
