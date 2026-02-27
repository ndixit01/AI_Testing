from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from enum import Enum


class GenerateLinkRequest(BaseModel):
    opportunity_id: str = Field(..., description="Salesforce Opportunity ID (18-char)")
    contact_id: Optional[str] = Field(None, description="Salesforce Contact ID if known")


class GenerateLinkResponse(BaseModel):
    token: str
    link: str
    opportunity_id: str
    expires_at: str


class DriverApplication(BaseModel):
    # Personal
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    date_of_birth: str  # ISO 8601

    # TLC / Licensing
    tlc_license_number: str
    tlc_expiration_date: str  # ISO 8601
    dmv_license_number: str
    dmv_license_state: str

    # Vehicle (if applicable)
    vehicle_vin: Optional[str] = None
    vehicle_year: Optional[int] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_color: Optional[str] = None
    vehicle_plate: Optional[str] = None

    # Insurance
    insurance_carrier: Optional[str] = None
    insurance_policy_number: Optional[str] = None
    insurance_expiration_date: Optional[str] = None


class SubmitResponse(BaseModel):
    success: bool
    opportunity_id: str
    s3_keys: list[str]
    sf_content_version_ids: list[str]
    audit_event_id: str
    message: str


class TokenPayload(BaseModel):
    opportunity_id: str
    contact_id: Optional[str]
    jti: str  # unique token ID for audit tracing
    exp: int
    iat: int
