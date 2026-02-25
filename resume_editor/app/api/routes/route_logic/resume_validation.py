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
