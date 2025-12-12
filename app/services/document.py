import uuid
import re
import os
from datetime import datetime, timezone
from typing import BinaryIO

from pymongo.database import Database
from qdrant_client import QdrantClient

from pymongo.errors import PyMongoError

from app.exceptions import (
    DocumentNotFoundError,
    DocumentUploadError,
    DocumentDeleteError,
    StorageError,
    VectorStoreError
)
from app.models.document import DocumentResponse, DocumentStatus
from app.services.s3 import upload_file_to_s3, delete_file_from_s3, generate_presigned_url
from app.services.qdrant import delete_document_vectors
from app.services.log import log_event


WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
}


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent security issues:
    - Remove path traversal attempts
    - Handle reserved Windows filenames
    - Limit length
    - Remove dangerous characters
    """
    if not filename or not filename.strip():
        raise DocumentUploadError("Filename cannot be empty")

    filename = os.path.basename(filename)

    filename = filename.replace('\x00', '')
    filename = filename.replace('/', '_')
    filename = filename.replace('\\', '_')
    filename = filename.replace('..', '_')

    filename = filename.replace(" ", "_")

    filename = re.sub(r"[^\w\-.]", "", filename)

    if not filename or filename == ".":
        raise DocumentUploadError("Filename is invalid after sanitization")

    parts = filename.rsplit(".", 1)
    name = parts[0]
    ext = parts[1] if len(parts) > 1 else ""

    if name.upper() in WINDOWS_RESERVED_NAMES:
        name = f"file_{name}"

    max_name_length = 200 if not ext else 200 - len(ext) - 1
    if len(name) > max_name_length:
        name = name[:max_name_length]

    sanitized = f"{name}.{ext}" if ext else name

    if len(sanitized) < 1 or len(sanitized) > 255:
        raise DocumentUploadError("Filename length is invalid")

    return sanitized


def create_document(
    course_code: str,
    filename: str,
    file_obj: BinaryIO,
    content_type: str,
    file_size: int,
    uploaded_by: str,
    db: Database
) -> DocumentResponse:
    document_id = str(uuid.uuid4())
    safe_filename = sanitize_filename(filename)
    s3_key = f"documents/{course_code}/{document_id}/{safe_filename}"

    try:
        upload_file_to_s3(file_obj, s3_key, content_type)
    except StorageError as e:
        raise DocumentUploadError(f"Failed to upload document: {str(e)}") from e

    document_doc = {
        "document_id": document_id,
        "course_code": course_code,
        "filename": filename,
        "s3_key": s3_key,
        "upload_timestamp": datetime.now(timezone.utc),
        "uploaded_by": uploaded_by,
        "file_size": file_size,
        "content_type": content_type,
        "status": DocumentStatus.UPLOADED.value
    }

    try:
        db.documents.insert_one(document_doc)
    except PyMongoError as e:
        try:
            delete_file_from_s3(s3_key)
            log_event(
                "document_rollback_success",
                level="info",
                details={"document_id": document_id, "s3_key": s3_key}
            )
        except StorageError as rollback_error:
            log_event(
                "document_rollback_failed",
                level="error",
                details={
                    "document_id": document_id,
                    "s3_key": s3_key,
                    "error": str(rollback_error)
                }
            )
        raise DocumentUploadError(f"Failed to save document metadata: {str(e)}") from e

    return DocumentResponse(
        document_id=document_id,
        course_code=course_code,
        filename=filename,
        s3_key=s3_key,
        upload_timestamp=document_doc["upload_timestamp"],
        uploaded_by=uploaded_by,
        file_size=file_size,
        content_type=content_type,
        status=DocumentStatus.UPLOADED
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
            content_type=doc["content_type"],
            status=doc.get("status", DocumentStatus.UPLOADED.value)
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
        content_type=doc["content_type"],
        status=doc.get("status", DocumentStatus.UPLOADED.value)
    )


def delete_document(document_id: str, db: Database, qdrant_client: QdrantClient) -> None:
    doc = db.documents.find_one({"document_id": document_id})
    if doc is None:
        raise DocumentNotFoundError(f"Document with ID {document_id} not found")

    s3_key = doc["s3_key"]

    try:
        delete_file_from_s3(s3_key)
    except StorageError as e:
        raise DocumentDeleteError(f"Failed to delete document from S3: {str(e)}") from e

    try:
        delete_document_vectors(qdrant_client, document_id)
    except VectorStoreError as e:
        log_event(
            "vector_deletion_failed",
            level="warning",
            details={"document_id": document_id, "error": str(e)}
        )

    result = db.documents.delete_one({"document_id": document_id})
    if result.deleted_count == 0:
        raise DocumentNotFoundError(f"Document with ID {document_id} not found")


def get_document_download_url(document_id: str, db: Database) -> str:
    doc = db.documents.find_one({"document_id": document_id})
    if doc is None:
        raise DocumentNotFoundError(f"Document with ID {document_id} not found")

    s3_key = doc["s3_key"]
    return generate_presigned_url(s3_key)
