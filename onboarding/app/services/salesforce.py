import base64
import logging
import mimetypes
from pathlib import Path
from typing import Optional

from simple_salesforce import Salesforce, SalesforceResourceNotFound

from app.config import get_settings

logger = logging.getLogger(__name__)


def _get_client() -> Salesforce:
    s = get_settings()
    return Salesforce(
        username=s.sf_username,
        password=s.sf_password,
        security_token=s.sf_security_token,
        domain=s.sf_domain,
    )


def get_opportunity(opportunity_id: str) -> dict:
    """Fetch an existing Opportunity by Salesforce ID."""
    sf = _get_client()
    try:
        opp = sf.Opportunity.get(opportunity_id)
        logger.info("sf_get_opportunity", extra={"opportunity_id": opportunity_id})
        return opp
    except SalesforceResourceNotFound:
        logger.warning(
            "sf_opportunity_not_found", extra={"opportunity_id": opportunity_id}
        )
        raise ValueError(f"Opportunity {opportunity_id} not found in Salesforce")


def update_opportunity(opportunity_id: str, fields: dict) -> int:
    """
    PATCH the Opportunity with application data.
    Returns the HTTP status code (204 = success).
    """
    sf = _get_client()
    result = sf.Opportunity.update(opportunity_id, fields)
    logger.info(
        "sf_update_opportunity",
        extra={"opportunity_id": opportunity_id, "fields": list(fields.keys()), "status": result},
    )
    return result


def upload_file_as_content_version(
    file_bytes: bytes,
    filename: str,
    opportunity_id: str,
    s3_key: str,
    s3_url: str,
) -> str:
    """
    Upload a file to Salesforce as a ContentVersion linked to the Opportunity.
    Also stores the S3 key and URL in the description for cross-reference traceability.
    Returns the ContentVersion ID.
    """
    sf = _get_client()
    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type:
        mime_type = "application/octet-stream"

    encoded = base64.b64encode(file_bytes).decode("utf-8")
    description = f"SOX_S3_KEY:{s3_key} | SOX_S3_URL:{s3_url}"

    cv_result = sf.ContentVersion.create(
        {
            "Title": Path(filename).stem,
            "PathOnClient": filename,
            "VersionData": encoded,
            "ContentLocation": "S",  # Salesforce-managed content
            "Description": description,
        }
    )

    if not cv_result.get("success"):
        errors = cv_result.get("errors", [])
        raise RuntimeError(f"ContentVersion creation failed: {errors}")

    content_version_id = cv_result["id"]

    # Retrieve the ContentDocumentId so we can link it to the Opportunity
    cv_record = sf.query(
        f"SELECT ContentDocumentId FROM ContentVersion WHERE Id = '{content_version_id}'"
    )
    content_document_id = cv_record["records"][0]["ContentDocumentId"]

    # Link the document to the Opportunity record
    sf.ContentDocumentLink.create(
        {
            "ContentDocumentId": content_document_id,
            "LinkedEntityId": opportunity_id,
            "ShareType": "V",  # Viewer permission
            "Visibility": "AllUsers",
        }
    )

    logger.info(
        "sf_content_version_uploaded",
        extra={
            "opportunity_id": opportunity_id,
            "content_version_id": content_version_id,
            "content_document_id": content_document_id,
            "filename": filename,
            "s3_key": s3_key,
        },
    )
    return content_version_id


def map_application_to_opportunity_fields(application: dict) -> dict:
    """
    Map driver application fields to Salesforce Opportunity custom fields.
    Adjust field API names to match your SF org's schema.
    """
    return {
        "Driver_First_Name__c": application.get("first_name"),
        "Driver_Last_Name__c": application.get("last_name"),
        "Driver_Email__c": application.get("email"),
        "Driver_Phone__c": application.get("phone"),
        "Driver_Date_of_Birth__c": application.get("date_of_birth"),
        "TLC_License_Number__c": application.get("tlc_license_number"),
        "TLC_Expiration_Date__c": application.get("tlc_expiration_date"),
        "DMV_License_Number__c": application.get("dmv_license_number"),
        "DMV_License_State__c": application.get("dmv_license_state"),
        "Vehicle_VIN__c": application.get("vehicle_vin"),
        "Vehicle_Year__c": application.get("vehicle_year"),
        "Vehicle_Make__c": application.get("vehicle_make"),
        "Vehicle_Model__c": application.get("vehicle_model"),
        "Vehicle_Color__c": application.get("vehicle_color"),
        "Vehicle_Plate__c": application.get("vehicle_plate"),
        "Insurance_Carrier__c": application.get("insurance_carrier"),
        "Insurance_Policy_Number__c": application.get("insurance_policy_number"),
        "Insurance_Expiration_Date__c": application.get("insurance_expiration_date"),
        "Application_Status__c": "Submitted",
        "Application_Submitted_At__c": application.get("submitted_at"),
    }
