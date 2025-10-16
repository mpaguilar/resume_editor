import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from resume_editor.app.api.dependencies import get_resume_for_user
from resume_editor.app.api.routes.route_logic.resume_crud import (
    ResumeUpdateParams,
)
from resume_editor.app.api.routes.route_logic.resume_crud import (
    update_resume as update_resume_db,
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
from resume_editor.app.api.routes.route_models import (
    CertificationsResponse,
    CertificationUpdateForm,
    CertificationUpdateRequest,
    EducationResponse,
    EducationUpdateForm,
    EducationUpdateRequest,
    ExperienceResponse,
    ExperienceUpdateForm,
    ExperienceUpdateRequest,
    PersonalInfoResponse,
    PersonalInfoUpdateRequest,
    ProjectsResponse,
    ProjectUpdateForm,
)
from resume_editor.app.database.database import get_db
from resume_editor.app.models.resume.certifications import Certification
from resume_editor.app.models.resume.education import Degree
from resume_editor.app.models.resume.experience import Project, Role
from resume_editor.app.models.resume_model import Resume as DatabaseResume

log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{resume_id}/personal")
async def get_personal_info(
    resume: Annotated[DatabaseResume, Depends(get_resume_for_user)],
) -> PersonalInfoResponse:
    """Get personal information from a resume.

    Args:
        resume (DatabaseResume): The resume fetched for the current user via dependency injection.

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


@router.put("/{resume_id}/personal", status_code=200)
async def update_personal_info_structured(
    request: PersonalInfoUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    resume: Annotated[DatabaseResume, Depends(get_resume_for_user)],
) -> Response:
    """Update personal information in a resume.

    Args:
        request (PersonalInfoUpdateRequest): The updated personal information payload.
        db (Session): Database session dependency.
        resume (DatabaseResume): The resume fetched for the current user via dependency injection.

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
        update_params = ResumeUpdateParams(content=updated_content)
        update_resume_db(db, resume, params=update_params)

        return Response(headers={"HX-Redirect": "/dashboard"})
    except (ValueError, TypeError, HTTPException) as e:
        detail = getattr(e, "detail", str(e))
        _msg = (
            f"Failed to update resume due to reconstruction/validation error: {detail}"
        )
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=_msg)


@router.post("/{resume_id}/edit/projects", status_code=200)
async def update_projects(
    db: Annotated[Session, Depends(get_db)],
    resume: Annotated[DatabaseResume, Depends(get_resume_for_user)],
    form: Annotated[ProjectUpdateForm, Depends()],
) -> Response:
    """Update projects information in a resume.

    Args:
        db (Session): The database session dependency.
        resume (DatabaseResume): The resume object from dependency injection.
        form (ProjectUpdateForm): The form data for the new project.

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
                "title": form.title,
                "url": form.url,
                "start_date": datetime.strptime(form.start_date, "%Y-%m-%d")
                if form.start_date
                else None,
                "end_date": datetime.strptime(form.end_date, "%Y-%m-%d")
                if form.end_date
                else None,
            },
            "description": {"text": form.description},
        }
        new_project = Project.model_validate(new_project_data)

        experience_info = extract_experience_info(resume.content)
        experience_info.projects.append(new_project)

        updated_content = update_resume_content_with_structured_data(
            current_content=resume.content,
            experience=experience_info,
        )

        perform_pre_save_validation(updated_content, resume.content)
        update_params = ResumeUpdateParams(content=updated_content)
        update_resume_db(db, resume=resume, params=update_params)

        return Response(headers={"HX-Redirect": "/dashboard"})
    except (ValueError, TypeError, HTTPException) as e:
        detail = getattr(e, "detail", str(e))
        _msg = f"Failed to update projects info: {detail}"
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=_msg)


@router.post("/{resume_id}/edit/certifications", status_code=200)
async def update_certifications(
    db: Annotated[Session, Depends(get_db)],
    resume: Annotated[DatabaseResume, Depends(get_resume_for_user)],
    form: Annotated[CertificationUpdateForm, Depends()],
) -> Response:
    """Update certifications information in a resume.

    Args:
        db (Session): The database session dependency.
        resume (DatabaseResume): The resume object from dependency injection.
        form (CertificationUpdateForm): The form data for the new certification.

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
            "name": form.name,
            "issuer": form.issuer,
            "certification_id": form.certification_id,
            "issued": datetime.strptime(form.issued_date, "%Y-%m-%d")
            if form.issued_date
            else None,
            "expires": datetime.strptime(form.expiry_date, "%Y-%m-%d")
            if form.expiry_date
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
        update_params = ResumeUpdateParams(content=updated_content)
        update_resume_db(db, resume=resume, params=update_params)

        return Response(headers={"HX-Redirect": "/dashboard"})
    except (ValueError, TypeError, HTTPException) as e:
        detail = getattr(e, "detail", str(e))
        _msg = f"Failed to update certifications info: {detail}"
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=_msg)


