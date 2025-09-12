import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from resume_editor.app.api.dependencies import get_resume_for_user
from resume_editor.app.api.routes.route_logic.resume_crud import (
    update_resume as update_resume_db,
)
from resume_editor.app.api.routes.html_fragments import _generate_resume_detail_html
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
from resume_editor.app.api.routes.route_models import (
    CertificationsResponse,
    CertificationUpdateRequest,
    EducationResponse,
    EducationUpdateRequest,
    ExperienceResponse,
    ExperienceUpdateRequest,
    PersonalInfoResponse,
    PersonalInfoUpdateRequest,
    ProjectsResponse,
)
from resume_editor.app.database.database import get_db
from resume_editor.app.models.resume.certifications import Certification
from resume_editor.app.models.resume.education import Degree
from resume_editor.app.models.resume.experience import Project, Role
from resume_editor.app.models.resume_model import Resume as DatabaseResume

log = logging.getLogger(__name__)

router = APIRouter()


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
