import logging
from dataclasses import dataclass
from typing import Annotated

import pendulum
from fastapi import APIRouter, Depends, Form, Query, Request, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

# Import database dependencies
from resume_editor.app.api.dependencies import get_resume_for_user
from resume_editor.app.api.routes.html_fragments import (
    GenerateResumeListHtmlParams,
    _generate_resume_detail_html,
    _generate_resume_list_html,
)

# Import route logic modules
from resume_editor.app.api.routes.route_logic.resume_crud import (
    DateRange,
    ResumeCreateParams,
    ResumeUpdateParams,
    get_oldest_resume_date,
    get_user_resumes,
    get_user_resumes_with_pagination,
)
from resume_editor.app.api.routes.route_logic.resume_crud import (
    create_resume as create_resume_db,
)
from resume_editor.app.api.routes.route_logic.resume_crud import (
    delete_resume as delete_resume_db,
)
from resume_editor.app.api.routes.route_logic.resume_crud import (
    update_resume as update_resume_db,
)
from resume_editor.app.api.routes.route_logic.resume_parsing import (
    parse_resume_content,
    validate_resume_content,
)
from resume_editor.app.api.routes.route_models import (
    ParseRequest,
    ParseResponse,
    ResumeCreateRequest,
    ResumeDetailResponse,
    ResumeResponse,
    ResumeSortBy,
)
from resume_editor.app.core.auth import get_current_user_from_cookie
from resume_editor.app.database.database import get_db
from resume_editor.app.models.resume_model import Resume as DatabaseResume
from resume_editor.app.models.user import User

from . import resume_ai, resume_edit, resume_export

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resumes", tags=["resumes"])

router.include_router(resume_export.router)
router.include_router(resume_ai.router)
router.include_router(resume_edit.router)


@dataclass
class ListResumesParams:
    """Parameters for the list_resumes function.

    Attributes:
        http_request: The HTTP request object.
        db: The database session.
        current_user: The current authenticated user.
        week_offset: Number of weeks to offset from current week.
        filter_query: Optional search query to filter by name/notes.
        sort_by: Optional sorting criterion.
        selected_id: Optional ID of the currently selected resume.

    """

    http_request: Request
    db: Session
    current_user: User
    week_offset: int
    filter_query: str | None
    sort_by: ResumeSortBy | None
    selected_id: int | None


@dataclass
class ResumeLists:
    """Container for base and refined resume lists."""

    base: list
    refined: list


@dataclass
class ListQueryParams:
    """Query parameters for list_resumes function.

    Attributes:
        week_offset: Number of weeks to offset from current week.
        filter_query: Optional search query to filter by name/notes.
        sort_by: Optional sorting criterion.
        selected_id: Optional ID of the currently selected resume.

    """

    week_offset: int | str = 0
    filter_query: Annotated[str | None, Query(alias="filter")] = None
    sort_by: ResumeSortBy | None = None
    selected_id: int | None = None


def _validate_week_offset(week_offset: int | str) -> int:
    """Validate and sanitize the week_offset parameter.

    Args:
        week_offset: The week offset value to validate.

    Returns:
        int: The validated and clamped week offset value.

    Notes:
        1. Converts string to int if necessary.
        2. Defaults to 0 on conversion error.
        3. Clamps to range -52 to 0.

    """
    try:
        validated = int(week_offset)
    except (ValueError, TypeError):
        _msg = "_validate_week_offset invalid week_offset, defaulting to 0"
        log.debug(_msg)
        validated = 0

    if validated < -52:
        validated = -52
    elif validated > 0:
        validated = 0

    return validated


def _calculate_pagination_boundaries(
    db: Session,
    user_id: int,
    week_offset: int,
    date_range: DateRange,
) -> tuple[bool, bool]:
    """Calculate pagination boundaries for resume listing.

    Args:
        db: The database session.
        user_id: The current user's ID.
        week_offset: The current week offset.
        date_range: The date range for the current view.

    Returns:
        tuple[bool, bool]: (has_older_resumes, has_newer_resumes) flags.

    Notes:
        1. Queries for the oldest resume date to determine pagination.
        2. Uses pendulum for date calculations.
        3. Performs database access to get oldest resume date.

    """
    oldest_date = get_oldest_resume_date(db, user_id)
    has_older_resumes = False

    if oldest_date and week_offset < 0:
        oldest_week_offset = -1
        max_iterations = 0
        max_weeks = 520
        oldest_date_naive = (
            oldest_date.replace(tzinfo=None) if oldest_date.tzinfo else oldest_date
        )
        while max_iterations < max_weeks:
            check_range = pendulum.now().add(weeks=oldest_week_offset + 1)
            if check_range.naive() < oldest_date_naive:
                break
            oldest_week_offset -= 1
            max_iterations += 1
        has_older_resumes = week_offset > oldest_week_offset
    elif oldest_date and week_offset == 0:
        has_older_resumes = oldest_date < date_range.start_date

    has_newer_resumes = week_offset < 0

    return has_older_resumes, has_newer_resumes


