from datetime import datetime
from pydantic import BaseModel


class DocumentResponse(BaseModel):
    document_id: str
    course_code: str
    filename: str
    s3_key: str
    upload_timestamp: datetime
    uploaded_by: str
    file_size: int
    content_type: str


class DocumentCreate(BaseModel):
    course_code: str
    filename: str
    file_size: int
    content_type: str


class DocumentWithDownloadUrl(BaseModel):
    document: DocumentResponse
    download_url: str


class DocumentDelete(BaseModel):
    document_id: str
