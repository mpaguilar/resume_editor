"""Role refinement functions for LLM orchestration."""

import asyncio
import json
import logging
from collections.abc import AsyncGenerator, Awaitable, Callable
from dataclasses import dataclass

from cryptography.fernet import InvalidToken
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.utils.json import parse_json_markdown
from langchain_openai import ChatOpenAI
from openai import AuthenticationError
from pydantic import ValidationError

from resume_editor.app.api.routes.route_logic.resume_serialization import (
    extract_experience_info,
)
from resume_editor.app.llm.models import (
    JobAnalysis,
    LLMConfig,
    RefinedRole,
    RoleRefinementJob,
)
from resume_editor.app.llm.orchestration_client import initialize_llm_client
from resume_editor.app.llm.orchestration_models import (
    HandleRetryDelayParams,
    ProcessRefinementErrorParams,
)
from resume_editor.app.llm.prompts import (
    ROLE_REFINE_HUMAN_PROMPT,
    ROLE_REFINE_SYSTEM_PROMPT,
)
from resume_editor.app.api.routes.route_models import ExperienceResponse
from resume_editor.app.models.resume.experience import Role

log = logging.getLogger(__name__)


@dataclass
class RefinementState:
    """State for experience section refinement.

    Attributes:
        job_analysis: Optional cached job analysis.
        skip_indices: Optional set of role indices to skip.

    """

    job_analysis: JobAnalysis | None = None
    skip_indices: set[int] | None = None


@dataclass
class RefinementOrchestratorParams:
    """Parameters for experience section refinement orchestration.

    Attributes:
        resume_content: The full Markdown content of the resume.
        job_description: The job description to align with.
        llm_config: LLM configuration.
        max_concurrency: Maximum roles to refine in parallel.
        state: Optional refinement state containing job_analysis and skip_indices.

    """

    resume_content: str
    job_description: str
    llm_config: LLMConfig
    max_concurrency: int = 5
    state: RefinementState | None = None


def _is_retryable_error(e: Exception) -> bool:
    """Determine if an error is retryable.

    Args:
        e: The exception to check.

    Returns:
        True if the error is retryable, False otherwise.

    Notes:
        1. Retryable: json.JSONDecodeError, TimeoutError, ConnectionError.
        2. Non-retryable: AuthenticationError, ValidationError, InvalidToken.

    """
    retryable_types = (json.JSONDecodeError, TimeoutError, ConnectionError)
    non_retryable_types = (AuthenticationError, ValidationError, InvalidToken)

    if isinstance(e, retryable_types):
        return True
    if isinstance(e, non_retryable_types):
        return False
    return False


def _truncate_for_log(text: str, max_len: int = 500) -> str:
    """Truncate text for logging purposes.

    Args:
        text: The text to potentially truncate.
        max_len: Maximum length before truncation. Defaults to 500.

    Returns:
        Original text if within max_len, otherwise truncated with "...".

    """
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text


def _log_failed_attempt(
    role: Role,
    attempt: int,
    response: str,
    error: Exception,
    job_analysis: JobAnalysis,
) -> None:
    """Log a failed role refinement attempt.

    Args:
        role: The role being refined.
        attempt: The attempt number that failed.
        response: The LLM response that caused the failure.
        error: The exception that occurred.
        job_analysis: The job analysis context.

    """
    truncated_response = _truncate_for_log(response)
    job_summary = job_analysis.model_dump_json(indent=2)
    error_type = type(error).__name__

    _msg = (
        f"Failed attempt {attempt} for role '{role.basics.title} @ {role.basics.company}'. "
        f"Error type: {error_type}. "
        f"Job analysis: {job_summary}. Response: {truncated_response}"
    )
    log.debug(_msg)


def _create_error_context(role: Role, max_attempts: int) -> str:
    """Create a user-friendly error message for failed refinement.

    Args:
        role: The role that failed to refine.
        max_attempts: The maximum number of attempts made.

    Returns:
        A formatted error message with instructions.

    """
    _msg = (
        f"Unable to refine '{role.basics.title} @ {role.basics.company}' "
        f"after {max_attempts} attempts. The AI service may be experiencing issues. "
        "Click Start Refinement to resume."
    )
    return _msg


