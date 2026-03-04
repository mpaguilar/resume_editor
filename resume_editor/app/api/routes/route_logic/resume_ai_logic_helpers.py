"""Helper functions for resume AI logic.

This module contains helper functions that don't belong to specific sub-modules
but are needed by the main resume_ai_logic module and other modules.
"""

import logging
from unittest.mock import Mock

from fastapi import HTTPException
from sqlalchemy.orm import Session

from resume_editor.app.api.routes.html_fragments import (
    RefineResultParams,
    _create_refine_result_html,
)
from resume_editor.app.api.routes.route_logic.resume_crud import (
    ResumeCreateParams,
)
from resume_editor.app.api.routes.route_logic.resume_crud import (
    create_resume as create_resume_db,
)
from resume_editor.app.api.routes.route_logic.resume_validation import (
    perform_pre_save_validation,
    validate_company_and_notes,
)
from resume_editor.app.api.routes.route_logic.settings_crud import get_user_settings
from resume_editor.app.api.routes.route_models import SaveAsNewParams
from resume_editor.app.core.security import decrypt_data
from resume_editor.app.models.resume_model import Resume as DatabaseResume

log = logging.getLogger(__name__)


def get_llm_config(
    db: Session,
    user_id: int,
) -> tuple[str | None, str | None, str | None]:
    """Retrieves LLM configuration for a user.

    Fetches user settings, decrypts the API key, and returns the LLM endpoint,
    model name, and API key.

    Args:
        db: The database session.
        user_id: The ID of the user.

    Returns:
        A tuple containing the llm_endpoint, llm_model_name, and decrypted api_key.

    Raises:
        InvalidToken: If the API key decryption fails.

    """
    _msg = "get_llm_config starting"
    log.debug(_msg)
    settings = get_user_settings(db, user_id)
    llm_endpoint = settings.llm_endpoint if settings else None
    llm_model_name = settings.llm_model_name if settings else None
    api_key = None

    if settings and settings.encrypted_api_key:
        api_key = decrypt_data(settings.encrypted_api_key)

    result = (llm_endpoint, llm_model_name, api_key)
    _msg = "get_llm_config returning"
    log.debug(_msg)

    return result


def _get_str_field_from_form(form_data: object, field_name: str) -> str | None:
    """Extract a string field from form data, handling Mock and Form objects.

    Args:
        form_data: The form data object.
        field_name: The name of the field to extract.

    Returns:
        The field value as a string, or None if it's a Mock, Form(None), or not present.

    """
    value = getattr(form_data, field_name, None)
    if isinstance(value, Mock):
        return None
    # Handle FastAPI Form/Default objects (when form is instantiated directly in tests)
    # These have 'default' attribute containing the actual default value
    type_name = type(value).__name__
    if type_name in ("Default", "Form") or hasattr(value, "default"):
        try:
            # Get the actual default value
            actual_value = value.default
            return actual_value if actual_value is not None else None
        except (AttributeError, TypeError):
            pass
    return value


def _build_notes_with_special_instructions(
    notes: str | None,
    special_instructions: str | None,
) -> str | None:
    """Append special instructions to notes if present.

    Args:
        notes: The existing notes.
        special_instructions: The special instructions to append.

    Returns:
        The combined notes string, or None if both inputs are None.

    """
    if not special_instructions:
        return notes

    if notes:
        return f"{notes}\n\nSpecial Instructions from Job Description:\n{special_instructions}"

    return f"Special Instructions from Job Description:\n{special_instructions}"


def process_refined_experience_result(  # noqa: PLR0913
    resume_id: int,
    final_content: str,
    job_description: str,
    introduction: str | None,
    limit_refinement_years: int | None,
    company: str | None = None,
    notes: str | None = None,
    extracted_company_name: str | None = None,
    extracted_job_title: str | None = None,
    extracted_pay_rate: str | None = None,
    extracted_contact_info: str | None = None,
    extracted_work_arrangement: str | None = None,
    extracted_location: str | None = None,
    extracted_special_instructions: str | None = None,
) -> str:
    """Generates the final HTML result for a refined experience.

    This function takes the final reconstructed content and generates the
    HTML for the 'done' SSE event.

    Args:
        resume_id: ID of the resume being processed.
        final_content: The final, fully reconstructed resume content.
        job_description: The job description used for refinement.
        introduction: The newly generated introduction.
        limit_refinement_years: The year limit used for filtering.
        company: The company name for the refined resume.
        notes: The notes for the refined resume.
        extracted_company_name: Company name extracted from job description.
        extracted_job_title: Job title extracted from job description.
        extracted_pay_rate: Pay rate extracted from job description.
        extracted_contact_info: Contact info extracted from job description.
        extracted_work_arrangement: Work arrangement extracted from job description.
        extracted_location: Location extracted from job description.
        extracted_special_instructions: Special instructions extracted from job description.

    Returns:
        The complete HTML content for the body of the `done` event.

    Notes:
        1. This function does not perform any content reconstruction.
        2. It passes the provided content and metadata to `_create_refine_result_html`
            to generate the final UI.

    """
    _msg = "process_refined_experience_result starting"
    log.debug(_msg)

    # Generate the final HTML for the refinement result UI
    result_html_params = RefineResultParams(
        resume_id=resume_id,
        refined_content=final_content,
        job_description=job_description,
        introduction=introduction or "",
        limit_refinement_years=limit_refinement_years,
        company=company,
        notes=notes,
        extracted_company_name=extracted_company_name,
        extracted_job_title=extracted_job_title,
        extracted_pay_rate=extracted_pay_rate,
        extracted_contact_info=extracted_contact_info,
        extracted_work_arrangement=extracted_work_arrangement,
        extracted_location=extracted_location,
        extracted_special_instructions=extracted_special_instructions,
    )
    result_html = _create_refine_result_html(params=result_html_params)

    _msg = "process_refined_experience_result returning"
    log.debug(_msg)

    return result_html


