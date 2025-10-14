import logging

from resume_writer.models.parsers import ParseContext
from resume_writer.models.resume import Resume as WriterResume

from resume_editor.app.api.routes.route_logic.resume_serialization_helpers import (
    _add_banner_markdown,
    _add_contact_info_markdown,
    _add_note_markdown,
    _add_project_description_markdown,
    _add_project_overview_markdown,
    _add_project_skills_markdown,
    _add_role_basics_markdown,
    _add_role_responsibilities_markdown,
    _add_role_skills_markdown,
    _add_role_summary_markdown,
    _add_visa_status_markdown,
    _add_websites_markdown,
    _check_for_unparsed_content,
    _convert_writer_project_to_dict,
    _convert_writer_role_to_dict,
    _extract_data_from_personal_section,
    _parse_resume,
)
from resume_editor.app.api.routes.route_models import (
    CertificationsResponse,
    EducationResponse,
    ExperienceResponse,
    PersonalInfoResponse,
)
from resume_editor.app.models.resume.experience import InclusionStatus

log = logging.getLogger(__name__)


def extract_personal_info(resume_content: str) -> PersonalInfoResponse:
    """
    Extract personal information from resume content.

    Args:
        resume_content (str): The Markdown content of the resume to parse.

    Returns:
        PersonalInfoResponse: Extracted personal information containing name, email, phone, location, and website.

    Raises:
        ValueError: If parsing fails due to invalid or malformed resume content.

    Notes:
        1. Parses the resume content using `_parse_resume`.
        2. Checks for unparsed content in the "personal" section using `_check_for_unparsed_content`.
        3. If no personal section was parsed, an empty response is returned.
        4. Extracts data from the parsed personal section using `_extract_data_from_personal_section`.
        5. Constructs and returns a `PersonalInfoResponse` with the extracted data.
    """
    log.debug("extract_personal_info starting")
    try:
        parsed_resume = _parse_resume(resume_content)
    except ValueError as e:
        _msg = "Failed to parse personal info from resume content."
        raise ValueError(_msg) from e

    personal = getattr(parsed_resume, "personal", None)
    data = _extract_data_from_personal_section(personal)

    if not data:
        # If no data was extracted from the 'personal' object, it implies
        # that either the section is genuinely empty or contains unparseable content.
        # We must manually check for the presence of raw, unparsed content.
        # Passing 'None' to '_check_for_unparsed_content' forces it to perform this scan.
        _check_for_unparsed_content(resume_content, "personal", None)

    response = PersonalInfoResponse(**data)
    log.debug("extract_personal_info returning")
    return response


def extract_education_info(resume_content: str) -> EducationResponse:
    """
    Extract education information from resume content.

    Args:
        resume_content (str): The Markdown content of the resume to parse.

    Returns:
        EducationResponse: Extracted education information containing a list of degree entries.

    Raises:
        ValueError: If parsing fails due to invalid or malformed resume content.

    Notes:
        1. Splits the resume content into lines.
        2. Creates a ParseContext for parsing.
        3. Parses the resume using the resume_writer module.
        4. Retrieves the education section from the parsed resume.
        5. Checks if education data is present; if not, returns an empty response.
        6. Loops through each degree and extracts school, degree, major, start_date, end_date, and gpa.
        7. Maps each degree's fields into a dictionary.
        8. Returns a list of dictionaries wrapped in the EducationResponse model.
        9. If parsing fails, returns an empty response.
        10. No network, disk, or database access is performed during this function.

    """
    try:
        parsed_resume = _parse_resume(resume_content)
    except ValueError as e:
        _msg = "Failed to parse education info from resume content."
        raise ValueError(_msg) from e

    education = parsed_resume.education

    if not education or not hasattr(education, "degrees") or not education.degrees:
        return EducationResponse(degrees=[])

    degrees_list = []
    for degree in education.degrees:
        degrees_list.append(
            {
                "school": degree.school if degree.school else None,
                "degree": degree.degree if degree.degree else None,
                "major": degree.major if degree.major else None,
                "start_date": degree.start_date,
                "end_date": degree.end_date,
                "gpa": degree.gpa if degree.gpa else None,
            },
        )

    return EducationResponse(degrees=degrees_list)


