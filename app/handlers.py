from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions import (
    AuthenticationError,
    UserNotFoundError,
    UnregisteredUserError,
    ForbiddenError,
    UserAlreadyExistsError,
    CannotDeleteSelfError,
    CourseNotFoundError,
    CourseAlreadyExistsError,
    DocumentNotFoundError,
    DocumentUploadError,
    DocumentDeleteError,
    FileTooLargeError
)


def create_error_handler(status_code: int):
    def handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status_code,
            content={"detail": str(exc)}
        )
    return handler


EXCEPTION_HANDLERS = {
    AuthenticationError: 401,
    UserNotFoundError: 404,
    CourseNotFoundError: 404,
    DocumentNotFoundError: 404,
    UnregisteredUserError: 403,
    ForbiddenError: 403,
    UserAlreadyExistsError: 409,
    CourseAlreadyExistsError: 409,
    CannotDeleteSelfError: 400,
    DocumentUploadError: 500,
    DocumentDeleteError: 500,
    FileTooLargeError: 413,
}


def register_exception_handlers(app):
    for exception_class, status_code in EXCEPTION_HANDLERS.items():
        app.add_exception_handler(
            exception_class,
            create_error_handler(status_code)
        )
