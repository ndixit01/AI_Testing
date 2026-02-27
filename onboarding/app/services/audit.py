"""
SOX Audit Logging Service

Every material event (link generated, application submitted, file stored) is written
as a structured JSON log entry. These logs flow to CloudWatch via the standard
Python logging handler and can be piped to Snowflake later via your existing
SnapLogic/Parabola pipelines.

Each event has a unique `event_id` for end-to-end traceability.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("sox_audit")


def _emit(event_type: str, payload: dict) -> str:
    """
    Write a structured audit event. Returns the event_id.
    All fields are top-level for easy CloudWatch Insights querying.
    """
    event_id = str(uuid.uuid4())
    entry = {
        "event_id": event_id,
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    # Using .info() with the raw JSON string ensures CloudWatch sees a single
    # parseable JSON line per event — compatible with metric filters and Insights.
    logger.info(json.dumps(entry))
    return event_id


def log_link_generated(
    opportunity_id: str,
    jti: str,
    expires_at: str,
    requested_by_ip: str,
) -> str:
    return _emit(
        "LINK_GENERATED",
        {
            "opportunity_id": opportunity_id,
            "token_jti": jti,
            "expires_at": expires_at,
            "requested_by_ip": requested_by_ip,
        },
    )


def log_link_verified(
    opportunity_id: str,
    jti: str,
    verified_from_ip: str,
) -> str:
    return _emit(
        "LINK_VERIFIED",
        {
            "opportunity_id": opportunity_id,
            "token_jti": jti,
            "verified_from_ip": verified_from_ip,
        },
    )


def log_application_submitted(
    opportunity_id: str,
    jti: str,
    s3_keys: list[str],
    sf_content_version_ids: list[str],
    sf_patch_status: int,
    submitted_from_ip: str,
    user_agent: str,
) -> str:
    return _emit(
        "APPLICATION_SUBMITTED",
        {
            "opportunity_id": opportunity_id,
            "token_jti": jti,
            "s3_keys": s3_keys,
            "sf_content_version_ids": sf_content_version_ids,
            "sf_patch_status": sf_patch_status,
            "submitted_from_ip": submitted_from_ip,
            "user_agent": user_agent,
        },
    )


def log_file_uploaded(
    opportunity_id: str,
    jti: str,
    filename: str,
    s3_key: str,
    sf_content_version_id: str,
) -> str:
    return _emit(
        "FILE_UPLOADED",
        {
            "opportunity_id": opportunity_id,
            "token_jti": jti,
            "filename": filename,
            "s3_key": s3_key,
            "sf_content_version_id": sf_content_version_id,
        },
    )


def log_error(
    event_context: str,
    opportunity_id: Optional[str],
    jti: Optional[str],
    error_message: str,
    client_ip: str,
) -> str:
    return _emit(
        "ERROR",
        {
            "event_context": event_context,
            "opportunity_id": opportunity_id,
            "token_jti": jti,
            "error_message": error_message,
            "client_ip": client_ip,
        },
    )