def _extract_form_data(params: SaveAsNewParams) -> dict:
    """Extract all relevant fields from form data.

    Args:
        params: The parameters containing form data.

    Returns:
        Dictionary with all extracted fields.

    """
    form_data = params.form_data
    return {
        "final_content": form_data.refined_content,
        "job_description_val": form_data.job_description,
        "introduction": form_data.introduction,
        "new_resume_name": form_data.new_resume_name,
        "company": _get_str_field_from_form(form_data, "company"),
        "notes": _get_str_field_from_form(form_data, "notes"),
        "extracted_company_name": _get_str_field_from_form(
            form_data, "extracted_company_name"
        ),
        "extracted_job_title": _get_str_field_from_form(
            form_data, "extracted_job_title"
        ),
        "extracted_pay_rate": _get_str_field_from_form(form_data, "extracted_pay_rate"),
        "extracted_contact_info": _get_str_field_from_form(
            form_data, "extracted_contact_info"
        ),
        "extracted_work_arrangement": _get_str_field_from_form(
            form_data, "extracted_work_arrangement"
        ),
        "extracted_location": _get_str_field_from_form(form_data, "extracted_location"),
        "extracted_special_instructions": _get_str_field_from_form(
            form_data, "extracted_special_instructions"
        ),
    }


def _validate_refinement_data(data: dict) -> None:
    """Validate refinement data before saving.

    Args:
        data: Dictionary containing form data fields.

    Raises:
        HTTPException: If validation fails.

    """
    # Validate resume content
    perform_pre_save_validation(data["final_content"])

    # Validate company and notes
    validation_result = validate_company_and_notes(
        data["company"],
        data["notes"],
    )
    if not validation_result.is_valid:
        raise HTTPException(status_code=400, detail=validation_result.errors)


def handle_save_as_new_refinement(params: SaveAsNewParams) -> DatabaseResume:  # noqa: C901
    """Orchestrates saving a refined resume as a new resume.

    This function takes the full refined resume content, validates it, and
    creates a new resume record in the database. The introduction is taken
    directly from the refinement context and persisted to its dedicated field.

    Args:
        params: The parameters for saving the new resume.

    Returns:
        The newly created resume object.

    Raises:
        HTTPException: If validation fails.

    Notes:
        1. The `refined_content` from the form is assumed to be the full, final resume content.
        2. The introduction is taken from the form context and passed directly to the database.
        3. No resume reconstruction or on-the-fly introduction generation occurs here.
        4. Company and notes are validated and included in the new resume.

    """
    _msg = "handle_save_as_new_refinement starting"
    log.debug(_msg)

    try:
        # Extract all form data
        data = _extract_form_data(params)

        # Append special_instructions to notes if present
        data["notes"] = _build_notes_with_special_instructions(
            data["notes"],
            data["extracted_special_instructions"],
        )

        # Validate the data
        _validate_refinement_data(data)
    except HTTPException:
        # Re-raise HTTPExceptions as-is (includes validation failures)
        raise
    except (ValueError, TypeError) as e:
        detail = getattr(e, "detail", str(e))
        _msg = f"Failed to validate refined resume content: {detail}"
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=_msg)

    # Create the new resume record
    create_params = ResumeCreateParams(
        user_id=params.user.id,
        name=data["new_resume_name"],
        content=data["final_content"],
        is_base=False,
        parent_id=params.resume.id,
        job_description=data["job_description_val"],
        introduction=data["introduction"],
        company=data["company"],
        notes=data["notes"],
        extracted_company_name=data["extracted_company_name"],
        extracted_job_title=data["extracted_job_title"],
        extracted_pay_rate=data["extracted_pay_rate"],
        extracted_contact_info=data["extracted_contact_info"],
        extracted_work_arrangement=data["extracted_work_arrangement"],
        extracted_location=data["extracted_location"],
        extracted_special_instructions=data["extracted_special_instructions"],
    )
    new_resume = create_resume_db(
        db=params.db,
        params=create_params,
    )

    _msg = "handle_save_as_new_refinement returning"
    log.debug(_msg)
    return new_resume
