import html
import io
import logging
from datetime import date, datetime

from cryptography.fernet import InvalidToken
from docx import Document
from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from resume_writer.main import ats_render, basic_render, plain_render
from resume_writer.resume_render.render_settings import ResumeRenderSettings
from sqlalchemy.orm import Session

# Import database dependencies
# Import route logic modules
from resume_editor.app.api.routes.route_logic.resume_crud import (
    create_resume as create_resume_db,
)
from resume_editor.app.api.routes.route_logic.resume_crud import (
    delete_resume as delete_resume_db,
)
from resume_editor.app.api.routes.route_logic.resume_crud import (
    get_resume_by_id_and_user,
    get_user_resumes,
)
from resume_editor.app.api.routes.route_logic.resume_crud import (
    update_resume as update_resume_db,
)
from resume_editor.app.api.routes.route_logic.resume_filtering import (
    filter_experience_by_date,
)
from resume_editor.app.api.routes.route_logic.resume_llm import (
    refine_resume_section_with_llm,
)
from resume_editor.app.api.routes.route_logic.resume_parsing import (
    parse_resume_content,
    parse_resume_to_writer_object,
    validate_resume_content,
)
from resume_editor.app.api.routes.route_logic.resume_reconstruction import (
    build_complete_resume_from_sections,
)
from resume_editor.app.api.routes.route_logic.resume_serialization import (
    extract_certifications_info,
    extract_education_info,
    extract_experience_info,
    extract_personal_info,
    update_resume_content_with_structured_data,
)
from resume_editor.app.api.routes.route_logic.resume_validation import (
    perform_pre_save_validation,
)
from resume_editor.app.api.routes.route_logic.settings_crud import get_user_settings
from resume_editor.app.api.routes.route_models import (
    CertificationsResponse,
    CertificationUpdateRequest,
    DocxFormat,
    EducationResponse,
    EducationUpdateRequest,
    ExperienceResponse,
    ExperienceUpdateRequest,
    ParseRequest,
    ParseResponse,
    PersonalInfoResponse,
    PersonalInfoUpdateRequest,
    ProjectsResponse,
    RefineAction,
    RefineResponse,
    RefineTargetSection,
    ResumeCreateRequest,
    ResumeDetailResponse,
    ResumeResponse,
    ResumeUpdateRequest,
)
from resume_editor.app.core.auth import get_current_user
from resume_editor.app.core.security import decrypt_data
from resume_editor.app.database.database import get_db
from resume_editor.app.models.resume.certifications import Certification
from resume_editor.app.models.resume.education import Degree
from resume_editor.app.models.resume.experience import Project, Role
from resume_editor.app.models.resume_model import Resume as DatabaseResume
from resume_editor.app.models.user import User

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


