from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import ensure_indexes
from app.exceptions import (
    AuthenticationError,
    UserNotFoundError,
    UnregisteredUserError,
    ForbiddenError,
    UserAlreadyExistsError,
    CannotDeleteSelfError
)
from app.handlers import (
    authentication_error_handler,
    user_not_found_error_handler,
    user_not_registered_error_handler,
    forbidden_error_handler,
    user_already_exists_error_handler,
    cannot_delete_self_error_handler
)
from app.routers import health, users


app = FastAPI()
ensure_indexes()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AuthenticationError, authentication_error_handler)
app.add_exception_handler(UserNotFoundError, user_not_found_error_handler)
app.add_exception_handler(UnregisteredUserError, user_not_registered_error_handler)
app.add_exception_handler(ForbiddenError, forbidden_error_handler)
app.add_exception_handler(UserAlreadyExistsError, user_already_exists_error_handler)
app.add_exception_handler(CannotDeleteSelfError, cannot_delete_self_error_handler)

app.include_router(health.router)
app.include_router(users.router)

