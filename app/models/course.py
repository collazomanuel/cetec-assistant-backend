import re
from pydantic import BaseModel, field_validator

from app.constants import COURSE_CODE_PATTERN


class CourseResponse(BaseModel):
    code: str
    name: str
    description: str | None = None


class CourseCreate(BaseModel):
    code: str
    name: str
    description: str | None = None

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Course code cannot be empty")
        v = v.strip().upper()
        if not re.match(COURSE_CODE_PATTERN, v):
            raise ValueError(
                "Course code must be 2-20 characters, containing only letters, numbers, and hyphens"
            )
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Course name cannot be empty")
        if len(v) > 200:
            raise ValueError("Course name cannot exceed 200 characters")
        return v.strip()

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        if v is not None:
            if len(v) > 2000:
                raise ValueError("Course description cannot exceed 2000 characters")
            return v.strip() if v.strip() else None
        return v


class CourseUpdate(BaseModel):
    code: str
    name: str | None = None
    description: str | None = None

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Course code cannot be empty")
        v = v.strip().upper()
        if not re.match(COURSE_CODE_PATTERN, v):
            raise ValueError(
                "Course code must be 2-20 characters, containing only letters, numbers, and hyphens"
            )
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        if v is not None:
            if not v.strip():
                raise ValueError("Course name cannot be empty")
            if len(v) > 200:
                raise ValueError("Course name cannot exceed 200 characters")
            return v.strip()
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        if v is not None:
            if len(v) > 2000:
                raise ValueError("Course description cannot exceed 2000 characters")
            return v.strip() if v.strip() else None
        return v


class CourseDelete(BaseModel):
    code: str

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Course code cannot be empty")
        v = v.strip().upper()
        if not re.match(COURSE_CODE_PATTERN, v):
            raise ValueError(
                "Course code must be 2-20 characters, containing only letters, numbers, and hyphens"
            )
        return v