async def get_resume_for_user(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DatabaseResume:
    """
    Dependency to get a specific resume for the current user.

    Args:
        resume_id (int): The unique identifier of the resume to retrieve.
        db (Session): The database session dependency.
        current_user (User): The current authenticated user.

    Returns:
        DatabaseResume: The resume object if found and belongs to the user.

    Raises:
        HTTPException: If the resume is not found or doesn't belong to the user.

    Notes:
        1. Queries the database for a resume with the given ID and user_id.
        2. If no resume is found, raises a 404 error.
        3. Performs database access: Reads from the database via db.query.
        4. Returns the resume object.

    """
    return get_resume_by_id_and_user(db, resume_id=resume_id, user_id=current_user.id)


def _generate_resume_list_html(
    resumes: list[DatabaseResume],
    selected_resume_id: int | None,
) -> str:
    """
    Generates HTML for a list of resumes, marking one as selected.

    Args:
        resumes (list[DatabaseResume]): The list of resumes to display.
        selected_resume_id (int | None): The ID of the resume to mark as selected.

    Returns:
        str: HTML string for the resume list.

    Notes:
        1. Checks if the resumes list is empty.
        2. If empty, returns a message indicating no resumes were found.
        3. Otherwise, generates HTML for each resume item with a selected class if it matches the selected ID.
        4. Returns the concatenated HTML string.

    """
    if not resumes:
        return """
        <div class="text-center py-8">
            <p class="text-gray-500">No resumes found.</p>
            <p class="text-gray-400 text-sm mt-2">Create your first resume using the "+ New Resume" button.</p>
        </div>
        """

    resume_items = []
    for r in resumes:
        selected_class = "selected" if r.id == selected_resume_id else ""
        resume_items.append(f"""
            <div class="resume-item p-3 rounded cursor-pointer border border-gray-200 mb-2 {selected_class}"
                 onclick="selectResume({r.id}, this)">
                <div class="font-medium text-gray-800">{r.name}</div>
                <div class="text-xs text-gray-500">ID: {r.id}</div>
            </div>
            """)
    return "\n".join(resume_items)


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
    return parse_resume_content(request.markdown_content)


@router.post("", response_model=ResumeResponse)
async def create_resume(
    http_request: Request,
    create_request: ResumeCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Save a new resume to the database, associating it with the current user.

    This endpoint handles both JSON API calls and HTMX form submissions that
    send JSON.

    Args:
        http_request (Request): The HTTP request object.
        create_request (ResumeCreateRequest): The data for the new resume, from JSON body.
        db (Session): The database session dependency.
        current_user (User): The current authenticated user.

    Returns:
        ResumeResponse | HTMLResponse: The created resume's ID and name, or HTML for HTMX.

    Raises:
        HTTPException: If there's an error saving the resume to the database or if Markdown validation fails.

    Notes:
        1. Validates the Markdown content using the resume parser.
        2. If validation fails, raises a 422 error with parsing details.
        3. Creates a new DatabaseResume instance with the provided name and content.
        4. Associates the resume with the current user using the user_id.
        5. Adds the new resume to the database session.
        6. Commits the transaction to save the data.
        7. Refreshes the resume object to ensure it has the latest state, including the ID.
        8. If the request is from HTMX, returns an HTML partial of the new resume detail view.
        9. Otherwise, returns a ResumeResponse with the resume ID and name.
        10. Performs database access: Writes to the database via db.add and db.commit.

    """
    # Validate Markdown content before saving
    validate_resume_content(create_request.content)

    resume = create_resume_db(
        db=db,
        user_id=current_user.id,
        name=create_request.name,
        content=create_request.content,
    )

    # Check if this is an HTMX request
    if "HX-Request" in http_request.headers:
        # For HTMX, return the detail view for the main content area
        detail_html = _generate_resume_detail_html(resume)
        return HTMLResponse(content=detail_html)

    return ResumeResponse(id=resume.id, name=resume.name)


@router.put("/{resume_id}", response_model=ResumeResponse)
async def update_resume(
    http_request: Request,
    update_data: ResumeUpdateRequest,
    db: Session = Depends(get_db),
    resume: DatabaseResume = Depends(get_resume_for_user),
):
    """
    Update an existing resume's name and/or content for the current user.

    This endpoint handles both JSON API calls and HTMX form submissions that
    send JSON.

    Args:
        http_request (Request): The HTTP request object.
        update_data (ResumeUpdateRequest): The data for the update, from JSON body.
        db (Session): The database session dependency.
        resume (DatabaseResume): The resume object to update, from dependency.

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
    # Validate Markdown content only if it's being updated
    if update_data.content is not None:
        validate_resume_content(update_data.content)

    updated_resume = update_resume_db(
        db=db, resume=resume, name=update_data.name, content=update_data.content
    )

    # Check if this is an HTMX request
    if "HX-Request" in http_request.headers:
        # For HTMX, return the detail view for the main content area
        detail_html = _generate_resume_detail_html(updated_resume)
        return HTMLResponse(content=detail_html)

    return ResumeResponse(id=updated_resume.id, name=updated_resume.name)


@router.delete("/{resume_id}")
async def delete_resume(
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
        html_content = _generate_resume_list_html(resumes, None)
        return HTMLResponse(content=html_content)

    return {"message": "Resume deleted successfully"}


@router.get("", response_model=list[ResumeResponse])
async def list_resumes(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
        html_content = _generate_resume_list_html(resumes, None)
        return HTMLResponse(content=html_content)

    return [ResumeResponse(id=resume.id, name=resume.name) for resume in resumes]


def _generate_resume_detail_html(resume: DatabaseResume) -> str:
    """
    Generate the HTML for the resume detail view.

    Args:
        resume (DatabaseResume): The resume object to generate HTML for.

    Returns:
        str: HTML string for the resume detail view.

    Notes:
        1. Creates HTML for the resume detail section with a header, content area, and footer.
        2. Includes buttons for refining with AI, exporting, and editing.
        3. Creates modal dialogs for export and refine actions with appropriate event handlers.
        4. Returns the complete HTML string.

    """
    return f"""
    <div class="h-full flex flex-col">
        <div class="flex justify-between items-center mb-4">
            <h2 class="text-xl font-semibold">{resume.name}</h2>
            <div class="flex space-x-2">
                <button
                    type="button"
                    onclick="document.getElementById('refine-modal-{resume.id}').classList.remove('hidden')"
                    class="bg-purple-500 hover:bg-purple-600 text-white px-3 py-1 rounded text-sm">
                    Refine with AI
                </button>
                 <button
                    type="button"
                    onclick="document.getElementById('export-modal-{resume.id}').classList.remove('hidden')"
                    class="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded text-sm">
                    Export
                </button>
                <button 
                    hx-get="/dashboard/edit-resume-form/{resume.id}"
                    hx-target="#resume-content" 
                    hx-swap="innerHTML"
                    class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm">
                    Edit
                </button>
            </div>
        </div>
        <div class="flex-grow">
            <textarea 
                readonly
                class="w-full h-96 px-3 py-2 border border-gray-300 rounded-md focus:outline-none font-mono text-sm resize-none"
                placeholder="Resume content will appear here...">{resume.content}</textarea>
        </div>
        <div class="mt-4 text-sm text-gray-500">
            <p>Resume ID: {resume.id}</p>
        </div>
        <div id="refine-result-container" class="mt-4"></div>
    </div>

    <!-- Export Modal -->
    <div id="export-modal-{resume.id}" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full hidden z-50">
        <div class="relative top-20 mx-auto p-5 border w-1/2 shadow-lg rounded-md bg-white">
            <div class="mt-3">
                <h3 class="text-lg leading-6 font-medium text-gray-900 text-center">Export Resume</h3>
                <div class="mt-2 px-7 py-3">
                    <div id="export-form-{resume.id}">
                        <p class="text-sm text-gray-600 mb-4">You can optionally filter the 'Experience' section by a date range.</p>
                        
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <label for="start_date_{resume.id}" class="block text-sm font-medium text-gray-700">Start Date</label>
                                <input type="date" name="start_date" id="start_date_{resume.id}" class="mt-1 p-2 border border-gray-300 rounded w-full">
                            </div>
                            <div>
                                <label for="end_date_{resume.id}" class="block text-sm font-medium text-gray-700">End Date</label>
                                <input type="date" name="end_date" id="end_date_{resume.id}" class="mt-1 p-2 border border-gray-300 rounded w-full">
                            </div>
                        </div>

                        <div class="mt-6 border-t pt-4">
                            <h4 class="font-medium text-gray-800 mb-2">Markdown</h4>
                            <button type="button" onclick="exportResume({resume.id}, 'markdown')" class="w-full px-4 py-2 bg-gray-600 text-white text-base font-medium rounded-md shadow-sm hover:bg-gray-700">
                                Export as Markdown
                            </button>
                        </div>

                        <div class="mt-4 border-t pt-4">
                            <h4 class="font-medium text-gray-800 mb-2">DOCX</h4>
                            <div class="grid grid-cols-3 gap-2">
                                 <button type="button" onclick="exportResume({resume.id}, 'docx', 'plain')" class="px-4 py-2 bg-indigo-500 text-white text-base font-medium rounded-md shadow-sm hover:bg-indigo-600">Plain</button>
                                 <button type="button" onclick="exportResume({resume.id}, 'docx', 'ats')" class="px-4 py-2 bg-indigo-500 text-white text-base font-medium rounded-md shadow-sm hover:bg-indigo-600">ATS</button>
                                 <button type="button" onclick="exportResume({resume.id}, 'docx', 'executive')" class="px-4 py-2 bg-indigo-500 text-white text-base font-medium rounded-md shadow-sm hover:bg-indigo-600">Executive</button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="px-7 pb-3">
                    <button
                        type="button"
                        onclick="document.getElementById('export-modal-{resume.id}').classList.add('hidden')"
                        class="w-full px-4 py-2 bg-gray-200 text-gray-800 text-base font-medium rounded-md shadow-sm hover:bg-gray-300">
                        Cancel
                    </button>
                </div>
            </div>
        </div>
    </div>
    <script>
    function exportResume(resumeId, type, format) {{
        const startDate = document.getElementById(`start_date_${{resumeId}}`).value;
        const endDate = document.getElementById(`end_date_${{resumeId}}`).value;
        
        let url = `/api/resumes/${{resumeId}}/export/${{type}}`;
        const params = new URLSearchParams();
        
        if (type === 'docx') {{
            params.append('format', format);
        }}
        if (startDate) {{
            params.append('start_date', startDate);
        }}
        if (endDate) {{
            params.append('end_date', endDate);
        }}
        
        if (params.toString()) {{
            url += '?' + params.toString();
        }}
        
        window.location.href = url;
        document.getElementById(`export-modal-${{resumeId}}`).classList.add('hidden');
    }}
    </script>

    <!-- Refine Modal -->
    <div id="refine-modal-{resume.id}" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full hidden z-50">
        <div class="relative top-20 mx-auto p-5 border w-1/2 shadow-lg rounded-md bg-white">
            <div class="mt-3">
                <h3 class="text-lg leading-6 font-medium text-gray-900 text-center">Refine Resume with Job Description</h3>
                <div class="mt-2 px-7 py-3">
                    <form id="refine-form-{resume.id}"
                          hx-post="/api/resumes/{resume.id}/refine"
                          hx-target="#refine-result-container"
                          hx-swap="innerHTML"
                          onsubmit="document.getElementById('refine-modal-{resume.id}').classList.add('hidden')">
                        
                        <label for="job_description" class="block text-sm font-medium text-gray-700">Job Description</label>
                        <textarea name="job_description" class="mt-1 w-full h-40 p-2 border border-gray-300 rounded" placeholder="Paste job description here..." required></textarea>
                        
                        <div class="mt-4">
                          <label for="target_section" class="block text-sm font-medium text-gray-700">Section to Refine</label>
                          <select name="target_section" id="target_section" class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md">
                              <option value="full">Full Resume</option>
                              <option value="personal">Personal</option>
                              <option value="education">Education</option>
                              <option value="experience">Experience</option>
                              <option value="certifications">Certifications</option>
                          </select>
                        </div>

                        <div class="mt-6">
                            <button type="submit" class="w-full px-4 py-2 bg-blue-500 text-white text-base font-medium rounded-md shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500">
                                Refine
                            </button>
                        </div>
                    </form>
                </div>
                
                <div class="px-7 pb-3">
                    <button
                        type="button"
                        onclick="document.getElementById('refine-modal-{resume.id}').classList.add('hidden')"
                        class="w-full px-4 py-2 bg-gray-200 text-gray-800 text-base font-medium rounded-md shadow-sm hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-300">
                        Cancel
                    </button>
                </div>
            </div>
        </div>
    </div>
    """


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
    # Check if this is an HTMX request
    if "HX-Request" in request.headers:
        html_content = _generate_resume_detail_html(resume)
        return HTMLResponse(content=html_content)

    return ResumeDetailResponse(
        id=resume.id,
        name=resume.name,
        content=resume.content,
    )


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


@router.get("/{resume_id}/export/docx")
async def export_resume_docx(
    format: DocxFormat,
    resume: DatabaseResume = Depends(get_resume_for_user),
    start_date: date | None = None,
    end_date: date | None = None,
):
    """
    Export a resume as a DOCX file in the specified format.

    Args:
        format (DocxFormat): The export format ('ats', 'plain', 'executive').
        resume (DatabaseResume): The resume object, injected by dependency.
        start_date (date | None): Optional start date to filter experience.
        end_date (date | None): Optional end date to filter experience.

    Returns:
        StreamingResponse: A streaming response with the generated DOCX file.

    Raises:
        HTTPException: If an invalid format is requested or if rendering fails.

    Notes:
        1. Fetches resume content from the database.
        2. If a date range is provided, filters the experience section before parsing.
        3. Parses the Markdown content into a `resume_writer` Resume object using `parse_resume_to_writer_object`.
        4. Initializes a new `docx.Document`.
        5. Initializes `ResumeRenderSettings`.
        6. Based on the requested format, calls the appropriate renderer from `resume_writer`.
            - For 'executive', enables `executive_summary` and `skills_matrix` in settings.
        7. Saves the generated document to a memory stream.
        8. Returns the stream as a downloadable file attachment.

    """
    _msg = f"export_resume_docx starting for format {format.value}"
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

        parsed_resume = parse_resume_to_writer_object(content_to_parse)
    except (ValueError, TypeError) as e:
        detail = getattr(e, "detail", str(e))
        _msg = (
            f"Failed to generate docx due to content parsing/filtering error: {detail}"
        )
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=_msg)

    # 2. Render to docx based on format
    document = Document()
    settings = ResumeRenderSettings(default_init=True)

    match format:
        case DocxFormat.ATS:
            ats_render(document, parsed_resume, settings)
        case DocxFormat.PLAIN:
            plain_render(document, parsed_resume, settings)
        case DocxFormat.EXECUTIVE:
            settings.executive_summary = True
            settings.skills_matrix = True
            basic_render(document, parsed_resume, settings)
        case _:
            # This should be caught by FastAPI's validation, but as a safeguard:
            raise HTTPException(status_code=400, detail="Invalid format specified")

    # 3. Save to memory stream and return
    file_stream = io.BytesIO()
    document.save(file_stream)
    file_stream.seek(0)

    headers = {
        "Content-Disposition": f'attachment; filename="{resume.name}_{format.value}.docx"',
    }
    return StreamingResponse(
        file_stream,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers=headers,
    )


@router.post("/{resume_id}/edit/personal")
async def update_personal_info(
    request: PersonalInfoUpdateRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    resume: DatabaseResume = Depends(get_resume_for_user),
):
    """
    Update personal information in a resume.

    Args:
        resume_id (int): The unique identifier of the resume to update.
        request (PersonalInfoUpdateRequest): The request containing updated personal information.
        http_request (Request): The HTTP request object.
        db (Session): The database session dependency.
        current_user (User): The current authenticated user.

    Returns:
        HTMLResponse: Updated resume content view.

    Raises:
        HTTPException: If the resume is not found or doesn't belong to the user.

    Notes:
        1. Queries the database for a resume with the given ID and user_id.
        2. If no resume is found, raises a 404 error.
        3. Updates the personal information section in the resume content.
        4. Commits the transaction to save the changes.
        5. Returns HTML for HTMX to update the resume content view.

    """
    try:
        updated_personal_info = PersonalInfoResponse(**request.model_dump())
        updated_content = update_resume_content_with_structured_data(
            current_content=resume.content,
            personal_info=updated_personal_info,
        )
        perform_pre_save_validation(updated_content, resume.content)
        updated_resume = update_resume_db(db, resume=resume, content=updated_content)
        return HTMLResponse(content=_generate_resume_detail_html(updated_resume))
    except (ValueError, TypeError, HTTPException) as e:
        detail = getattr(e, "detail", str(e))
        _msg = f"Failed to update personal info: {detail}"
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=_msg)


@router.post("/{resume_id}/edit/education")
async def update_education(
    http_request: Request,
    db: Session = Depends(get_db),
    resume: DatabaseResume = Depends(get_resume_for_user),
    school: str = Form(...),
    degree: str | None = Form(None),
    major: str | None = Form(None),
    start_date: str | None = Form(None),
    end_date: str | None = Form(None),
    gpa: str | None = Form(None),
):
    """
    Update education information in a resume.

    Args:
        http_request (Request): The HTTP request object.
        db (Session): The database session dependency.
        resume (DatabaseResume): The resume object from dependency injection.
        school (str): The school name.
        degree (str | None): The degree obtained.
        major (str | None): The major field of study.
        start_date (str | None): The start date of the degree in YYYY-MM-DD format.
        end_date (str | None): The end date of the degree in YYYY-MM-DD format.
        gpa (str | None): The grade point average.

    Returns:
        HTMLResponse: Updated resume content view for HTMX.

    Raises:
        HTTPException: If processing or validation fails.

    Notes:
        1. Parses form data to create a new `Degree` object.
        2. Appends the new degree to the existing education section.
        3. Reconstructs, validates, and saves the updated resume content.
        4. Returns an HTML partial of the updated resume view.

    """
    try:
        new_degree_data = {
            "school": school,
            "degree": degree,
            "major": major,
            "start_date": datetime.strptime(start_date, "%Y-%m-%d")
            if start_date
            else None,
            "end_date": datetime.strptime(end_date, "%Y-%m-%d") if end_date else None,
            "gpa": gpa,
        }
        new_degree = Degree(**new_degree_data)

        education_info = extract_education_info(resume.content)
        education_info.degrees.append(new_degree)

        updated_content = update_resume_content_with_structured_data(
            current_content=resume.content,
            education=education_info,
        )

        perform_pre_save_validation(updated_content, resume.content)
        updated_resume = update_resume_db(db, resume=resume, content=updated_content)

        return HTMLResponse(content=_generate_resume_detail_html(updated_resume))
    except (ValueError, TypeError, HTTPException) as e:
        detail = getattr(e, "detail", str(e))
        _msg = f"Failed to update education info: {detail}"
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=_msg)


@router.post("/{resume_id}/edit/experience")
async def update_experience(
    http_request: Request,
    db: Session = Depends(get_db),
    resume: DatabaseResume = Depends(get_resume_for_user),
    company: str = Form(...),
    title: str = Form(...),
    start_date: str = Form(...),
    end_date: str | None = Form(None),
    description: str | None = Form(None),
):
    """
    Update experience information in a resume.

    Args:
        http_request (Request): The HTTP request object.
        db (Session): The database session dependency.
        resume (DatabaseResume): The resume object from dependency injection.
        company (str): The company name.
        title (str): The job title.
        start_date (str): The start date of the role in YYYY-MM-DD format.
        end_date (str | None): The end date of the role in YYYY-MM-DD format.
        description (str | None): A summary of the role.

    Returns:
        HTMLResponse: Updated resume content view for HTMX.

    Raises:
        HTTPException: If processing or validation fails.

    Notes:
        1. Parses form data to create a new `Role` object.
        2. Appends the new role to the existing experience section.
        3. Reconstructs, validates, and saves the updated resume content.
        4. Returns an HTML partial of the updated resume view.

    """
    try:
        new_role_data = {
            "basics": {
                "company": company,
                "title": title,
                "start_date": datetime.strptime(start_date, "%Y-%m-%d"),
                "end_date": datetime.strptime(end_date, "%Y-%m-%d")
                if end_date
                else None,
            },
            "summary": {"text": description} if description else None,
        }
        new_role = Role.model_validate(new_role_data)

        experience_info = extract_experience_info(resume.content)
        experience_info.roles.append(new_role)

        updated_content = update_resume_content_with_structured_data(
            current_content=resume.content,
            experience=experience_info,
        )

        perform_pre_save_validation(updated_content, resume.content)
        updated_resume = update_resume_db(db, resume=resume, content=updated_content)

        return HTMLResponse(content=_generate_resume_detail_html(updated_resume))
    except (ValueError, TypeError, HTTPException) as e:
        detail = getattr(e, "detail", str(e))
        _msg = f"Failed to update experience info: {detail}"
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=_msg)


