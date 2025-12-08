class AuthenticationError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class UnregisteredUserError(Exception):
    pass


class ForbiddenError(Exception):
    pass


class UserAlreadyExistsError(Exception):
    pass


class CannotDeleteSelfError(Exception):
    pass


class CourseNotFoundError(Exception):
    pass


class CourseAlreadyExistsError(Exception):
    pass


class DocumentNotFoundError(Exception):
    pass


class DocumentUploadError(Exception):
    pass


class FileTooLargeError(Exception):
    pass

