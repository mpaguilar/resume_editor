"""Streaming functions for resume AI logic."""

import logging
from datetime import datetime
from typing import Any, AsyncGenerator

from cryptography.fernet import InvalidToken
from openai import AuthenticationError

from resume_editor.app.api.routes.route_logic.resume_ai_logic_params import (
    ProcessExperienceResultParams,
)
from resume_editor.app.api.routes.route_logic.resume_ai_logic_reconstruction import (
    _reconstruct_refined_resume_content,
)
from resume_editor.app.api.routes.route_logic.resume_ai_logic_sse import (
    create_sse_close_message,
    create_sse_done_message,
    create_sse_error_message,
    create_sse_progress_message,
)
from resume_editor.app.api.routes.route_logic.resume_serialization import (
    extract_banner_text,
)
from resume_editor.app.api.routes.route_models import ExperienceRefinementParams
from resume_editor.app.llm.models import LLMConfig, RefinedRoleRecord, RunningLog
from resume_editor.app.llm.orchestration import generate_introduction_from_resume
from resume_editor.app.llm.orchestration_banner import generate_banner_from_running_log
from resume_editor.app.llm.orchestration_refinement import (
    async_refine_experience_section,
)
from resume_editor.app.models.resume.experience import Role
from resume_editor.app.api.routes.route_logic.refinement_checkpoint import (
    running_log_manager,
)
from resume_editor.app.api.routes.route_logic.resume_ai_logic_extraction import (
    reconstruct_resume_with_new_introduction,
)
from resume_editor.app.api.routes.route_logic.resume_ai_logic_helpers import (
    get_llm_config,
    process_refined_experience_result,
)

log = logging.getLogger(__name__)


def _process_single_event(event: dict, refined_roles: dict) -> str | None:
    """Process a single SSE event and return an SSE message.

    Args:
        event: The event data from the stream.
        refined_roles: Dictionary to update with refined role data.

    Returns:
        SSE message string or None if no message should be yielded.

    """
    _msg = f"_process_single_event starting with event: {event}"
    log.debug(_msg)

    status = event.get("status")
    sse_message = None

    if status == "in_progress":
        sse_message = create_sse_progress_message(event.get("message", ""))
    elif status == "job_analysis_complete":
        message = event.get("message", "")
        sse_message = create_sse_progress_message(message)
    elif status == "role_refined":
        sse_message = _handle_role_refined_sse_event(event, refined_roles)
    else:
        _msg = f"Unhandled SSE event received: {event}"
        log.warning(_msg)

    _msg = "_process_single_event returning"
    log.debug(_msg)
    return sse_message


def _handle_role_refined_sse_event(event: dict, refined_roles: dict) -> str | None:
    """Handle a role_refined event and return SSE progress message.

    Args:
        event: The event containing role_refined data.
        refined_roles: Dictionary to update with role data.

    Returns:
        SSE message or None if validation fails.

    """
    index = event.get("original_index")
    data = event.get("data")

    if index is None or data is None:
        _msg = f"Malformed role_refined event received: {event}"
        log.warning(_msg)
        return None

    try:
        role = Role.model_validate(data)
        if not role.basics:
            raise ValueError("Refined role data is missing 'basics' section.")

        refined_roles[index] = role.model_dump(mode="json")
        return create_sse_progress_message(
            f"Refined Role: {role.basics.title} at {role.basics.company}",
        )
    except Exception as e:
        _msg = f"Failed to validate refined role data: {e!s}"
        log.exception(_msg)

    return None


def _handle_job_analysis_event(
    event: dict,
    running_log: RunningLog | None,
    resume_id: int,
    user_id: int,
) -> None:
    """Handle job_analysis_complete event by storing in running log.

    Args:
        event: The event containing job_analysis data.
        running_log: The running log to update.
        resume_id: ID of the resume being processed.
        user_id: ID of the user.

    """
    job_analysis_data = event.get("job_analysis")
    if job_analysis_data and running_log:
        try:
            from resume_editor.app.llm.models import JobAnalysis

            job_analysis = JobAnalysis.model_validate(job_analysis_data)
            running_log_manager.update_job_analysis(
                resume_id=resume_id,
                user_id=user_id,
                job_analysis=job_analysis,
            )
            _msg = "Stored job_analysis in running log"
            log.debug(_msg)
        except Exception as e:
            _msg = f"Failed to store job_analysis: {e!s}"
            log.exception(_msg)