@router.post("/{resume_id}/edit/projects")
async def update_projects(
    http_request: Request,
    db: Session = Depends(get_db),
    resume: DatabaseResume = Depends(get_resume_for_user),
    title: str = Form(...),
    description: str = Form(...),
    url: str | None = Form(None),
    start_date: str | None = Form(None),
    end_date: str | None = Form(None),
):
    """
    Update projects information in a resume.

    Args:
        http_request (Request): The HTTP request object.
        db (Session): The database session dependency.
        resume (DatabaseResume): The resume object from dependency injection.
        title (str): The title of the project.
        description (str): A description of the project.
        url (str | None): A URL associated with the project.
        start_date (str | None): The start date of the project in YYYY-MM-DD format.
        end_date (str | None): The end date of the project in YYYY-MM-DD format.

    Returns:
        HTMLResponse: Updated resume content view for HTMX.

    Raises:
        HTTPException: If processing or validation fails.

    Notes:
        1. Parses form data to create a new `Project` object.
        2. Appends the new project to the existing experience section.
        3. Reconstructs, validates, and saves the updated resume content.
        4. Returns an HTML partial of the updated resume view.

    """
    try:
        new_project_data = {
            "overview": {
                "title": title,
                "url": url,
                "start_date": datetime.strptime(start_date, "%Y-%m-%d")
                if start_date
                else None,
                "end_date": datetime.strptime(end_date, "%Y-%m-%d")
                if end_date
                else None,
            },
            "description": {"text": description},
        }
        new_project = Project.model_validate(new_project_data)

        experience_info = extract_experience_info(resume.content)
        experience_info.projects.append(new_project)

        updated_content = update_resume_content_with_structured_data(
            current_content=resume.content,
            experience=experience_info,
        )

        perform_pre_save_validation(updated_content, resume.content)
        updated_resume = update_resume_db(db, resume=resume, content=updated_content)

        return HTMLResponse(content=_generate_resume_detail_html(updated_resume))
    except (ValueError, TypeError, HTTPException) as e:
        detail = getattr(e, "detail", str(e))
        _msg = f"Failed to update projects info: {detail}"
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=_msg)