def _build_html_response(
    params: ListResumesParams,
    resume_lists: ResumeLists,
    has_older_resumes: bool,
    has_newer_resumes: bool,
    date_range: DateRange,
) -> HTMLResponse:
    """Build HTML response for HTMX requests.

    Args:
        params: The list resumes parameters.
        resume_lists: Container with base and refined resume lists.
        has_older_resumes: Whether there are older resumes.
        has_newer_resumes: Whether there are newer resumes.
        date_range: The date range for the current view.

    Returns:
        HTMLResponse: The HTML response containing the resume list.

    Notes:
        1. Generates resume list HTML using _generate_resume_list_html.
        2. Includes pagination and filter state.

    """
    _msg = "_build_html_response generating HTML for HTMX request"
    log.debug(_msg)

    sort_by_str = params.sort_by.value if params.sort_by else None
    html_content = _generate_resume_list_html(
        GenerateResumeListHtmlParams(
            base_resumes=resume_lists.base,
            refined_resumes=resume_lists.refined,
            selected_resume_id=params.selected_id,
            sort_by=sort_by_str,
            week_offset=params.week_offset,
            has_older_resumes=has_older_resumes,
            has_newer_resumes=has_newer_resumes,
            current_filter=params.filter_query,
            week_start=date_range.start_date,
            week_end=date_range.end_date,
            wrap_in_div=True,
        )
    )
    return HTMLResponse(content=html_content)


def _build_json_response(resumes: list) -> list[ResumeResponse]:
    """Build JSON response for API requests.

    Args:
        resumes: List of resume objects.

    Returns:
        list[ResumeResponse]: List of resume response objects.

    Notes:
        1. Converts resume objects to ResumeResponse objects.

    """
    _msg = "_build_json_response returning JSON for API request"
    log.debug(_msg)

    return [
        ResumeResponse(
            id=r.id,
            name=r.name,
        )
        for r in resumes
    ]


@router.post("/parse")
async def parse_resume_endpoint(request: ParseRequest) -> ParseResponse:
    """Parse Markdown resume content and return structured data.

    Args:
        request (ParseRequest): The request containing the Markdown content to parse.

    Returns:
        ParseResponse: A response containing the structured resume data as a dictionary.

    Raises:
        HTTPException: If the resume_writer module is not available or parsing fails.

    Notes:
        1. Checks if the resume_writer module is available.
        2. If not available, raises a 501 error.
        3. Attempts to parse the Markdown content using the resume_writer's parse_resume function.
        4. Converts the parsed resume object to a dictionary using model_dump.
        5. Returns a ParseResponse with the structured data.
        6. If an error occurs during parsing, logs the exception and raises a 400 error.
        7. Performs database access: None.
        8. Performs network access: None.

    """
    return ParseResponse(resume_data=parse_resume_content(request.markdown_content))


@router.post("", response_model=ResumeResponse)
async def create_resume(
    http_request: Request,
    request: ResumeCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_from_cookie)],
) -> Response:
    """Save a new resume to the database via API, associating it with the current user.

    This endpoint handles both standard JSON API calls and HTMX form submissions that
    trigger a page redirect.

    Args:
        http_request (Request): The HTTP request object.
        request (ResumeCreateRequest): The request containing the resume name and content.
        db (Session): The database session dependency.
        current_user (User): The current authenticated user.

    Returns:
        ResumeResponse | HTMLResponse: For HTMX requests, returns an empty response with
                                       an `HX-Redirect` header. For standard API
                                       calls, returns the created resume's data.

    Raises:
        HTTPException: If there's an error saving the resume to the database or if Markdown validation fails.

    Notes:
        1. Validates the Markdown content using the resume parser.
        2. Creates a new DatabaseResume instance with the provided name and content.
        3. Associates the resume with the current user.
        4. Saves the new resume to the database.
        5. If the request is from HTMX, returns an HTMLResponse with a `HX-Redirect`
           header pointing to the new resume's edit page.
        6. Otherwise, returns a JSON response with the new resume's data.

    """
    # Validate Markdown content before saving
    validate_resume_content(request.content)

    resume_params = ResumeCreateParams(
        user_id=current_user.id,
        name=request.name,
        content=request.content,
    )
    resume = create_resume_db(db=db, params=resume_params)

    if "HX-Request" in http_request.headers:
        return HTMLResponse(headers={"HX-Redirect": f"/resumes/{resume.id}/edit"})

    return ResumeResponse(id=resume.id, name=resume.name)


