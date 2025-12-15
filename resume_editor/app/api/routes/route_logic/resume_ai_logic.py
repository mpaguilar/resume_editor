import asyncio
import html
import logging
from pathlib import Path
from typing import Any, AsyncGenerator

from cryptography.fernet import InvalidToken
from fastapi import HTTPException, Response
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from openai import AuthenticationError
from pydantic import BaseModel
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
    generate_introduction_from_resume,
    refine_resume_section_with_llm,
)
from resume_editor.app.models.resume.experience import Role
from resume_editor.app.models.resume.personal import Banner
from resume_editor.app.models.resume_model import Resume as DatabaseResume

log = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "templates"
env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)


def reconstruct_resume_markdown(
    personal_info: Any,
    education: Any,
    experience: Any,
    certifications: Any,
) -> str:
    """Wrapper delegating to build_complete_resume_from_sections.
    Args:
        personal_info (Any): The personal information section model.
        education (Any): The education section model.
        experience (Any): The experience section model.
        certifications (Any): The certifications section model.
    Returns:
        str: The reconstructed resume markdown.
    Notes:
        1. This wrapper exists to provide a stable name for tests that patch 'reconstruct_resume_markdown'.
        2. It simply calls 'build_complete_resume_from_sections' with the same arguments.

    """
    _msg = "reconstruct_resume_markdown starting"
    log.debug(_msg)
    result = build_complete_resume_from_sections(
        personal_info=personal_info,
        education=education,
        experience=experience,
        certifications=certifications,
    )
    _msg = "reconstruct_resume_markdown returning"
    log.debug(_msg)
    return result


def reconstruct_resume_with_new_introduction(
    resume_content: str,
    introduction: str | None,
) -> str:
    """Reconstructs resume content with a new introduction banner.

    This function parses a resume's Markdown content, replaces the banner
    text in the personal information section with the provided introduction,
    and then reconstructs and returns the full Markdown content.

    Args:
        resume_content (str): The original Markdown content of the resume.
        introduction (str | None): The new introduction text to be placed in
            the banner. If None or an empty/whitespace string, the original
            `resume_content` is returned unchanged.

    Returns:
        str: The updated resume content as a Markdown string, or the
             original content if `introduction` is empty.

    Raises:
        ValueError: If the resume content is malformed and cannot be parsed.

    Notes:
        1.  Check if `introduction` is `None` or an empty/whitespace string. If so, return `resume_content` immediately.
        2.  Parse the `resume_content` into its main sections (personal, education, experience, certifications) using `extract_*` helpers. This can raise a `ValueError` on failure.
        3.  If a `personal_info` section is found, update its `banner` attribute with the new `introduction` text.
        4.  Reconstruct the full resume markdown using `reconstruct_resume_markdown`, passing the modified `personal_info` and the other original sections.
        5.  Return the newly reconstructed Markdown string.

    """
    _msg = "reconstruct_resume_with_new_introduction starting"
    log.debug(_msg)

    if introduction is None or not introduction.strip():
        _msg = "reconstruct_resume_with_new_introduction returning original content (no introduction)"
        log.debug(_msg)
        return resume_content

    try:
        personal_info = extract_personal_info(resume_content)
        education_info = extract_education_info(resume_content)
        experience_info = extract_experience_info(resume_content)
        certifications_info = extract_certifications_info(resume_content)
    except Exception as e:
        _msg = f"reconstruct_resume_with_new_introduction failed to parse resume content: {e!s}"
        log.exception(_msg)
        raise

    if personal_info is not None:
        personal_info.banner = Banner(text=introduction)

    try:
        updated_content = reconstruct_resume_markdown(
            personal_info=personal_info,
            education=education_info,
            experience=experience_info,
            certifications=certifications_info,
        )
    except Exception as e:
        _msg = f"reconstruct_resume_with_new_introduction failed to reconstruct resume: {e!s}"
        log.exception(_msg)
        raise

    _msg = "reconstruct_resume_with_new_introduction returning"
    log.debug(_msg)
    return updated_content