@router.get("/{resume_id}/projects")
async def get_projects_info(
    resume: Annotated[DatabaseResume, Depends(get_resume_for_user)],
) -> ProjectsResponse:
    """Get projects information from a resume.

    Args:
        resume (DatabaseResume): The resume fetched for the current user via dependency injection.

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


@router.put("/{resume_id}/projects", status_code=200)
async def update_projects_info_structured(
    request: ExperienceUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    resume: Annotated[DatabaseResume, Depends(get_resume_for_user)],
) -> Response:
    """Update projects information in a resume.

    Args:
        request (ExperienceUpdateRequest): The updated projects information.
        db (Session): Database session dependency.
        resume (DatabaseResume): The resume fetched for the current user via dependency injection.

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

        update_params = ResumeUpdateParams(content=updated_content)
        update_resume_db(db, resume, params=update_params)

        return Response(headers={"HX-Redirect": "/dashboard"})
    except (ValueError, TypeError, HTTPException) as e:
        detail = getattr(e, "detail", str(e))
        _msg = (
            f"Failed to update resume due to reconstruction/validation error: {detail}"
        )
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=_msg)


@router.get("/{resume_id}/certifications")
async def get_certifications_info(
    resume: Annotated[DatabaseResume, Depends(get_resume_for_user)],
) -> CertificationsResponse:
    """Get certifications information from a resume.

    Args:
        resume (DatabaseResume): The resume fetched for the current user via dependency injection.

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


@router.put("/{resume_id}/certifications", status_code=200)
async def update_certifications_info_structured(
    request: CertificationUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    resume: Annotated[DatabaseResume, Depends(get_resume_for_user)],
) -> Response:
    """Update certifications information in a resume.

    Args:
        request (CertificationUpdateRequest): The updated certifications information.
        db (Session): Database session dependency.
        resume (DatabaseResume): The resume fetched for the current user via dependency injection.

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

        update_params = ResumeUpdateParams(content=updated_content)
        update_resume_db(db, resume, params=update_params)

        return Response(headers={"HX-Redirect": "/dashboard"})
    except (ValueError, TypeError, HTTPException) as e:
        detail = getattr(e, "detail", str(e))
        _msg = (
            f"Failed to update resume due to reconstruction/validation error: {detail}"
        )
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=_msg)


@router.post("/{resume_id}/edit/experience", status_code=200)
async def update_experience(
    db: Annotated[Session, Depends(get_db)],
    resume: Annotated[DatabaseResume, Depends(get_resume_for_user)],
    form: Annotated[ExperienceUpdateForm, Depends()],
) -> Response:
    """Update experience information in a resume.

    Args:
        db (Session): The database session dependency.
        resume (DatabaseResume): The resume object from dependency injection.
        form (ExperienceUpdateForm): The form data for the new experience role.

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
                "company": form.company,
                "title": form.title,
                "start_date": datetime.strptime(form.start_date, "%Y-%m-%d"),
                "end_date": datetime.strptime(form.end_date, "%Y-%m-%d")
                if form.end_date
                else None,
            },
            "summary": {"text": form.description} if form.description else None,
        }
        new_role = Role.model_validate(new_role_data)

        experience_info = extract_experience_info(resume.content)
        experience_info.roles.append(new_role)

        updated_content = update_resume_content_with_structured_data(
            current_content=resume.content,
            experience=experience_info,
        )

        perform_pre_save_validation(updated_content, resume.content)
        update_params = ResumeUpdateParams(content=updated_content)
        update_resume_db(db, resume=resume, params=update_params)

        return Response(headers={"HX-Redirect": "/dashboard"})
    except (ValueError, TypeError, HTTPException) as e:
        detail = getattr(e, "detail", str(e))
        _msg = f"Failed to update experience info: {detail}"
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=_msg)


@router.get("/{resume_id}/experience")
async def get_experience_info(
    resume: Annotated[DatabaseResume, Depends(get_resume_for_user)],
) -> ExperienceResponse:
    """Get experience information from a resume.

    Args:
        resume (DatabaseResume): The resume fetched for the current user via dependency injection.

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