async def _attempt_refine_role(
    chain: object,
    job_analysis_json: str,
    role_json: str,
) -> tuple[bool, RefinedRole | None, Exception | None]:
    """Attempt a single LLM refinement invocation.

    Args:
        chain: The LangChain runnable chain to invoke.
        job_analysis_json: JSON string of the job analysis.
        role_json: JSON string of the role to refine.

    Returns:
        Tuple of (success, result, error).

    Raises:
        AuthenticationError: Re-raises immediately if authentication fails.

    Network access:
        - Makes a network request to the LLM endpoint.

    """
    try:
        response_str = await chain.ainvoke(
            {
                "job_analysis_json": job_analysis_json,
                "role_json": role_json,
            },
        )
        parsed_json = parse_json_markdown(response_str)
        refined_role = RefinedRole.model_validate(parsed_json)
        return True, refined_role, None
    except AuthenticationError:
        raise
    except Exception as e:
        return False, None, e


async def _handle_retry_delay(params: HandleRetryDelayParams) -> None:
    """Handle the delay and logging between retry attempts.

    Args:
        params: Parameters including attempt, role, response, error, etc.

    Notes:
        1. Logs the failed attempt.
        2. Calls progress_callback with retry message if provided.
        3. Releases semaphore if provided.
        4. Sleeps for 3 seconds.
        5. Re-acquires semaphore if provided.

    """
    _log_failed_attempt(
        role=params.role,
        attempt=params.attempt + 1,
        response=params.response_str,
        error=params.error,
        job_analysis=params.job_analysis,
    )

    if params.progress_callback is not None:
        _retry_msg = (
            f"Retrying role refinement for '{params.role.basics.title} @ {params.role.basics.company}' "
            f"(attempt {params.attempt + 2}/3)..."
        )
        await params.progress_callback(_retry_msg)

    if params.semaphore is not None:
        params.semaphore.release()

    await asyncio.sleep(3)

    if params.semaphore is not None:
        await params.semaphore.acquire()


async def _process_refinement_error(params: ProcessRefinementErrorParams) -> bool:
    """Process an error from a refinement attempt.

    Args:
        params: Parameters including error, attempt, role, etc.

    Returns:
        True if should retry, False if max attempts reached.

    Raises:
        Exception: Re-raises if error is not retryable.

    """
    if not _is_retryable_error(params.error):
        raise params.error

    if params.attempt < 2:  # Not the last attempt
        delay_params = HandleRetryDelayParams(
            attempt=params.attempt,
            role=params.role,
            response_str=params.response_str,
            error=params.error,
            job_analysis=params.job_analysis,
            semaphore=params.semaphore,
            progress_callback=params.progress_callback,
        )
        await _handle_retry_delay(delay_params)
        return True
    return False


async def refine_role(
    role: Role,
    job_analysis: JobAnalysis,
    llm_config: LLMConfig,
    semaphore: asyncio.Semaphore | None = None,
    progress_callback: Callable[[str], Awaitable[None]] | None = None,
) -> RefinedRole:
    """Uses an LLM to refine a single resume Role.

    Args:
        role: The structured Role object to refine.
        job_analysis: The structured job analysis to align with.
        llm_config: LLM configuration.
        semaphore: Optional semaphore for retry delays.
        progress_callback: Optional callback for progress updates.

    Returns:
        The refined and validated Role object.

    Raises:
        ValueError: If all retries fail.
        AuthenticationError: If authentication fails.

    Notes:
        1. Sets up PydanticOutputParser for RefinedRole.
        2. Serializes role and job_analysis to JSON.
        3. Creates prompt and initializes LLM client.
        4. Attempts up to 3 times with retry logic.
        5. Preserves original inclusion_status.

    Network access:
        - Makes network requests to the LLM endpoint.

    """
    _msg = "refine_role starting"
    log.debug(_msg)

    parser = PydanticOutputParser(pydantic_object=RefinedRole)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", ROLE_REFINE_SYSTEM_PROMPT),
            ("human", ROLE_REFINE_HUMAN_PROMPT),
        ],
    ).partial(format_instructions=parser.get_format_instructions())

    llm = initialize_llm_client(llm_config)

    from langchain_core.output_parsers import StrOutputParser

    chain = prompt | llm | StrOutputParser()

    role_json = role.model_dump_json(indent=2)
    job_analysis_json = job_analysis.model_dump_json(indent=2)

    last_error: Exception | None = None
    refined_role: RefinedRole | None = None

    for attempt in range(3):
        success, result, error = await _attempt_refine_role(
            chain=chain,
            job_analysis_json=job_analysis_json,
            role_json=role_json,
        )

        if success:
            refined_role = result
            break

        last_error = error
        error_params = ProcessRefinementErrorParams(
            attempt=attempt,
            error=last_error,
            role=role,
            response_str="",  # Populated by _log_failed_attempt if needed
            job_analysis=job_analysis,
            semaphore=semaphore,
            progress_callback=progress_callback,
        )
        should_retry = await _process_refinement_error(error_params)

        if not should_retry:
            break

    if refined_role is None:
        _error_msg = _create_error_context(role, 3)
        raise ValueError(_error_msg) from last_error

    refined_role.basics.inclusion_status = role.basics.inclusion_status

    _msg = "refine_role returning"
    log.debug(_msg)
    return refined_role


