import html
import logging
from typing import AsyncGenerator

from cryptography.fernet import InvalidToken
from fastapi import HTTPException, Response
from fastapi.responses import HTMLResponse
from openai import AuthenticationError
from sqlalchemy.orm import Session
from starlette.middleware.base import ClientDisconnect

from resume_editor.app.api.routes.html_fragments import _create_refine_result_html
from resume_editor.app.api.routes.route_logic.resume_crud import (
    ResumeCreateParams,
    ResumeUpdateParams,
)
from resume_editor.app.api.routes.route_logic.resume_crud import (
    create_resume as create_resume_db,
)
from resume_editor.app.api.routes.route_logic.resume_crud import (
    update_resume as update_resume_db,
)
from resume_editor.app.api.routes.route_logic.resume_reconstruction import (
    build_complete_resume_from_sections,
)
from resume_editor.app.api.routes.route_logic.resume_serialization import (
    extract_certifications_info,
    extract_education_info,
    extract_experience_info,
    extract_personal_info,
)
from resume_editor.app.api.routes.route_logic.resume_validation import (
    perform_pre_save_validation,
)
from resume_editor.app.api.routes.route_logic.settings_crud import get_user_settings
from resume_editor.app.api.routes.route_models import (
    ExperienceResponse,
    RefineResponse,
    RefineTargetSection,
    SaveAsNewParams,
    SyncRefinementParams,
)
from resume_editor.app.core.security import decrypt_data
from resume_editor.app.llm.models import LLMConfig
from resume_editor.app.llm.orchestration import (
    async_refine_experience_section,
    refine_resume_section_with_llm,
)
from resume_editor.app.models.resume.experience import Role
from resume_editor.app.models.resume_model import Resume as DatabaseResume
from resume_editor.app.models.user import User

log = logging.getLogger(__name__)


def get_llm_config(
    db: Session,
    user_id: int,
) -> tuple[str | None, str | None, str | None]:
    """Retrieves LLM configuration for a user.

    Fetches user settings, decrypts the API key, and returns the LLM endpoint,
    model name, and API key.

    Args:
        db (Session): The database session.
        user_id (int): The ID of the user.

    Returns:
        tuple[str | None, str | None, str | None]: A tuple containing the
            llm_endpoint, llm_model_name, and decrypted api_key.

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


def create_sse_message(event: str, data: str) -> str:
    """Formats a message for Server-Sent Events (SSE).

    Args:
        event (str): The event name.
        data (str): The data to send. Can be multi-line.

    Returns:
        str: The formatted SSE message string.

    """
    if "\n" in data:
        data_payload = "\n".join(f"data: {line}" for line in data.splitlines())
        return f"event: {event}\n{data_payload}\n\n"
    return f"event: {event}\ndata: {data}\n\n"


def create_sse_progress_message(message: str) -> str:
    """Creates an SSE 'progress' message.

    Args:
        message (str): The progress message content.

    Returns:
        str: The formatted SSE 'progress' message.

    """
    _msg = f"create_sse_progress_message with message: {message}"
    log.debug(_msg)
    progress_html = f"<li>{html.escape(message)}</li>"
    return create_sse_message(event="progress", data=progress_html)


def create_sse_introduction_message(introduction: str) -> str:
    """Creates an SSE 'introduction_generated' message.

    Args:
        introduction (str): The introduction text.

    Returns:
        str: The formatted SSE 'introduction_generated' message.

    """
    intro_html = f"""<div id="introduction-container" hx-swap-oob="true">
