import re
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, field_validator

from app.constants import COURSE_CODE_PATTERN


class DocumentStatus(str, Enum):
    UPLOADED = "UPLOADED"
    INGESTED = "INGESTED"
    FAILED = "FAILED"


class DocumentResponse(BaseModel):
    document_id: str
    course_code: str
    filename: str
    s3_key: str
    upload_timestamp: datetime
    uploaded_by: str
    file_size: int
    content_type: str
    status: DocumentStatus = DocumentStatus.UPLOADED


class DocumentCreate(BaseModel):
    course_code: str
    filename: str
    file_size: int
    content_type: str

    @field_validator("course_code")
    @classmethod
    def validate_course_code(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Course code cannot be empty")
        v = v.strip().upper()
        if not re.match(COURSE_CODE_PATTERN, v):
            raise ValueError(
                "Course code must be 2-20 characters, containing only letters, numbers, and hyphens"
            )
        return v

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Filename cannot be empty")
        if len(v) > 255:
            raise ValueError("Filename cannot exceed 255 characters")
        return v.strip()

    @field_validator("file_size")
    @classmethod
    def validate_file_size(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("File size must be positive")
        return v

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Content type cannot be empty")
        if not re.match(r"^[a-z]+/[a-z0-9\+\-\.]+$", v.lower()):
            raise ValueError("Invalid content type format")
        return v.lower()


class DocumentWithDownloadUrl(BaseModel):
    document: DocumentResponse
    download_url: str


class DocumentDelete(BaseModel):
    document_id: str

    @field_validator("document_id")
    @classmethod
    def validate_document_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Document ID cannot be empty")
        if not re.match(r"^[a-f0-9\-]{36}$", v.lower()):
            raise ValueError("Document ID must be a valid UUID")
        return v.strip()
