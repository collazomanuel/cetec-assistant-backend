import boto3
from botocore.exceptions import ClientError
from app.config import settings


def get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_region,
    )


def upload_file_to_s3(file_content: bytes, s3_key: str, content_type: str) -> None:
    s3_client = get_s3_client()
    try:
        s3_client.put_object(
            Bucket=settings.s3_bucket_name,
            Key=s3_key,
            Body=file_content,
            ContentType=content_type,
        )
    except ClientError as e:
        raise Exception(f"Failed to upload file to S3: {str(e)}")


def generate_presigned_url(s3_key: str, expiration: int = 3600) -> str:
    s3_client = get_s3_client()
    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.s3_bucket_name, "Key": s3_key},
            ExpiresIn=expiration,
        )
        return url
    except ClientError as e:
        raise Exception(f"Failed to generate presigned URL: {str(e)}")


def delete_file_from_s3(s3_key: str) -> None:
    s3_client = get_s3_client()
    try:
        s3_client.delete_object(Bucket=settings.s3_bucket_name, Key=s3_key)
    except ClientError as e:
        raise Exception(f"Failed to delete file from S3: {str(e)}")