def _unwrap_exception_group(e: Exception) -> None:
    """Unwraps an ExceptionGroup if it contains a single non-cancellation error.

    Args:
        e: The exception to inspect.

    Raises:
        The unwrapped exception or the original exception.

    """
    if isinstance(e, ExceptionGroup):
        non_cancel_errors = [
            exc for exc in e.exceptions if not isinstance(exc, asyncio.CancelledError)
        ]
        if len(non_cancel_errors) == 1:
            raise non_cancel_errors[0]
    raise e


async def _refine_role_and_put_on_queue(
    job: RoleRefinementJob,
    semaphore: asyncio.Semaphore,
    event_queue: asyncio.Queue,
) -> None:
    """Refines a single role and puts events onto a queue.

    Args:
        job: The refinement job containing role, job analysis, etc.
        semaphore: The semaphore to control concurrency.
        event_queue: The queue to send events to.

    """
    log.debug(
        "Waiting on semaphore for role refinement for index %d",
        job.original_index,
    )
    async with semaphore:
        role_title = f"{job.role.basics.title} @ {job.role.basics.company}"
        await event_queue.put(
            {
                "status": "in_progress",
                "message": f"Refining role '{role_title}'...",
            },
        )

        log.debug(
            "Semaphore acquired, refining role for index %d",
            job.original_index,
        )

        async def _progress_callback(message: str) -> None:
            await event_queue.put({"status": "in_progress", "message": message})

        refined_role = await refine_role(
            role=job.role,
            job_analysis=job.job_analysis,
            llm_config=job.llm_config,
            semaphore=semaphore,
            progress_callback=_progress_callback,
        )
        await event_queue.put(
            {
                "status": "role_refined",
                "data": refined_role.model_dump(mode="json"),
                "original_index": job.original_index,
            },
        )


def _get_role_title(role: Role, index: int) -> str:
    """Generate a display title for a role.

    Args:
        role: The role object.
        index: The role index as fallback.

    Returns:
        Formatted role title string.

    """
    if role.basics:
        return f"{role.basics.title} @ {role.basics.company}"
    return f"Role {index}"


def _build_roles_to_refine(
    experience_info: ExperienceResponse,
    skip_indices: set[int],
) -> list[tuple[int, Role]]:
    """Build list of roles that need refinement.

    Args:
        experience_info: Parsed experience section.
        skip_indices: Indices to skip.

    Returns:
        List of (index, role) tuples to refine.

    """
    return [
        (i, role)
        for i, role in enumerate(experience_info.roles)
        if i not in skip_indices
    ]


async def _analyze_job_if_needed(
    params: RefinementOrchestratorParams,
) -> JobAnalysis:
    """Analyze job description if not already provided.

    Args:
        params: The refinement parameters.

    Returns:
        JobAnalysis object.

    """
    if params.state and params.state.job_analysis is not None:
        return params.state.job_analysis

    from resume_editor.app.llm.orchestration_analysis import analyze_job_description

    job_analysis, _ = await analyze_job_description(
        job_description=params.job_description,
        llm_config=params.llm_config,
        resume_content_for_context=params.resume_content,
    )
    return job_analysis


