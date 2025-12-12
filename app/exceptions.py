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


class DocumentDeleteError(Exception):
    pass


class FileTooLargeError(Exception):
    pass


class IngestionJobNotFoundError(Exception):
    pass


class IngestionJobError(Exception):
    pass


class PDFExtractionError(Exception):
    pass


class EmbeddingError(Exception):
    pass


class VectorStoreError(Exception):
    pass


class StorageError(Exception):
    """Base exception for S3/storage operations."""
    pass


class StorageUploadError(StorageError):
    """Exception for S3 upload failures."""
    pass


class StorageDownloadError(StorageError):
    """Exception for S3 download failures."""
    pass


class StorageDeleteError(StorageError):
    """Exception for S3 deletion failures."""
    pass


class StorageURLError(StorageError):
    """Exception for presigned URL generation failures."""
    pass

