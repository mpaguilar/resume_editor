import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Annotated, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session

from resume_editor.app.api.dependencies import get_resume_for_user
from resume_editor.app.api.routes.route_logic.resume_ai_logic import (
    create_sse_close_message,
    create_sse_error_message,
    experience_refinement_sse_generator,
    handle_save_as_new_refinement,
    handle_sync_refinement,
)
from resume_editor.app.api.routes.route_logic.resume_filtering import (
    filter_experience_by_date,
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
from resume_editor.app.api.routes.route_models import (
    ExperienceRefinementParams,
    RefineForm,
    RefineTargetSection,
    SaveAsNewForm,
    SaveAsNewParams,
    SyncRefinementParams,
)
from resume_editor.app.core.auth import get_current_user_from_cookie
from resume_editor.app.database.database import get_db
from resume_editor.app.models.resume_model import Resume as DatabaseResume
from resume_editor.app.models.user import User

log = logging.getLogger(__name__)


@dataclass
class _ExperienceStreamParams:
    """Aggregated parameters for the experience SSE stream helper.

    Purpose:
        Groups arguments commonly passed to the private SSE stream helper into a single object
        to reduce parameter count and improve readability. No side effects and no I/O.

    Attributes:
        resume (DatabaseResume): The resume being refined.
        parsed_limit_years (int | None): Parsed positive years limit or None.
        db (Session): SQLAlchemy session.
        current_user (User): Authenticated user.
        job_description (str): Job description text for alignment.
        limit_refinement_years (str | None): Original string form of the years limit for metadata.

    """

    resume: DatabaseResume
    parsed_limit_years: int | None
    db: Session
    current_user: User
    job_description: str
    limit_refinement_years: str | None


router = APIRouter()

templates = Jinja2Templates(directory="resume_editor/app/templates")


class RefineStreamQueryParams(BaseModel):
    """Query parameters for GET /{resume_id}/refine/stream.

    Args:
        job_description (str): The job description to align the resume with.
        limit_refinement_years (str | None): Optional year limit for experience filtering as a string.

    Notes:
        1. Acts as a container for query parameters to keep route signatures small.
        2. No network, disk, or database access is performed.

    """

    job_description: str
    limit_refinement_years: str | None = None


def get_refine_stream_query(
    job_description: Annotated[str, Query(...)],
    limit_refinement_years: Annotated[str | None, Query()] = None,
) -> RefineStreamQueryParams:
    """Dependency to collect and validate refine/stream query parameters.

    Args:
        job_description (str): The job description to align the resume with.
        limit_refinement_years (str | None): Year limit for filtering experience, if provided.

    Returns:
        RefineStreamQueryParams: Aggregated query parameters object.

    Notes:
        1. Performs only basic typing via FastAPI's Query parameters.
        2. No disk, network, or database access is performed.

    """
    _msg = "get_refine_stream_query starting"
    log.debug(_msg)

    params = RefineStreamQueryParams(
        job_description=job_description,
        limit_refinement_years=limit_refinement_years,
    )

    _msg = "get_refine_stream_query returning"
    log.debug(_msg)
    return params


def _make_early_error_stream_response(message: str) -> StreamingResponse:
    """Create a short SSE stream response that sends an error and closes.

    Args:
        message (str): The error message to send.

    Returns:
        StreamingResponse: A streaming response that emits an error and close event.

    Notes:
        1. Builds a minimal async generator to emit two SSE events.
        2. No disk, network, or database access is performed.

    """
    _msg = "make_early_error_stream_response starting"
    log.debug(_msg)

    async def _early_error_stream() -> AsyncGenerator[str, None]:
        yield create_sse_error_message(message)
        yield create_sse_close_message()

    result = StreamingResponse(
        _early_error_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
    _msg = "make_early_error_stream_response returning"
    log.debug(_msg)
    return result


def _parse_limit_years_for_stream(
    limit_refinement_years: str | None,
) -> tuple[int | None, StreamingResponse | None]:
    """Parse and validate the limit_refinement_years value for streaming endpoints.

    Args:
        limit_refinement_years (str | None): The user-supplied string for years.

    Returns:
        tuple[int | None, StreamingResponse | None]: The parsed positive integer years (or None),
            and an optional early StreamingResponse if validation fails.

    Notes:
        1. Accepts None and returns (None, None) to indicate no limit.
        2. Returns an early error StreamingResponse when invalid, to be returned directly by the route.

    """
    _msg = "parse_limit_years_for_stream starting"
    log.debug(_msg)

    if limit_refinement_years is None:
        _msg = "parse_limit_years_for_stream returning"
        log.debug(_msg)
        return None, None

    try:
        years = int(limit_refinement_years)
    except ValueError:
        result = _make_early_error_stream_response(
            "Limit refinement years must be a valid number.",
        )
        _msg = "parse_limit_years_for_stream returning"
        log.debug(_msg)
        return None, result

    if years <= 0:
        result = _make_early_error_stream_response(
            "Limit refinement years must be a positive number.",
        )
        _msg = "parse_limit_years_for_stream returning"
        log.debug(_msg)
        return None, result

    _msg = "parse_limit_years_for_stream returning"
    log.debug(_msg)
    return years, None


def _build_filtered_content_if_needed(
    resume_content: str,
    limit_years: int | None,
) -> str:
    """Optionally filter experience by a date window and rebuild resume content.

    Args:
        resume_content (str): The original full resume content.
        limit_years (int | None): The positive number of years to include, or None.

    Returns:
        str: The content to refine (filtered if a limit was supplied).

    Notes:
        1. If limit_years is None, returns the original content unchanged.
        2. Otherwise:
            a. Computes a start_date of (today - limit_years years).
            b. Extracts all sections from the original content.
            c. Filters experience by date range.
            d. Rebuilds a complete resume from the sections.
        3. This function may raise exceptions from extract/serialize helpers.

    """
    _msg = "build_filtered_content_if_needed starting"
    log.debug(_msg)

    if not limit_years:
        _msg = "build_filtered_content_if_needed returning"
        log.debug(_msg)
        return resume_content

    start_date = datetime.now(timezone.utc).date() - timedelta(
        days=int(limit_years * 365.25),
    )

    personal_info = extract_personal_info(resume_content)
    education_info = extract_education_info(resume_content)
    experience_info = extract_experience_info(resume_content)
    certifications_info = extract_certifications_info(resume_content)

    filtered_experience = filter_experience_by_date(
        experience=experience_info,
        start_date=start_date,
        end_date=None,
    )

    result = build_complete_resume_from_sections(
        personal_info=personal_info,
        education=education_info,
        experience=filtered_experience,
        certifications=certifications_info,
    )
    _msg = "build_filtered_content_if_needed returning"
    log.debug(_msg)
    return result


async def _experience_refinement_stream(
    params: _ExperienceStreamParams,
) -> AsyncGenerator[str, None]:
    """Core SSE generator for experience refinement, handling filtering and error reporting.

    Args:
        params (_ExperienceStreamParams): Aggregated parameters for the SSE refinement stream.

    Yields:
        str: Server-Sent Events for progress, data, or errors.

    Notes:
        1. Calls `_build_filtered_content_if_needed` to get content to refine.
        2. Handles exceptions during filtering and sends an SSE error.
        3. Validates that roles exist to refine after filtering, sending an SSE warning if not.
        4. Invokes `experience_refinement_sse_generator` with prepared parameters.

    """
    _msg = "Starting SSE stream for experience refinement"
    log.debug(_msg)
    try:
        content_to_refine = _build_filtered_content_if_needed(
            resume_content=params.resume.content,
            limit_years=params.parsed_limit_years,
        )
    except Exception as e:
        _msg = f"Error during experience filtering: {e!s}"
        log.exception(_msg)
        yield create_sse_error_message(
            "An error occurred while filtering experience.",
        )
        yield create_sse_close_message()
        return

    experience = extract_experience_info(content_to_refine)
    if not experience.roles:
        yield create_sse_error_message(
            "No roles available to refine within the specified date range.",
            is_warning=True,
        )
        yield create_sse_close_message()
        return

    exp_params = ExperienceRefinementParams(
        db=params.db,
        user=params.current_user,
        resume=params.resume,
        resume_content_to_refine=content_to_refine,
        original_resume_content=params.resume.content,
        job_description=params.job_description,
        limit_refinement_years=params.limit_refinement_years,
    )
    generator = experience_refinement_sse_generator(params=exp_params)
    async for item in generator:
        yield item


async def _extract_original_limit_str_from_post(
    http_request: Request,
    form_data: RefineForm,
) -> str | None:
    """Extract the original limit_refinement_years string value from POST data, preserving raw input if DI coerces it.

    Args:
        http_request (Request): The incoming request to read the raw form from when needed.
        form_data (RefineForm): The dependency-injected form data.

    Returns:
        str | None: The original string for limit_refinement_years if present; otherwise None.

    Notes:
        1. Reads http_request.form() only when form_data.limit_refinement_years is None.
        2. If the raw form read fails, returns None.
        3. Trims whitespace; empty strings are treated as absent (None).

    """
    _msg = "extract_original_limit_str_from_post starting"
    log.debug(_msg)

    original_limit_str = form_data.limit_refinement_years
    if original_limit_str is None:
        try:
            form = await http_request.form()
        except Exception as _e:
            # If we cannot read the raw form, continue with None
            form = None
        else:
            raw_value = None if form is None else form.get("limit_refinement_years")
            if raw_value is not None:
                raw_str = str(raw_value).strip()
                if raw_str != "":
                    original_limit_str = raw_str

    _msg = "extract_original_limit_str_from_post returning"
    log.debug(_msg)
    return original_limit_str


def _validate_and_parse_limit_for_post(
    original_limit_str: str | None,
) -> tuple[int | None, StreamingResponse | None]:
    """Validate and parse the limit years for POST refine stream.

    Args:
        original_limit_str (str | None): The original user-supplied string, possibly None.

    Returns:
        tuple[int | None, StreamingResponse | None]: Parsed integer years (or None) and
            an optional early StreamingResponse when numeric validation fails.

    Notes:
        1. Non-numeric values are treated as None (no limit, no early error).
        2. Numeric values are validated via _parse_limit_years_for_stream.

    """
    _msg = "validate_and_parse_limit_for_post starting"
    log.debug(_msg)

    if original_limit_str is None:
        _msg = "validate_and_parse_limit_for_post returning"
        log.debug(_msg)
        return None, None

    try:
        int(original_limit_str)
    except ValueError:
        # Keep non-numeric as None with no early error
        _msg = "validate_and_parse_limit_for_post returning"
        log.debug(_msg)
        return None, None

    parsed_limit_years, early_error_response = _parse_limit_years_for_stream(
        original_limit_str,
    )

    _msg = "validate_and_parse_limit_for_post returning"
    log.debug(_msg)
    return parsed_limit_years, early_error_response


@router.get("/{resume_id}/refine/stream", response_class=StreamingResponse)
async def refine_resume_stream_get(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_from_cookie)],
    resume: Annotated[DatabaseResume, Depends(get_resume_for_user)],
    query: Annotated[RefineStreamQueryParams, Depends(get_refine_stream_query)],
) -> StreamingResponse:
    """Refine the experience section of a resume using an LLM stream via GET."""

    # Early validation of limit_refinement_years with immediate SSE error response on failure
    parsed_limit_years, early_error_response = _parse_limit_years_for_stream(
        query.limit_refinement_years,
    )
    if early_error_response is not None:
        return early_error_response

    return StreamingResponse(
        _experience_refinement_stream(
            params=_ExperienceStreamParams(
                resume=resume,
                parsed_limit_years=parsed_limit_years,
                db=db,
                current_user=current_user,
                job_description=query.job_description,
                limit_refinement_years=query.limit_refinement_years,
            ),
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{resume_id}/refine/stream", response_class=StreamingResponse)
async def refine_resume_stream(
    http_request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_from_cookie)],
    resume: Annotated[DatabaseResume, Depends(get_resume_for_user)],
    form_data: Annotated[RefineForm, Depends()],
) -> StreamingResponse:
    """Refine the experience section of a resume using an LLM stream.

    This endpoint uses Server-Sent Events (SSE) to provide real-time feedback.
    It performs early validation of query parameters and optionally filters
    the experience section by a date window before invoking the SSE generator.

    """
    _msg = "refine_resume_stream starting"
    log.debug(_msg)

    # If HTMX posts directly to this endpoint, return the loader fragment so the browser opens a GET EventSource.
    if "HX-Request" in http_request.headers:
        result = templates.TemplateResponse(
            http_request,
            "partials/resume/_refine_sse_loader.html",
            {
                "resume_id": resume.id,
                "job_description": form_data.job_description,
                "limit_refinement_years": form_data.limit_refinement_years,
            },
        )
        _msg = "refine_resume_stream returning"
        log.debug(_msg)
        return result

    # Obtain the original limit string, preserving user input when DI coerces unexpected values to None.
    original_limit_str = await _extract_original_limit_str_from_post(
        http_request=http_request,
        form_data=form_data,
    )

    # POST-specific parsing: treat non-numeric as None; numeric <= 0 yields early error.
    parsed_limit_years, early_error_response = _validate_and_parse_limit_for_post(
        original_limit_str=original_limit_str,
    )
    if early_error_response is not None:
        _msg = "refine_resume_stream returning"
        log.debug(_msg)
        return early_error_response

    result = StreamingResponse(
        _experience_refinement_stream(
            params=_ExperienceStreamParams(
                resume=resume,
                parsed_limit_years=parsed_limit_years,
                db=db,
                current_user=current_user,
                job_description=form_data.job_description,
                limit_refinement_years=original_limit_str,
            ),
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
    _msg = "refine_resume_stream returning"
    log.debug(_msg)
    return result


@router.post("/{resume_id}/refine")
async def refine_resume(
    http_request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_from_cookie)],
    resume: Annotated[DatabaseResume, Depends(get_resume_for_user)],
    form_data: Annotated[RefineForm, Depends()],
) -> Response:
    """Refine a resume section using an LLM to align with a job description.

    This endpoint handles both JSON API calls and HTMX form submissions.

    Args:
        http_request (Request): The HTTP request object to check for HTMX headers.
        db (Session): The database session dependency.
        current_user (User): The current authenticated user.
        resume (DatabaseResume): The resume to be refined.
        form_data (RefineForm): The form data for the refinement request.

    Returns:
        RefineResponse | HTMLResponse: The response type
            depends on the request headers.

    """
    _msg = f"Refining resume {resume.id} for section {form_data.target_section.value}"
    log.debug(_msg)

    if form_data.target_section == RefineTargetSection.EXPERIENCE:
        return templates.TemplateResponse(
            http_request,
            "partials/resume/_refine_sse_loader.html",
            {
                "resume_id": resume.id,
                "job_description": form_data.job_description,
                "limit_refinement_years": form_data.limit_refinement_years,
            },
        )

    params = SyncRefinementParams(
        request=http_request,
        db=db,
        user=current_user,
        resume=resume,
        job_description=form_data.job_description,
        target_section=form_data.target_section,
        limit_refinement_years=form_data.limit_refinement_years,
    )
    return await handle_sync_refinement(sync_params=params)


