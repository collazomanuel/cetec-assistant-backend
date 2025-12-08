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

