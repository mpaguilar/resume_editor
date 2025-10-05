import html
import json
import logging
from typing import AsyncGenerator
import asyncio

from cryptography.fernet import InvalidToken
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.templating import Jinja2Templates
from openai import AuthenticationError
from sqlalchemy.orm import Session
from starlette.middleware.base import ClientDisconnect
from fastapi.responses import HTMLResponse, StreamingResponse

from resume_editor.app.api.dependencies import get_resume_for_user
from resume_editor.app.api.routes.route_logic.settings_crud import get_user_settings
from resume_editor.app.api.routes.route_logic.resume_crud import (
    create_resume as create_resume_db,
)
from resume_editor.app.api.routes.route_logic.resume_crud import get_user_resumes
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
from resume_editor.app.api.routes.route_models import (
    ExperienceResponse,
    RefineAction,
    RefineResponse,
    RefineTargetSection,
)
from resume_editor.app.core.auth import get_current_user_from_cookie
from resume_editor.app.core.security import decrypt_data
from resume_editor.app.database.database import get_db
from resume_editor.app.llm.orchestration import (
    async_refine_experience_section,
    refine_resume_section_with_llm,
)
from resume_editor.app.models.resume.experience import Role
from resume_editor.app.models.resume_model import Resume as DatabaseResume
from .html_fragments import (
    _create_refine_result_html,
    _generate_resume_detail_html,
    _generate_resume_list_html,
)
from resume_editor.app.models.user import User

log = logging.getLogger(__name__)

router = APIRouter()

templates = Jinja2Templates(directory="resume_editor/app/templates")


@router.get("/{resume_id}/refine/stream")
async def refine_resume_stream(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
    resume: DatabaseResume = Depends(get_resume_for_user),
    job_description: str = "",
    generate_introduction: bool = True,
) -> StreamingResponse:
    """
    Refine the experience section of a resume using an LLM stream.
    This endpoint uses Server-Sent Events (SSE) to provide real-time feedback.
    """
    _msg = f"Streaming refinement for resume {resume.id} for section experience"
    log.debug(_msg)

    async def sse_generator() -> AsyncGenerator[str, None]:
        # This generator encapsulates the entire process, including error handling,
        # to ensure that any failures are reported over the SSE stream.
        settings = get_user_settings(db, current_user.id)
        llm_endpoint = settings.llm_endpoint if settings else None
        llm_model_name = settings.llm_model_name if settings else None
        api_key = None

        try:
            if settings and settings.encrypted_api_key:
                api_key = decrypt_data(settings.encrypted_api_key)

            refined_roles = {}
            introduction = None
            async for event in async_refine_experience_section(
                resume_content=resume.content,
                job_description=job_description,
                llm_endpoint=llm_endpoint,
                api_key=api_key,
                llm_model_name=llm_model_name,
                generate_introduction=generate_introduction,
            ):
                if isinstance(event, dict) and event.get("status") == "in_progress":
                    progress_html = f"<li>{html.escape(event.get('message', ''))}</li>"
                    yield f"event: progress\ndata: {progress_html}\n\n"
                elif (
                    isinstance(event, dict)
                    and event.get("status") == "introduction_generated"
                ):
                    introduction = event.get("data")
                    if introduction:
                        intro_html = f"""<div id="introduction-container" hx-swap-oob="true">
    <h4 class="text-lg font-semibold text-gray-700">Suggested Introduction:</h4>
    <p class="mt-1 text-sm text-gray-600 bg-gray-50 p-3 rounded-md border">{html.escape(introduction)}</p>
</div>"""
                        data_payload = "\n".join(
                            f"data: {line}" for line in intro_html.splitlines()
                        )
                        yield f"event: introduction_generated\n{data_payload}\n\n"
                elif isinstance(event, dict) and event.get("status") == "role_refined":
                    index = event.get("original_index")
                    data = event.get("data")
                    if index is not None and data is not None:
                        refined_roles[index] = data

            if refined_roles:
                personal_info = extract_personal_info(resume.content)
                education_info = extract_education_info(resume.content)
                experience_info = extract_experience_info(resume.content)
                certifications_info = extract_certifications_info(resume.content)

                # Sort roles by original index to preserve order
                sorted_roles_data = [
                    role_data for _, role_data in sorted(refined_roles.items())
                ]
                roles_to_reconstruct = [
                    Role.model_validate(data) for data in sorted_roles_data
                ]

                refined_experience = ExperienceResponse(
                    roles=roles_to_reconstruct, projects=experience_info.projects
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
                data_payload = "\n".join(
                    f"data: {line}" for line in result_html.splitlines()
                )
                yield f"event: done\n{data_payload}\n\n"
            else:
                error_html = "<div role='alert' class='text-yellow-500 p-2'>Refinement finished, but no roles were found to refine.</div>"
                data_payload = "\n".join(
                    f"data: {line}" for line in error_html.splitlines()
                )
                yield f"event: error\n{data_payload}\n\n"

        except ClientDisconnect:
            _msg = f"Client disconnected from SSE stream for resume {resume.id}."
            log.warning(_msg)
        except (InvalidToken, AuthenticationError, ValueError, Exception) as e:
            error_message = "An unexpected error occurred."
            if isinstance(e, InvalidToken):
                error_message = "Invalid API key. Please update your settings."
            elif isinstance(e, AuthenticationError):
                error_message = "LLM authentication failed. Please check your API key."
            elif isinstance(e, ValueError):
                error_message = f"Refinement failed: {e!s}"

            _msg = f"SSE stream error for resume {resume.id}: {error_message}"
            log.exception(_msg)
            error_html = f"<div role='alert' class='text-red-500 p-2'>{html.escape(error_message)}</div>"
            data_payload = "\n".join(
                f"data: {line}" for line in error_html.splitlines()
            )
            yield f"event: error\n{data_payload}\n\n"
        finally:
            yield "event: close\ndata: stream complete\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
    )