@router.post("/{resume_id}/edit/certifications")
async def update_certifications(
    http_request: Request,
    db: Session = Depends(get_db),
    resume: DatabaseResume = Depends(get_resume_for_user),
    name: str = Form(...),
    issuer: str | None = Form(None),
    certification_id: str | None = Form(None, alias="id"),
    issued_date: str | None = Form(None),
    expiry_date: str | None = Form(None),
):
    """
    Update certifications information in a resume.

    Args:
        http_request (Request): The HTTP request object.
        db (Session): The database session dependency.
        resume (DatabaseResume): The resume object from dependency injection.
        name (str): The name of the certification.
        issuer (str | None): The issuing organization.
        certification_id (str | None): The ID of the certification (form field name 'id').
        issued_date (str | None): The date the certification was issued in YYYY-MM-DD format.
        expiry_date (str | None): The date the certification expires in YYYY-MM-DD format.

    Returns:
        HTMLResponse: Updated resume content view for HTMX.

    Raises:
        HTTPException: If processing or validation fails.

    Notes:
        1. Parses form data to create a new `Certification` object.
        2. Appends the new certification to the existing certifications section.
        3. Reconstructs, validates, and saves the updated resume content.
        4. Returns an HTML partial of the updated resume view.

    """
    try:
        new_cert_data = {
            "name": name,
            "issuer": issuer,
            "certification_id": certification_id,
            "issued": datetime.strptime(issued_date, "%Y-%m-%d")
            if issued_date
            else None,
            "expires": datetime.strptime(expiry_date, "%Y-%m-%d")
            if expiry_date
            else None,
        }
        new_cert = Certification.model_validate(new_cert_data)

        certifications_info = extract_certifications_info(resume.content)
        certifications_info.certifications.append(new_cert)

        updated_content = update_resume_content_with_structured_data(
            current_content=resume.content,
            certifications=certifications_info,
        )

        perform_pre_save_validation(updated_content, resume.content)
        updated_resume = update_resume_db(db, resume=resume, content=updated_content)

        return HTMLResponse(content=_generate_resume_detail_html(updated_resume))
    except (ValueError, TypeError, HTTPException) as e:
        detail = getattr(e, "detail", str(e))
        _msg = f"Failed to update certifications info: {detail}"
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=_msg)


