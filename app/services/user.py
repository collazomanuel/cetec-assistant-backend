from pymongo import ReturnDocument
from pymongo.database import Database

from app.exceptions import UserAlreadyExistsError, UserNotFoundError
from app.models.user import Role, UserResponse


def get_user_by_email(email: str, db: Database) -> UserResponse | None:
    user_doc = db.users.find_one({"email": email})
    if user_doc is None:
        return None
    return UserResponse(
        email=user_doc["email"],
        name=user_doc["name"],
        roles=user_doc["roles"]
    )


def get_all_users(db: Database) -> list[UserResponse]:
    users = []
    for user_doc in db.users.find():
        users.append(UserResponse(
            email=user_doc["email"],
            name=user_doc["name"],
            roles=user_doc["roles"]
        ))
    return users


def create_user(email: str, name: str, roles: list[Role], db: Database) -> UserResponse:
    existing_user = db.users.find_one({"email": email})
    if existing_user:
        raise UserAlreadyExistsError(f"User with email {email} already exists")

    user_doc = {
        "email": email,
        "name": name,
        "roles": roles
    }
    db.users.insert_one(user_doc)
    return UserResponse(email=email, name=name, roles=roles)


def update_user(email: str, db: Database, name: str | None = None, roles: list[Role] | None = None) -> UserResponse:
    
    update_fields = {}
    if name is not None:
        update_fields["name"] = name
    if roles is not None:
        update_fields["roles"] = roles

    if not update_fields:
        user_doc = db.users.find_one({"email": email})
        if not user_doc:
            raise UserNotFoundError(f"User with email {email} not found")
        return UserResponse(
            email=user_doc["email"],
            name=user_doc["name"],
            roles=user_doc["roles"]
        )

    updated_user = db.users.find_one_and_update(
        {"email": email},
        {"$set": update_fields},
        return_document=ReturnDocument.AFTER
    )

    if not updated_user:
        raise UserNotFoundError(f"User with email {email} not found")

    return UserResponse(
        email=updated_user["email"],
        name=updated_user["name"],
        roles=updated_user["roles"]
    )


def delete_user(email: str, db: Database) -> None:
    result = db.users.delete_one({"email": email})
    if result.deleted_count == 0:
        raise UserNotFoundError(f"User with email {email} not found")