def _handle_role_refined_event(
    event: dict,
    running_log: RunningLog | None,
    resume_id: int,
    user_id: int,
) -> None:
    """Handle role_refined event by adding to running log.

    Args:
        event: The event containing role_refined data.
        running_log: The running log to update.
        resume_id: ID of the resume being processed.
        user_id: ID of the user.

    """
    if running_log:
        original_index = event.get("original_index")
        data = event.get("data")
        if original_index is not None and data:
            try:
                role_record = _create_refined_role_record(original_index, data)
                running_log_manager.add_refined_role(
                    resume_id=resume_id,
                    user_id=user_id,
                    role_record=role_record,
                )
                _msg = f"Added refined role at index {original_index} to running log"
                log.debug(_msg)
            except Exception as e:
                _msg = f"Failed to create refined role record: {e!s}"
                log.exception(_msg)


def _create_refined_role_record(
    original_index: int,
    role_data: dict,
) -> RefinedRoleRecord:
    """Create a RefinedRoleRecord from refined role data.

    Args:
        original_index: The position of this role in the original resume.
        role_data: The refined role data dictionary from the LLM.

    Returns:
        A record tracking the refined role.

    """
    _msg = "_create_refined_role_record starting"
    log.debug(_msg)

    basics = role_data.get("basics", {})
    summary = role_data.get("summary", {})
    skills = role_data.get("skills", {})

    company = basics.get("company", "")
    title = basics.get("title", "")
    start_date_str = basics.get("start_date")
    end_date_str = basics.get("end_date")

    start_date = datetime.now()
    if start_date_str:
        try:
            start_date = datetime.fromisoformat(start_date_str)
        except ValueError:
            pass

    end_date = None
    if end_date_str:
        try:
            end_date = datetime.fromisoformat(end_date_str)
        except ValueError:
            pass

    refined_description = summary.get("text", "") if isinstance(summary, dict) else ""
    relevant_skills = skills.get("items", []) if isinstance(skills, dict) else []

    record = RefinedRoleRecord(
        original_index=original_index,
        company=company,
        title=title,
        refined_description=refined_description,
        relevant_skills=relevant_skills,
        start_date=start_date,
        end_date=end_date,
        timestamp=datetime.now(),
    )

    _msg = "_create_refined_role_record returning"
    log.debug(_msg)
    return record


def _build_skip_indices_from_log(running_log: RunningLog | None) -> set[int]:
    """Extract already-refined role indices from running log.

    Args:
        running_log: The running log containing refined roles, or None.

    Returns:
        A set of original indices that have already been refined.

    """
    _msg = "_build_skip_indices_from_log starting"
    log.debug(_msg)

    if not running_log or not running_log.refined_roles:
        _msg = "_build_skip_indices_from_log returning empty set"
        log.debug(_msg)
        return set()

    indices = {role.original_index for role in running_log.refined_roles}

    _msg = "_build_skip_indices_from_log returning"
    log.debug(_msg)
    return indices


def _get_refinement_config(
    running_log: RunningLog | None,
) -> tuple[set[int], Any]:
    """Get skip indices and job analysis from running log.

    Args:
        running_log: The running log containing checkpoint data.

    Returns:
        Tuple of skip indices set and job analysis.

    """
    skip_indices = _build_skip_indices_from_log(running_log)
    if skip_indices:
        _msg = f"Skipping already refined roles: {skip_indices}"
        log.debug(_msg)

    job_analysis = running_log.job_analysis if running_log else None
    if job_analysis:
        _msg = "Using cached job analysis from running log"
        log.debug(_msg)

    return skip_indices, job_analysis


def _process_refinement_event(
    event: dict,
    running_log: RunningLog | None,
    resume_id: int,
    user_id: int,
    refined_roles: dict,
) -> str | None:
    """Process a single refinement event.

    Args:
        event: The event from the refinement stream.
        running_log: The running log for checkpoint updates.
        resume_id: The resume ID.
        user_id: The user ID.
        refined_roles: Dictionary to collect refined role data.

    Returns:
        SSE message string or None.

    """
    if event.get("status") == "job_analysis_complete":
        _handle_job_analysis_event(event, running_log, resume_id, user_id)

    if event.get("status") == "role_refined":
        _handle_role_refined_event(event, running_log, resume_id, user_id)

    return _process_single_event(event, refined_roles)


