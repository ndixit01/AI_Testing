import logging
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

from app.config import get_settings

logger = logging.getLogger(__name__)


def _get_client():
    s = get_settings()
    return boto3.client(
        "s3",
        aws_access_key_id=s.aws_access_key_id,
        aws_secret_access_key=s.aws_secret_access_key,
        region_name=s.aws_region,
    )


def _build_key(opportunity_id: str, filename: str) -> str:
    """
    Build an immutable, timestamped S3 key for SOX traceability.
    Pattern: opportunities/{opp_id}/{UTC_timestamp}/{filename}
    """
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_filename = filename.replace(" ", "_")
    return f"opportunities/{opportunity_id}/{ts}/{safe_filename}"


def upload_file(
    file_bytes: bytes,
    filename: str,
    opportunity_id: str,
    content_type: str = "application/octet-stream",
) -> dict:
    """
    Upload a file to S3 under the opportunity's folder.
    Returns a dict with 'key' and 'url'.
    The bucket must be private and versioning-enabled for SOX compliance.
    """
    s = get_settings()
    client = _get_client()
    key = _build_key(opportunity_id, filename)

    try:
        client.put_object(
            Bucket=s.s3_bucket_name,
            Key=key,
            Body=file_bytes,
            ContentType=content_type,
            Metadata={
                "opportunity-id": opportunity_id,
                "original-filename": filename,
                "uploaded-at": datetime.now(timezone.utc).isoformat(),
            },
            ServerSideEncryption="AES256",  # SSE-S3 encryption at rest
        )
    except ClientError as exc:
        logger.error(
            "s3_upload_failed",
            extra={"opportunity_id": opportunity_id, "filename": filename, "error": str(exc)},
        )
        raise

    # S3 URL (path-style, private — access via presigned URL if needed)
    url = f"https://s3.amazonaws.com/{s.s3_bucket_name}/{key}"

    logger.info(
        "s3_upload_success",
        extra={"opportunity_id": opportunity_id, "key": key, "bucket": s.s3_bucket_name},
    )
    return {"key": key, "url": url}


def generate_presigned_url(key: str, expiry_seconds: int = 3600) -> str:
    """Generate a presigned GET URL for internal review access."""
    s = get_settings()
    client = _get_client()
    try:
        url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": s.s3_bucket_name, "Key": key},
            ExpiresIn=expiry_seconds,
        )
        return url
    except ClientError as exc:
        logger.error("s3_presign_failed", extra={"key": key, "error": str(exc)})
        raise