@router.get("/{resume_id}/personal", response_model=PersonalInfoResponse)
async def get_personal_info(
    resume: DatabaseResume = Depends(get_resume_for_user),
):
    """
    Get personal information from a resume.

    Args:
        resume_id: The ID of the resume.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        PersonalInfoResponse: The personal information from the resume.

    Raises:
        HTTPException: If the resume is not found.

    Notes:
        1. Queries the database for a resume with the given ID and user_id.
        2. If no resume is found, raises a 404 error.
        3. Extracts personal information from the resume content using extract_personal_info.
        4. Returns the personal information as a PersonalInfoResponse.
        5. Performs database access: Reads from the database via db.query.
        6. Performs network access: None.

    """
    return extract_personal_info(resume.content)


@router.put("/{resume_id}/personal", response_model=PersonalInfoResponse)
async def update_personal_info_structured(
    request: PersonalInfoUpdateRequest,
    db: Session = Depends(get_db),
    resume: DatabaseResume = Depends(get_resume_for_user),
):
    """
    Update personal information in a resume.

    Args:
        resume_id: The ID of the resume.
        request: The updated personal information.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        PersonalInfoResponse: The updated personal information.

    Raises:
        HTTPException: If the resume is not found.

    Notes:
        1. Queries the database for a resume with the given ID and user_id.
        2. If no resume is found, raises a 404 error.
        3. Creates an updated personal info object with the provided data.
        4. Extracts other sections from the resume, then reconstructs the full Markdown with the updated personal info.
        5. Performs pre-save validation on the updated content.
        6. Saves the updated content to the database.
        7. Returns the updated personal information.
        8. This function performs database read and write operations.

    """
    try:
        # Create updated personal info object
        updated_info = PersonalInfoResponse(**request.model_dump())

        # Reconstruct resume with updated personal info
        updated_content = update_resume_content_with_structured_data(
            current_content=resume.content,
            personal_info=updated_info,
        )

        # Perform pre-save validation
        perform_pre_save_validation(updated_content, resume.content)

        # Save updated content to database
        update_resume_db(db, resume, content=updated_content)

        return updated_info
    except (ValueError, TypeError, HTTPException) as e:
        detail = getattr(e, "detail", str(e))
        _msg = (
            f"Failed to update resume due to reconstruction/validation error: {detail}"
        )
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=_msg)


