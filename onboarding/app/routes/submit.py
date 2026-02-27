import mimetypes
from datetime import datetime, timezone
from typing import List

import jwt
from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Form

from app.config import get_settings
from app.models import SubmitResponse
from app.services import audit, s3 as s3_service, salesforce

router = APIRouter(prefix="/api/submit", tags=["submit"])

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/heic",
    "image/webp",
}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB per file


def _decode_token(token: str) -> dict:
    s = get_settings()
    try:
        return jwt.decode(token, s.jwt_secret, algorithms=[s.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Link has expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token.")


@router.post("/application", response_model=SubmitResponse)
async def submit_application(
    request: Request,
    token: str = Form(...),
    # Personal
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    date_of_birth: str = Form(...),
    # TLC
    tlc_license_number: str = Form(...),
    tlc_expiration_date: str = Form(...),
    dmv_license_number: str = Form(...),
    dmv_license_state: str = Form(...),
    # Vehicle (optional)
    vehicle_vin: str = Form(None),
    vehicle_year: str = Form(None),
    vehicle_make: str = Form(None),
    vehicle_model: str = Form(None),
    vehicle_color: str = Form(None),
    vehicle_plate: str = Form(None),
    # Insurance (optional)
    insurance_carrier: str = Form(None),
    insurance_policy_number: str = Form(None),
    insurance_expiration_date: str = Form(None),
    # Documents — one or more files
    documents: List[UploadFile] = File(...),
):
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")

    token_payload = _decode_token(token)
    opportunity_id = token_payload["opportunity_id"]
    jti = token_payload.get("jti", "")

    submitted_at = datetime.now(timezone.utc).isoformat()

    # --- 1. Validate and upload documents ---
    s3_keys: list[str] = []
    sf_content_version_ids: list[str] = []

    for doc in documents:
        file_bytes = await doc.read()

        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File '{doc.filename}' exceeds the 20 MB size limit.",
            )

        content_type = doc.content_type or (
            mimetypes.guess_type(doc.filename or "")[0] or "application/octet-stream"
        )
        if content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=415,
                detail=f"File type '{content_type}' is not allowed. Use PDF, JPEG, or PNG.",
            )

        # Upload to S3 first (SOX source of truth)
        s3_result = s3_service.upload_file(
            file_bytes=file_bytes,
            filename=doc.filename or "document",
            opportunity_id=opportunity_id,
            content_type=content_type,
        )
        s3_keys.append(s3_result["key"])

        # Upload to Salesforce ContentVersion (linked to Opportunity)
        cv_id = salesforce.upload_file_as_content_version(
            file_bytes=file_bytes,
            filename=doc.filename or "document",
            opportunity_id=opportunity_id,
            s3_key=s3_result["key"],
            s3_url=s3_result["url"],
        )
        sf_content_version_ids.append(cv_id)

        # SOX: log each individual file
        audit.log_file_uploaded(
            opportunity_id=opportunity_id,
            jti=jti,
            filename=doc.filename or "document",
            s3_key=s3_result["key"],
            sf_content_version_id=cv_id,
        )

    # --- 2. Update the Salesforce Opportunity ---
    application_data = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "date_of_birth": date_of_birth,
        "tlc_license_number": tlc_license_number,
        "tlc_expiration_date": tlc_expiration_date,
        "dmv_license_number": dmv_license_number,
        "dmv_license_state": dmv_license_state,
        "vehicle_vin": vehicle_vin,
        "vehicle_year": int(vehicle_year) if vehicle_year else None,
        "vehicle_make": vehicle_make,
        "vehicle_model": vehicle_model,
        "vehicle_color": vehicle_color,
        "vehicle_plate": vehicle_plate,
        "insurance_carrier": insurance_carrier,
        "insurance_policy_number": insurance_policy_number,
        "insurance_expiration_date": insurance_expiration_date,
        "submitted_at": submitted_at,
    }
    sf_fields = salesforce.map_application_to_opportunity_fields(application_data)
    sf_status = salesforce.update_opportunity(opportunity_id, sf_fields)

    # --- 3. SOX: single consolidated submission event ---
    event_id = audit.log_application_submitted(
        opportunity_id=opportunity_id,
        jti=jti,
        s3_keys=s3_keys,
        sf_content_version_ids=sf_content_version_ids,
        sf_patch_status=sf_status,
        submitted_from_ip=client_ip,
        user_agent=user_agent,
    )

    return SubmitResponse(
        success=True,
        opportunity_id=opportunity_id,
        s3_keys=s3_keys,
        sf_content_version_ids=sf_content_version_ids,
        audit_event_id=event_id,
        message="Application submitted successfully. Your information has been received.",
    )
