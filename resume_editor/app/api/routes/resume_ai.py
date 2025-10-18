import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated, AsyncGenerator

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from resume_editor.app.api.dependencies import get_resume_for_user
from resume_editor.app.api.routes.route_logic.resume_ai_logic import (
    create_sse_close_message,
    create_sse_error_message,
    experience_refinement_sse_generator,
    handle_accept_refinement,
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

from .html_fragments import (
    _generate_resume_detail_html,
)

log = logging.getLogger(__name__)

router = APIRouter()

templates = Jinja2Templates(directory="resume_editor/app/templates")


@router.post("/{resume_id}/refine/stream", response_class=StreamingResponse)
async def refine_resume_stream(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_from_cookie)],
    resume: Annotated[DatabaseResume, Depends(get_resume_for_user)],
    form_data: Annotated[RefineForm, Depends()],
) -> StreamingResponse:
    """Refine the experience section of a resume using an LLM stream.
    This endpoint uses Server-Sent Events (SSE) to provide real-time feedback.
    """

    async def sse_generator_wrapper() -> AsyncGenerator[str, None]:
        _msg = "Starting SSE wrapper for experience refinement"
        log.debug(_msg)
        if (
            form_data.limit_refinement_years is not None
            and form_data.limit_refinement_years <= 0
        ):
            yield create_sse_error_message(
                "Limit refinement years must be a positive number.",
            )
            yield create_sse_close_message()
            return

        content_to_refine = resume.content
        if form_data.limit_refinement_years:
            try:
                start_date = datetime.now(timezone.utc).date() - timedelta(
                    days=int(form_data.limit_refinement_years * 365.25),
                )

                personal_info = extract_personal_info(resume.content)
                education_info = extract_education_info(resume.content)
                experience_info = extract_experience_info(resume.content)
                certifications_info = extract_certifications_info(resume.content)

                filtered_experience = filter_experience_by_date(
                    experience=experience_info,
                    start_date=start_date,
                    end_date=None,
                )

                content_to_refine = build_complete_resume_from_sections(
                    personal_info=personal_info,
                    education=education_info,
                    experience=filtered_experience,
                    certifications=certifications_info,
                )
            except Exception as e:
                _msg = f"Error during experience filtering: {e!s}"
                log.exception(_msg)
                yield create_sse_error_message(
                    "An error occurred while filtering experience.",
                )
                yield create_sse_close_message()
                return

        params = ExperienceRefinementParams(
            db=db,
            user=current_user,
            resume=resume,
            resume_content_to_refine=content_to_refine,
            job_description=form_data.job_description,
            generate_introduction=form_data.generate_introduction,
        )
        generator = experience_refinement_sse_generator(params=params)
        async for item in generator:
            yield item

    return StreamingResponse(
        sse_generator_wrapper(),
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
        generate_introduction=form_data.generate_introduction,
    )
    return await handle_sync_refinement(sync_params=params)


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
        Response: A response with an `HX-Redirect` header to the new resume's view page.

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
