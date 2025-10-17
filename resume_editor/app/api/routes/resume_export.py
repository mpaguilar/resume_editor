import logging
from copy import deepcopy
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from resume_editor.app.api.dependencies import get_resume_for_user
from resume_editor.app.api.routes.route_logic.resume_export import (
    render_resume_to_docx_stream,
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
    RenderFormat,
    RenderSettingsName,
)
from resume_editor.app.core.rendering_settings import get_render_settings
from resume_editor.app.database.database import get_db
from resume_editor.app.models.resume_model import Resume as DatabaseResume

log = logging.getLogger(__name__)

router = APIRouter()


class ResumeExportSettingsForm:
    """Form data for resume export settings."""

    def __init__(
        self,
        include_projects: bool = Query(False),
        render_projects_first: bool = Query(False),
        include_education: bool = Query(False),
    ):
        self.include_projects = include_projects
        self.render_projects_first = render_projects_first
        self.include_education = include_education


class DownloadParams:
    """Parameters for downloading a rendered resume."""

    def __init__(
        self,
        render_format: RenderFormat,
        settings_name: RenderSettingsName,
        start_date: Annotated[str | None, Query()] = None,
        end_date: Annotated[str | None, Query()] = None,
    ):
        self.render_format = render_format
        self.settings_name = settings_name
        self.start_date = start_date
        self.end_date = end_date


def _parse_date_range(
    start_date: str | None,
    end_date: str | None,
) -> tuple[date | None, date | None]:
    """Parses start and end date strings into date objects."""
    parsed_start_date: date | None = None
    parsed_end_date: date | None = None
    try:
        if start_date:
            parsed_start_date = date.fromisoformat(start_date)
        if end_date:
            parsed_end_date = date.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Please use YYYY-MM-DD.",
        )
    return parsed_start_date, parsed_end_date


def _get_filtered_resume_content(
    resume_content: str,
    start_date: date | None,
    end_date: date | None,
) -> str:
    """Filters resume content by date range if dates are provided."""
    if not start_date and not end_date:
        return resume_content

    personal_info = extract_personal_info(resume_content)
    education_info = extract_education_info(resume_content)
    experience_info = extract_experience_info(resume_content)
    certifications_info = extract_certifications_info(resume_content)

    filtered_experience = filter_experience_by_date(
        experience_info,
        start_date,
        end_date,
    )

    return build_complete_resume_from_sections(
        personal_info=personal_info,
        education=education_info,
        experience=filtered_experience,
        certifications=certifications_info,
    )


@router.get("/{resume_id}/export/markdown")
async def export_resume_markdown(
    resume: Annotated[DatabaseResume, Depends(get_resume_for_user)],
    start_date: Annotated[str | None, Query()] = None,
    end_date: Annotated[str | None, Query()] = None,
) -> Response:
    """Export a resume as a Markdown file.

    Args:
        resume (DatabaseResume): The resume object, injected by dependency.
        start_date (str | None): Optional start date to filter experience (YYYY-MM-DD).
        end_date (str | None): Optional end date to filter experience (YYYY-MM-DD).

    Returns:
        Response: A response object containing the resume's Markdown content as a downloadable file.

    Raises:
        HTTPException: If the resume is not found or does not belong to the user (handled by dependency).

    Notes:
        1. Fetches the resume using the get_resume_for_user dependency.
        2. If a date range is provided, filters the experience section before exporting.
        3. Creates a Response object with the resume's content.
        4. Sets the 'Content-Type' header to 'text/markdown'.
        5. Sets the 'Content-Disposition' header to trigger a file download with the resume's name.
        6. Returns the response.

    """
    parsed_start_date, parsed_end_date = _parse_date_range(start_date, end_date)

    try:
        content_to_export = _get_filtered_resume_content(
            resume.content,
            parsed_start_date,
            parsed_end_date,
        )
    except (ValueError, TypeError) as e:
        detail = getattr(e, "detail", str(e))
        _msg = f"Failed to filter resume due to content parsing error: {detail}"
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=_msg)

    headers = {
        "Content-Disposition": f'attachment; filename="{resume.name}.md"',
    }
    return Response(
        content=content_to_export,
        media_type="text/markdown",
        headers=headers,
    )


@router.get("/{resume_id}/download")
async def download_resume(
    download_params: Annotated[DownloadParams, Depends()],
    resume: Annotated[DatabaseResume, Depends(get_resume_for_user)],
    settings_form: Annotated[ResumeExportSettingsForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> StreamingResponse:
    """Download a rendered resume as a DOCX file.

    This endpoint generates and streams a DOCX file for the specified resume,
    using the given render format and settings. It also persists the user's
    chosen export settings for future use.

    Args:
        download_params (DownloadParams): Parameters for the download, including format, settings, and date range.
        resume (DatabaseResume): The resume object, injected by dependency.
        settings_form (ResumeExportSettingsForm): Form data with export settings.
        db (Session): The database session, injected by dependency.

    Returns:
        StreamingResponse: A streaming response with the generated DOCX file.

    Raises:
        HTTPException: If the resume is not found, or if rendering fails.

    """
    _msg = (
        f"download_resume starting for format {download_params.render_format.value}, "
        f"settings: {download_params.settings_name.value}"
    )
    log.debug(_msg)

    resume.export_settings_include_projects = settings_form.include_projects
    resume.export_settings_render_projects_first = settings_form.render_projects_first
    resume.export_settings_include_education = settings_form.include_education
    db.add(resume)
    db.commit()

    parsed_start_date, parsed_end_date = _parse_date_range(
        download_params.start_date,
        download_params.end_date,
    )

    try:
        content_to_parse = _get_filtered_resume_content(
            resume.content,
            parsed_start_date,
            parsed_end_date,
        )
    except (ValueError, TypeError) as e:
        detail = getattr(e, "detail", str(e))
        _msg = (
            f"Failed to generate docx due to content parsing/filtering error: {detail}"
        )
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=_msg)

    try:
        settings_dict = deepcopy(
            get_render_settings(download_params.settings_name.value),
        )
        # Override with per-resume settings
        settings_dict["education"] = resume.export_settings_include_education
        settings_dict["section"]["experience"]["projects"] = (
            resume.export_settings_include_projects
        )
        settings_dict["section"]["experience"]["render_projects_first"] = (
            resume.export_settings_render_projects_first
        )

        file_stream = render_resume_to_docx_stream(
            resume_content=content_to_parse,
            render_format=download_params.render_format.value,
            settings_dict=settings_dict,
        )
    except ValueError as e:
        _msg = str(e)
        log.error(_msg)
        raise HTTPException(status_code=400, detail=_msg)
    except Exception as e:
        _msg = f"Failed to generate docx during rendering: {e}"
        log.exception(_msg)
        raise HTTPException(status_code=500, detail=_msg)

    filename = (
        f"{resume.name.replace(' ', '_')}-"
        f"{download_params.render_format.value}-{download_params.settings_name.value}.docx"
    )

    headers = {
        "Content-Disposition": f"attachment; filename={filename}",
    }
    return StreamingResponse(
        file_stream,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers=headers,
    )