@router.post("/{resume_id}/refine/save_as_new")
async def save_refined_resume_as_new(
    resume: Annotated[DatabaseResume, Depends(get_resume_for_user)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_from_cookie)],
    form_data: Annotated[SaveAsNewForm, Depends()],
) -> Response:
    """Save a refined resume as a new resume.

    Args:
        resume (DatabaseResume): The original resume being modified.
        db (Session): The database session.
        current_user (User): The current authenticated user.
        form_data (SaveAsNewForm): The form data for saving as new.

    Returns:
        Response: A response with an `HX-Redirect` header to the new resume's view page.

    """
    if not form_data.new_resume_name:
        raise HTTPException(
            status_code=400,
            detail="New resume name is required for 'save as new' action.",
        )

    params = SaveAsNewParams(
        db=db,
        user=current_user,
        resume=resume,
        form_data=form_data,
    )
    new_resume = handle_save_as_new_refinement(params)

    return Response(headers={"HX-Redirect": f"/resumes/{new_resume.id}/view"})


@router.post("/{resume_id}/refine/discard")
async def discard_refined_resume(
    resume: Annotated[DatabaseResume, Depends(get_resume_for_user)],
) -> Response:
    """Discards a refinement and redirects to the resume editor.

    This is used when a user rejects an AI suggestion and is redirected
    to the editor page for the original resume. A 303 See Other is used
    to indicate that the client should make a GET request to the new URL.
    """
    return RedirectResponse(url=f"/resumes/{resume.id}/edit", status_code=303)
