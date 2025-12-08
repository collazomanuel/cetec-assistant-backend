import uuid
import re
from datetime import datetime, timezone
from pymongo.database import Database
from app.models.document import DocumentResponse
from app.exceptions import DocumentNotFoundError, DocumentUploadError
from app.services.s3 import upload_file_to_s3, delete_file_from_s3, generate_presigned_url


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe S3 storage.
    Replaces spaces with underscores and removes special characters.
    """
    # Replace spaces with underscores
    filename = filename.replace(" ", "_")
    # Remove any character that's not alphanumeric, underscore, dash, or dot
    filename = re.sub(r"[^\w\-.]", "", filename)
    return filename


def create_document(
    course_code: str,
    filename: str,
    file_content: bytes,
    content_type: str,
    file_size: int,
    uploaded_by: str,
    db: Database
) -> DocumentResponse:
    document_id = str(uuid.uuid4())
    # Sanitize the filename for S3 key
    safe_filename = sanitize_filename(filename)
    s3_key = f"documents/{course_code}/{document_id}/{safe_filename}"

    try:
        upload_file_to_s3(file_content, s3_key, content_type)
    except Exception as e:
        raise DocumentUploadError(f"Failed to upload document: {str(e)}")

    document_doc = {
        "document_id": document_id,
        "course_code": course_code,
        "filename": filename,
        "s3_key": s3_key,
        "upload_timestamp": datetime.now(timezone.utc),
        "uploaded_by": uploaded_by,
        "file_size": file_size,
        "content_type": content_type
    }

    db.documents.insert_one(document_doc)

    return DocumentResponse(
        document_id=document_id,
        course_code=course_code,
        filename=filename,
        s3_key=s3_key,
        upload_timestamp=document_doc["upload_timestamp"],
        uploaded_by=uploaded_by,
        file_size=file_size,
        content_type=content_type
    )


def get_documents_by_course(course_code: str, db: Database) -> list[DocumentResponse]:
    documents = []
    for doc in db.documents.find({"course_code": course_code}):
        documents.append(DocumentResponse(
            document_id=doc["document_id"],
            course_code=doc["course_code"],
            filename=doc["filename"],
            s3_key=doc["s3_key"],
            upload_timestamp=doc["upload_timestamp"],
            uploaded_by=doc["uploaded_by"],
            file_size=doc["file_size"],
            content_type=doc["content_type"]
        ))
    return documents


def get_document_by_id(document_id: str, db: Database) -> DocumentResponse | None:
    doc = db.documents.find_one({"document_id": document_id})
    if doc is None:
        return None

    return DocumentResponse(
        document_id=doc["document_id"],
        course_code=doc["course_code"],
        filename=doc["filename"],
        s3_key=doc["s3_key"],
        upload_timestamp=doc["upload_timestamp"],
        uploaded_by=doc["uploaded_by"],
        file_size=doc["file_size"],
        content_type=doc["content_type"]
    )


def delete_document(document_id: str, db: Database) -> None:
    doc = db.documents.find_one({"document_id": document_id})
    if doc is None:
        raise DocumentNotFoundError(f"Document with ID {document_id} not found")

    s3_key = doc["s3_key"]

    try:
        delete_file_from_s3(s3_key)
    except Exception as e:
        raise DocumentUploadError(f"Failed to delete document from S3: {str(e)}")

    result = db.documents.delete_one({"document_id": document_id})
    if result.deleted_count == 0:
        raise DocumentNotFoundError(f"Document with ID {document_id} not found")


def get_document_download_url(document_id: str, db: Database) -> str:
    doc = db.documents.find_one({"document_id": document_id})
    if doc is None:
        raise DocumentNotFoundError(f"Document with ID {document_id} not found")

    s3_key = doc["s3_key"]
    return generate_presigned_url(s3_key)
