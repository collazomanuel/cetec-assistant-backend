from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.database import get_database
from app.dependencies import get_current_user, require_admin
from app.exceptions import UserNotFoundError, CannotDeleteSelfError
from app.models.user import UserResponse, UserCreate, UserUpdate, UserDelete
from app.services import user as user_service
from app.services.log import log_event


router = APIRouter(prefix="/users")


@router.get("/me")
async def get_me(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    return current_user


@router.get("")
async def get_users(
    email: str | None = None,
    current_user: UserResponse = Depends(require_admin),
    db: Database = Depends(get_database)
) -> list[UserResponse]:
    if email:
        user = user_service.get_user_by_email(email, db)
        if user is None:
            raise UserNotFoundError(f"User with email {email} not found")
        return [user]
    return user_service.get_all_users(db)


@router.post("")
async def create_user(
    user_data: UserCreate,
    current_user: UserResponse = Depends(require_admin),
    db: Database = Depends(get_database)
) -> UserResponse:
    user = user_service.create_user(user_data.email, user_data.name, user_data.roles, db)
    log_event(
        "user_created",
        level="info",
        user_email=current_user.email,
        details={"created_user_email": user.email}
    )
    return user


@router.patch("")
async def update_user(
    user_data: UserUpdate,
    current_user: UserResponse = Depends(require_admin),
    db: Database = Depends(get_database)
) -> UserResponse:
    user = user_service.update_user(user_data.email, db, name=user_data.name, roles=user_data.roles)
    log_event(
        "user_updated",
        level="info",
        user_email=current_user.email,
        details={"updated_user_email": user.email}
    )
    return user


@router.delete("")
async def delete_user(
    user_data: UserDelete,
    current_user: UserResponse = Depends(require_admin),
    db: Database = Depends(get_database)
) -> dict[str, str]:
    if user_data.email == current_user.email:
        raise CannotDeleteSelfError("Cannot delete your own account")

    user_service.delete_user(user_data.email, db)
    log_event(
        "user_deleted",
        level="info",
        user_email=current_user.email,
        details={"deleted_user_email": user_data.email}
    )
    return {"message": "User deleted successfully"}

