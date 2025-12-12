import re
import boto3
from botocore.exceptions import ClientError

from app.config import settings
from app.exceptions import StorageUploadError, StorageDownloadError, StorageDeleteError, StorageURLError


def validate_s3_config() -> None:
    """Validate that all required S3 configuration is present."""
    missing_configs = []

    if not settings.aws_access_key_id:
        missing_configs.append("AWS_ACCESS_KEY_ID")
    if not settings.aws_secret_access_key:
        missing_configs.append("AWS_SECRET_ACCESS_KEY")
    if not settings.aws_region:
        missing_configs.append("AWS_REGION")
    if not settings.s3_bucket_name:
        missing_configs.append("S3_BUCKET_NAME")

    if missing_configs:
        raise ValueError(
            f"Missing required S3 configuration: {', '.join(missing_configs)}. "
            "Please check your environment variables."
        )


def validate_s3_key(s3_key: str) -> None:
    """
    Validate S3 key format to prevent path traversal and other security issues.

    S3 keys should:
    - Not be empty
    - Not contain consecutive slashes
    - Not contain path traversal patterns (../)
    - Not start with a slash
    - Only contain safe characters
    """
    if not s3_key or not s3_key.strip():
        raise ValueError("S3 key cannot be empty")

    if s3_key.startswith("/"):
        raise ValueError("S3 key cannot start with a slash")

    if "//" in s3_key:
        raise ValueError("S3 key cannot contain consecutive slashes")

    if "../" in s3_key or "/.." in s3_key:
        raise ValueError("S3 key cannot contain path traversal patterns")

    # Allow alphanumeric, hyphens, underscores, dots, and forward slashes
    if not re.match(r'^[a-zA-Z0-9/_.\-]+$', s3_key):
        raise ValueError("S3 key contains invalid characters")


def validate_expiration(expiration: int) -> None:
    """
    Validate presigned URL expiration time.

    Max allowed: 7 days (604800 seconds)
    Min allowed: 1 second
    """
    MAX_EXPIRATION = 604800  # 7 days in seconds
    MIN_EXPIRATION = 1

    if expiration < MIN_EXPIRATION:
        raise ValueError(f"Expiration time must be at least {MIN_EXPIRATION} second")

    if expiration > MAX_EXPIRATION:
        raise ValueError(f"Expiration time cannot exceed {MAX_EXPIRATION} seconds (7 days)")


def get_s3_client():
    validate_s3_config()
    return boto3.client(
        "s3",
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_region,
    )


def upload_file_to_s3(file_obj, s3_key: str, content_type: str) -> None:
    validate_s3_key(s3_key)
    s3_client = get_s3_client()
    try:
        s3_client.put_object(
            Bucket=settings.s3_bucket_name,
            Key=s3_key,
            Body=file_obj,
            ContentType=content_type,
        )
    except ClientError as e:
        raise StorageUploadError(f"Failed to upload file to S3: {str(e)}") from e


def generate_presigned_url(s3_key: str, expiration: int = 3600) -> str:
    validate_s3_key(s3_key)
    validate_expiration(expiration)
    s3_client = get_s3_client()
    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.s3_bucket_name, "Key": s3_key},
            ExpiresIn=expiration,
        )
        return url
    except ClientError as e:
        raise StorageURLError(f"Failed to generate presigned URL: {str(e)}") from e


def delete_file_from_s3(s3_key: str) -> None:
    validate_s3_key(s3_key)
    s3_client = get_s3_client()
    try:
        s3_client.delete_object(Bucket=settings.s3_bucket_name, Key=s3_key)
    except ClientError as e:
        raise StorageDeleteError(f"Failed to delete file from S3: {str(e)}") from e


def download_file_from_s3(s3_key: str) -> bytes:
    validate_s3_key(s3_key)
    s3_client = get_s3_client()
    try:
        response = s3_client.get_object(Bucket=settings.s3_bucket_name, Key=s3_key)
        return response["Body"].read()
    except ClientError as e:
        raise StorageDownloadError(f"Failed to download file from S3: {str(e)}") from e
