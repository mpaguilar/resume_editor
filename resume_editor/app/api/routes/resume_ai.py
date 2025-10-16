import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from resume_editor.app.api.dependencies import get_resume_for_user
from resume_editor.app.api.routes.route_logic.resume_ai_logic import (
    experience_refinement_sse_generator,
    handle_accept_refinement,
    handle_save_as_new_refinement,
    handle_sync_refinement,
)
from resume_editor.app.api.routes.route_models import (
    RefineForm,
    RefineTargetSection,
    SaveAsNewForm,
    SaveAsNewParams,
    SyncRefinementParams,
)
from resume_editor.app.api.routes.route_models import RefineTargetSection
from resume_editor.app.core.auth import get_current_user_from_cookie
from resume_editor.app.database.database import get_db
from resume_editor.app.models.resume_model import Resume as DatabaseResume
from resume_editor.app.models.user import User

from .html_fragments import (
    _generate_resume_detail_html,
)

log = logging.getLogger(__name__)

router = APIRouter()

templates = Jinja2Templates(directory="resume_editor/app/templates")


@router.get("/{resume_id}/refine/stream")
async def refine_resume_stream(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_from_cookie)],
    resume: Annotated[DatabaseResume, Depends(get_resume_for_user)],
    job_description: str = "",
    generate_introduction: bool = True,
) -> StreamingResponse:
    """Refine the experience section of a resume using an LLM stream.
    This endpoint uses Server-Sent Events (SSE) to provide real-time feedback.
    """
    generator = experience_refinement_sse_generator(
        db=db,
        user=current_user,
        resume=resume,
        job_description=job_description,
        generate_introduction=generate_introduction,
    )
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
    )


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
                "generate_introduction": form_data.generate_introduction,
            },
        )

    params = SyncRefinementParams(
        request=http_request,
        db=db,
        user=current_user,
        resume=resume,
        job_description=form_data.job_description,
        target_section=form_data.target_section,
        generate_introduction=form_data.generate_introduction,
    )
    return await handle_sync_refinement(params)


@router.post("/{resume_id}/refine/accept", status_code=200)
async def accept_refined_resume(
    resume: Annotated[DatabaseResume, Depends(get_resume_for_user)],
    db: Annotated[Session, Depends(get_db)],
    refined_content: Annotated[str, Form(...)],
    target_section: Annotated[RefineTargetSection, Form(...)],
    introduction: Annotated[str | None, Form()] = None,
) -> Response:
    """Accept a refined resume section and persist the changes by overwriting.

    Args:
        resume (DatabaseResume): The original resume being modified.
        db (Session): The database session.
        refined_content (str): The refined markdown from the LLM.
        target_section (RefineTargetSection): The section that was refined.
        introduction (str | None): An optional new introduction.

    Returns:
        Response: A response with an `HX-Redirect` header to the dashboard.

    """
    handle_accept_refinement(
        db=db,
        resume=resume,
        refined_content=refined_content,
        target_section=target_section,
        introduction=introduction,
    )
    return Response(headers={"HX-Redirect": "/dashboard"})


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
        Response: A response with an `HX-Redirect` header to the dashboard.

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
    handle_save_as_new_refinement(params)

    return Response(headers={"HX-Redirect": "/dashboard"})


@router.post("/{resume_id}/refine/discard", response_class=HTMLResponse)
async def discard_refined_resume(
    resume: Annotated[DatabaseResume, Depends(get_resume_for_user)],
) -> HTMLResponse:
    """Discards a refinement and returns the original resume detail view.

    This is used when a user rejects an AI suggestion, and it re-renders
    the resume detail partial to clear the suggestion from the UI.
    """
    detail_html = _generate_resume_detail_html(resume)
    return HTMLResponse(content=detail_html)