async def _stream_llm_events(
    params: ExperienceRefinementParams,
    llm_config: LLMConfig,
    refined_roles: dict,
    running_log: RunningLog | None = None,
) -> AsyncGenerator[str, None]:
    """Stream events from the LLM and yield SSE messages.

    Args:
        params: The refinement parameters.
        llm_config: The LLM configuration.
        refined_roles: Dictionary to collect refined role data.
        running_log: Optional running log for checkpoint/resumption support.

    Yields:
        SSE formatted messages.

    """
    _msg = "_stream_llm_events starting"
    log.debug(_msg)

    skip_indices, job_analysis = _get_refinement_config(running_log)

    from resume_editor.app.llm.orchestration_refinement import RefinementState

    refinement_state = RefinementState(
        job_analysis=job_analysis,
        skip_indices=skip_indices,
    )
    refinement_stream = async_refine_experience_section(
        resume_content=params.resume_content_to_refine,
        job_description=params.job_description,
        llm_config=llm_config,
        state=refinement_state,
    )

    try:
        async for event in refinement_stream:
            sse_message = _process_refinement_event(
                event, running_log, params.resume.id, params.user.id, refined_roles
            )
            if sse_message:
                yield sse_message
    finally:
        await refinement_stream.aclose()

    _msg = "_stream_llm_events returning"
    log.debug(_msg)


async def _try_generate_from_running_log(
    running_log: RunningLog,
    resume_content: str,
    llm_config: LLMConfig,
    original_banner: str | None,
) -> str | None:
    """Try to generate introduction from running log.

    Args:
        running_log: The running log containing refined roles.
        resume_content: The reconstructed resume content.
        llm_config: The LLM configuration.
        original_banner: The original banner text for context.

    Returns:
        Generated introduction or None if failed.

    """
    _msg = "Attempting banner generation from running log"
    log.debug(_msg)
    try:
        intro = generate_banner_from_running_log(
            running_log=running_log,
            original_resume_content=resume_content,
            llm_config=llm_config,
            original_banner=original_banner,
        )
        if intro and intro.strip():
            _msg = "Banner generated successfully from running log"
            log.debug(_msg)
            return intro
        _msg = "Banner generation from running log returned empty, falling back"
        log.warning(_msg)
    except Exception as e:
        _msg = f"Banner generation from running log failed: {e!s}"
        log.warning(_msg)
    return None


async def _try_generate_with_retries(
    resume_content: str,
    job_description: str,
    llm_config: LLMConfig,
    original_banner: str | None,
) -> str | None:
    """Try to generate introduction with retries.

    Args:
        resume_content: The reconstructed resume content.
        job_description: The job description for context.
        llm_config: The LLM configuration.
        original_banner: The original banner text for context.

    Returns:
        Generated introduction or None if all retries fail.

    """
    for i in range(3):
        try:
            _msg = f"Attempt {i + 1} to generate introduction (legacy method)."
            log.debug(_msg)
            intro = generate_introduction_from_resume(
                resume_content=resume_content,
                job_description=job_description,
                llm_config=llm_config,
                original_banner=original_banner,
            )
            if intro and intro.strip():
                _msg = "Introduction generated successfully (legacy method)."
                log.debug(_msg)
                return intro
            _msg = f"Attempt {i + 1} yielded empty introduction."
            log.warning(_msg)
        except Exception as e:
            _msg = f"Attempt {i + 1} to generate introduction failed: {e!s}"
            log.warning(_msg)
    return None


def _get_default_introduction() -> str:
    """Return default introduction when generation fails.

    Returns:
        Default introduction text.

    """
    _msg = "Failed to generate introduction after all retries. Using default."
    log.error(_msg)
    return (
        "Professional summary tailored to the provided job description. "
        "Customize this section to emphasize your most relevant experience, "
        "accomplishments, and skills."
    )