async def _process_events_from_queue(
    event_queue: asyncio.Queue,
    num_roles_to_refine: int,
) -> AsyncGenerator[dict, None]:
    """Process events from the queue until all roles are refined.

    Args:
        event_queue: The queue to read events from.
        num_roles_to_refine: Number of roles to wait for.

    Yields:
        Status events and refined role data.

    """
    processed_count = 0
    while processed_count < num_roles_to_refine:
        event = await event_queue.get()
        if event.get("status") == "role_refined":
            processed_count += 1
        yield event
        event_queue.task_done()


async def _run_refinement_tasks(
    params: RefinementOrchestratorParams,
    job_analysis: JobAnalysis,
    roles_to_refine: list[tuple[int, Role]],
) -> AsyncGenerator[dict, None]:
    """Run the refinement tasks concurrently.

    Args:
        params: The refinement parameters.
        job_analysis: The job analysis to use.
        roles_to_refine: List of (index, role) tuples to refine.

    Yields:
        Status events and refined role data.

    """
    event_queue: asyncio.Queue = asyncio.Queue()
    semaphore = asyncio.Semaphore(params.max_concurrency)
    num_roles_to_refine = len(roles_to_refine)

    try:
        async with asyncio.TaskGroup() as tg:
            for index, role in roles_to_refine:
                job = RoleRefinementJob(
                    role=role,
                    job_analysis=job_analysis,
                    llm_config=params.llm_config,
                    original_index=index,
                )
                tg.create_task(
                    _refine_role_and_put_on_queue(
                        job=job,
                        semaphore=semaphore,
                        event_queue=event_queue,
                    ),
                )

            async for event in _process_events_from_queue(
                event_queue, num_roles_to_refine
            ):
                yield event
    except Exception as e:
        log.exception("Error during role refinement task group.")
        _unwrap_exception_group(e)


async def _yield_skipped_roles(
    experience_info: ExperienceResponse,
    skip_indices: set[int],
) -> AsyncGenerator[dict, None]:
    """Yield progress messages for skipped roles.

    Args:
        experience_info: Parsed experience section.
        skip_indices: Indices to skip.

    Yields:
        Status events for skipped roles.

    """
    for index, role in enumerate(experience_info.roles):
        if index in skip_indices:
            role_title = _get_role_title(role, index)
            yield {
                "status": "in_progress",
                "message": f"Skipping role '{role_title}' (already refined)",
            }


async def async_refine_experience_section(
    resume_content: str,
    job_description: str,
    llm_config: LLMConfig,
    max_concurrency: int = 5,
    state: RefinementState | None = None,
) -> AsyncGenerator[dict, None]:
    """Orchestrates concurrent refinement of the experience section.

    Args:
        resume_content: The full Markdown content of the resume.
        job_description: The job description to align with.
        llm_config: LLM configuration.
        max_concurrency: Maximum roles to refine in parallel.
        state: Optional refinement state containing job_analysis and skip_indices.

    Yields:
        Status updates and refined role data.

    """
    _msg = "async_refine_experience_section starting"
    log.debug(_msg)

    state = state or RefinementState()

    params = RefinementOrchestratorParams(
        resume_content=resume_content,
        job_description=job_description,
        llm_config=llm_config,
        max_concurrency=max_concurrency,
        state=state,
    )

    skip_indices = params.state.skip_indices or set()

    yield {"status": "in_progress", "message": "Parsing resume..."}
    experience_info = extract_experience_info(resume_content)

    if params.state.job_analysis is None:
        yield {"status": "in_progress", "message": "Analyzing job description..."}

    job_analysis = await _analyze_job_if_needed(params)

    yield {
        "status": "job_analysis_complete",
        "message": "Job analysis complete.",
        "job_analysis": job_analysis.model_dump(mode="json"),
    }

    roles_to_refine = _build_roles_to_refine(experience_info, skip_indices)

    async for event in _yield_skipped_roles(experience_info, skip_indices):
        yield event

    if not roles_to_refine:
        _msg = "No roles to refine after filtering"
        log.debug(_msg)
        return

    async for event in _run_refinement_tasks(params, job_analysis, roles_to_refine):
        yield event

    _msg = "async_refine_experience_section finishing"
    log.debug(_msg)