@router.post("/{resume_id}/refine")
async def refine_resume(
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
    resume: DatabaseResume = Depends(get_resume_for_user),
    job_description: str = Form(...),
    target_section: RefineTargetSection = Form(...),
    generate_introduction: bool = Form(False),
):
    """
    Refine a resume section using an LLM to align with a job description.

    This endpoint handles both JSON API calls and HTMX form submissions.

    Args:
        http_request (Request): The HTTP request object to check for HTMX headers.
        db (Session): The database session dependency.
        current_user (User): The current authenticated user.
        resume (DatabaseResume): The resume to be refined.
        job_description (str): The job description to align the resume with.
        target_section (RefineTargetSection): The section of the resume to refine.

    Returns:
        RefineResponse | HTMLResponse: The response type
            depends on the request headers.

    """
    _msg = f"Refining resume {resume.id} for section {target_section.value}"
    log.debug(_msg)

    if target_section == RefineTargetSection.EXPERIENCE:
        return templates.TemplateResponse(
            http_request,
            "partials/resume/_refine_sse_loader.html",
            {
                "resume_id": resume.id,
                "job_description": job_description,
                "generate_introduction": generate_introduction,
            },
        )

    settings = get_user_settings(db, current_user.id)
    llm_endpoint = settings.llm_endpoint if settings else None
    llm_model_name = settings.llm_model_name if settings else None
    api_key = None
    if settings and settings.encrypted_api_key:
        try:
            api_key = decrypt_data(settings.encrypted_api_key)
        except InvalidToken:
            detail = "Invalid API key. Please update your settings."
            _msg = f"API key decryption failed for user {current_user.id}"
            log.warning(_msg)
            if "HX-Request" in http_request.headers:
                return HTMLResponse(
                    f'<div role="alert" class="text-red-500 p-2">{detail}</div>',
                    status_code=200,
                )
            raise HTTPException(status_code=400, detail=detail)

    try:
        # Handle other sections synchronously
        refined_content, introduction = refine_resume_section_with_llm(
            resume_content=resume.content,
            job_description=job_description,
            target_section=target_section.value,
            llm_endpoint=llm_endpoint,
            api_key=api_key,
            llm_model_name=llm_model_name,
            generate_introduction=generate_introduction,
        )

        if "HX-Request" in http_request.headers:
            html_content = _create_refine_result_html(
                resume_id=resume.id,
                target_section_val=target_section.value,
                refined_content=refined_content,
                job_description=job_description,
                introduction=introduction,
            )
            return HTMLResponse(content=html_content)

        return RefineResponse(
            refined_content=refined_content, introduction=introduction
        )
    except AuthenticationError as e:
        detail = "LLM authentication failed. Please check your API key in settings."
        _msg = f"LLM authentication failed for user {current_user.id}: {e!s}"
        log.warning(_msg)
        if "HX-Request" in http_request.headers:
            return HTMLResponse(
                f'<div role="alert" class="text-red-500 p-2">{detail}</div>',
                status_code=200,
            )
        raise HTTPException(status_code=401, detail=detail)
    except ValueError as e:
        detail = str(e)
        _msg = f"LLM refinement failed for resume {resume.id} with ValueError: {detail}"
        log.warning(_msg)
        if "HX-Request" in http_request.headers:
            return HTMLResponse(
                f'<div role="alert" class="text-red-500 p-2">Refinement failed: {detail}</div>',
                status_code=200,
            )
        raise HTTPException(status_code=400, detail=detail)
    except Exception as e:
        detail = f"An unexpected error occurred during refinement: {e!s}"
        _msg = f"LLM refinement failed for resume {resume.id}: {e!s}"
        log.exception(_msg)
        if "HX-Request" in http_request.headers:
            return HTMLResponse(
                f'<div role="alert" class="text-red-500 p-2">{detail}</div>',
                status_code=200,
            )
        raise HTTPException(status_code=500, detail=f"LLM refinement failed: {e!s}")