@router.get("/{resume_id}/education", response_model=EducationResponse)
async def get_education_info(
    resume: DatabaseResume = Depends(get_resume_for_user),
):
    """
    Get education information from a resume.

    Args:
        resume_id: The ID of the resume.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        EducationResponse: The education information from the resume.

    Raises:
        HTTPException: If the resume is not found.

    Notes:
        1. Queries the database for a resume with the given ID and user_id.
        2. If no resume is found, raises a 404 error.
        3. Extracts education information from the resume content using extract_education_info.
        4. Returns the education information as an EducationResponse.
        5. Performs database access: Reads from the database via db.query.
        6. Performs network access: None.

    """
    return extract_education_info(resume.content)


@router.put("/{resume_id}/education", response_model=EducationResponse)
async def update_education_info_structured(
    request: EducationUpdateRequest,
    db: Session = Depends(get_db),
    resume: DatabaseResume = Depends(get_resume_for_user),
):
    """
    Update education information in a resume.

    Args:
        resume_id: The ID of the resume.
        request: The updated education information.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        EducationResponse: The updated education information.

    Raises:
        HTTPException: If the resume is not found.

    Notes:
        1. Queries the database for a resume with the given ID and user_id.
        2. If no resume is found, raises a 404 error.
        3. Creates an updated education info object with the provided data.
        4. Extracts other sections from the resume, then reconstructs the full Markdown with the updated education info.
        5. Performs pre-save validation on the updated content.
        6. Saves the updated content to the database.
        7. Returns the updated education information.
        8. This function performs database read and write operations.

    """
    try:
        # Create updated education info object
        updated_info = EducationResponse(**request.model_dump())

        # Reconstruct resume with updated education info
        updated_content = update_resume_content_with_structured_data(
            current_content=resume.content,
            education=updated_info,
        )

        # Perform pre-save validation
        perform_pre_save_validation(updated_content, resume.content)

        # Save updated content to database
        update_resume_db(db, resume, content=updated_content)

        return updated_info
    except (ValueError, TypeError, HTTPException) as e:
        detail = getattr(e, "detail", str(e))
        _msg = (
            f"Failed to update resume due to reconstruction/validation error: {detail}"
        )
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=_msg)


@router.get("/{resume_id}/experience", response_model=ExperienceResponse)
async def get_experience_info(
    resume: DatabaseResume = Depends(get_resume_for_user),
):
    """
    Get experience information from a resume.

    Args:
        resume_id: The ID of the resume.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        ExperienceResponse: The experience information from the resume.

    Raises:
        HTTPException: If the resume is not found.

    Notes:
        1. Queries the database for a resume with the given ID and user_id.
        2. If no resume is found, raises a 404 error.
        3. Extracts experience information from the resume content using extract_experience_info.
        4. Returns the experience information as an ExperienceResponse.
        5. Performs database access: Reads from the database via db.query.
        6. Performs network access: None.

    """
    return extract_experience_info(resume.content)


