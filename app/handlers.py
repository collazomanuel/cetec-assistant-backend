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
    FileTooLargeError
)


def authentication_error_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc)}
    )


def user_not_found_error_handler(request: Request, exc: UserNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)}
    )


def user_not_registered_error_handler(request: Request, exc: UnregisteredUserError) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={"detail": str(exc)}
    )


def forbidden_error_handler(request: Request, exc: ForbiddenError) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={"detail": str(exc)}
    )


def user_already_exists_error_handler(request: Request, exc: UserAlreadyExistsError) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": str(exc)}
    )


def cannot_delete_self_error_handler(request: Request, exc: CannotDeleteSelfError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )


def course_not_found_error_handler(request: Request, exc: CourseNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)}
    )


def course_already_exists_error_handler(request: Request, exc: CourseAlreadyExistsError) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": str(exc)}
    )


def document_not_found_error_handler(request: Request, exc: DocumentNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)}
    )


def document_upload_error_handler(request: Request, exc: DocumentUploadError) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )


def file_too_large_error_handler(request: Request, exc: FileTooLargeError) -> JSONResponse:
    return JSONResponse(
        status_code=413,
        content={"detail": str(exc)}
    )