@router.post("/{resume_id}/refine/accept", response_class=HTMLResponse)
async def accept_refined_resume(
    resume: DatabaseResume = Depends(get_resume_for_user),
    db: Session = Depends(get_db),
    refined_content: str = Form(...),
    target_section: RefineTargetSection = Form(...),
    introduction: str | None = Form(None),
):
    """
    Accept a refined resume section and persist the changes by overwriting.

    Args:
        resume (DatabaseResume): The original resume being modified.
        db (Session): The database session.
        refined_content (str): The refined markdown from the LLM.
        target_section (RefineTargetSection): The section that was refined.

    Returns:
        HTMLResponse: An HTML partial containing the updated resume detail view.

    """
    updated_content = ""
    try:
        if target_section == RefineTargetSection.FULL:
            updated_content = refined_content
        else:
            # Based on the target section, use the refined content for that section
            # and the original content for all others.
            personal_info = extract_personal_info(
                refined_content
                if target_section == RefineTargetSection.PERSONAL
                else resume.content,
            )
            education_info = extract_education_info(
                refined_content
                if target_section == RefineTargetSection.EDUCATION
                else resume.content,
            )
            experience_info = extract_experience_info(
                refined_content
                if target_section == RefineTargetSection.EXPERIENCE
                else resume.content,
            )
            certifications_info = extract_certifications_info(
                refined_content
                if target_section == RefineTargetSection.CERTIFICATIONS
                else resume.content,
            )

            updated_content = build_complete_resume_from_sections(
                personal_info=personal_info,
                education=education_info,
                experience=experience_info,
                certifications=certifications_info,
            )
        perform_pre_save_validation(updated_content, resume.content)
    except (ValueError, TypeError, HTTPException) as e:
        detail = getattr(e, "detail", str(e))
        _msg = f"Failed to reconstruct resume from refined section: {detail}"
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=_msg)

    update_resume_db(
        db=db, resume=resume, content=updated_content, introduction=introduction
    )
    # For HTMX, return the detail view for the main content area
    detail_html = _generate_resume_detail_html(resume)
    return HTMLResponse(content=detail_html)


