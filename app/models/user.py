from typing import Literal
from pydantic import BaseModel, EmailStr


Role = Literal["student", "professor", "admin"]


class UserResponse(BaseModel):
    email: EmailStr
    name: str
    roles: list[Role]


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    roles: list[Role]


class UserUpdate(BaseModel):
    email: EmailStr
    name: str | None = None
    roles: list[Role] | None = None


class UserDelete(BaseModel):
    email: EmailStr

