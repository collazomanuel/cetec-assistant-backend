from typing import TYPE_CHECKING

from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pymongo.database import Database
from qdrant_client import QdrantClient

from app.database import get_database
from app.exceptions import AuthenticationError, UnregisteredUserError, ForbiddenError
from app.models.user import UserResponse
from app.services.auth import verify_google_token
from app.services.user import get_user_by_email
from app.services.log import log_event

if TYPE_CHECKING:
    from app.services.embedder import BaseEmbedder


security = HTTPBearer()


def get_embedder(request: Request) -> "BaseEmbedder":
    """Dependency to get the embedder instance from app state."""
    return request.app.state.embedder


def get_qdrant_client(request: Request) -> QdrantClient:
    """Dependency to get the Qdrant client instance from app state."""
    return request.app.state.qdrant_client


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Database = Depends(get_database)
) -> UserResponse:
    token = credentials.credentials

    try:
        email = verify_google_token(token)
    except AuthenticationError as e:
        log_event("auth_failure", level="warning", user_email=None, details={"reason": str(e)})
        raise

    user = get_user_by_email(email, db)
    if user is None:
        log_event("auth_failure", level="warning", user_email=email, details={"reason": "User not registered"})
        raise UnregisteredUserError(f"User with email {email} is not registered")

    log_event("auth_success", level="info", user_email=email, details={"roles": user.roles})
    return user


def require_student(user: UserResponse = Depends(get_current_user)) -> UserResponse:
    if not any(role in user.roles for role in ["student", "professor", "admin"]):
        raise ForbiddenError("Student, professor, or admin role required")
    return user


def require_professor(user: UserResponse = Depends(get_current_user)) -> UserResponse:
    if not any(role in user.roles for role in ["professor", "admin"]):
        raise ForbiddenError("Professor or admin role required")
    return user


def require_admin(user: UserResponse = Depends(get_current_user)) -> UserResponse:
    if "admin" not in user.roles:
        raise ForbiddenError("Admin role required")
    return user