@router.put("/{resume_id}/experience", response_model=ExperienceResponse)
async def update_experience_info_structured(
    request: ExperienceUpdateRequest,
    db: Session = Depends(get_db),
    resume: DatabaseResume = Depends(get_resume_for_user),
):
    """
    Update experience information in a resume.

    Args:
        resume_id: The ID of the resume.
        request: The updated experience information.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        ExperienceResponse: The updated experience information.

    Raises:
        HTTPException: If the resume is not found.

    Notes:
        1. Queries the database for a resume with the given ID and user_id.
        2. If no resume is found, raises a 404 error.
        3. Creates an updated experience info object with the provided data.
        4. Extracts other sections from the resume, then reconstructs the full Markdown with the updated experience section.
        5. Performs pre-save validation on the updated content.
        6. Saves the updated content to the database.
        7. Returns the updated experience information.
        8. This function performs database read and write operations.

    """
    try:
        # Create updated experience object, using new data if provided, else current
        current_experience = extract_experience_info(resume.content)
        updated_experience = ExperienceResponse(
            roles=request.roles
            if request.roles is not None
            else current_experience.roles,
            projects=(
                request.projects
                if request.projects is not None
                else current_experience.projects
            ),
        )

        # Reconstruct the resume content with the updated experience section
        updated_content = update_resume_content_with_structured_data(
            current_content=resume.content,
            experience=updated_experience,
        )

        # Perform pre-save validation
        perform_pre_save_validation(updated_content, resume.content)

        # Save updated content to database
        update_resume_db(db, resume, content=updated_content)

        return updated_experience
    except (ValueError, TypeError, HTTPException) as e:
        detail = getattr(e, "detail", str(e))
        _msg = (
            f"Failed to update resume due to reconstruction/validation error: {detail}"
        )
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=_msg)


@router.get("/{resume_id}/projects", response_model=ProjectsResponse)
async def get_projects_info(
    resume: DatabaseResume = Depends(get_resume_for_user),
):
    """
    Get projects information from a resume.

    Args:
        resume_id: The ID of the resume.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        ProjectsResponse: The projects information from the resume.

    Raises:
        HTTPException: If the resume is not found.

    Notes:
        1. Queries the database for a resume with the given ID and user_id.
        2. If no resume is found, raises a 404 error.
        3. Extracts experience information (which includes projects) from the resume content.
        4. Returns the projects information as a ProjectsResponse.
        5. Performs database access: Reads from the database via db.query.
        6. Performs network access: None.

    """
    experience = extract_experience_info(resume.content)
    return ProjectsResponse(projects=experience.projects)


@router.put("/{resume_id}/projects", response_model=ProjectsResponse)
async def update_projects_info_structured(
    request: ExperienceUpdateRequest,
    db: Session = Depends(get_db),
    resume: DatabaseResume = Depends(get_resume_for_user),
):
    """
    Update projects information in a resume.

    Args:
        resume_id: The ID of the resume.
        request: The updated projects information.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        ProjectsResponse: The updated projects information.

    Raises:
        HTTPException: If the resume is not found.

    Notes:
        1. Queries the database for a resume with the given ID and user_id.
        2. If no resume is found, raises a 404 error.
        3. Creates an updated projects info object with the provided data.
        4. Extracts other sections from the resume, then reconstructs the full Markdown with the new projects information.
        5. Performs pre-save validation on the updated content.
        6. Saves the updated content to the database.
        7. Returns the updated projects information.
        8. This function performs database read and write operations.

    """
    try:
        projects_to_update = request.projects or []
        updated_projects = ProjectsResponse(projects=projects_to_update)

        current_experience = extract_experience_info(resume.content)

        # To update only projects, we need to preserve roles from the current experience.
        experience_with_updated_projects = ExperienceResponse(
            roles=current_experience.roles,
            projects=projects_to_update,
        )

        updated_content = update_resume_content_with_structured_data(
            current_content=resume.content,
            experience=experience_with_updated_projects,
        )

        perform_pre_save_validation(updated_content, resume.content)

        update_resume_db(db, resume, content=updated_content)

        return updated_projects
    except (ValueError, TypeError, HTTPException) as e:
        detail = getattr(e, "detail", str(e))
        _msg = (
            f"Failed to update resume due to reconstruction/validation error: {detail}"
        )
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=_msg)


@router.get("/{resume_id}/certifications", response_model=CertificationsResponse)
async def get_certifications_info(
    resume: DatabaseResume = Depends(get_resume_for_user),
):
    """
    Get certifications information from a resume.

    Args:
        resume_id: The ID of the resume.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        CertificationsResponse: The certifications information from the resume.

    Raises:
        HTTPException: If the resume is not found.

    Notes:
        1. Queries the database for a resume with the given ID and user_id.
        2. If no resume is found, raises a 404 error.
        3. Extracts certifications information from the resume content using extract_certifications_info.
        4. Returns the certifications information as a CertificationsResponse.
        5. Performs database access: Reads from the database via db.query.
        6. Performs network access: None.

    """
    return extract_certifications_info(resume.content)


@router.put("/{resume_id}/certifications", response_model=CertificationsResponse)
async def update_certifications_info_structured(
    request: CertificationUpdateRequest,
    db: Session = Depends(get_db),
    resume: DatabaseResume = Depends(get_resume_for_user),
):
    """
    Update certifications information in a resume.

    Args:
        resume_id: The ID of the resume.
        request: The updated certifications information.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        CertificationsResponse: The updated certifications information.

    Raises:
        HTTPException: If the resume is not found.

    Notes:
        1. Queries the database for a resume with the given ID and user_id.
        2. If no resume is found, raises a 404 error.
        3. Creates an updated certifications info object with the provided data.
        4. Extracts other sections from the resume, then reconstructs the full Markdown with updated certifications information.
        5. Performs pre-save validation on the updated content.
        6. Saves the updated content to the database.
        7. Returns the updated certifications information.
        8. This function performs database read and write operations.

    """
    try:
        updated_certifications = CertificationsResponse(
            certifications=request.certifications,
        )

        # Reconstruct resume with updated certifications
        updated_content = update_resume_content_with_structured_data(
            current_content=resume.content,
            certifications=updated_certifications,
        )

        perform_pre_save_validation(updated_content, resume.content)

        update_resume_db(db, resume, content=updated_content)

        return updated_certifications
    except (ValueError, TypeError, HTTPException) as e:
        detail = getattr(e, "detail", str(e))
        _msg = (
            f"Failed to update resume due to reconstruction/validation error: {detail}"
        )
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=_msg)


