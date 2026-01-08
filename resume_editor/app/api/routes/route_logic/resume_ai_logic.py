import asyncio
import html
import logging
from pathlib import Path
from typing import AsyncGenerator

from cryptography.fernet import InvalidToken
from fastapi import HTTPException
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
from resume_editor.app.api.routes.route_logic.resume_serialization import (
    extract_experience_info,
    serialize_experience_to_markdown,
)
from resume_editor.app.api.routes.route_logic.resume_validation import (
    perform_pre_save_validation,
)
from resume_editor.app.api.routes.route_logic.settings_crud import get_user_settings
from resume_editor.app.api.routes.route_models import (
    ExperienceResponse,
    SaveAsNewParams,
)
from resume_editor.app.core.security import decrypt_data
from resume_editor.app.llm.models import LLMConfig
from resume_editor.app.llm.orchestration import (
    async_refine_experience_section,
    generate_introduction_from_resume,
)
from resume_editor.app.models.resume.experience import Role
from resume_editor.app.models.resume_model import Resume as DatabaseResume

log = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "templates"
env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)


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
        2.  Extract raw sections for Personal, Education, Certifications, and Experience.
        3.  Update the banner in the raw Personal section using `_update_banner_in_raw_personal`.
        4.  Concatenate the sections to form the updated resume content.
        5.  Return the newly reconstructed Markdown string.

    """
    _msg = "reconstruct_resume_with_new_introduction starting"
    log.debug(_msg)

    if introduction is None or not introduction.strip():
        _msg = "reconstruct_resume_with_new_introduction returning original content (no introduction)"
        log.debug(_msg)
        return resume_content

    # Extract raw sections
    raw_personal = _extract_raw_section(resume_content, "personal")
    raw_education = _extract_raw_section(resume_content, "education")
    raw_certifications = _extract_raw_section(resume_content, "certifications")
    raw_experience = _extract_raw_section(resume_content, "experience")

    # Update banner in raw personal section
    updated_raw_personal = _update_banner_in_raw_personal(
        raw_personal,
        introduction,
    )

    # Reconstruct content
    sections = []
    if updated_raw_personal.strip():
        sections.append(updated_raw_personal.strip() + "\n")
    if raw_education.strip():
        sections.append(raw_education.strip() + "\n")
    if raw_certifications.strip():
        sections.append(raw_certifications.strip() + "\n")
    if raw_experience.strip():
        sections.append(raw_experience.strip() + "\n")

    updated_content = "\n".join(filter(None, sections))

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


def _extract_raw_section(resume_content: str, section_name: str) -> str:
    """Extract the raw text of a section from the resume content."""
    lines = resume_content.splitlines()
    section_header = f"# {section_name.lower()}"
    in_section = False
    captured_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("## "):
            if stripped.lower() == section_header:
                in_section = True
                captured_lines.append(line)
                continue
            elif in_section:
                break

        if in_section:
            captured_lines.append(line)

    result = "\n".join(captured_lines)
    if result and not result.endswith("\n"):
        result += "\n"
    return result


def _update_banner_in_raw_personal(raw_personal: str, introduction: str | None) -> str:
    """Update the Banner subsection in a raw Personal section string.

    If `introduction` is None or empty, return `raw_personal` unchanged.
    It parses the `raw_personal` string to find the `## Banner` subsection.
    If found, it replaces the content of the Banner subsection with the new `introduction`.
    If not found, it appends a new `## Banner` section with the `introduction` at the end of the Personal section.
    It preserves all other lines in the Personal section exactly as they are.

    Notes:
        1. It carefully handles newlines, ensuring there is a blank line between
           the '## Banner' header and its content for correct paragraph and
           list rendering in Markdown.

    """
    if not introduction or not introduction.strip():
        return raw_personal

    stripped_intro = introduction.strip()
    lines = raw_personal.splitlines()
    new_lines = []
    banner_found = False

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check for start of Banner section
        if stripped.lower().startswith("## banner"):
            banner_found = True
            new_lines.append("## Banner")
            new_lines.append("")
            new_lines.append(stripped_intro)
            new_lines.append("")

            # Skip existing banner content until next subsection or end of string
            i += 1
            while i < len(lines):
                next_line = lines[i]
                next_stripped = next_line.strip()
                # Check for next subsection (## ) or next section (# )
                # Note: raw_personal should only contain the Personal section, so # is unlikely unless malformed
                if next_stripped.startswith("## ") or next_stripped.startswith("# "):
                    # Found next section/subsection, stop skipping and back up
                    i -= 1
                    break
                i += 1
        else:
            new_lines.append(line)
        i += 1

    if not banner_found:
        # Append banner if not found
        if new_lines and new_lines[-1].strip():
            new_lines.append("")

        new_lines.append("## Banner")
        new_lines.append("")
        new_lines.append(stripped_intro)
        new_lines.append("")

    result = "\n".join(new_lines)
    if result and not result.endswith("\n"):
        result += "\n"
    return result


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
        1.  Extracts raw sections for Personal, Education, and Certifications to preserve them exactly.
        2.  Updates the banner in the raw Personal section if an introduction is provided.
        3.  Extracts projects from `original_resume_content` and roles from `resume_content_to_refine`.
        4.  Updates the roles list with the `refined_roles` data from the LLM.
        5.  Creates a new `ExperienceResponse` with the refined roles and original projects.
        6.  Reconstructs the resume using updated raw personal, raw education/certifications, and serialized experience.
        7.  The final, complete markdown is passed to `_create_refine_result_html` to generate the HTML for the UI.

    """
    _msg = "process_refined_experience_result starting"
    log.debug(_msg)

    # 1. Extract raw sections to preserve formatting and IDs
    raw_personal = _extract_raw_section(params.original_resume_content, "personal")
    raw_education = _extract_raw_section(params.original_resume_content, "education")
    raw_certifications = _extract_raw_section(
        params.original_resume_content,
        "certifications",
    )

    # 2. Update the banner in the raw personal section
    updated_raw_personal = _update_banner_in_raw_personal(
        raw_personal,
        params.introduction,
    )

    # 3. Extract experience from original content to preserve projects
    original_experience_info = extract_experience_info(params.original_resume_content)

    # 4. Get the roles that were subject to refinement (from potentially filtered content)
    refinement_base_experience = extract_experience_info(
        params.resume_content_to_refine,
    )
    # Create a mutable copy
    final_roles = list(refinement_base_experience.roles)

    # 5. Update the roles list with the refined data from the LLM
    for index, role_data in params.refined_roles.items():
        if 0 <= index < len(final_roles):
            final_roles[index] = Role.model_validate(role_data)

    # 6. Create the final ExperienceResponse with refined roles and original projects
    updated_experience = ExperienceResponse(
        roles=final_roles,
        projects=original_experience_info.projects,
    )

    # 7. Reconstruct the full resume markdown string
    # We manually combine sections to use raw content where needed
    sections = []

    # Personal (Raw + Updated Banner)
    if updated_raw_personal.strip():
        sections.append(updated_raw_personal.strip() + "\n")

    # Education (Raw)
    if raw_education.strip():
        sections.append(raw_education.strip() + "\n")

    # Certifications (Raw)
    if raw_certifications.strip():
        sections.append(raw_certifications.strip() + "\n")

    # Experience (Serialized)
    sections.append(serialize_experience_to_markdown(updated_experience))

    final_content = "\n".join(filter(None, sections))

    # 8. Generate the final HTML for the refinement result UI
    result_html_params = RefineResultParams(
        resume_id=params.resume_id,
        target_section_val="experience",
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

    This function takes the full refined resume content, validates it, and
    creates a new resume record in the database. The introduction is taken
    directly from the refinement context and persisted to its dedicated field.

    Args:
        params (SaveAsNewParams): The parameters for saving the new resume.

    Returns:
        DatabaseResume: The newly created resume object.

    Raises:
        HTTPException: If validation fails.

    Notes:
        1. The `refined_content` from the form is assumed to be the full, final resume content.
        2. The introduction is taken from the form context and passed directly to the database.
        3. No resume reconstruction or on-the-fly introduction generation occurs here.

    """
    _msg = "handle_save_as_new_refinement starting"
    log.debug(_msg)

    try:
        final_content = params.form_data.refined_content
        job_description_val = params.form_data.job_description
        introduction = params.form_data.introduction
        new_resume_name = params.form_data.new_resume_name

        perform_pre_save_validation(final_content)
    except (ValueError, TypeError, HTTPException) as e:
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
    )
    new_resume = create_resume_db(
        db=params.db,
        params=create_params,
    )

    _msg = "handle_save_as_new_refinement returning"
    log.debug(_msg)
    return new_resume