class UpdateResumeForm:
    """Represents the form data for updating a resume."""

    def __init__(
        self,
        name: str = Form(...),
        content: str | None = Form(None),
        from_editor: str | None = Form(None),
        sort_by: ResumeSortBy | None = Form(None),
    ):
        """Initializes the form data.

        Args:
            name (str): The new name for the resume.
            content (str | None): The new content for the resume.
            from_editor (str | None): Flag indicating if the update is from the editor.
            sort_by (ResumeSortBy | None): The sorting criteria.

        """
        self.name = name
        self.content = content
        self.from_editor = from_editor
        self.sort_by = sort_by


@router.put("/{resume_id}", response_model=ResumeResponse)
async def update_resume_details(
    http_request: Request,
    db: Annotated[Session, Depends(get_db)],
    resume: Annotated[DatabaseResume, Depends(get_resume_for_user)],
    form_data: Annotated[UpdateResumeForm, Depends()],
) -> Response:
    """Update an existing resume's name and/or content for the current user.

    This endpoint handles both JSON API calls and HTMX form submissions.

    Args:
        http_request (Request): The HTTP request object.
        db (Session): The database session dependency.
        resume (DatabaseResume): The resume object to update, from dependency.
        form_data (UpdateResumeForm): The resume form data.


    Returns:
        Response | ResumeResponse: For HTMX requests from the editor, returns a response with
                                   an `HX-Redirect` header. For other HTMX requests, returns
                                   an `HTMLResponse`. For standard API calls, returns `ResumeResponse`.

    Raises:
        HTTPException: If validation fails or an error occurs during the update.

    Notes:
        1. Validates resume content if it is being updated.
        2. Updates the resume's name and/or content.
        3. For HTMX requests from the editor page, returns an `HX-Redirect` to the dashboard.
        4. For other HTMX requests, returns an HTML response containing both the updated resume
           list (for OOB swap) and the updated detail view.
        5. For regular API calls, returns a JSON response with the updated resume's ID and name.
        6. Performs database reads and writes.

    """
    # Validate Markdown content only if it's a non-empty string
    if form_data.content:
        validate_resume_content(form_data.content)

    # If content is an empty string, treat it as None to prevent wiping content.
    content_to_update = form_data.content if form_data.content else None
    update_params = ResumeUpdateParams(
        name=form_data.name,
        content=content_to_update,
    )
    updated_resume = update_resume_db(
        db=db,
        resume=resume,
        params=update_params,
    )

    if "HX-Request" in http_request.headers:
        if form_data.from_editor:
            # When saving from the editor, redirect back to the dashboard.
            return Response(headers={"HX-Redirect": "/dashboard"})

        # After an update, we need to regenerate both the list and the detail view
        sort_by_val = form_data.sort_by.value if form_data.sort_by else None
        all_resumes = get_user_resumes(
            db=db,
            user_id=resume.user_id,
            sort_by=sort_by_val,
        )
        base_resumes = [r for r in all_resumes if r.is_base]
        refined_resumes = [r for r in all_resumes if not r.is_base]
        list_html = _generate_resume_list_html(
            GenerateResumeListHtmlParams(
                base_resumes=base_resumes,
                refined_resumes=refined_resumes,
                selected_resume_id=updated_resume.id,
                sort_by=sort_by_val,
                wrap_in_div=False,
            )
        )
        detail_html = _generate_resume_detail_html(resume=updated_resume)

        # Use Out-of-Band swap to update both parts of the page
        html_content = f"""<div id="resume-list" hx-swap-oob="true">{list_html}</div>
<div id="resume-detail">{detail_html}</div>"""
        return HTMLResponse(content=html_content)

    return ResumeResponse(id=updated_resume.id, name=updated_resume.name)


