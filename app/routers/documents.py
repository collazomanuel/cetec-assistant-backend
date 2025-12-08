from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from pymongo.database import Database
from app.config import settings
from app.database import get_database
from app.dependencies import require_professor
from app.models.user import UserResponse
from app.models.document import DocumentResponse, DocumentWithDownloadUrl, DocumentDelete
from app.services import document as document_service
from app.services import course as course_service
from app.services.log import log_event
from app.exceptions import DocumentNotFoundError, FileTooLargeError, CourseNotFoundError

router = APIRouter(prefix="/documents")


@router.get("/course")
def list_documents(
    course_code: str = Query(..., description="Course code to filter documents"),
    current_user: UserResponse = Depends(require_professor),
    db: Database = Depends(get_database)
) -> list[DocumentResponse]:
    documents = document_service.get_documents_by_course(course_code, db)
    log_event(
        "documents_listed",
        level="info",
        user_email=current_user.email,
        details={"course_code": course_code, "count": len(documents)}
    )
    return documents


@router.get("/download")
def get_document(
    document_id: str = Query(..., description="Document ID to retrieve"),
    current_user: UserResponse = Depends(require_professor),
    db: Database = Depends(get_database)
) -> DocumentWithDownloadUrl:
    document = document_service.get_document_by_id(document_id, db)
    if document is None:
        raise DocumentNotFoundError(f"Document with ID {document_id} not found")

    download_url = document_service.get_document_download_url(document_id, db)
    log_event(
        "document_accessed",
        level="info",
        user_email=current_user.email,
        details={"document_id": document_id, "filename": document.filename}
    )
    return DocumentWithDownloadUrl(
        document=document,
        download_url=download_url
    )


@router.post("")
def upload_document(
    course_code: str = Form(...),
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(require_professor),
    db: Database = Depends(get_database)
) -> DocumentResponse:
    course = course_service.get_course_by_code(course_code, db)
    if course is None:
        raise CourseNotFoundError(f"Course with code {course_code} not found")
    
    try:
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > settings.max_file_size:
            raise FileTooLargeError(
                f"File size ({file_size} bytes) exceeds maximum allowed size "
                f"of {settings.max_file_size} bytes ({settings.max_file_size // (1024 * 1024)}MB)"
            )
        
        content_type = file.content_type or "application/octet-stream"

        document = document_service.create_document(
            course_code=course_code,
            filename=file.filename,
            file_obj=file.file,
            content_type=content_type,
            file_size=file_size,
            uploaded_by=current_user.email,
            db=db
        )

        log_event(
            "document_uploaded",
            level="info",
            user_email=current_user.email,
            details={
                "document_id": document.document_id,
                "course_code": course_code,
                "filename": file.filename,
                "file_size": file_size
            }
        )

        return document
    finally:
        file.file.close()


@router.delete("")
def delete_document(
    document_data: DocumentDelete,
    current_user: UserResponse = Depends(require_professor),
    db: Database = Depends(get_database)
) -> dict[str, str]:
    document = document_service.get_document_by_id(document_data.document_id, db)
    if document is None:
        raise DocumentNotFoundError(f"Document with ID {document_data.document_id} not found")

    document_service.delete_document(document_data.document_id, db)

    log_event(
        "document_deleted",
        level="info",
        user_email=current_user.email,
        details={
            "document_id": document_data.document_id,
            "filename": document.filename,
            "course_code": document.course_code
        }
    )

    return {"message": "Document deleted successfully"}