@router.post("/{resume_id}/refine", response_model=RefineResponse)
async def refine_resume(
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    resume: DatabaseResume = Depends(get_resume_for_user),
    job_description: str = Form(...),
    target_section: RefineTargetSection = Form(...),
):
    """
    Refine a resume section using an LLM to align with a job description.

    Args:
        http_request (Request): The HTTP request object to check for HTMX headers.
        db (Session): The database session dependency.
        current_user (User): The current authenticated user.
        resume (DatabaseResume): The resume to be refined.
        job_description (str): The job description to align the resume with.
        target_section (RefineTargetSection): The section of the resume to refine.

    Returns:
        RefineResponse | HTMLResponse: The LLM's refined content as Markdown, or an HTML partial for HTMX.

    Notes:
        1. Fetches the user's settings, including the custom LLM endpoint and encrypted API key.
        2. Decrypts the API key if it exists.
        3. Delegates to the `refine_resume_section_with_llm` function to perform the refinement.
        4. If the request is from HTMX, returns an HTML partial with the suggestion and action buttons.
        5. Otherwise, returns the refined content in a `RefineResponse`.
        6. This function performs database reads to get user settings.
        7. This function performs network access to call the LLM.

    """
    _msg = f"Refining resume {resume.id} for section {target_section.value}"
    log.debug(_msg)

    try:
        settings = get_user_settings(db, current_user.id)

        llm_endpoint = settings.llm_endpoint if settings else None
        api_key = None
        if settings and settings.encrypted_api_key:
            api_key = decrypt_data(settings.encrypted_api_key)

        refined_content = refine_resume_section_with_llm(
            resume_content=resume.content,
            job_description=job_description,
            target_section=target_section.value,
            llm_endpoint=llm_endpoint,
            api_key=api_key,
        )

        if "HX-Request" in http_request.headers:
            target_section_val = target_section.value
            html_content = f"""
            <div id="refine-result" class="mt-4 p-4 border rounded-lg bg-gray-50">
                <h4 class="font-semibold text-lg mb-2">AI Refinement Suggestion</h4>
                <p class="text-sm text-gray-600 mb-2">Review the suggestion for the '{target_section_val}' section.</p>
                <form 
                    hx-post="/api/resumes/{resume.id}/refine/accept"
                    hx-target="#left-sidebar-content" 
                    hx-swap="innerHTML">
                    <input type="hidden" name="target_section" value="{target_section_val}">
                    <textarea name="refined_content" class="w-full h-48 p-2 border rounded font-mono text-sm">{html.escape(refined_content)}</textarea>
                    <div class="mt-4 flex items-center justify-between">
                        <div>
                            <button type="submit" name="action" value="overwrite" class="bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600">
                                Accept & Overwrite
                            </button>
                            <button type="button" onclick="this.closest('#refine-result').remove()" class="bg-gray-500 text-white px-3 py-1 rounded text-sm hover:bg-gray-600 ml-2">
                                Reject
                            </button>
                        </div>
                        <div class="flex items-center">
                            <input type="text" name="new_resume_name" placeholder="Name for new resume" class="border rounded px-2 py-1 text-sm">
                            <button type="submit" name="action" value="save_as_new" class="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600 ml-2">
                                Save as New
                            </button>
                        </div>
                    </div>
                </form>
            </div>
            """
            return HTMLResponse(content=html_content)

        return RefineResponse(refined_content=refined_content)
    except InvalidToken:
        _msg = f"API key decryption failed for user {current_user.id}"
        log.warning(_msg)
        raise HTTPException(
            status_code=400,
            detail="Invalid API key. Please update your settings.",
        )
    except Exception as e:
        _msg = f"LLM refinement failed for resume {resume.id}: {e!s}"
        log.exception(_msg)
        raise HTTPException(status_code=500, detail=f"LLM refinement failed: {e!s}")


@router.post("/{resume_id}/refine/accept", response_class=HTMLResponse)
async def accept_refined_resume(
    resume: DatabaseResume = Depends(get_resume_for_user),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    refined_content: str = Form(...),
    target_section: RefineTargetSection = Form(...),
    action: RefineAction = Form(...),
    new_resume_name: str | None = Form(None),
):
    """
    Accept a refined resume section and persist the changes.

    Args:
        resume (DatabaseResume): The original resume being modified.
        db (Session): The database session.
        current_user (User): The current authenticated user.
        refined_content (str): The refined markdown from the LLM.
        target_section (RefineTargetSection): The section that was refined.
        action (RefineAction): The action to take (overwrite or save as new).
        new_resume_name (str | None): The name for the new resume if saving as new.

    Returns:
        HTMLResponse: An HTML partial containing the updated list of resumes.

    """
    if action == RefineAction.SAVE_AS_NEW and not new_resume_name:
        raise HTTPException(
            status_code=400,
            detail="New resume name is required for 'save as new' action.",
        )

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

    newly_selected_id = resume.id
    if action == RefineAction.OVERWRITE:
        update_resume_db(db=db, resume=resume, content=updated_content)
    else:  # This must be RefineAction.SAVE_AS_NEW
        new_resume = create_resume_db(
            db=db,
            user_id=current_user.id,
            name=new_resume_name,
            content=updated_content,
        )
        newly_selected_id = new_resume.id

    resumes = get_user_resumes(db, current_user.id)
    html_content = _generate_resume_list_html(resumes, newly_selected_id)
    return HTMLResponse(content=html_content)