def _replace_resume_banner(resume_content: str, introduction: str | None) -> str:
    """Parse a resume, replace its banner, and reconstruct it.

    This function is a wrapper that calls `reconstruct_resume_with_new_introduction`
    to update the banner section of a resume with a new introduction.

    Args:
        resume_content (str): The full markdown content of the resume.
        introduction (str | None): The new introduction text for the banner.
            If None or whitespace-only, the original content is returned unchanged.

    Returns:
        str: The reconstructed markdown string with the updated banner.

    Notes:
        1. This function delegates its logic to `reconstruct_resume_with_new_introduction`.

    """
    _msg = "_replace_resume_banner starting"
    log.debug(_msg)
    result = reconstruct_resume_with_new_introduction(
        resume_content=resume_content,
        introduction=introduction,
    )
    _msg = "_replace_resume_banner returning"
    log.debug(_msg)
    return result


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
    # An SSE message can have multiple data lines but must end with two newlines.
    if "\n" in data:
        data_payload = "\n".join(f"data: {line}" for line in data.splitlines())
    else:
        data_payload = f"data: {data}"

    return f"event: {event}\n{data_payload}\n\n"


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
    intro_template = env.get_template("partials/resume/_refine_result_intro.html")
    intro_html = intro_template.render(introduction=introduction)
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


class ProcessExperienceResultParams(BaseModel):
    """Parameters for processing refined experience results."""

    resume_id: int
    original_resume_content: str
    resume_content_to_refine: str
    refined_roles: dict
    job_description: str
    introduction: str | None
    limit_refinement_years: int | None


def create_sse_close_message() -> str:
    """Creates an SSE 'close' message.

    Returns:
        str: The formatted SSE 'close' message.

    """
    return create_sse_message(event="close", data="stream complete")


def process_refined_experience_result(params: ProcessExperienceResultParams) -> str:
    """Processes refined experience roles and reconstructs the full resume.

    This function takes the refined roles from the LLM, combines them with the
    original projects, and reconstructs the entire resume. It then generates
    the final HTML result to be sent in the 'done' SSE event.

    Args:
        params (ProcessExperienceResultParams): An object containing all parameters
            needed for processing the result.

    Returns:
        str: The complete HTML content for the body of the `done` event.

    Notes:
        1.  Extracts personal, education, and certification sections from `original_resume_content`.
        2.  Extracts projects from `original_resume_content` and roles from `resume_content_to_refine`.
        3.  Updates the roles list with the `refined_roles` data from the LLM.
        4.  Creates a new `ExperienceResponse` with the refined roles and original projects.
        5.  Calls `build_complete_resume_from_sections` to reconstruct the resume markdown.
        6.  If an introduction is provided in `params`, calls `_replace_resume_banner` to insert it into the reconstructed markdown.
        7.  The final, complete markdown is passed to `_create_refine_result_html` to generate the HTML for the UI.

    """
    _msg = "process_refined_experience_result starting"
    log.debug(_msg)

    # 1. Parse all sections from the original, unfiltered resume content
    personal_info = extract_personal_info(params.original_resume_content)
    education_info = extract_education_info(params.original_resume_content)
    certifications_info = extract_certifications_info(params.original_resume_content)
    original_experience_info = extract_experience_info(params.original_resume_content)

    # 2. Get the roles that were subject to refinement (from potentially filtered content)
    refinement_base_experience = extract_experience_info(
        params.resume_content_to_refine,
    )
    # Create a mutable copy
    final_roles = list(refinement_base_experience.roles)

    # 3. Update the roles list with the refined data from the LLM
    for index, role_data in params.refined_roles.items():
        if 0 <= index < len(final_roles):
            final_roles[index] = Role.model_validate(role_data)

    # 4. Create the final ExperienceResponse with refined roles and original projects
    updated_experience = ExperienceResponse(
        roles=final_roles,
        projects=original_experience_info.projects,
    )

    # 5. Reconstruct the full resume markdown string
    reconstructed_content = reconstruct_resume_markdown(
        personal_info=personal_info,
        education=education_info,
        experience=updated_experience,
        certifications=certifications_info,
    )

    # 6. If an introduction was generated, replace the banner with it.
    final_content = _replace_resume_banner(
        resume_content=reconstructed_content,
        introduction=params.introduction,
    )

    # 7. Generate the final HTML for the refinement result UI
    result_html_params = RefineResultParams(
        resume_id=params.resume_id,
        target_section_val=RefineTargetSection.EXPERIENCE.value,
        refined_content=final_content,
        job_description=params.job_description,
        introduction=params.introduction or "",
        limit_refinement_years=params.limit_refinement_years,
    )
    result_html = _create_refine_result_html(params=result_html_params)

    _msg = "process_refined_experience_result returning"
    log.debug(_msg)

    return result_html


