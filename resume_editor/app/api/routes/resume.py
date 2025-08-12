import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Import resume_writer parser
try:
    from resume_writer import parse_resume
    from resume_writer.models.resume import Resume as WriterResume

    PARSER_AVAILABLE = True
except ImportError:
    PARSER_AVAILABLE = False
    parse_resume = None
    WriterResume = None
    logging.warning(
        "resume_writer module not available. Parsing functionality will be disabled.",
    )

# Import database dependencies
from resume_editor.app.database.database import get_db
from resume_editor.app.models.resume_model import Resume as DatabaseResume
from resume_editor.app.models.user import User

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


# Request/Response models
class ParseRequest(BaseModel):
    """Request model for resume parsing.

    Attributes:
        markdown_content (str): The Markdown content of the resume to parse.

    """

    markdown_content: str


class ParseResponse(BaseModel):
    """Response model for resume parsing.

    Attributes:
        resume_data (dict[str, Any]): The structured resume data extracted from the Markdown content.

    """

    resume_data: dict[str, Any]


class ResumeCreateRequest(BaseModel):
    """Request model for creating a new resume.

    Attributes:
        name (str): The name of the resume.
        content (str): The Markdown content of the resume.

    """

    name: str
    content: str


class ResumeUpdateRequest(BaseModel):
    """Request model for updating an existing resume.

    Attributes:
        name (str | None): The updated name of the resume, or None to keep unchanged.
        content (str | None): The updated Markdown content of the resume, or None to keep unchanged.

    """

    name: str | None = None
    content: str | None = None


class ResumeResponse(BaseModel):
    """Response model for a resume.

    Attributes:
        id (int): The unique identifier for the resume.
        name (str): The name of the resume.

    """

    id: int
    name: str


class ResumeDetailResponse(BaseModel):
    """Response model for detailed resume content.

    Attributes:
        id (int): The unique identifier for the resume.
        name (str): The name of the resume.
        content (str): The Markdown content of the resume.

    """

    id: int
    name: str
    content: str