async def _generate_introduction_with_fallback(
    resume_content: str,
    job_description: str,
    llm_config: LLMConfig,
    original_banner: str | None,
    running_log: RunningLog | None,
) -> str:
    """Generate introduction with fallback mechanisms.

    Args:
        resume_content: The reconstructed resume content.
        job_description: The job description for context.
        llm_config: The LLM configuration.
        original_banner: The original banner text for context.
        running_log: Optional running log for banner generation.

    Returns:
        The generated introduction text.

    """
    generated_introduction = None

    if running_log is not None and running_log.refined_roles:
        generated_introduction = await _try_generate_from_running_log(
            running_log, resume_content, llm_config, original_banner
        )

    if generated_introduction is None:
        generated_introduction = await _try_generate_with_retries(
            resume_content, job_description, llm_config, original_banner
        )

    if not generated_introduction:
        generated_introduction = _get_default_introduction()

    return generated_introduction


async def _stream_final_events(
    refined_roles: dict,
    params: ExperienceRefinementParams,
    llm_config: LLMConfig,
    running_log: RunningLog | None = None,
) -> AsyncGenerator[str, None]:
    """Handle the final sequential steps of AI refinement.

    Args:
        refined_roles: A dictionary of refined role data.
        params: The original refinement parameters.
        llm_config: The LLM configuration.
        running_log: Optional running log for banner generation.

    Yields:
        SSE messages for introduction progress, potential warnings, and final events.

    """
    limit_years_int = (
        int(params.limit_refinement_years) if params.limit_refinement_years else None
    )

    reconstruct_params = ProcessExperienceResultParams(
        resume_id=params.resume.id,
        original_resume_content=params.original_resume_content,
        resume_content_to_refine=params.resume_content_to_refine,
        refined_roles=refined_roles,
        job_description=params.job_description,
        limit_refinement_years=limit_years_int,
    )
    resume_with_refined_roles = _reconstruct_refined_resume_content(
        params=reconstruct_params,
    )

    original_banner = extract_banner_text(params.original_resume_content)

    yield create_sse_progress_message("Generating AI introduction...")

    generated_introduction = await _generate_introduction_with_fallback(
        resume_content=resume_with_refined_roles,
        job_description=params.job_description,
        llm_config=llm_config,
        original_banner=original_banner,
        running_log=running_log,
    )

    final_content = reconstruct_resume_with_new_introduction(
        resume_content=resume_with_refined_roles,
        introduction=generated_introduction,
    )

    if not refined_roles:
        yield create_sse_error_message(
            "Refinement finished, but no roles were found to refine.",
            is_warning=True,
        )

    result_html = process_refined_experience_result(
        resume_id=params.resume.id,
        final_content=final_content,
        job_description=params.job_description,
        introduction=generated_introduction,
        limit_refinement_years=limit_years_int,
        company=params.company,
        notes=params.notes,
    )
    yield create_sse_done_message(result_html)


def _prepare_refinement_params(params: ExperienceRefinementParams) -> LLMConfig:
    """Prepare LLM configuration from refinement parameters.

    Args:
        params: The refinement parameters containing user and db info.

    Returns:
        The configured LLMConfig object.

    """
    llm_endpoint, llm_model_name, api_key = get_llm_config(params.db, params.user.id)
    return LLMConfig(
        llm_endpoint=llm_endpoint,
        api_key=api_key,
        llm_model_name=llm_model_name,
    )