def _process_refined_role_event(
    event: dict,
    refined_roles: dict,
) -> str | None:
    """Processes a 'role_refined' event and returns a progress message."""
    index = event.get("original_index")
    data = event.get("data")

    if index is None or data is None:
        _msg = f"Malformed role_refined event received: {event}"
        log.warning(_msg)
        return None

    try:
        # Validate data and create a progress message
        role = Role.model_validate(data)
        refined_roles[index] = data
        if role.basics and role.basics.title and role.basics.company:
            return create_sse_progress_message(
                f"Refined Role: {role.basics.title} at {role.basics.company}",
            )
    except Exception as e:
        _msg = f"Failed to validate refined role data: {e!s}"
        log.exception(_msg)

    return None


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

    status = event.get("status")

    if status == "in_progress":
        sse_message = create_sse_progress_message(event.get("message", ""))
    elif status == "introduction_generated":
        new_introduction = event.get("data")
        if new_introduction:
            sse_message = create_sse_introduction_message(new_introduction)
    elif status == "role_refined":
        sse_message = _process_refined_role_event(event, refined_roles)
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


async def _process_llm_stream_events(
    params: "ExperienceRefinementParams",
    llm_config: LLMConfig,
    message_queue: asyncio.Queue,
) -> tuple[dict, str | None]:
    """Process events from the LLM stream and put them on the queue."""
    refined_roles = {}
    introduction = None

    async for event in async_refine_experience_section(
        resume_content=params.resume_content_to_refine,
        job_description=params.job_description,
        llm_config=llm_config,
    ):
        sse_message, new_introduction = _process_sse_event(event, refined_roles)
        if sse_message:
            await message_queue.put(sse_message)
        if new_introduction is not None:
            introduction = new_introduction

    return refined_roles, introduction


async def _finalize_llm_refinement(
    refined_roles: dict,
    introduction: str | None,
    params: "ExperienceRefinementParams",
    message_queue: asyncio.Queue,
    llm_config: LLMConfig,
):
    """Finalize refinement, process results, and queue done/error messages."""
    # Always ensure an introduction is produced.
    needs_intro = introduction is None or (
        isinstance(introduction, str) and not introduction.strip()
    )
    if needs_intro:
        _msg = "No introduction captured from stream; generating introduction fallback."
        log.debug(_msg)
        try:
            introduction = generate_introduction_from_resume(
                resume_content=params.original_resume_content,
                job_description=params.job_description,
                llm_config=llm_config,
            )
        except Exception as e:
            _msg = f"Failed to generate introduction fallback: {e!s}"
            log.exception(_msg)

    # If still missing, provide a deterministic default introduction.
    if introduction is None or (
        isinstance(introduction, str) and not introduction.strip()
    ):
        introduction = "Professional summary tailored to the provided job description. Customize this section to emphasize your most relevant experience, accomplishments, and skills."

    if not refined_roles:
        await message_queue.put(
            create_sse_error_message(
                "Refinement finished, but no roles were found to refine.",
                is_warning=True,
            ),
        )
    limit_years_int = (
        int(params.limit_refinement_years) if params.limit_refinement_years else None
    )
    process_params = ProcessExperienceResultParams(
        resume_id=params.resume.id,
        original_resume_content=params.original_resume_content,
        resume_content_to_refine=params.resume_content_to_refine,
        refined_roles=refined_roles,
        job_description=params.job_description,
        introduction=introduction,
        limit_refinement_years=limit_years_int,
    )
    result_html = process_refined_experience_result(process_params)
    await message_queue.put(create_sse_done_message(result_html))