<h4 class="text-lg font-semibold text-gray-700">Suggested Introduction:</h4>
<p class="mt-1 text-sm text-gray-600 bg-gray-50 p-3 rounded-md border">{html.escape(introduction)}</p>
</div>"""
    return create_sse_message(event="introduction_generated", data=intro_html)


def create_sse_error_message(message: str, is_warning: bool = False) -> str:
    """Creates an SSE 'error' message.

    Args:
        message (str): The error or warning message.
        is_warning (bool): If True, formats as a warning (yellow). Defaults to False (red).

    Returns:
        str: The formatted SSE 'error' message.

    """
    color_class = "text-yellow-500" if is_warning else "text-red-500"
    error_html = (
        f"<div role='alert' class='{color_class} p-2'>{html.escape(message)}</div>"
    )
    return create_sse_message(event="error", data=error_html)


def create_sse_done_message(html_content: str) -> str:
    """Creates an SSE 'done' message.

    Args:
        html_content (str): The final HTML content to be sent.

    Returns:
        str: The formatted SSE 'done' message.

    """
    return create_sse_message(event="done", data=html_content)


def create_sse_close_message() -> str:
    """Creates an SSE 'close' message.

    Returns:
        str: The formatted SSE 'close' message.

    """
    return create_sse_message(event="close", data="stream complete")


def process_refined_experience_result(
    resume: DatabaseResume,
    refined_roles: dict,
    job_description: str,
    introduction: str | None,
) -> str:
    """Processes refined experience roles and generates final HTML.

    This function takes the refined roles from the LLM, reconstructs the full
    resume content, and then generates the final HTML result to be sent in the
    'done' SSE event.

    Args:
        resume (DatabaseResume): The original resume object.
        refined_roles (dict): A dictionary of refined role data from the LLM,
                              keyed by their original index.
        job_description (str): The job description used for refinement.
        introduction (str | None): The LLM-generated introduction, if any.

    Returns:
        str: The complete HTML content for the body of the `done` event.

    """
    _msg = "process_refined_experience_result starting"
    log.debug(_msg)
    personal_info = extract_personal_info(resume.content)
    education_info = extract_education_info(resume.content)
    experience_info = extract_experience_info(resume.content)
    certifications_info = extract_certifications_info(resume.content)

    # Sort roles by original index to preserve order
    sorted_roles_data = [role_data for _, role_data in sorted(refined_roles.items())]
    roles_to_reconstruct = [Role.model_validate(data) for data in sorted_roles_data]

    refined_experience = ExperienceResponse(
        roles=roles_to_reconstruct,
        projects=experience_info.projects,
    )

    updated_resume_content = build_complete_resume_from_sections(
        personal_info=personal_info,
        education=education_info,
        experience=refined_experience,
        certifications=certifications_info,
    )

    result_html = _create_refine_result_html(
        resume.id,
        "experience",
        updated_resume_content,
        job_description=job_description,
        introduction=introduction,
    )

    _msg = "process_refined_experience_result returning"
    log.debug(_msg)

    return result_html


def _process_sse_event(
    event: dict,
    refined_roles: dict,
) -> tuple[str | None, str | None]:
    """Processes a single SSE event from the experience refinement stream.

    This helper function updates the state of refined roles and determines
    what message, if any, should be yielded to the client.

    Args:
        event (dict): The event data from the async generator.
        refined_roles (dict): A dictionary to be updated with refined role data.

    Returns:
        tuple[str | None, str | None]: A tuple containing an optional SSE message
                                       to yield and optional new introduction text.

    """
    _msg = f"_process_sse_event starting with event: {event}"
    log.debug(_msg)

    sse_message = None
    new_introduction = None

    if isinstance(event, dict) and event.get("status") == "in_progress":
        sse_message = create_sse_progress_message(event.get("message", ""))
    elif isinstance(event, dict) and event.get("status") == "introduction_generated":
        new_introduction = event.get("data")
        if new_introduction:
            sse_message = create_sse_introduction_message(new_introduction)
    elif isinstance(event, dict) and event.get("status") == "role_refined":
        index = event.get("original_index")
        data = event.get("data")
        if index is not None and data is not None:
            refined_roles[index] = data
        else:
            _msg = f"Malformed role_refined event received: {event}"
            log.warning(_msg)
    else:
        _msg = f"Unhandled SSE event received: {event}"
        log.warning(_msg)

    result = (sse_message, new_introduction)
    _msg = "_process_sse_event returning"
    log.debug(_msg)
    return result


def _handle_sse_exception(e: Exception, resume_id: int) -> str:
    """Handles exceptions during an SSE stream and formats an error message.

    Args:
        e (Exception): The exception that was raised.
        resume_id (int): The ID of the resume being processed.

    Returns:
        str: A formatted SSE error message string.

    """
    _msg = f"_handle_sse_exception starting for resume ID: {resume_id}"
    log.debug(_msg)

    error_message = "An unexpected error occurred."
    if isinstance(e, InvalidToken):
        error_message = "Invalid API key. Please update your settings."
    elif isinstance(e, AuthenticationError):
        error_message = "LLM authentication failed. Please check your API key."
    elif isinstance(e, ValueError):
        error_message = f"Refinement failed: {e!s}"

    _msg = f"SSE stream error for resume {resume_id}: {error_message}"
    log.exception(_msg)

    result = create_sse_error_message(error_message)
    _msg = f"_handle_sse_exception returning for resume ID: {resume_id}"
    log.debug(_msg)
    return result


def reconstruct_resume_from_refined_section(
    original_resume_content: str,
    refined_content: str,
    target_section: RefineTargetSection,
) -> str:
    """Rebuilds a complete resume by combining a refined section with original sections.

    This function takes a refined content string for a specific section and reconstructs
    the full resume markdown by parsing all sections, replacing the target section
    with the refined version, and then building the complete markdown from these parts.

    Args:
        original_resume_content (str): The full markdown content of the original resume.
        refined_content (str): The markdown content of the section that has been refined.
        target_section (RefineTargetSection): The enum member indicating which section was refined.

    Returns:
        str: The full markdown content of the reconstructed resume.

    """
    _msg = f"reconstruct_resume_from_refined_section starting for section {target_section.value}"
    log.debug(_msg)

    if target_section == RefineTargetSection.FULL:
        updated_content = refined_content
    else:
        # Based on the target section, use the refined content for that section
        # and the original content for all others.
        personal_info = extract_personal_info(
            refined_content
            if target_section == RefineTargetSection.PERSONAL
            else original_resume_content,
        )
        education_info = extract_education_info(
            refined_content
            if target_section == RefineTargetSection.EDUCATION
            else original_resume_content,
        )
        experience_info = extract_experience_info(
            refined_content
            if target_section == RefineTargetSection.EXPERIENCE
            else original_resume_content,
        )
        certifications_info = extract_certifications_info(
            refined_content
            if target_section == RefineTargetSection.CERTIFICATIONS
            else original_resume_content,
        )

        updated_content = build_complete_resume_from_sections(
            personal_info=personal_info,
            education=education_info,
            experience=experience_info,
            certifications=certifications_info,
        )

    _msg = "reconstruct_resume_from_refined_section returning"
    log.debug(_msg)
    return updated_content


async def handle_sync_refinement(params: SyncRefinementParams) -> Response:
    """Handles synchronous (non-streaming) resume section refinement."""
    try:
        llm_endpoint, llm_model_name, api_key = get_llm_config(
            params.db,
            params.user.id,
        )

        llm_config = LLMConfig(
            llm_endpoint=llm_endpoint,
            api_key=api_key,
            llm_model_name=llm_model_name,
        )

        # Handle other sections synchronously
        refined_content, introduction = refine_resume_section_with_llm(
            resume_content=params.resume.content,
            job_description=params.job_description,
            target_section=params.target_section.value,
            llm_config=llm_config,
            generate_introduction=params.generate_introduction,
        )

        if "HX-Request" in params.request.headers:
            html_content = _create_refine_result_html(
                resume_id=params.resume.id,
                target_section_val=params.target_section.value,
                refined_content=refined_content,
                job_description=params.job_description,
                introduction=introduction,
            )
            return HTMLResponse(content=html_content)

        return RefineResponse(
            refined_content=refined_content,
            introduction=introduction,
        )
    except InvalidToken:
        detail = "Invalid API key. Please update your settings."
        _msg = f"API key decryption failed for user {params.user.id}"
        log.warning(_msg)
        if "HX-Request" in params.request.headers:
            return HTMLResponse(
                f'<div role="alert" class="text-red-500 p-2">{detail}</div>',
                status_code=200,
            )
        raise HTTPException(status_code=400, detail=detail)
    except AuthenticationError as e:
        detail = "LLM authentication failed. Please check your API key in settings."
        _msg = f"LLM authentication failed for user {params.user.id}: {e!s}"
        log.warning(_msg)
        if "HX-Request" in params.request.headers:
            return HTMLResponse(
                f'<div role="alert" class="text-red-500 p-2">{detail}</div>',
                status_code=200,
            )
        raise HTTPException(status_code=401, detail=detail)
    except ValueError as e:
        detail = str(e)
        _msg = f"LLM refinement failed for resume {params.resume.id} with ValueError: {detail}"
        log.warning(_msg)
        if "HX-Request" in params.request.headers:
            return HTMLResponse(
                f'<div role="alert" class="text-red-500 p-2">Refinement failed: {detail}</div>',
                status_code=200,
            )
        raise HTTPException(status_code=400, detail=detail)
    except Exception as e:
        detail = f"An unexpected error occurred during refinement: {e!s}"
        _msg = f"LLM refinement failed for resume {params.resume.id}: {e!s}"
        log.exception(_msg)
        if "HX-Request" in params.request.headers:
            return HTMLResponse(
                f'<div role="alert" class="text-red-500 p-2">{detail}</div>',
                status_code=200,
            )
        raise HTTPException(status_code=500, detail=f"LLM refinement failed: {e!s}")


async def experience_refinement_sse_generator(
    db: Session,
    user: User,
    resume: DatabaseResume,
    job_description: str,
    generate_introduction: bool,
) -> AsyncGenerator[str, None]:
    """Generates SSE events for the experience refinement process."""
    _msg = f"Streaming refinement for resume {resume.id} for section experience"
    log.debug(_msg)

    try:
        llm_endpoint, llm_model_name, api_key = get_llm_config(db, user.id)

        llm_config = LLMConfig(
            llm_endpoint=llm_endpoint,
            api_key=api_key,
            llm_model_name=llm_model_name,
        )
        refined_roles = {}
        introduction = None

        async for event in async_refine_experience_section(
            resume_content=resume.content,
            job_description=job_description,
            llm_config=llm_config,
            generate_introduction=generate_introduction,
        ):
            sse_message, new_introduction = _process_sse_event(event, refined_roles)
            if sse_message:
                yield sse_message
            if new_introduction is not None:
                introduction = new_introduction

        if refined_roles:
            result_html = process_refined_experience_result(
                resume,
                refined_roles,
                job_description,
                introduction,
            )
            yield create_sse_done_message(result_html)
        else:
            yield create_sse_error_message(
                "Refinement finished, but no roles were found to refine.",
                is_warning=True,
            )

    except ClientDisconnect:
        _msg = f"Client disconnected from SSE stream for resume {resume.id}."
        log.warning(_msg)
    except (InvalidToken, AuthenticationError, ValueError, Exception) as e:
        yield _handle_sse_exception(e, resume.id)
    finally:
        yield create_sse_close_message()


def handle_accept_refinement(
    db: Session,
    resume: DatabaseResume,
    refined_content: str,
    target_section: RefineTargetSection,
    introduction: str | None,
) -> DatabaseResume:
    """Orchestrates accepting a refined resume section.

    This involves reconstructing the resume, validating it, and updating the database.

    Args:
        db (Session): The database session.
        resume (DatabaseResume): The original resume to update.
        refined_content (str): The refined content for the target section.
        target_section (RefineTargetSection): The section that was refined.
        introduction (str | None): An optional new introduction.

    Returns:
        DatabaseResume: The updated resume object.

    Raises:
        HTTPException: If reconstruction or validation fails.

    """
    _msg = "handle_accept_refinement starting"
    log.debug(_msg)

    try:
        updated_content = reconstruct_resume_from_refined_section(
            original_resume_content=resume.content,
            refined_content=refined_content,
            target_section=target_section,
        )
        perform_pre_save_validation(updated_content)
    except (ValueError, TypeError, HTTPException) as e:
        detail = getattr(e, "detail", str(e))
        _msg = f"Failed to reconstruct resume from refined section: {detail}"
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=_msg)

    update_params = ResumeUpdateParams(
        content=updated_content,
        introduction=introduction,
    )
    updated_resume = update_resume_db(
        db=db,
        resume=resume,
        params=update_params,
    )

    _msg = "handle_accept_refinement returning"
    log.debug(_msg)
    return updated_resume


def handle_save_as_new_refinement(params: SaveAsNewParams) -> DatabaseResume:
    """Orchestrates saving a refined resume as a new resume.

    This involves reconstructing the resume, validating it, and creating a new record in the database.

    Args:
        params (SaveAsNewParams): The parameters for saving the new resume.

    Returns:
        DatabaseResume: The newly created resume object.

    Raises:
        HTTPException: If reconstruction or validation fails.

    """
    _msg = "handle_save_as_new_refinement starting"
    log.debug(_msg)

    try:
        updated_content = reconstruct_resume_from_refined_section(
            original_resume_content=params.resume.content,
            refined_content=params.form_data.refined_content,
            target_section=params.form_data.target_section,
        )
        perform_pre_save_validation(updated_content)
    except (ValueError, TypeError, HTTPException) as e:
        detail = getattr(e, "detail", str(e))
        _msg = f"Failed to reconstruct resume from refined section: {detail}"
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=_msg)

    create_params = ResumeCreateParams(
        user_id=params.user.id,
        name=params.form_data.new_resume_name,
        content=updated_content,
        is_base=False,
        parent_id=params.resume.id,
        job_description=params.form_data.job_description,
        introduction=params.form_data.introduction,
    )
    new_resume = create_resume_db(
        db=params.db,
        params=create_params,
    )

    _msg = "handle_save_as_new_refinement returning"
    log.debug(_msg)
    return new_resume
