import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from resume_editor.app.models.resume.certifications import Certification
from resume_editor.app.models.resume.education import Degree
from resume_editor.app.models.resume.experience import Project, Role

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


class PersonalInfoUpdateRequest(BaseModel):
    """Request model for updating personal information.

    Attributes:
        name (str): The full name.
        email (str | None): The email address.
        phone (str | None): The phone number.
        location (str | None): The location.
        website (str | None): The website URL.
        github (str | None): The GitHub profile URL.
        linkedin (str | None): The LinkedIn profile URL.
        twitter (str | None): The Twitter profile URL.
        work_authorization (str | None): The work authorization status.
        require_sponsorship (bool | None): Whether sponsorship is required.
        banner (str | None): The personal banner.
        note (str | None): A personal note.

    """

    name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    website: str | None = None
    github: str | None = None
    linkedin: str | None = None
    twitter: str | None = None
    work_authorization: str | None = None
    require_sponsorship: bool | None = None
    banner: str | None = None
    note: str | None = None


class EducationUpdateRequest(BaseModel):
    """Request model for updating education information.

    Attributes:
        degrees (list[Degree]): List of degrees with their details.

    """

    degrees: list[Degree]


class ExperienceUpdateRequest(BaseModel):
    """Request model for updating experience information.

    Attributes:
        roles (list[Role] | None): List of roles with their details.
        projects (list[Project] | None): List of projects with their details.

    """

    roles: list[Role] | None = None
    projects: list[Project] | None = None


class CertificationUpdateRequest(BaseModel):
    """Request model for updating certification information.

    Attributes:
        certifications (list[Certification]): List of certifications with their details.

    """

    certifications: list[Certification]


# Response models for structured data
class PersonalInfoResponse(BaseModel):
    """Response model for personal information.

    Attributes:
        name (str | None): The full name.
        email (str | None): The email address.
        phone (str | None): The phone number.
        location (str | None): The location.
        website (str | None): The website URL.
        github (str | None): The GitHub profile URL.
        linkedin (str | None): The LinkedIn profile URL.
        twitter (str | None): The Twitter profile URL.
        work_authorization (str | None): The work authorization status.
        require_sponsorship (bool | None): Whether sponsorship is required.
        banner (str | None): The personal banner.
        note (str | None): A personal note.

    """

    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    website: str | None = None
    github: str | None = None
    linkedin: str | None = None
    twitter: str | None = None
    work_authorization: str | None = None
    require_sponsorship: bool | None = None
    banner: str | None = None
    note: str | None = None


class EducationResponse(BaseModel):
    """Response model for education information.

    Attributes:
        degrees (list[Degree]): List of degrees with their details.

    """

    degrees: list[Degree]


class ExperienceResponse(BaseModel):
    """Response model for experience information.

    Attributes:
        roles (list[Role]): List of roles with their details.
        projects (list[Project]): List of projects with their details.

    """

    roles: list[Role]
    projects: list[Project] = []


class ProjectsResponse(BaseModel):
    """Response model for projects information.

    Attributes:
        projects (list[Project]): List of projects with their details.

    """

    projects: list[Project]


class CertificationsResponse(BaseModel):
    """Response model for certifications information.

    Attributes:
        certifications (list[Certification]): List of certifications with their details.

    """

    certifications: list[Certification]