async def _llm_task(params: "ExperienceRefinementParams", message_queue: asyncio.Queue):
    """The main background task for performing LLM refinement."""
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

        refined_roles, introduction = await _process_llm_stream_events(
            params=params,
            llm_config=llm_config,
            message_queue=message_queue,
        )

        await _finalize_llm_refinement(
            refined_roles=refined_roles,
            introduction=introduction,
            params=params,
            message_queue=message_queue,
            llm_config=llm_config,
        )

    except Exception as e:
        await message_queue.put(_handle_sse_exception(e, params.resume.id))
    finally:
        await message_queue.put(create_sse_close_message())


async def _yield_messages_from_queue(
    message_queue: asyncio.Queue,
    main_task: asyncio.Task,
) -> AsyncGenerator[str, None]:
    """Yields messages from the queue until a 'close' event is received."""
    while True:
        try:
            message = await asyncio.wait_for(message_queue.get(), timeout=1)
            yield message
            if "event: close" in message:
                break
        except asyncio.TimeoutError:
            if main_task.done() and message_queue.empty():
                log.debug("LLM task finished and queue is empty. Closing stream.")
                break


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


async def handle_sync_refinement(sync_params: SyncRefinementParams) -> Response:
    """Handles synchronous (non-streaming) resume section refinement."""
    _msg = "handle_sync_refinement starting"
    log.debug(_msg)
    try:
        llm_endpoint, llm_model_name, api_key = get_llm_config(
            sync_params.db,
            sync_params.user.id,
        )

        llm_config = LLMConfig(
            llm_endpoint=llm_endpoint,
            api_key=api_key,
            llm_model_name=llm_model_name,
        )

        # Handle other sections synchronously
        refined_content, introduction = refine_resume_section_with_llm(
            resume_content=sync_params.resume.content,
            job_description=sync_params.job_description,
            target_section=sync_params.target_section.value,
            llm_config=llm_config,
        )

        if "HX-Request" in sync_params.request.headers:
            html_params = RefineResultParams(
                resume_id=sync_params.resume.id,
                target_section_val=sync_params.target_section.value,
                refined_content=refined_content,
                job_description=sync_params.job_description,
                introduction=introduction or "",
                limit_refinement_years=sync_params.limit_refinement_years,
            )
            html_content = _create_refine_result_html(params=html_params)
            return HTMLResponse(content=html_content)

        return RefineResponse(
            refined_content=refined_content,
            introduction=introduction,
        )
    except InvalidToken:
        detail = "Invalid API key. Please update your settings."
        _msg = f"API key decryption failed for user {sync_params.user.id}"
        log.warning(_msg)
        if "HX-Request" in sync_params.request.headers:
            return HTMLResponse(
                f'<div role="alert" class="text-red-500 p-2">{detail}</div>',
                status_code=200,
            )
        raise HTTPException(status_code=400, detail=detail)
    except AuthenticationError as e:
        detail = "LLM authentication failed. Please check your API key in settings."
        _msg = f"LLM authentication failed for user {sync_params.user.id}: {e!s}"
        log.warning(_msg)
        if "HX-Request" in sync_params.request.headers:
            return HTMLResponse(
                f'<div role="alert" class="text-red-500 p-2">{detail}</div>',
                status_code=200,
            )
        raise HTTPException(status_code=401, detail=detail)
    except ValueError as e:
        detail = str(e)
        _msg = f"LLM refinement failed for resume {sync_params.resume.id} with ValueError: {detail}"
        log.warning(_msg)
        if "HX-Request" in sync_params.request.headers:
            return HTMLResponse(
                f'<div role="alert" class="text-red-500 p-2">Refinement failed: {detail}</div>',
                status_code=200,
            )
        raise HTTPException(status_code=400, detail=detail)
    except Exception as e:
        detail = f"An unexpected error occurred during refinement: {e!s}"
        _msg = f"LLM refinement failed for resume {sync_params.resume.id}: {e!s}"
        log.exception(_msg)
        if "HX-Request" in sync_params.request.headers:
            return HTMLResponse(
                f'<div role="alert" class="text-red-500 p-2">{detail}</div>',
                status_code=200,
            )
        raise HTTPException(status_code=500, detail=f"LLM refinement failed: {e!s}")


