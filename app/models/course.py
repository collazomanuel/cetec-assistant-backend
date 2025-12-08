from pydantic import BaseModel, Field


class CourseResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str | None = None


class CourseCreate(BaseModel):
    code: str
    name: str
    description: str | None = None


class CourseUpdate(BaseModel):
    id: str
    code: str | None = None
    name: str | None = None
    description: str | None = None


class CourseDelete(BaseModel):
    id: str
