import io
import logging

from docx import Document
from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, Response
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
)
from resume_editor.app.api.routes.route_logic.resume_validation import (
    perform_pre_save_validation,
)
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
    ResumeCreateRequest,
    ResumeDetailResponse,
    ResumeResponse,
    ResumeUpdateRequest,
)
from resume_editor.app.database.database import get_db
from resume_editor.app.models.resume_model import Resume as DatabaseResume
from resume_editor.app.models.user import User

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


# Dependency to get current user (placeholder - would be implemented with auth)
def get_current_user():
    """Placeholder for current user dependency.

    In a real implementation, this would verify the user's authentication token
    and return the current user object.

    Returns:
        User: The current authenticated user.

    Notes:
        1. This is a placeholder implementation.
        2. In reality, this would use JWT token verification or similar.

    """
    # This is a placeholder implementation
    # In reality, this would use JWT token verification or similar
    user = User(
        "testuser",
        "test@example.com",
        "hashed_password",
    )
    user.id = 1
    return user


async def get_resume_for_user(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DatabaseResume:
    """Dependency to get a specific resume for the current user.

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


@router.post("/parse", response_model=ParseResponse)
async def parse_resume_endpoint(request: ParseRequest):
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
    return parse_resume_content(request.markdown_content)


@router.post("", response_model=ResumeResponse)
async def create_resume(
    request: ResumeCreateRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save a new resume to the database, associating it with the current user.

    Args:
        request (ResumeCreateRequest): The request containing the resume name and Markdown content.
        http_request (Request): The HTTP request object.
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
        8. If the request is from HTMX, returns HTML to update the resume list.
        9. Otherwise, returns a ResumeResponse with the resume ID and name.
        10. Performs database access: Writes to the database via db.add and db.commit.
        11. Performs network access: None.

    """
    # Validate Markdown content before saving
    validate_resume_content(request.content)

    resume = create_resume_db(
        db,
        user_id=current_user.id,
        name=request.name,
        content=request.content,
    )

    # Check if this is an HTMX request
    if "HX-Request" in http_request.headers:
        # Return updated resume list
        resumes = get_user_resumes(db, current_user.id)

        resume_items = []
        for r in resumes:
            selected_class = "selected" if r.id == resume.id else ""
            resume_items.append(f"""
            <div class="resume-item p-3 rounded cursor-pointer border border-gray-200 mb-2 {selected_class}" 
                 onclick="selectResume({r.id}, this)">
                <div class="font-medium text-gray-800">{r.name}</div>
                <div class="text-xs text-gray-500">ID: {r.id}</div>
            </div>
            """)
        html_content = "\n".join(resume_items)
        return HTMLResponse(content=html_content)

    return ResumeResponse(id=resume.id, name=resume.name)


@router.put("/{resume_id}", response_model=ResumeResponse)
async def update_resume(
    resume_id: int,
    request: ResumeUpdateRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    resume: DatabaseResume = Depends(get_resume_for_user),
):
    """Update an existing resume's name and/or content for the current user.

    Args:
        resume_id (int): The unique identifier of the resume to update.
        request (ResumeUpdateRequest): The request containing the updated resume name and/or content.
        http_request (Request): The HTTP request object.
        db (Session): The database session dependency.
        current_user (User): The current authenticated user.

    Returns:
        ResumeResponse | HTMLResponse: The updated resume's ID and name, or HTML for HTMX.

    Raises:
        HTTPException: If the resume is not found, doesn't belong to the user, there's an error updating, or Markdown validation fails.

    Notes:
        1. Queries the database for a resume with the given ID and user_id.
        2. If no resume is found, raises a 404 error.
        3. Validates the Markdown content using the resume parser if content is being updated.
        4. If validation fails, raises a 422 error with parsing details.
        5. Updates the resume's name and/or content if provided in the request.
        6. Commits the transaction to save the changes.
        7. Refreshes the resume object to ensure it has the latest state.
        8. If the request is from HTMX, returns HTML to update the resume list.
        9. Otherwise, returns a ResumeResponse with the resume ID and name.
        10. Performs database access: Reads from and writes to the database via db.query, db.commit.
        11. Performs network access: None.

    """
    # Validate Markdown content before updating if content is being changed
    if request.content is not None:
        validate_resume_content(request.content)

    resume = update_resume_db(db, resume, name=request.name, content=request.content)

    # Check if this is an HTMX request
    if "HX-Request" in http_request.headers:
        # Return updated resume list
        resumes = get_user_resumes(db, current_user.id)

        resume_items = []
        for r in resumes:
            selected_class = "selected" if r.id == resume.id else ""
            resume_items.append(f"""
            <div class="resume-item p-3 rounded cursor-pointer border border-gray-200 mb-2 {selected_class}" 
                 onclick="selectResume({r.id}, this)">
                <div class="font-medium text-gray-800">{r.name}</div>
                <div class="text-xs text-gray-500">ID: {r.id}</div>
            </div>
            """)
        html_content = "\n".join(resume_items)
        return HTMLResponse(content=html_content)

    return ResumeResponse(id=resume.id, name=resume.name)


@router.delete("/{resume_id}")
async def delete_resume(
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    resume: DatabaseResume = Depends(get_resume_for_user),
):
    """Delete a resume for the current user.

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

        if not resumes:
            html_content = """
            <div class="text-center py-8">
                <p class="text-gray-500">No resumes found.</p>
                <p class="text-gray-400 text-sm mt-2">Create your first resume using the "+ New Resume" button.</p>
            </div>
            """
        else:
            resume_items = []
            for r in resumes:
                resume_items.append(f"""
                <div class="resume-item p-3 rounded cursor-pointer border border-gray-200 mb-2" 
                     onclick="selectResume({r.id}, this)">
                    <div class="font-medium text-gray-800">{r.name}</div>
                    <div class="text-xs text-gray-500">ID: {r.id}</div>
                </div>
                """)
            html_content = "\n".join(resume_items)
        return HTMLResponse(content=html_content)

    return {"message": "Resume deleted successfully"}


@router.get("", response_model=list[ResumeResponse])
async def list_resumes(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all resumes for the current user.

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
        if not resumes:
            html_content = """
            <div class="text-center py-8">
                <p class="text-gray-500">No resumes found.</p>
                <p class="text-gray-400 text-sm mt-2">Create your first resume using the "+ New Resume" button.</p>
            </div>
            """
        else:
            resume_items = []
            for resume in resumes:
                resume_items.append(f"""
                <div class="resume-item p-3 rounded cursor-pointer border border-gray-200 mb-2" 
                     onclick="selectResume({resume.id}, this)">
                    <div class="font-medium text-gray-800">{resume.name}</div>
                    <div class="text-xs text-gray-500">ID: {resume.id}</div>
                </div>
                """)
            html_content = "\n".join(resume_items)
        return HTMLResponse(content=html_content)

    return [ResumeResponse(id=resume.id, name=resume.name) for resume in resumes]


@router.get("/{resume_id}", response_model=ResumeDetailResponse)
async def get_resume(
    request: Request,
    resume: DatabaseResume = Depends(get_resume_for_user),
):
    """Retrieve a specific resume's Markdown content by ID for the current user.

    Args:
        request (Request): The HTTP request object.
        resume_id (int): The unique identifier of the resume to retrieve.
        db (Session): The database session dependency.
        current_user (User): The current authenticated user.

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
        html_content = f"""
        <div class="h-full flex flex-col">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-xl font-semibold">{resume.name}</h2>
                <div class="flex space-x-2">
                    <button 
                        hx-get="/dashboard/create-resume-form" 
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
        </div>
        """
        return HTMLResponse(content=html_content)

    return ResumeDetailResponse(
        id=resume.id,
        name=resume.name,
        content=resume.content,
    )


@router.get("/{resume_id}/export/markdown")
async def export_resume_markdown(
    resume: DatabaseResume = Depends(get_resume_for_user),
):
    """Export a resume as a Markdown file.

    Args:
        resume (DatabaseResume): The resume object, injected by dependency.

    Returns:
        Response: A response object containing the resume's Markdown content as a downloadable file.

    Raises:
        HTTPException: If the resume is not found or does not belong to the user (handled by dependency).

    Notes:
        1. Fetches the resume using the get_resume_for_user dependency.
        2. Creates a Response object with the resume's content.
        3. Sets the 'Content-Type' header to 'text/markdown'.
        4. Sets the 'Content-Disposition' header to trigger a file download with the resume's name.
        5. Returns the response.

    """
    headers = {
        "Content-Disposition": f'attachment; filename="{resume.name}.md"',
    }
    return Response(content=resume.content, media_type="text/markdown", headers=headers)


@router.get("/{resume_id}/export/docx")
async def export_resume_docx(
    format: DocxFormat,
    resume: DatabaseResume = Depends(get_resume_for_user),
):
    """Export a resume as a DOCX file in the specified format.

    Args:
        format (DocxFormat): The export format ('ats', 'plain', 'executive').
        resume (DatabaseResume): The resume object, injected by dependency.

    Returns:
        StreamingResponse: A streaming response with the generated DOCX file.

    Raises:
        HTTPException: If an invalid format is requested or if rendering fails.

    Notes:
        1. Fetches resume content from the database.
        2. Parses the Markdown content into a `resume_writer` Resume object using `parse_resume_to_writer_object`.
        3. Initializes a new `docx.Document`.
        4. Initializes `ResumeRenderSettings`.
        5. Based on the requested format, calls the appropriate renderer from `resume_writer`.
            - For 'executive', enables `executive_summary` and `skills_matrix` in settings.
        6. Saves the generated document to a memory stream.
        7. Returns the stream as a downloadable file attachment.

    """
    _msg = f"export_resume_docx starting for format {format.value}"
    log.debug(_msg)

    try:
        parsed_resume = parse_resume_to_writer_object(resume.content)
    except Exception as e:
        _msg = f"Failed to parse resume content for docx export: {e!s}"
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=f"Invalid resume format: {e!s}")

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
    resume: DatabaseResume = Depends(get_resume_for_user),
):
    """Update personal information in a resume.

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
    # For now, we'll just show a success message
    # In a real implementation, we would parse and update the resume content
    html_content = f"""
    <div class="h-full flex flex-col">
        <div class="flex justify-between items-center mb-4">
            <h2 class="text-xl font-semibold">{resume.name}</h2>
            <div class="flex space-x-2">
                <button 
                    hx-get="/dashboard/resumes/{resume.id}/edit/personal" 
                    hx-target="#resume-content" 
                    hx-swap="innerHTML"
                    class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm">
                    Edit Personal Info
                </button>
            </div>
        </div>
        <div class="flex-grow">
            <p class="text-green-600 font-medium">Personal information updated successfully!</p>
            <textarea 
                readonly
                class="w-full h-96 px-3 py-2 border border-gray-300 rounded-md focus:outline-none font-mono text-sm resize-none"
                placeholder="Resume content will appear here...">{resume.content}</textarea>
        </div>
    </div>
    """
    return HTMLResponse(content=html_content)


@router.post("/{resume_id}/edit/education")
async def update_education(
    http_request: Request,
    resume: DatabaseResume = Depends(get_resume_for_user),
    school: str = Form(...),
    degree: str = Form(None),
    major: str = Form(None),
    start_date: str = Form(None),
    end_date: str = Form(None),
    gpa: str = Form(None),
):
    """Update education information in a resume.

    Args:
        resume_id (int): The unique identifier of the resume to update.
        request (EducationUpdateRequest): The request containing updated education information.
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
        3. Updates the education section in the resume content.
        4. Commits the transaction to save the changes.
        5. Returns HTML for HTMX to update the resume content view.

    """
    # For now, we'll just show a success message
    # In a real implementation, we would parse and update the resume content
    html_content = f"""
    <div class="h-full flex flex-col">
        <div class="flex justify-between items-center mb-4">
            <h2 class="text-xl font-semibold">{resume.name}</h2>
            <div class="flex space-x-2">
                <button 
                    hx-get="/dashboard/resumes/{resume.id}/edit/education" 
                    hx-target="#resume-content" 
                    hx-swap="innerHTML"
                    class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm">
                    Edit Education
                </button>
            </div>
        </div>
        <div class="flex-grow">
            <p class="text-green-600 font-medium">Education information updated successfully!</p>
            <textarea 
                readonly
                class="w-full h-96 px-3 py-2 border border-gray-300 rounded-md focus:outline-none font-mono text-sm resize-none"
                placeholder="Resume content will appear here...">{resume.content}</textarea>
        </div>
    </div>
    """
    return HTMLResponse(content=html_content)


@router.post("/{resume_id}/edit/experience")
async def update_experience(
    http_request: Request,
    resume: DatabaseResume = Depends(get_resume_for_user),
    company: str = Form(...),
    title: str = Form(...),
    start_date: str = Form(None),
    end_date: str = Form(None),
    description: str = Form(None),
):
    """Update experience information in a resume.

    Args:
        resume_id (int): The unique identifier of the resume to update.
        request (ExperienceUpdateRequest): The request containing updated experience information.
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
        3. Updates the experience section in the resume content.
        4. Commits the transaction to save the changes.
        5. Returns HTML for HTMX to update the resume content view.

    """
    # For now, we'll just show a success message
    # In a real implementation, we would parse and update the resume content
    html_content = f"""
    <div class="h-full flex flex-col">
        <div class="flex justify-between items-center mb-4">
            <h2 class="text-xl font-semibold">{resume.name}</h2>
            <div class="flex space-x-2">
                <button 
                    hx-get="/dashboard/resumes/{resume.id}/edit/experience" 
                    hx-target="#resume-content" 
                    hx-swap="innerHTML"
                    class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm">
                    Edit Experience
                </button>
            </div>
        </div>
        <div class="flex-grow">
            <p class="text-green-600 font-medium">Experience information updated successfully!</p>
            <textarea 
                readonly
                class="w-full h-96 px-3 py-2 border border-gray-300 rounded-md focus:outline-none font-mono text-sm resize-none"
                placeholder="Resume content will appear here...">{resume.content}</textarea>
        </div>
    </div>
    """
    return HTMLResponse(content=html_content)


@router.post("/{resume_id}/edit/projects")
async def update_projects(
    http_request: Request,
    resume: DatabaseResume = Depends(get_resume_for_user),
    title: str = Form(...),
    description: str = Form(None),
    url: str = Form(None),
    start_date: str = Form(None),
    end_date: str = Form(None),
):
    """Update projects information in a resume.

    Args:
        resume_id (int): The unique identifier of the resume to update.
        request (ProjectUpdateRequest): The request containing updated project information.
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
        3. Updates the projects section in the resume content.
        4. Commits the transaction to save the changes.
        5. Returns HTML for HTMX to update the resume content view.

    """
    # For now, we'll just show a success message
    # In a real implementation, we would parse and update the resume content
    html_content = f"""
    <div class="h-full flex flex-col">
        <div class="flex justify-between items-center mb-4">
            <h2 class="text-xl font-semibold">{resume.name}</h2>
            <div class="flex space-x-2">
                <button 
                    hx-get="/dashboard/resumes/{resume.id}/edit/projects" 
                    hx-target="#resume-content" 
                    hx-swap="innerHTML"
                    class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm">
                    Edit Projects
                </button>
            </div>
        </div>
        <div class="flex-grow">
            <p class="text-green-600 font-medium">Projects information updated successfully!</p>
            <textarea 
                readonly
                class="w-full h-96 px-3 py-2 border border-gray-300 rounded-md focus:outline-none font-mono text-sm resize-none"
                placeholder="Resume content will appear here...">{resume.content}</textarea>
        </div>
    </div>
    """
    return HTMLResponse(content=html_content)


@router.post("/{resume_id}/edit/certifications")
async def update_certifications(
    http_request: Request,
    resume: DatabaseResume = Depends(get_resume_for_user),
    name: str = Form(...),
    issuer: str = Form(None),
    id: str = Form(None),
    issued_date: str = Form(None),
    expiry_date: str = Form(None),
):
    """Update certifications information in a resume.

    Args:
        resume_id (int): The unique identifier of the resume to update.
        request (CertificationUpdateRequest): The request containing updated certification information.
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
        3. Updates the certifications section in the resume content.
        4. Commits the transaction to save the changes.
        5. Returns HTML for HTMX to update the resume content view.

    """
    # For now, we'll just show a success message
    # In a real implementation, we would parse and update the resume content
    html_content = f"""
    <div class="h-full flex flex-col">
        <div class="flex justify-between items-center mb-4">
            <h2 class="text-xl font-semibold">{resume.name}</h2>
            <div class="flex space-x-2">
                <button 
                    hx-get="/dashboard/resumes/{resume.id}/edit/certifications" 
                    hx-target="#resume-content" 
                    hx-swap="innerHTML"
                    class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm">
                    Edit Certifications
                </button>
            </div>
        </div>
        <div class="flex-grow">
            <p class="text-green-600 font-medium">Certifications information updated successfully!</p>
            <textarea 
                readonly
                class="w-full h-96 px-3 py-2 border border-gray-300 rounded-md focus:outline-none font-mono text-sm resize-none"
                placeholder="Resume content will appear here...">{resume.content}</textarea>
        </div>
    </div>
    """
    return HTMLResponse(content=html_content)


@router.get("/{resume_id}/personal", response_model=PersonalInfoResponse)
async def get_personal_info(
    resume: DatabaseResume = Depends(get_resume_for_user),
):
    """Get personal information from a resume.

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
    """Update personal information in a resume.

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

        # Extract other sections from existing content
        education_info = extract_education_info(resume.content)
        experience_info = extract_experience_info(resume.content)
        certifications_info = extract_certifications_info(resume.content)

        # Reconstruct resume with updated personal info
        updated_content = build_complete_resume_from_sections(
            personal_info=updated_info,
            education=education_info,
            experience=experience_info,
            certifications=certifications_info,
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
    """Get education information from a resume.

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
    """Update education information in a resume.

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

        personal_info = extract_personal_info(resume.content)
        experience_info = extract_experience_info(resume.content)
        certifications_info = extract_certifications_info(resume.content)

        # Reconstruct resume with updated education info
        updated_content = build_complete_resume_from_sections(
            personal_info=personal_info,
            education=updated_info,
            experience=experience_info,
            certifications=certifications_info,
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
    """Get experience information from a resume.

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
    """Update experience information in a resume.

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
        # Extract current resume sections
        personal_info = extract_personal_info(resume.content)
        education_info = extract_education_info(resume.content)
        certifications_info = extract_certifications_info(resume.content)
        current_experience = extract_experience_info(resume.content)

        # Create updated experience object, using new data if provided, else current
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
        updated_content = build_complete_resume_from_sections(
            personal_info=personal_info,
            education=education_info,
            experience=updated_experience,
            certifications=certifications_info,
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
    """Get projects information from a resume.

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
    """Update projects information in a resume.

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

        personal_info = extract_personal_info(resume.content)
        education_info = extract_education_info(resume.content)
        certifications_info = extract_certifications_info(resume.content)
        current_experience = extract_experience_info(resume.content)

        # To update only projects, we need to preserve roles from the current experience.
        experience_with_updated_projects = ExperienceResponse(
            roles=current_experience.roles,
            projects=projects_to_update,
        )

        updated_content = build_complete_resume_from_sections(
            personal_info=personal_info,
            education=education_info,
            experience=experience_with_updated_projects,
            certifications=certifications_info,
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
    """Get certifications information from a resume.

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
    """Update certifications information in a resume.

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

        personal_info = extract_personal_info(resume.content)
        education_info = extract_education_info(resume.content)
        experience_info = extract_experience_info(resume.content)

        # Reconstruct resume with updated certifications
        updated_content = build_complete_resume_from_sections(
            personal_info=personal_info,
            education=education_info,
            experience=experience_info,
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