def _handle_sse_exception(e: Exception, resume_id: int) -> str:
    """Handle exceptions during an SSE stream and format an error message.

    Args:
        e: The exception that was raised.
        resume_id: ID of the resume being processed.

    Returns:
        A formatted SSE error message string.

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


def _get_running_log(resume_id: int, user_id: int) -> tuple[RunningLog | None, bool]:
    """Get running log and determine if resuming from checkpoint.

    Args:
        resume_id: The ID of the resume being refined.
        user_id: The ID of the user performing the refinement.

    Returns:
        Tuple of (running_log, is_resuming).

    """
    running_log = running_log_manager.get_log(resume_id, user_id)
    if running_log:
        _msg = f"Found existing running log for resume {resume_id}"
        log.debug(_msg)
    else:
        _msg = f"No existing running log for resume {resume_id}"
        log.debug(_msg)

    is_resuming = running_log is not None and len(running_log.refined_roles) > 0
    if is_resuming:
        _msg = f"Resuming refinement for resume {resume_id} with {len(running_log.refined_roles)} roles already refined"
        log.debug(_msg)

    return running_log, is_resuming


def _convert_role_record_to_dict(role_record: RefinedRoleRecord) -> dict:
    """Convert a RefinedRoleRecord to a dictionary.

    Args:
        role_record: The role record to convert.

    Returns:
        Dictionary representation of the role record.

    """
    return {
        "basics": {
            "company": role_record.company,
            "title": role_record.title,
            "start_date": role_record.start_date.isoformat(),
            "end_date": role_record.end_date.isoformat()
            if role_record.end_date
            else None,
        },
        "summary": {"text": role_record.refined_description},
        "skills": {"items": role_record.relevant_skills},
    }


def _prepopulate_refined_roles(
    running_log: RunningLog | None,
) -> dict[int, Any]:
    """Pre-populate refined roles from running log.

    Args:
        running_log: The running log containing refined roles.

    Returns:
        Dictionary of refined roles by index.

    """
    refined_roles: dict[int, Any] = {}

    if running_log:
        for role_record in running_log.refined_roles:
            role_dict = _convert_role_record_to_dict(role_record)
            refined_roles[role_record.original_index] = role_dict
            _msg = f"Pre-populated refined role at index {role_record.original_index}"
            log.debug(_msg)

    return refined_roles


async def _stream_refinement_events(
    params: ExperienceRefinementParams,
    llm_config: LLMConfig,
    running_log: RunningLog | None,
) -> AsyncGenerator[str, None]:
    """Stream all refinement events from LLM and final processing.

    Args:
        params: The refinement parameters.
        llm_config: The LLM configuration.
        running_log: Optional running log for checkpoint support.

    Yields:
        SSE formatted messages.

    """
    refined_roles = _prepopulate_refined_roles(running_log)

    async for sse_message in _stream_llm_events(
        params=params,
        llm_config=llm_config,
        refined_roles=refined_roles,
        running_log=running_log,
    ):
        yield sse_message

    async for sse_message in _stream_final_events(
        refined_roles=refined_roles,
        params=params,
        llm_config=llm_config,
        running_log=running_log,
    ):
        yield sse_message


async def _yield_resumption_message(is_resuming: bool) -> AsyncGenerator[str, None]:
    """Yield resumption message if resuming from checkpoint.

    Args:
        is_resuming: Whether resuming from a previous checkpoint.

    Yields:
        SSE progress message if resuming.

    """
    if is_resuming:
        yield create_sse_progress_message("Resuming from previous attempt...")


async def _handle_stream_completion(
    closed_by_client: bool,
) -> AsyncGenerator[str, None]:
    """Handle stream completion by yielding close message.

    Args:
        closed_by_client: Whether the stream was closed by the client.

    Yields:
        SSE close message if not closed by client.

    """
    if not closed_by_client:
        yield create_sse_close_message()
        _msg = "SSE generator finished."
        log.debug(_msg)


async def _run_refinement(
    params: ExperienceRefinementParams,
) -> AsyncGenerator[str, None]:
    """Run the refinement process.

    Args:
        params: The refinement parameters.

    Yields:
        SSE formatted messages.

    """
    running_log, is_resuming = _get_running_log(params.resume.id, params.user.id)
    llm_config = _prepare_refinement_params(params)

    async for msg in _yield_resumption_message(is_resuming):
        yield msg

    async for sse_message in _stream_refinement_events(params, llm_config, running_log):
        yield sse_message


async def experience_refinement_sse_generator(
    params: ExperienceRefinementParams,
) -> AsyncGenerator[str, None]:
    """Orchestrate the entire sequential AI refinement process via SSE.

    Args:
        params: An object containing all parameters needed for the SSE generation.

    Yields:
        Formatted SSE message strings for progress, errors, and completion.

    """
    _msg = f"Streaming refinement for resume {params.resume.id} for section experience"
    log.debug(_msg)

    closed_by_client = False
    try:
        async for msg in _run_refinement(params):
            yield msg
    except GeneratorExit:
        closed_by_client = True
        _msg = f"SSE stream closed for resume {params.resume.id}."
        log.warning(_msg)
    except Exception as e:
        yield _handle_sse_exception(e, params.resume.id)

    if not closed_by_client:
        yield create_sse_close_message()
        _msg = "SSE generator finished."
        log.debug(_msg)