@router.delete("/{resume_id}")
async def delete_resume(
    http_request: Request,
    db: Annotated[Session, Depends(get_db)],
    resume: Annotated[DatabaseResume, Depends(get_resume_for_user)],
) -> Response:
    """Delete a resume for the current user.

    The `get_resume_for_user` dependency handles fetching the resume and ensuring
    it belongs to the authenticated user.

    Args:
        http_request (Request): The HTTP request object.
        db (Session): The database session dependency.
        resume (DatabaseResume): The resume to delete, injected via dependency.

    Returns:
        dict | Response: A success message, or an empty response with HX-Redirect header for HTMX.

    Raises:
        HTTPException: If the resume is not found, doesn't belong to the user, or there's an error deleting.

    Notes:
        1. The `get_resume_for_user` dependency validates that the resume exists and belongs to the current user.
        2. Deletes the resume from the database using `delete_resume_db`.
        3. If the request is from HTMX, returns a response with an `HX-Redirect` header to redirect the user to the dashboard.
        4. Otherwise, returns a JSON success message.
        5. Performs database access: Reads via `get_resume_for_user` dependency and writes via `delete_resume_db`.
        6. Performs network access: None.

    """
    # Delete the resume
    delete_resume_db(db, resume)

    # Check if this is an HTMX request
    if "HX-Request" in http_request.headers:
        # For HTMX requests, redirect to the dashboard. This is more robust
        # than a refresh, as it avoids a 404 if the user is on the deleted
        # resume's edit page.
        return Response(status_code=200, headers={"HX-Redirect": "/dashboard"})

    return {"message": "Resume deleted successfully"}


@router.get("", response_model=list[ResumeResponse])
async def list_resumes(
    http_request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_from_cookie)],
    query_params: Annotated[ListQueryParams, Depends()],
) -> Response | list[ResumeResponse]:
    """List resumes for the current user with optional pagination and filtering.

    Args:
        http_request: The HTTP request object.
        db: The database session dependency.
        current_user: The current authenticated user.
        query_params: Query parameters including week_offset, filter_query,
            sort_by, and selected_id.

    Returns:
        Response: HTML response for HTMX requests, JSON for API requests.

    Notes:
        1. Validates week_offset is an integer (defaults to 0 if invalid).
        2. Gets date range based on week_offset using pendulum.
        3. Retrieves base resumes (always shown) and refined resumes (date-filtered).
        4. If filter is provided, refined resumes are additionally filtered
           by name/notes (case-insensitive, partial match, AND logic).
        5. Determines pagination boundaries based on oldest resume date.
        6. Returns HTML fragment for HTMX requests, JSON for API requests.
        7. Performs database queries to retrieve resumes and determine boundaries.

    """
    _msg = "list_resumes starting for user_id=%s week_offset=%s filter=%s"
    log.debug(
        _msg, current_user.id, query_params.week_offset, query_params.filter_query
    )

    validated_offset = _validate_week_offset(query_params.week_offset)

    if query_params.filter_query:
        query_params.filter_query = query_params.filter_query[:100]

    sort_by_str = query_params.sort_by.value if query_params.sort_by else None
    resumes, date_range = get_user_resumes_with_pagination(
        db=db,
        user_id=current_user.id,
        week_offset=validated_offset,
        search_query=query_params.filter_query,
        sort_by=sort_by_str,
    )

    base_resumes = [r for r in resumes if r.is_base]
    refined_resumes = [r for r in resumes if not r.is_base]

    has_older_resumes, has_newer_resumes = _calculate_pagination_boundaries(
        db=db,
        user_id=current_user.id,
        week_offset=validated_offset,
        date_range=date_range,
    )

    if "HX-Request" in http_request.headers:
        params = ListResumesParams(
            http_request=http_request,
            db=db,
            current_user=current_user,
            week_offset=validated_offset,
            filter_query=query_params.filter_query,
            sort_by=query_params.sort_by,
            selected_id=query_params.selected_id,
        )
        resume_lists = ResumeLists(base=base_resumes, refined=refined_resumes)
        return _build_html_response(
            params=params,
            resume_lists=resume_lists,
            has_older_resumes=has_older_resumes,
            has_newer_resumes=has_newer_resumes,
            date_range=date_range,
        )

    return _build_json_response(resumes)


@router.get("/{resume_id}", response_model=ResumeDetailResponse)
async def get_resume(
    request: Request,
    resume: Annotated[DatabaseResume, Depends(get_resume_for_user)],
) -> Response:
    """Retrieve a specific resume's Markdown content by ID for the current user.

    Args:
        request (Request): The HTTP request object.
        resume (DatabaseResume): The resume object from dependency.

    Returns:
        ResumeDetailResponse | HTMLResponse: The resume's ID, name, and content, or HTML for HTMX.

    Raises:
        HTTPException: If the resume is not found or doesn't belong to the user.

    Notes:
        1. Queries the database for a resume with the given ID and user_id.
        2. If no resume is found, raises a 404 error.
        3. If the request is from HTMX, returns HTML for the resume content.
        4. Otherwise, returns a ResumeDetailResponse with the resume's ID, name, and content.
        5. Performs database access: Reads from the database via db.query.
        6. Performs network access: None.

    """
    if "HX-Request" in request.headers:
        html_content = _generate_resume_detail_html(resume)
        return HTMLResponse(content=html_content)

    return ResumeDetailResponse(
        id=resume.id,
        name=resume.name,
        content=resume.content,
    )
