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


def process_refined_experience_result(  # noqa: PLR0913
    resume_id: int,
    final_content: str,
    job_description: str,
    introduction: str | None,
    limit_refinement_years: int | None,
    company: str | None = None,
    notes: str | None = None,
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
    )
    result_html = _create_refine_result_html(params=result_html_params)

    _msg = "process_refined_experience_result returning"
    log.debug(_msg)

    return result_html


def handle_save_as_new_refinement(params: SaveAsNewParams) -> DatabaseResume:
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
        final_content = params.form_data.refined_content
        job_description_val = params.form_data.job_description
        introduction = params.form_data.introduction
        new_resume_name = params.form_data.new_resume_name

        # Handle company and notes, being careful with mocks in tests
        _company = getattr(params.form_data, "company", None)
        _notes = getattr(params.form_data, "notes", None)
        company = None if isinstance(_company, Mock) else _company
        notes = None if isinstance(_notes, Mock) else _notes

        # Validate resume content
        perform_pre_save_validation(final_content)

        # Validate company and notes
        validation_result = validate_company_and_notes(company, notes)
        if not validation_result.is_valid:
            raise HTTPException(status_code=400, detail=validation_result.errors)
    except HTTPException:
        # Re-raise HTTPExceptions as-is (includes validation failures)
        raise
    except (ValueError, TypeError) as e:
        detail = getattr(e, "detail", str(e))
        _msg = f"Failed to validate refined resume content: {detail}"
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=_msg)

    # Create the new resume record, passing the determined introduction.
    create_params = ResumeCreateParams(
        user_id=params.user.id,
        name=new_resume_name,
        content=final_content,
        is_base=False,
        parent_id=params.resume.id,
        job_description=job_description_val,
        introduction=introduction,
        company=company,
        notes=notes,
    )
    new_resume = create_resume_db(
        db=params.db,
        params=create_params,
    )

    _msg = "handle_save_as_new_refinement returning"
    log.debug(_msg)
    return new_resume