def extract_experience_info(resume_content: str) -> ExperienceResponse:
    """
    Extract experience information from resume content.

    Args:
        resume_content (str): The Markdown content of the resume to parse.

    Returns:
        ExperienceResponse: Extracted experience information containing lists of roles and projects.

    Raises:
        ValueError: If parsing fails due to invalid or malformed resume content.

    Notes:
        1. Parses the resume content using `_parse_resume`.
        2. Retrieves the experience section. If it's missing but raw content exists, raises ValueError via `_check_for_unparsed_content`.
        3. Loops through each role, converting it to a dictionary via `_convert_writer_role_to_dict`.
        4. Loops through each project, converting it to a dictionary via `_convert_writer_project_to_dict`.
        5. Collects non-empty dictionaries into lists.
        6. Returns an `ExperienceResponse` with the collected lists.

    """
    try:
        parsed_resume = _parse_resume(resume_content)
    except ValueError as e:
        _msg = "Failed to parse experience info from resume content."
        raise ValueError(_msg) from e

    experience = parsed_resume.experience

    roles_list = []
    if experience and hasattr(experience, "roles") and experience.roles is not None:
        for role in experience.roles:
            role_dict = _convert_writer_role_to_dict(role)
            if role_dict:
                roles_list.append(role_dict)

    projects_list = []
    if experience and hasattr(experience, "projects") and experience.projects is not None:
        for project in experience.projects:
            project_dict = _convert_writer_project_to_dict(project)
            if project_dict:
                projects_list.append(project_dict)

    if not roles_list and not projects_list:
        _check_for_unparsed_content(resume_content, "experience", None)

    return ExperienceResponse(roles=roles_list, projects=projects_list)


def extract_certifications_info(resume_content: str) -> CertificationsResponse:
    """
    Extract certifications information from resume content.

    Args:
        resume_content (str): The Markdown content of the resume to parse.

    Returns:
        CertificationsResponse: Extracted certifications information containing a list of certifications.

    Raises:
        ValueError: If parsing fails due to invalid or malformed resume content.

    Notes:
        1. Splits the resume content into lines.
        2. Creates a ParseContext for parsing.
        3. Parses the resume using the resume_writer module.
        4. Retrieves the certifications section from the parsed resume.
        5. Checks if certifications data is present; if not, returns an empty response.
        6. Loops through each certification and extracts name, issuer, certification_id, issued, and expires.
        7. Maps the extracted data into a dictionary.
        8. Returns a list of dictionaries wrapped in the CertificationsResponse model.
        9. If parsing fails, returns an empty response.
        10. No network, disk, or database access is performed during this function.

    """
    try:
        parsed_resume = _parse_resume(resume_content)
    except ValueError as e:
        _msg = "Failed to parse certifications info from resume content."
        raise ValueError(_msg) from e

    certifications = parsed_resume.certifications

    if not certifications or not hasattr(certifications, "__iter__"):
        return CertificationsResponse(certifications=[])

    certs_list = []
    for cert in certifications:
        issued = getattr(cert, "issued", None)
        expires = getattr(cert, "expires", None)
        certs_list.append(
            {
                "name": getattr(cert, "name", None),
                "issuer": getattr(cert, "issuer", None),
                "certification_id": getattr(cert, "certification_id", None),
                "issued": issued,
                "expires": expires,
            },
        )

    return CertificationsResponse(certifications=certs_list)


def serialize_personal_info_to_markdown(personal_info: PersonalInfoResponse | None) -> str:
    """
    Serialize personal information to Markdown format.

    Args:
        personal_info (PersonalInfoResponse | None): Personal information to serialize.

    Returns:
        str: Markdown formatted personal information section.

    Notes:
        1. Returns an empty string if `personal_info` is `None`.
        2. Initializes an empty list `lines`.
        3. Calls helper functions to add contact info, websites, visa status,
           banner, and note sections to `lines`.
        4. If `lines` is not empty, constructs the final string:
            a. Starts with `# Personal\n\n`.
            b. Joins the elements of `lines` with newlines.
            c. Appends a final newline.
        5. Otherwise, returns an empty string.
    """
    if not personal_info:
        return ""

    lines = []
    _add_contact_info_markdown(personal_info, lines)
    _add_websites_markdown(personal_info, lines)
    _add_visa_status_markdown(personal_info, lines)
    _add_banner_markdown(personal_info, lines)
    _add_note_markdown(personal_info, lines)

    if not lines:
        return ""

    return "# Personal\n\n" + "\n".join(lines) + "\n"


