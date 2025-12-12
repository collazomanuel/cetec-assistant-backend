from typing import Literal
from pydantic import BaseModel, EmailStr, field_validator


Role = Literal["student", "professor", "admin"]


class UserResponse(BaseModel):
    email: EmailStr
    name: str
    roles: list[Role]


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    roles: list[Role]

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        if len(v) > 200:
            raise ValueError("Name cannot exceed 200 characters")
        return v.strip()

    @field_validator("roles")
    @classmethod
    def validate_roles(cls, v: list[Role]) -> list[Role]:
        if not v:
            raise ValueError("User must have at least one role")
        if len(v) > 10:
            raise ValueError("User cannot have more than 10 roles")
        seen = set()
        unique_roles = []
        for role in v:
            if role not in seen:
                seen.add(role)
                unique_roles.append(role)
        return unique_roles


class UserUpdate(BaseModel):
    email: EmailStr
    name: str | None = None
    roles: list[Role] | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        if v is not None:
            if not v.strip():
                raise ValueError("Name cannot be empty")
            if len(v) > 200:
                raise ValueError("Name cannot exceed 200 characters")
            return v.strip()
        return v

    @field_validator("roles")
    @classmethod
    def validate_roles(cls, v: list[Role] | None) -> list[Role] | None:
        if v is not None:
            if not v:
                raise ValueError("User must have at least one role")
            if len(v) > 10:
                raise ValueError("User cannot have more than 10 roles")
            seen = set()
            unique_roles = []
            for role in v:
                if role not in seen:
                    seen.add(role)
                    unique_roles.append(role)
            return unique_roles
        return v


class UserDelete(BaseModel):
    email: EmailStr