async def experience_refinement_sse_generator(
    params: "ExperienceRefinementParams",
) -> AsyncGenerator[str, None]:
    """Generates SSE events for the experience refinement process.

    This function orchestrates the asynchronous experience refinement by running a
    background task (`_llm_task`) that performs the LLM calls. It yields
    messages from a queue, including progress, generated introductions, and the
    final result.

    The background task captures the introduction from the LLM stream and passes
    it to `process_refined_experience_result` to ensure the final preview
    includes it.

    Args:
        params (ExperienceRefinementParams): An object containing all parameters
            needed for the SSE generation.

    Yields:
        str: Formatted SSE message strings.

    """
    _msg = f"Streaming refinement for resume {params.resume.id} for section experience"
    log.debug(_msg)
    message_queue: asyncio.Queue = asyncio.Queue()

    main_task = asyncio.create_task(_llm_task(params, message_queue))

    try:
        async for message in _yield_messages_from_queue(message_queue, main_task):
            yield message
    except GeneratorExit:
        _msg = f"SSE stream closed for resume {params.resume.id}."
        log.warning(_msg)
    finally:
        # Ensure the background task is cancelled if the client disconnects or
        # the stream is otherwise closed.
        if not main_task.done():
            main_task.cancel()
        _msg = "SSE generator finished."
        log.debug(_msg)


def handle_save_as_new_refinement(params: SaveAsNewParams) -> DatabaseResume:
    """Orchestrates saving a refined resume as a new resume.

    This involves reconstructing the resume from the refined content, and then
    handling the introduction. It correctly uses the introduction from the form
    data if provided. If the introduction is missing and a job description is
    available, a new introduction is generated via an LLM. The final content is
    validated, and a new resume record is created in the database, persisting
    the introduction to its dedicated field.

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
        # 1. Reconstruct the full resume content with the refined section.
        updated_content = reconstruct_resume_from_refined_section(
            original_resume_content=params.resume.content,
            refined_content=params.form_data.refined_content,
            target_section=params.form_data.target_section,
        )

        job_description_val = params.form_data.job_description
        introduction = params.form_data.introduction
        new_resume_name = params.form_data.new_resume_name

        _msg = f"Introduction from form: '{introduction}'"
        log.debug(_msg)

        # 2. Conditionally generate an introduction.
        # If user provided one, use it. Otherwise, if a JD is present, generate one.
        if not introduction or not introduction.strip():
            if job_description_val:
                _msg = "User-provided introduction is empty and job description is present. Generating new introduction."
                log.debug(_msg)
                llm_endpoint, llm_model_name, api_key = get_llm_config(
                    params.db,
                    params.user.id,
                )
                llm_config = LLMConfig(
                    llm_endpoint=llm_endpoint,
                    api_key=api_key,
                    llm_model_name=llm_model_name,
                )
                introduction = generate_introduction_from_resume(
                    resume_content=updated_content,
                    job_description=job_description_val,
                    llm_config=llm_config,
                )
            else:
                _msg = "No user-provided introduction and no job description. Introduction will be None."
                log.debug(_msg)
                introduction = None
        else:
            _msg = "Using user-provided introduction."
            log.debug(_msg)

        # 3. The final content for the resume record is the reconstructed content.
        # The introduction is now stored in a separate DB field.
        final_content = updated_content
        perform_pre_save_validation(final_content)
    except (ValueError, TypeError, HTTPException) as e:
        detail = getattr(e, "detail", str(e))
        _msg = f"Failed to reconstruct resume from refined section: {detail}"
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=_msg)

    # 4. Create the new resume record, passing the determined introduction.
    _msg = f"Final introduction before DB save: '{introduction}'"
    log.debug(_msg)
    create_params = ResumeCreateParams(
        user_id=params.user.id,
        name=new_resume_name,
        content=final_content,
        is_base=False,
        parent_id=params.resume.id,
        job_description=job_description_val,
        introduction=introduction,
    )
    new_resume = create_resume_db(
        db=params.db,
        params=create_params,
    )

    _msg = "handle_save_as_new_refinement returning"
    log.debug(_msg)
    return new_resume