def serialize_education_to_markdown(education) -> str:
    """
    Serialize education information to Markdown format.

    Args:
        education: Education information to serialize, containing a list of degree entries.

    Returns:
        str: Markdown formatted education section.

    Notes:
        1. Initializes an empty list of lines and adds a heading.
        2. For each degree in the list:
            a. Adds a subsection header.
            b. Adds each field (school, degree, major, start_date, end_date, gpa) as a direct field if present.
            c. Adds a blank line after each degree.
        3. Joins the lines with newlines.
        4. Returns the formatted string with a trailing newline.
        5. No network, disk, or database access is performed during this function.

    """
    if not education or not hasattr(education, "degrees"):
        education = EducationResponse(degrees=[])

    lines = ["# Education", "", "## Degrees", ""]

    for degree in education.degrees:
        lines.append("### Degree")
        lines.append("")
        if getattr(degree, "school", None):
            lines.append(f"School: {degree.school}")
        if getattr(degree, "degree", None):
            lines.append(f"Degree: {degree.degree}")
        if getattr(degree, "major", None):
            lines.append(f"Major: {degree.major}")
        if getattr(degree, "start_date", None):
            lines.append(f"Start date: {degree.start_date.strftime('%m/%Y')}")
        if getattr(degree, "end_date", None):
            lines.append(f"End date: {degree.end_date.strftime('%m/%Y')}")
        if getattr(degree, "gpa", None):
            lines.append(f"GPA: {degree.gpa}")
        lines.append("")

    # Only return content if there are degrees
    if education.degrees:
        return "\n".join(lines) + "\n"

    return ""


def _serialize_project_to_markdown(project) -> list[str]:
    """
    Serialize a single project to markdown lines.

    Args:
        project: A project object to serialize.

    Returns:
        list[str]: A list of markdown lines representing the project.

    Notes:
        1. Gets the overview from the project.
        2. Checks if the inclusion status is OMIT; if so, returns an empty list.
        3. Calls `_add_project_overview_markdown` to add the overview section.
        4. If inclusion status is not `NOT_RELEVANT`, calls `_add_project_description_markdown` and `_add_project_skills_markdown`.
        5. If any content is generated, prepends the `### Project` header.
        6. Returns the full project content as a list of lines.

    """
    overview = getattr(project, "overview", None)
    if not overview:
        return []

    inclusion_status = getattr(overview, "inclusion_status", InclusionStatus.INCLUDE)
    if inclusion_status == InclusionStatus.OMIT:
        return []

    project_content = []
    _add_project_overview_markdown(overview, project_content)

    if inclusion_status != InclusionStatus.NOT_RELEVANT:
        description = getattr(project, "description", None)
        _add_project_description_markdown(description, project_content)

        skills = getattr(project, "skills", None)
        _add_project_skills_markdown(skills, project_content)

    if project_content:
        return ["### Project", ""] + project_content
    return []


def _serialize_role_to_markdown(role) -> list[str]:
    """
    Serialize a single role to markdown lines.

    Args:
        role: A role object to serialize.

    Returns:
        list[str]: A list of markdown lines representing the role.

    Notes:
        1. Gets the `basics` section from the role. If not present, returns an empty list.
        2. Checks the `inclusion_status` on the `basics` object. If `OMIT`, returns an empty list.
        3. Orchestrates calls to helper functions to serialize different parts of the role:
           - `_add_role_basics_markdown` for company, title, dates, etc.
           - `_add_role_summary_markdown` for the summary text.
           - `_add_role_responsibilities_markdown` for responsibilities, handling inclusion status.
           - `_add_role_skills_markdown` for the list of skills.
        4. If any content is generated, prepends the `### Role` header.
        5. Returns the combined list of Markdown lines for the role.

    """
    basics = getattr(role, "basics", None)
    if not basics:
        return []

    inclusion_status = getattr(basics, "inclusion_status", InclusionStatus.INCLUDE)
    if inclusion_status == InclusionStatus.OMIT:
        return []

    role_content = []
    _add_role_basics_markdown(basics, role_content)

    summary = getattr(role, "summary", None)
    _add_role_summary_markdown(summary, role_content)

    responsibilities = getattr(role, "responsibilities", None)
    _add_role_responsibilities_markdown(
        responsibilities, inclusion_status, role_content
    )

    skills = getattr(role, "skills", None)
    _add_role_skills_markdown(skills, role_content)

    if role_content:
        return ["### Role", ""] + role_content
    return []


