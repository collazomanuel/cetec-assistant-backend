import re
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, field_validator

from app.constants import COURSE_CODE_PATTERN


class IngestionMode(str, Enum):
    NEW = "NEW"
    SELECTED = "SELECTED"
    ALL = "ALL"
    REINGEST = "REINGEST"


class IngestionStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


class IngestionJobCreate(BaseModel):
    course_code: str
    mode: IngestionMode = IngestionMode.NEW
    document_ids: list[str] | None = None
    max_retries: int = 3

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

    @field_validator("document_ids")
    @classmethod
    def validate_document_ids(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            if len(v) > 1000:
                raise ValueError("Cannot process more than 1000 documents in a single job")
            for doc_id in v:
                if not re.match(r"^[a-f0-9\-]{36}$", doc_id.lower()):
                    raise ValueError(f"Invalid document ID format: {doc_id}")
        return v

    @field_validator("max_retries")
    @classmethod
    def validate_max_retries(cls, v: int) -> int:
        if v < 0:
            raise ValueError("max_retries cannot be negative")
        if v > 10:
            raise ValueError("max_retries cannot exceed 10")
        return v


class IngestionJobCancel(BaseModel):
    job_id: str

    @field_validator("job_id")
    @classmethod
    def validate_job_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Job ID cannot be empty")
        if not re.match(r"^[a-f0-9\-]{36}$", v.lower()):
            raise ValueError("Job ID must be a valid UUID")
        return v.strip()


class IngestionJobRetry(BaseModel):
    job_id: str

    @field_validator("job_id")
    @classmethod
    def validate_job_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Job ID cannot be empty")
        if not re.match(r"^[a-f0-9\-]{36}$", v.lower()):
            raise ValueError("Job ID must be a valid UUID")
        return v.strip()


class IngestionJobResponse(BaseModel):
    job_id: str
    course_code: str
    status: IngestionStatus
    mode: IngestionMode
    docs_total: int
    docs_done: int
    vectors_created: int
    created_at: datetime
    updated_at: datetime
    created_by: str
    error_message: str | None = None
    retry_count: int = 0
    max_retries: int = 3
