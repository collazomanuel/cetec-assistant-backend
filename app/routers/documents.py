from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from pymongo.database import Database
from app.database import get_database
from app.dependencies import require_professor
from app.models.user import UserResponse
from app.models.document import DocumentResponse
from app.services.document import (
    create_document as create_document_service,
    get_documents_by_course as get_documents_by_course_service,
    get_document_by_id as get_document_by_id_service,
    delete_document as delete_document_service,
    get_document_download_url as get_document_download_url_service
)
from app.services.log import log_event
from app.exceptions import DocumentNotFoundError

router = APIRouter(prefix="/documents")


@router.get("")
def list_documents(
    course_code: str = Query(..., description="Course code to filter documents"),
    current_user: UserResponse = Depends(require_professor),
    db: Database = Depends(get_database)
) -> list[DocumentResponse]:
    documents = get_documents_by_course_service(course_code, db)
    log_event(
        "documents_listed",
        level="info",
        user_email=current_user.email,
        details={"course_code": course_code, "count": len(documents)}
    )
    return documents


@router.get("/{document_id}")
def get_document(
    document_id: str,
    current_user: UserResponse = Depends(require_professor),
    db: Database = Depends(get_database)
) -> dict:
    document = get_document_by_id_service(document_id, db)
    if document is None:
        raise DocumentNotFoundError(f"Document with ID {document_id} not found")

    download_url = get_document_download_url_service(document_id, db)
    log_event(
        "document_accessed",
        level="info",
        user_email=current_user.email,
        details={"document_id": document_id, "filename": document.filename}
    )
    return {
        "document": document,
        "download_url": download_url
    }


@router.post("")
def upload_document(
    course_code: str = Form(...),
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(require_professor),
    db: Database = Depends(get_database)
) -> DocumentResponse:
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    content_type = file.content_type or "application/octet-stream"

    document = create_document_service(
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


@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    current_user: UserResponse = Depends(require_professor),
    db: Database = Depends(get_database)
) -> dict:
    document = get_document_by_id_service(document_id, db)
    if document is None:
        raise DocumentNotFoundError(f"Document with ID {document_id} not found")

    delete_document_service(document_id, db)

    log_event(
        "document_deleted",
        level="info",
        user_email=current_user.email,
        details={
            "document_id": document_id,
            "filename": document.filename,
            "course_code": document.course_code
        }
    )

    return {"message": f"Document {document_id} deleted successfully"}