def serialize_experience_to_markdown(experience) -> str:
    """
    Serialize experience information to Markdown format.

    Args:
        experience: Experience information to serialize, containing lists of roles and projects.

    Returns:
        str: Markdown formatted experience section.

    Notes:
        1. Checks if the experience object is empty.
        2. Initializes an empty list of lines.
        3. If projects exist, serializes each one using `_serialize_project_to_markdown`.
        4. If roles exist, serializes each one using `_serialize_role_to_markdown`.
        5. If any content was generated, builds the final Markdown string with `# Experience`, `## Projects` (if any), and `## Roles` (if any) headers.
        6. Joins the lines with newlines and returns the formatted string with a trailing newline.
        7. Returns an empty string if no experience data is present or all items are omitted.
        8. No network, disk, or database access is performed during this function.

    """
    if not experience:
        experience = ExperienceResponse(roles=[], projects=[])

    project_lines = []
    if hasattr(experience, "projects") and experience.projects:
        for project in experience.projects:
            project_lines.extend(_serialize_project_to_markdown(project))

    role_lines = []
    if hasattr(experience, "roles") and experience.roles:
        for role in experience.roles:
            role_lines.extend(_serialize_role_to_markdown(role))

    if not project_lines and not role_lines:
        return ""

    lines = ["# Experience", ""]
    if project_lines:
        lines.extend(["## Projects", ""])
        lines.extend(project_lines)
    if role_lines:
        lines.extend(["## Roles", ""])
        lines.extend(role_lines)

    return "\n".join(lines) + "\n"


def serialize_certifications_to_markdown(certifications) -> str:
    """
    Serialize certifications information to Markdown format.

    Args:
        certifications: Certifications information to serialize, containing a list of certifications.

    Returns:
        str: Markdown formatted certifications section.

    Notes:
        1. Initializes an empty list of lines and adds a heading.
        2. For each certification in the list:
            a. Adds a subsection header.
            b. Adds each field (name, issuer, id, issued_date, expiry_date) as direct fields if present.
            c. Adds a blank line after each certification.
        3. Joins the lines with newlines.
        4. Returns the formatted string with a trailing newline.
        5. No network, disk, or database access is performed during this function.

    """
    if not certifications or not hasattr(certifications, "certifications"):
        certifications = CertificationsResponse(certifications=[])

    lines = ["# Certifications", ""]

    for cert in certifications.certifications:
        lines.append("## Certification")
        lines.append("")
        if getattr(cert, "name", None):
            lines.append(f"Name: {cert.name}")
        if getattr(cert, "issuer", None):
            lines.append(f"Issuer: {cert.issuer}")
        if getattr(cert, "issued", None):
            lines.append(f"Issued: {cert.issued.strftime('%m/%Y')}")
        if getattr(cert, "expires", None):
            lines.append(f"Expires: {cert.expires.strftime('%m/%Y')}")
        if getattr(cert, "certification_id", None):
            lines.append(f"Certification ID: {cert.certification_id}")
        lines.append("")

    if certifications.certifications:
        return "\n".join(lines) + "\n"
    return ""


def update_resume_content_with_structured_data(
    current_content: str,
    personal_info=None,
    education=None,
    certifications=None,
    experience=None,
) -> str:
    """
    Update resume content with structured data by replacing specific sections.

    Args:
        current_content (str): Current resume Markdown content to update.
        personal_info: Updated personal information to insert. If None, the existing info is preserved.
        education: Updated education information to insert. If None, the existing info is preserved.
        certifications: Updated certifications information to insert. If None, the existing info is preserved.
        experience: Updated experience information to insert. If None, the existing info is preserved.

    Returns:
        str: Updated resume content with new structured data.

    Notes:
        1. Extracts existing sections from `current_content` if they are not provided as arguments.
        2. reconstructs the full resume using the combination of new and existing data.

    """
    from resume_editor.app.api.routes.route_logic.resume_reconstruction import (
        reconstruct_resume_markdown,
    )

    if personal_info is None:
        personal_info = extract_personal_info(current_content)

    if education is None:
        education = extract_education_info(current_content)

    if experience is None:
        experience = extract_experience_info(current_content)

    if certifications is None:
        certifications = extract_certifications_info(current_content)

    return reconstruct_resume_markdown(
        personal_info=personal_info,
        education=education,
        certifications=certifications,
        experience=experience,
    )
