"""Validation utilities for resume operations."""

import logging
from dataclasses import dataclass

from resume_editor.app.api.routes.route_logic.resume_parsing import (
    validate_resume_content,
)

log = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    is_valid: bool
    errors: dict[str, str]


# Constants for validation
MAX_COMPANY_LENGTH = 255
MAX_NOTES_LENGTH = 5000
MAX_JOB_TITLE_LENGTH = 255
MAX_PAY_RATE_LENGTH = 100
MAX_CONTACT_INFO_LENGTH = 500
MAX_WORK_ARRANGEMENT_LENGTH = 50
MAX_LOCATION_LENGTH = 255
MAX_SPECIAL_INSTRUCTIONS_LENGTH = 5000


def validate_company_and_notes(
    company: str | None,
    notes: str | None,
) -> ValidationResult:
    """Validate company and notes fields.

    Args:
        company: The company name to validate (optional).
        notes: The notes to validate (optional).

    Returns:
        ValidationResult: Object containing is_valid boolean and errors dict.
            Errors dict has field names as keys and error messages as values.

    Notes:
        1. Company max length: 255 characters.
        2. Notes max length: 5000 characters.
        3. Both fields are optional (None or empty string is valid).
        4. Returns all validation errors, not just the first one.
    """
    _msg = "validate_company_and_notes starting"
    log.debug(_msg)

    errors: dict[str, str] = {}

    # Validate company length
    if company is not None and len(company) > MAX_COMPANY_LENGTH:
        _msg = f"Company name exceeds max length: {len(company)} > {MAX_COMPANY_LENGTH}"
        log.debug(_msg)
        errors["company"] = (
            f"Company name must be {MAX_COMPANY_LENGTH} characters or less"
        )

    # Validate notes length
    if notes is not None and len(notes) > MAX_NOTES_LENGTH:
        _msg = f"Notes exceed max length: {len(notes)} > {MAX_NOTES_LENGTH}"
        log.debug(_msg)
        errors["notes"] = f"Notes must be {MAX_NOTES_LENGTH} characters or less"

    is_valid = len(errors) == 0

    _msg = f"validate_company_and_notes returning: is_valid={is_valid}"
    log.debug(_msg)
    return ValidationResult(is_valid=is_valid, errors=errors)


def _validate_single_field(
    field_value: str | None,
    field_name: str,
    max_length: int,
    errors: dict[str, str],
) -> None:
    """Validate a single field against max length.

    Args:
        field_value: The value to validate.
        field_name: The name of the field for error messages.
        max_length: The maximum allowed length.
        errors: Dictionary to add errors to.

    """
    if field_value is None:
        return

    if len(field_value) > max_length:
        _msg = (
            f"Field {field_name} exceeds max length: {len(field_value)} > {max_length}"
        )
        log.warning(_msg)
        errors[field_name] = (
            f"{field_name.replace('_', ' ').title()} must be {max_length} characters or less"
        )


def validate_extracted_job_details(  # noqa: PLR0913
    extracted_company_name: str | None,
    extracted_job_title: str | None,
    extracted_pay_rate: str | None,
    extracted_contact_info: str | None,
    extracted_work_arrangement: str | None,
    extracted_location: str | None,
    extracted_special_instructions: str | None,
) -> ValidationResult:
    """Validate extracted job detail fields.

    Args:
        extracted_company_name: The extracted company name (optional).
        extracted_job_title: The extracted job title (optional).
        extracted_pay_rate: The extracted pay rate (optional).
        extracted_contact_info: The extracted contact info (optional).
        extracted_work_arrangement: The extracted work arrangement (optional).
        extracted_location: The extracted location (optional).
        extracted_special_instructions: The extracted special instructions (optional).

    Returns:
        ValidationResult: Object containing is_valid boolean and errors dict.
            Errors dict has field names as keys and error messages as values.

    Notes:
        1. All fields are optional (None or empty string is valid).
        2. Fields that exceed max length are truncated with a warning logged.
        3. Returns all validation errors, not just the first one.

    """
    _msg = "validate_extracted_job_details starting"
    log.debug(_msg)

    errors: dict[str, str] = {}

    # Validate all fields using helper function
    _validate_single_field(
        extracted_company_name,
        "extracted_company_name",
        MAX_COMPANY_LENGTH,
        errors,
    )
    _validate_single_field(
        extracted_job_title,
        "extracted_job_title",
        MAX_JOB_TITLE_LENGTH,
        errors,
    )
    _validate_single_field(
        extracted_pay_rate, "extracted_pay_rate", MAX_PAY_RATE_LENGTH, errors
    )
    _validate_single_field(
        extracted_contact_info,
        "extracted_contact_info",
        MAX_CONTACT_INFO_LENGTH,
        errors,
    )
    _validate_single_field(
        extracted_work_arrangement,
        "extracted_work_arrangement",
        MAX_WORK_ARRANGEMENT_LENGTH,
        errors,
    )
    _validate_single_field(
        extracted_location,
        "extracted_location",
        MAX_LOCATION_LENGTH,
        errors,
    )
    _validate_single_field(
        extracted_special_instructions,
        "extracted_special_instructions",
        MAX_SPECIAL_INSTRUCTIONS_LENGTH,
        errors,
    )

    is_valid = len(errors) == 0

    _msg = f"validate_extracted_job_details returning: is_valid={is_valid}"
    log.debug(_msg)
    return ValidationResult(is_valid=is_valid, errors=errors)


def validate_refinement_form(
    job_description: str | None,
    company: str | None,
    notes: str | None,
) -> ValidationResult:
    """Validate the refinement form data.

    Args:
        job_description: The job description (required).
        company: The company name (optional).
        notes: The notes (optional).

    Returns:
        ValidationResult: Object containing is_valid boolean and errors dict.

    Notes:
        1. Job description is required (must be non-empty).
        2. Company and notes have length limits.
    """
    _msg = "validate_refinement_form starting"
    log.debug(_msg)

    errors: dict[str, str] = {}

    # Validate job description is present
    if not job_description or not job_description.strip():
        errors["job_description"] = "Job description is required"

    # Validate company and notes
    company_notes_result = validate_company_and_notes(company, notes)
    errors.update(company_notes_result.errors)

    is_valid = len(errors) == 0

    _msg = f"validate_refinement_form returning: is_valid={is_valid}"
    log.debug(_msg)
    return ValidationResult(is_valid=is_valid, errors=errors)


def perform_pre_save_validation(
    markdown_content: str,
) -> None:
    """Perform comprehensive pre-save validation on resume content.

    Args:
        markdown_content (str): The updated resume Markdown content to validate.

    Returns:
        None: This function does not return any value.

    Raises:
        HTTPException: If validation fails with status code 422.

    Notes:
        1. Run the updated Markdown through the existing parser to ensure
           it's still valid.
        2. If any validation fails, raise an HTTPException with detailed
           error messages.
        3. This function performs validation checks on resume content before
           saving to ensure data integrity.
        4. Validation includes parsing the Markdown content to verify its
           structure and format.
        5. The function accesses the resume parsing module to validate the
           content structure.

    """
    validate_resume_content(markdown_content)