# Dependency to get current user (placeholder - would be implemented with auth)
def get_current_user():
    """Placeholder for current user dependency.

    In a real implementation, this would verify the user's authentication token
    and return the current user object.

    Returns:
        User: The current authenticated user.

    """
    # This is a placeholder implementation
    # In reality, this would use JWT token verification or similar
    return User(
        "testuser",
        "test@example.com",
        "hashed_password",
    )


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
    if not PARSER_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Resume parsing functionality not available",
        )

    try:
        # Parse the Markdown content using resume_writer
        resume: WriterResume = parse_resume(request.markdown_content)

        # Convert to dict for JSON serialization
        resume_dict = resume.model_dump()

        return ParseResponse(resume_data=resume_dict)
    except Exception as e:
        log.exception("Failed to parse resume")
        raise HTTPException(status_code=400, detail=f"Failed to parse resume: {str(e)}")


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
        10. If an error occurs, logs the exception, rolls back the transaction, and raises a 500 error.
        11. Performs database access: Writes to the database via db.add and db.commit.
        12. Performs network access: None.

    """
    # Validate Markdown content before saving
    if PARSER_AVAILABLE:
        try:
            parse_resume(request.content)
        except Exception as e:
            log.warning(f"Markdown validation failed: {str(e)}")
            raise HTTPException(
                status_code=422, detail=f"Invalid Markdown format: {str(e)}",
            )
    else:
        log.warning(
            "Resume parsing functionality not available. Skipping Markdown validation.",
        )

    try:
        # Create new resume instance
        resume = DatabaseResume(
            user_id=current_user.id,
            name=request.name,
            content=request.content,
        )

        # Add to database session and commit
        db.add(resume)
        db.commit()
        db.refresh(resume)

        # Check if this is an HTMX request
        if "HX-Request" in http_request.headers:
            # Return updated resume list
            resumes = (
                db.query(DatabaseResume)
                .filter(DatabaseResume.user_id == current_user.id)
                .all()
            )

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
    except HTTPException:
        # Re-raise HTTP exceptions (like 422) without modification
        raise
    except Exception as e:
        log.exception("Failed to create resume")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create resume: {str(e)}",
        )


@router.put("/{resume_id}", response_model=ResumeResponse)
async def update_resume(
    resume_id: int,
    request: ResumeUpdateRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
        10. If an error occurs, logs the exception, rolls back the transaction, and raises a 500 error.
        11. Performs database access: Reads from and writes to the database via db.query, db.commit.
        12. Performs network access: None.

    """
    try:
        # Find the resume
        resume = (
            db.query(DatabaseResume)
            .filter(
                DatabaseResume.id == resume_id,
                DatabaseResume.user_id == current_user.id,
            )
            .first()
        )

        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")

        # Validate Markdown content before updating if content is being changed
        if request.content is not None and PARSER_AVAILABLE:
            try:
                parse_resume(request.content)
            except Exception as e:
                log.warning(f"Markdown validation failed: {str(e)}")
                raise HTTPException(
                    status_code=422, detail=f"Invalid Markdown format: {str(e)}",
                )
        elif request.content is not None and not PARSER_AVAILABLE:
            log.warning(
                "Resume parsing functionality not available. Skipping Markdown validation.",
            )

        # Update fields if provided
        if request.name is not None:
            resume.name = request.name
        if request.content is not None:
            resume.content = request.content

        # Commit changes
        db.commit()
        db.refresh(resume)

        # Check if this is an HTMX request
        if "HX-Request" in http_request.headers:
            # Return updated resume list
            resumes = (
                db.query(DatabaseResume)
                .filter(DatabaseResume.user_id == current_user.id)
                .all()
            )

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
    except HTTPException:
        # Re-raise HTTP exceptions (like 422) without modification
        raise
    except Exception as e:
        log.exception("Failed to update resume")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update resume: {str(e)}",
        )


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: int,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
        7. If an error occurs, logs the exception, rolls back the transaction, and raises a 500 error.
        8. Performs database access: Reads from and writes to the database via db.query, db.delete, db.commit.
        9. Performs network access: None.

    """
    try:
        # Find the resume
        resume = (
            db.query(DatabaseResume)
            .filter(
                DatabaseResume.id == resume_id,
                DatabaseResume.user_id == current_user.id,
            )
            .first()
        )

        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")

        # Delete the resume
        db.delete(resume)
        db.commit()

        # Check if this is an HTMX request
        if "HX-Request" in http_request.headers:
            # Return updated resume list
            resumes = (
                db.query(DatabaseResume)
                .filter(DatabaseResume.user_id == current_user.id)
                .all()
            )

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
    except HTTPException:
        raise
    except Exception as e:
        log.exception("Failed to delete resume")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete resume: {str(e)}",
        )


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
        6. If an error occurs, logs the exception and raises a 500 error.
        7. Performs database access: Reads from the database via db.query.
        8. Performs network access: None.

    """
    try:
        resumes = (
            db.query(DatabaseResume)
            .filter(DatabaseResume.user_id == current_user.id)
            .all()
        )

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
    except Exception as e:
        log.exception("Failed to list resumes")
        raise HTTPException(status_code=500, detail=f"Failed to list resumes: {str(e)}")


@router.get("/{resume_id}", response_model=ResumeDetailResponse)
async def get_resume(
    request: Request,
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
        5. If an error occurs, logs the exception and raises a 500 error.
        6. Performs database access: Reads from the database via db.query.
        7. Performs network access: None.

    """
    try:
        resume = (
            db.query(DatabaseResume)
            .filter(
                DatabaseResume.id == resume_id,
                DatabaseResume.user_id == current_user.id,
            )
            .first()
        )

        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")

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
    except HTTPException:
        raise
    except Exception as e:
        log.exception("Failed to retrieve resume")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve resume: {str(e)}",
        )
