import io
import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse

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
    DocxFormat,
    RenderFormat,
    RenderSettingsName,
)
from resume_editor.app.core.rendering_settings import get_render_settings
from resume_editor.app.models.resume_model import Resume as DatabaseResume

log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{resume_id}/export/markdown")
async def export_resume_markdown(
    resume: DatabaseResume = Depends(get_resume_for_user),
    start_date: date | None = None,
    end_date: date | None = None,
):
    """
    Export a resume as a Markdown file.

    Args:
        resume (DatabaseResume): The resume object, injected by dependency.
        start_date (date | None): Optional start date to filter experience.
        end_date (date | None): Optional end date to filter experience.

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
    try:
        content_to_export = resume.content

        if start_date or end_date:
            # If filtering is needed, parse, filter, and reconstruct.
            personal_info = extract_personal_info(resume.content)
            education_info = extract_education_info(resume.content)
            experience_info = extract_experience_info(resume.content)
            certifications_info = extract_certifications_info(resume.content)

            filtered_experience = filter_experience_by_date(
                experience_info,
                start_date,
                end_date,
            )

            content_to_export = build_complete_resume_from_sections(
                personal_info=personal_info,
                education=education_info,
                experience=filtered_experience,
                certifications=certifications_info,
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
async def download_rendered_resume(
    render_format: RenderFormat,
    settings_name: RenderSettingsName,
    resume: DatabaseResume = Depends(get_resume_for_user),
    start_date: date | None = None,
    end_date: date | None = None,
):
    """
    Download a rendered resume as a DOCX file.

    This endpoint generates and streams a DOCX file for the specified resume,
    using the given render format and settings.

    Args:
        render_format (RenderFormat): The rendering format for the DOCX file.
        settings_name (RenderSettingsName): The name of the render settings to apply.
        resume (DatabaseResume): The resume object, injected by dependency.
        start_date (date | None): Optional start date to filter experience.
        end_date (date | None): Optional end date to filter experience.

    Returns:
        StreamingResponse: A streaming response with the generated DOCX file.

    Raises:
        HTTPException: If the resume is not found, or if rendering fails.
    """
    _msg = (
        f"download_rendered_resume starting for format {render_format.value}, "
        f"settings: {settings_name.value}"
    )
    log.debug(_msg)
    try:
        content_to_parse = resume.content
        if start_date or end_date:
            personal_info = extract_personal_info(resume.content)
            education_info = extract_education_info(resume.content)
            experience_info = extract_experience_info(resume.content)
            certifications_info = extract_certifications_info(resume.content)

            filtered_experience = filter_experience_by_date(
                experience_info,
                start_date,
                end_date,
            )

            content_to_parse = build_complete_resume_from_sections(
                personal_info=personal_info,
                education=education_info,
                experience=filtered_experience,
                certifications=certifications_info,
            )

    except (ValueError, TypeError) as e:
        detail = getattr(e, "detail", str(e))
        _msg = (
            f"Failed to generate docx due to content parsing/filtering error: {detail}"
        )
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=_msg)

    try:
        settings_dict = get_render_settings(settings_name.value)

        file_stream = render_resume_to_docx_stream(
            resume_content=content_to_parse,
            render_format=render_format.value,
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
        f"{render_format.value}-{settings_name.value}.docx"
    )

    headers = {
        "Content-Disposition": f"attachment; filename={filename}",
    }
    return StreamingResponse(
        file_stream,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers=headers,
    )
