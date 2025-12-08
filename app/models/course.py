from pydantic import BaseModel, Field


class CourseResponse(BaseModel):
    code: str
    name: str
    description: str | None = None


class CourseCreate(BaseModel):
    code: str
    name: str
    description: str | None = None


class CourseUpdate(BaseModel):
    code: str
    new_code: str | None = None
    name: str | None = None
    description: str | None = None


class CourseDelete(BaseModel):
    code: str