@router.put("/{resume_id}/experience", status_code=200)
async def update_experience_info_structured(
    request: ExperienceUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    resume: Annotated[DatabaseResume, Depends(get_resume_for_user)],
) -> Response:
    """Update experience information in a resume.

    Args:
        request (ExperienceUpdateRequest): The updated experience information.
        db (Session): Database session dependency.
        resume (DatabaseResume): The resume fetched for the current user via dependency injection.

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
        update_params = ResumeUpdateParams(content=updated_content)
        update_resume_db(db, resume, params=update_params)

        return Response(headers={"HX-Redirect": "/dashboard"})
    except (ValueError, TypeError, HTTPException) as e:
        detail = getattr(e, "detail", str(e))
        _msg = (
            f"Failed to update resume due to reconstruction/validation error: {detail}"
        )
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=_msg)


@router.post("/{resume_id}/edit/education", status_code=200)
async def update_education(
    db: Annotated[Session, Depends(get_db)],
    resume: Annotated[DatabaseResume, Depends(get_resume_for_user)],
    form: Annotated[EducationUpdateForm, Depends()],
) -> Response:
    """Update education information in a resume.

    Args:
        db (Session): The database session dependency.
        resume (DatabaseResume): The resume object from dependency injection.
        form (EducationUpdateForm): The form data for the new education entry.

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
            "school": form.school,
            "degree": form.degree,
            "major": form.major,
            "start_date": datetime.strptime(form.start_date, "%Y-%m-%d")
            if form.start_date
            else None,
            "end_date": datetime.strptime(form.end_date, "%Y-%m-%d")
            if form.end_date
            else None,
            "gpa": form.gpa,
        }
        new_degree = Degree(**new_degree_data)

        education_info = extract_education_info(resume.content)
        education_info.degrees.append(new_degree)

        updated_content = update_resume_content_with_structured_data(
            current_content=resume.content,
            education=education_info,
        )

        perform_pre_save_validation(updated_content, resume.content)
        update_params = ResumeUpdateParams(content=updated_content)
        update_resume_db(db, resume=resume, params=update_params)

        return Response(headers={"HX-Redirect": "/dashboard"})
    except (ValueError, TypeError, HTTPException) as e:
        detail = getattr(e, "detail", str(e))
        _msg = f"Failed to update education info: {detail}"
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=_msg)


@router.get("/{resume_id}/education")
async def get_education_info(
    resume: Annotated[DatabaseResume, Depends(get_resume_for_user)],
) -> EducationResponse:
    """Get education information from a resume.

    Args:
        resume (DatabaseResume): The resume fetched for the current user via dependency injection.

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


@router.put("/{resume_id}/education", status_code=200)
async def update_education_info_structured(
    request: EducationUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    resume: Annotated[DatabaseResume, Depends(get_resume_for_user)],
) -> Response:
    """Update education information in a resume.

    Args:
        request (EducationUpdateRequest): The updated education information.
        db (Session): Database session dependency.
        resume (DatabaseResume): The resume fetched for the current user via dependency injection.

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
        update_params = ResumeUpdateParams(content=updated_content)
        update_resume_db(db, resume, params=update_params)

        return Response(headers={"HX-Redirect": "/dashboard"})
    except (ValueError, TypeError, HTTPException) as e:
        detail = getattr(e, "detail", str(e))
        _msg = (
            f"Failed to update resume due to reconstruction/validation error: {detail}"
        )
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=_msg)