@router.post("/{resume_id}/refine/save_as_new", response_class=HTMLResponse)
async def save_refined_resume_as_new(
    resume: DatabaseResume = Depends(get_resume_for_user),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
    refined_content: str = Form(...),
    target_section: RefineTargetSection = Form(...),
    new_resume_name: str | None = Form(None),
    job_description: str | None = Form(None),
    introduction: str | None = Form(None),
):
    """
    Save a refined resume as a new resume.

    Args:
        resume (DatabaseResume): The original resume being modified.
        db (Session): The database session.
        current_user (User): The current authenticated user.
        refined_content (str): The refined markdown from the LLM.
        target_section (RefineTargetSection): The section that was refined.
        new_resume_name (str | None): The name for the new resume.

    Returns:
        HTMLResponse: An HTML partial containing both the new resume detail view
                      and an out-of-band swap for the sidebar resume list.
    """
    if not new_resume_name:
        raise HTTPException(
            status_code=400,
            detail="New resume name is required for 'save as new' action.",
        )

    updated_content = ""
    try:
        if target_section == RefineTargetSection.FULL:
            updated_content = refined_content
        else:
            personal_info = extract_personal_info(
                refined_content
                if target_section == RefineTargetSection.PERSONAL
                else resume.content
            )
            education_info = extract_education_info(
                refined_content
                if target_section == RefineTargetSection.EDUCATION
                else resume.content
            )
            experience_info = extract_experience_info(
                refined_content
                if target_section == RefineTargetSection.EXPERIENCE
                else resume.content
            )
            certifications_info = extract_certifications_info(
                refined_content
                if target_section == RefineTargetSection.CERTIFICATIONS
                else resume.content
            )
            updated_content = build_complete_resume_from_sections(
                personal_info=personal_info,
                education=education_info,
                experience=experience_info,
                certifications=certifications_info,
            )
        perform_pre_save_validation(updated_content, resume.content)
    except (ValueError, TypeError, HTTPException) as e:
        detail = getattr(e, "detail", str(e))
        _msg = f"Failed to reconstruct resume from refined section: {detail}"
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=_msg)

    new_resume = create_resume_db(
        db=db,
        user_id=current_user.id,
        name=new_resume_name,
        content=updated_content,
        is_base=False,
        parent_id=resume.id,
        job_description=job_description,
        introduction=introduction,
    )

    resumes = get_user_resumes(db, current_user.id)
    base_resumes = [r for r in resumes if r.is_base]
    refined_resumes = [r for r in resumes if not r.is_base]
    sidebar_html = _generate_resume_list_html(
        base_resumes=base_resumes,
        refined_resumes=refined_resumes,
        selected_resume_id=new_resume.id,
    )
    detail_html = _generate_resume_detail_html(new_resume)

    # Use OOB swap to update sidebar, and return main content normally
    response_html = f"""
    <div id="left-sidebar-content" hx-swap-oob="true">
        {sidebar_html}
    </div>
    {detail_html}
    """
    return HTMLResponse(content=response_html)


@router.post("/{resume_id}/refine/discard", response_class=HTMLResponse)
async def discard_refined_resume(
    resume: DatabaseResume = Depends(get_resume_for_user),
):
    """
    Discards a refinement and returns the original resume detail view.

    This is used when a user rejects an AI suggestion, and it re-renders
    the resume detail partial to clear the suggestion from the UI.
    """
    detail_html = _generate_resume_detail_html(resume)
    return HTMLResponse(content=detail_html)
