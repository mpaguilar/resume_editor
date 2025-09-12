import logging
from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

# Import database dependencies
from resume_editor.app.api.dependencies import get_resume_for_user
# Import route logic modules
from resume_editor.app.api.routes.route_logic.resume_crud import (
    create_resume as create_resume_db,
)
from resume_editor.app.api.routes.route_logic.resume_crud import (
    delete_resume as delete_resume_db,
)
from resume_editor.app.api.routes.route_logic.resume_crud import (
    get_user_resumes,
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
from resume_editor.app.api.routes.route_logic.resume_parsing import (
    parse_resume_content,
    validate_resume_content,
)
from resume_editor.app.api.routes.route_models import (
    ParseRequest,
    ParseResponse,
    RefineTargetSection,
    ResumeCreateRequest,
    ResumeDetailResponse,
    ResumeResponse,
)
from resume_editor.app.api.routes.html_fragments import (
    _generate_resume_detail_html,
    _generate_resume_list_html,
)
from resume_editor.app.core.auth import get_current_user_from_cookie
from resume_editor.app.database.database import get_db
from resume_editor.app.models.resume_model import Resume as DatabaseResume
from resume_editor.app.models.user import User
from . import resume_export, resume_ai, resume_edit

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resumes", tags=["resumes"])

router.include_router(resume_export.router)
router.include_router(resume_ai.router)
router.include_router(resume_edit.router)


@router.post("/parse", response_model=ParseResponse)
async def parse_resume_endpoint(request: ParseRequest):
    """
    Parse Markdown resume content and return structured data.

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """
    Save a new resume to the database via API, associating it with the current user.

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

    resume = create_resume_db(
        db=db,
        user_id=current_user.id,
        name=request.name,
        content=request.content,
    )

    if "HX-Request" in http_request.headers:
        return HTMLResponse(headers={"HX-Redirect": f"/resumes/{resume.id}/edit"})

    return ResumeResponse(id=resume.id, name=resume.name)


@router.put("/{resume_id}", response_model=ResumeResponse)
async def update_resume(
    http_request: Request,
    db: Session = Depends(get_db),
    resume: DatabaseResume = Depends(get_resume_for_user),
    name: str = Form(...),
    content: str | None = Form(None),
):
    """
    Update an existing resume's name and/or content for the current user.

    This endpoint handles both JSON API calls and HTMX form submissions.

    Args:
        http_request (Request): The HTTP request object.
        db (Session): The database session dependency.
        resume (DatabaseResume): The resume object to update, from dependency.
        name (str): The resume name from form data.
        content (str): The resume content from form data.


    Returns:
        ResumeResponse | HTMLResponse: JSON response for API call, or HTML for HTMX.

    Raises:
        HTTPException: If validation fails or an error occurs during the update.

    Notes:
        1. Validates resume content if it is being updated.
        2. Updates the resume's name and/or content.
        3. For HTMX requests, returns an HTML partial of the updated resume detail view.
        4. For regular API calls, returns a JSON response with the updated resume's ID and name.
        5. Performs database reads and writes.

    """
    # Validate Markdown content only if it's a non-empty string
    if content:
        validate_resume_content(content)

    # If content is an empty string, treat it as None to prevent wiping content.
    content_to_update = content if content else None
    updated_resume = update_resume_db(
        db=db, resume=resume, name=name, content=content_to_update
    )

    return ResumeResponse(id=updated_resume.id, name=updated_resume.name)


@router.delete("/{resume_id}")
async def delete_resume(
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
    resume: DatabaseResume = Depends(get_resume_for_user),
):
    """
    Delete a resume for the current user.

    Args:
        resume_id (int): The unique identifier of the resume to delete.
        http_request (Request): The HTTP request object.
        db (Session): The database session dependency.
        current_user (User): The current authenticated user.

    Returns:
        dict | HTMLResponse: A success message, or HTML for HTMX.

    Raises:
        HTTPException: If the resume is not found, doesn't belong to the user, or there's an error deleting.

    Notes:
        1. Queries the database for a resume with the given ID and user_id.
        2. If no resume is found, raises a 404 error.
        3. Deletes the resume from the database.
        4. Commits the transaction to save the changes.
        5. If the request is from HTMX, returns HTML to update the resume list.
        6. Otherwise, returns a success message.
        7. Performs database access: Reads from and writes to the database via db.query, db.delete, db.commit.
        8. Performs network access: None.

    """
    # Delete the resume
    delete_resume_db(db, resume)

    # Check if this is an HTMX request
    if "HX-Request" in http_request.headers:
        # Return updated resume list
        resumes = get_user_resumes(db, current_user.id)
        html_content = _generate_resume_list_html(resumes)
        return HTMLResponse(content=html_content)

    return {"message": "Resume deleted successfully"}


@router.get("", response_model=list[ResumeResponse])
async def list_resumes(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """
    List all resumes for the current user.

    Args:
        request (Request): The HTTP request object.
        db (Session): The database session dependency.
        current_user (User): The current authenticated user.

    Returns:
        List[ResumeResponse] | HTMLResponse: A list of resumes with their IDs and names, or HTML for HTMX.

    Raises:
        HTTPException: If there's an error retrieving the resumes from the database.

    Notes:
        1. Queries the database for all resumes belonging to the current user.
        2. Filters results by matching the user_id.
        3. Converts each resume object into a ResumeResponse.
        4. If the request is from HTMX, returns HTML for the resume list.
        5. Otherwise, returns the list of ResumeResponse objects.
        6. Performs database access: Reads from the database via db.query.
        7. Performs network access: None.

    """
    resumes = get_user_resumes(db, current_user.id)

    # Check if this is an HTMX request
    if "HX-Request" in request.headers:
        html_content = _generate_resume_list_html(resumes)
        return HTMLResponse(content=html_content)

    return [ResumeResponse(id=resume.id, name=resume.name) for resume in resumes]




@router.get("/{resume_id}", response_model=ResumeDetailResponse)
async def get_resume(
    request: Request,
    resume: DatabaseResume = Depends(get_resume_for_user),
):
    """
    Retrieve a specific resume's Markdown content by ID for the current user.

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
    return ResumeDetailResponse(
        id=resume.id,
        name=resume.name,
        content=resume.content,
    )














