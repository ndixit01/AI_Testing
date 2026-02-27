import uuid
from datetime import datetime, timezone, timedelta

import jwt
from fastapi import APIRouter, Request, HTTPException

from app.config import get_settings
from app.models import GenerateLinkRequest, GenerateLinkResponse
from app.services import audit, salesforce

router = APIRouter(prefix="/api/links", tags=["links"])


@router.post("/generate", response_model=GenerateLinkResponse)
def generate_link(payload: GenerateLinkRequest, request: Request):
    """
    Generate a secure, time-limited JWT link for a driver to complete their application.
    The Opportunity must already exist in Salesforce (created upstream via Facebook Ad).
    Requires internal authorization — this endpoint should be behind a VPN or API key in prod.
    """
    s = get_settings()
    client_ip = request.client.host if request.client else "unknown"

    # Verify the opportunity exists before issuing a link
    try:
        salesforce.get_opportunity(payload.opportunity_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    jti = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=s.jwt_expiry_hours)

    token_data = {
        "opportunity_id": payload.opportunity_id,
        "contact_id": payload.contact_id,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    token = jwt.encode(token_data, s.jwt_secret, algorithm=s.jwt_algorithm)

    # SOX: log every link generation with token identity
    audit.log_link_generated(
        opportunity_id=payload.opportunity_id,
        jti=jti,
        expires_at=expires_at.isoformat(),
        requested_by_ip=client_ip,
    )

    base_url = str(request.base_url).rstrip("/")
    link = f"{base_url}/apply?token={token}"

    return GenerateLinkResponse(
        token=token,
        link=link,
        opportunity_id=payload.opportunity_id,
        expires_at=expires_at.isoformat(),
    )


@router.get("/verify")
def verify_link(token: str, request: Request):
    """
    Verify a JWT token and return the Opportunity data to pre-populate the form.
    Called by the frontend on page load.
    """
    s = get_settings()
    client_ip = request.client.host if request.client else "unknown"

    try:
        payload = jwt.decode(token, s.jwt_secret, algorithms=[s.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="This link has expired. Please request a new one.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid link.")

    opportunity_id = payload["opportunity_id"]
    jti = payload.get("jti", "")

    try:
        opportunity = salesforce.get_opportunity(opportunity_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    audit.log_link_verified(
        opportunity_id=opportunity_id,
        jti=jti,
        verified_from_ip=client_ip,
    )

    # Return only the fields the frontend needs to pre-populate
    return {
        "opportunity_id": opportunity_id,
        "jti": jti,
        "driver_name": opportunity.get("Name", ""),
        "email": opportunity.get("Driver_Email__c", ""),
        "phone": opportunity.get("Driver_Phone__c", ""),
    }
