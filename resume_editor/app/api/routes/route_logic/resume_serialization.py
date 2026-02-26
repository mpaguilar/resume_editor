import logging

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
from resume_editor.app.models.resume.experience import InclusionStatus, Project, Role

log = logging.getLogger(__name__)


def extract_personal_info(resume_content: str) -> PersonalInfoResponse:
    """Extract personal information from resume content.

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
    """Extract education information from resume content.

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


def _extract_roles_list(experience: any) -> list[dict]:
    """Extract roles from experience object into a list of dictionaries.

    Args:
        experience: The experience object from parsed resume, may be None.

    Returns:
        list[dict]: List of role dictionaries extracted from the experience.

    Notes:
        1. Returns empty list if experience is None or has no roles attribute.
        2. Iterates through each role in experience.roles.
        3. Converts each role to dictionary using `_convert_writer_role_to_dict`.
        4. Filters out empty dictionaries.
        5. Returns the collected list of role dictionaries.

    """
    roles_list = []
    if experience and hasattr(experience, "roles") and experience.roles is not None:
        for role in experience.roles:
            role_dict = _convert_writer_role_to_dict(role)
            if role_dict:
                roles_list.append(role_dict)
    return roles_list


def _extract_projects_list(experience: any) -> list[dict]:
    """Extract projects from experience object into a list of dictionaries.

    Args:
        experience: The experience object from parsed resume, may be None.

    Returns:
        list[dict]: List of project dictionaries extracted from the experience.

    Notes:
        1. Returns empty list if experience is None or has no projects attribute.
        2. Iterates through each project in experience.projects.
        3. Converts each project to dictionary using `_convert_writer_project_to_dict`.
        4. Filters out empty dictionaries.
        5. Returns the collected list of project dictionaries.

    """
    projects_list = []
    if (
        experience
        and hasattr(experience, "projects")
        and experience.projects is not None
    ):
        for project in experience.projects:
            project_dict = _convert_writer_project_to_dict(project)
            if project_dict:
                projects_list.append(project_dict)
    return projects_list


def extract_experience_info(resume_content: str) -> ExperienceResponse:
    """Extract experience information from resume content.

    Args:
        resume_content (str): The Markdown content of the resume to parse.

    Returns:
        ExperienceResponse: Extracted experience information containing lists of roles and projects.

    Raises:
        ValueError: If parsing fails due to invalid or malformed resume content.

    Notes:
        1. Parses the resume content using `_parse_resume`.
        2. Retrieves the experience section. If it's missing but raw content exists, raises ValueError via `_check_for_unparsed_content`.
        3. Extracts roles list using `_extract_roles_list`.
        4. Extracts projects list using `_extract_projects_list`.
        5. If both lists are empty, checks for unparsed content.
        6. Returns an `ExperienceResponse` with the collected lists.

    """
    try:
        parsed_resume = _parse_resume(resume_content)
    except ValueError as e:
        _msg = "Failed to parse experience info from resume content."
        raise ValueError(_msg) from e

    experience = parsed_resume.experience

    roles_list = _extract_roles_list(experience)
    projects_list = _extract_projects_list(experience)

    if not roles_list and not projects_list:
        _check_for_unparsed_content(resume_content, "experience", None)

    return ExperienceResponse(roles=roles_list, projects=projects_list)


def extract_certifications_info(resume_content: str) -> CertificationsResponse:
    """Extract certifications information from resume content.

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
                "certification_id": getattr(
                    cert,
                    "certification_id",
                    getattr(cert, "id", None),
                ),
                "issued": issued,
                "expires": expires,
            },
        )

    return CertificationsResponse(certifications=certs_list)


def extract_banner_text(resume_content: str) -> str | None:
    """Extract banner text from resume content.

    Args:
        resume_content (str): The Markdown content of the resume to parse.

    Returns:
        str | None: The banner text if found, otherwise None.

    Notes:
        1. Parses the resume content using `_parse_resume`.
        2. Safely accesses the `personal` section and its `banner` attribute.
        3. Extracts the text from the banner object.
        4. Returns the banner text or None if not found or on parsing error.

    """
    log.debug("extract_banner_text starting")
    try:
        parsed_resume = _parse_resume(resume_content)
        personal_section = getattr(parsed_resume, "personal", None)
        if personal_section:
            banner = getattr(personal_section, "banner", None)
            if banner and hasattr(banner, "text"):
                log.debug("extract_banner_text returning")
                return banner.text
    except ValueError:
        log.warning("Could not parse resume to extract banner text.")
        # Return None on parsing error as per design for this simple extractor
        return None

    log.debug("extract_banner_text returning")
    return None


def serialize_personal_info_to_markdown(
    personal_info: PersonalInfoResponse | None,
) -> str:
    """Serialize personal information to Markdown format.

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


def _format_degree_field_line(degree: any, field_name: str, label: str) -> str | None:
    """Format a single degree field as a markdown line if present.

    Args:
        degree: The degree object containing the field.
        field_name (str): The attribute name to get from the degree.
        label (str): The label to use in the markdown output.

    Returns:
        str | None: Formatted markdown line or None if field is not present.

    Notes:
        1. Gets the field value using getattr.
        2. If value exists, formats it as "Label: Value".
        3. Returns the formatted string or None.

    """
    value = getattr(degree, field_name, None)
    if value:
        return f"{label}: {value}"
    return None


def _format_degree_date_line(degree: any, field_name: str, label: str) -> str | None:
    """Format a degree date field as a markdown line if present.

    Args:
        degree: The degree object containing the date field.
        field_name (str): The attribute name to get from the degree.
        label (str): The label to use in the markdown output.

    Returns:
        str | None: Formatted markdown line or None if date is not present.

    Notes:
        1. Gets the date value using getattr.
        2. If date exists, formats it as "Label: MM/YYYY".
        3. Returns the formatted string or None.

    """
    date_value = getattr(degree, field_name, None)
    if date_value:
        return f"{label}: {date_value.strftime('%m/%Y')}"
    return None


def _add_degree_fields_to_lines(degree: any, lines: list[str]) -> None:
    """Add all degree fields to the lines list if present.

    Args:
        degree: The degree object containing fields to serialize.
        lines (list[str]): The list to append formatted lines to.

    Notes:
        1. Adds school, degree, major fields if present.
        2. Adds start_date and end_date formatted as MM/YYYY if present.
        3. Adds GPA if present.

    """
    fields = [
        ("school", "School", _format_degree_field_line),
        ("degree", "Degree", _format_degree_field_line),
        ("major", "Major", _format_degree_field_line),
        ("start_date", "Start date", _format_degree_date_line),
        ("end_date", "End date", _format_degree_date_line),
        ("gpa", "GPA", _format_degree_field_line),
    ]

    for field_name, label, formatter in fields:
        line = formatter(degree, field_name, label)
        if line:
            lines.append(line)


def _serialize_single_degree(degree: any) -> list[str]:
    """Serialize a single degree entry to markdown lines.

    Args:
        degree: The degree object to serialize.

    Returns:
        list[str]: List of markdown lines for the degree.

    Notes:
        1. Adds the "### Degree" header and blank line.
        2. Adds all degree fields using `_add_degree_fields_to_lines`.
        3. Adds trailing blank line.
        4. Returns the list of markdown lines.

    """
    lines = ["### Degree", ""]
    _add_degree_fields_to_lines(degree, lines)
    lines.append("")
    return lines


def serialize_education_to_markdown(education: EducationResponse | None) -> str:
    """Serialize education information to Markdown format.

    Args:
        education (EducationResponse | None): Education information to serialize, containing a list of degree entries.

    Returns:
        str: Markdown formatted education section.

    Notes:
        1. Initializes education with empty degrees if not provided.
        2. Initializes lines list with headers.
        3. For each degree, serializes it using `_serialize_single_degree`.
        4. If any degrees were serialized, returns the formatted string.
        5. Returns empty string if no degrees present.
        6. No network, disk, or database access is performed during this function.

    """
    if not education or not hasattr(education, "degrees"):
        education = EducationResponse(degrees=[])

    lines = ["# Education", "", "## Degrees", ""]

    for degree in education.degrees:
        lines.extend(_serialize_single_degree(degree))

    # Only return content if there are degrees
    if education.degrees:
        return "\n".join(lines) + "\n"

    return ""


def _serialize_project_to_markdown(project: Project) -> list[str]:
    """Serialize a single project to markdown lines.

    Args:
        project (Project): A project object to serialize.

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


def _serialize_role_to_markdown(role: Role) -> list[str]:
    """Serialize a single role to markdown lines.

    Args:
        role (Role): A role object to serialize.

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
        responsibilities,
        inclusion_status,
        role_content,
    )

    skills = getattr(role, "skills", None)
    _add_role_skills_markdown(skills, role_content)

    if role_content:
        return ["### Role", ""] + role_content
    return []


def _extract_roles_from_experience(experience: ExperienceResponse) -> list[str]:
    """Extract and serialize roles from experience into markdown lines.

    Args:
        experience (ExperienceResponse): Experience object containing roles.

    Returns:
        list[str]: List of markdown lines for all roles.

    Notes:
        1. Checks if experience has a roles attribute with data.
        2. Iterates through each role and serializes it using `_serialize_role_to_markdown`.
        3. Collects all serialized role lines into a single list.
        4. Returns the combined list of markdown lines.

    """
    role_lines = []
    if hasattr(experience, "roles") and experience.roles:
        for role in experience.roles:
            role_lines.extend(_serialize_role_to_markdown(role))
    return role_lines


def _extract_projects_from_experience(experience: ExperienceResponse) -> list[str]:
    """Extract and serialize projects from experience into markdown lines.

    Args:
        experience (ExperienceResponse): Experience object containing projects.

    Returns:
        list[str]: List of markdown lines for all projects.

    Notes:
        1. Checks if experience has a projects attribute with data.
        2. Iterates through each project and serializes it using `_serialize_project_to_markdown`.
        3. Collects all serialized project lines into a single list.
        4. Returns the combined list of markdown lines.

    """
    project_lines = []
    if hasattr(experience, "projects") and experience.projects:
        for project in experience.projects:
            project_lines.extend(_serialize_project_to_markdown(project))
    return project_lines


def _build_experience_markdown(
    project_lines: list[str],
    role_lines: list[str],
) -> str:
    """Build the final experience markdown string from project and role lines.

    Args:
        project_lines (list[str]): Markdown lines for projects section.
        role_lines (list[str]): Markdown lines for roles section.

    Returns:
        str: Complete markdown formatted experience section.

    Notes:
        1. Returns empty string if both project_lines and role_lines are empty.
        2. Initializes the lines list with the main "# Experience" header.
        3. If project_lines exist, adds the "## Projects" header and project content.
        4. If role_lines exist, adds the "## Roles" header and role content.
        5. Joins all lines with newlines and appends a trailing newline.
        6. Returns the formatted markdown string.

    """
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


def serialize_experience_to_markdown(experience: ExperienceResponse | None) -> str:
    """Serialize experience information to Markdown format.

    Args:
        experience (ExperienceResponse | None): Experience information to serialize, containing lists of roles and projects.

    Returns:
        str: Markdown formatted experience section.

    Notes:
        1. Checks if the experience object is empty, creates empty response if so.
        2. Extracts project lines using `_extract_projects_from_experience`.
        3. Extracts role lines using `_extract_roles_from_experience`.
        4. Builds final markdown using `_build_experience_markdown`.
        5. No network, disk, or database access is performed during this function.

    """
    if not experience:
        experience = ExperienceResponse(roles=[], projects=[])

    project_lines = _extract_projects_from_experience(experience)
    role_lines = _extract_roles_from_experience(experience)

    return _build_experience_markdown(project_lines, role_lines)


def _format_certification_field(cert: any, field: str, label: str) -> str | None:
    """Format a certification field as a markdown line if present.

    Args:
        cert: The certification object containing the field.
        field (str): The attribute name to get from the certification.
        label (str): The label to use in the markdown output.

    Returns:
        str | None: Formatted markdown line or None if field is not present.

    Notes:
        1. Gets the field value using getattr.
        2. If value exists, formats it as "Label: Value".
        3. Returns the formatted string or None.

    """
    value = getattr(cert, field, None)
    if value:
        return f"{label}: {value}"
    return None


def _format_certification_date(cert: any, field: str, label: str) -> str | None:
    """Format a certification date field as a markdown line if present.

    Args:
        cert: The certification object containing the date field.
        field (str): The attribute name to get from the certification.
        label (str): The label to use in the markdown output.

    Returns:
        str | None: Formatted markdown line or None if date is not present.

    Notes:
        1. Gets the date value using getattr.
        2. If date exists, formats it as "Label: MM/YYYY".
        3. Returns the formatted string or None.

    """
    date_value = getattr(cert, field, None)
    if date_value:
        return f"{label}: {date_value.strftime('%m/%Y')}"
    return None


def _append_field_if_present(
    cert: any,
    lines: list[str],
    field: str,
    label: str,
    formatter: any,
) -> None:
    """Append a formatted field line if the field is present.

    Args:
        cert: The object containing the field.
        lines (list[str]): The list to append to.
        field (str): The attribute name to get.
        label (str): The label for the output.
        formatter: The formatting function to use.

    """
    line = formatter(cert, field, label)
    if line:
        lines.append(line)


def _add_certification_fields_to_lines(cert: any, lines: list[str]) -> None:
    """Add all certification fields to the lines list if present.

    Args:
        cert: The certification object containing fields to serialize.
        lines (list[str]): The list to append formatted lines to.

    Notes:
        1. Adds name, issuer, certification_id fields if present.
        2. Adds issued and expires dates formatted as MM/YYYY if present.

    """
    # Simple text fields
    _append_field_if_present(cert, lines, "name", "Name", _format_certification_field)
    _append_field_if_present(
        cert, lines, "issuer", "Issuer", _format_certification_field
    )

    # Date fields
    _append_field_if_present(
        cert, lines, "issued", "Issued", _format_certification_date
    )
    _append_field_if_present(
        cert, lines, "expires", "Expires", _format_certification_date
    )

    # ID field
    _append_field_if_present(
        cert, lines, "certification_id", "Certification ID", _format_certification_field
    )


def _serialize_single_certification(cert: any) -> list[str]:
    """Serialize a single certification entry to markdown lines.

    Args:
        cert: The certification object to serialize.

    Returns:
        list[str]: List of markdown lines for the certification.

    Notes:
        1. Adds the "## Certification" header and blank line.
        2. Adds all certification fields using `_add_certification_fields_to_lines`.
        3. Adds trailing blank line.
        4. Returns the list of markdown lines.

    """
    lines = ["## Certification", ""]
    _add_certification_fields_to_lines(cert, lines)
    lines.append("")
    return lines


def serialize_certifications_to_markdown(
    certifications: CertificationsResponse | None,
) -> str:
    """Serialize certifications information to Markdown format.

    Args:
        certifications (CertificationsResponse | None): Certifications information to serialize, containing a list of certifications.

    Returns:
        str: Markdown formatted certifications section.

    Notes:
        1. Initializes certifications with empty list if not provided.
        2. Initializes lines list with header.
        3. For each certification, serializes it using `_serialize_single_certification`.
        4. If any certifications were serialized, returns the formatted string.
        5. Returns empty string if no certifications present.
        6. No network, disk, or database access is performed during this function.

    """
    if not certifications or not hasattr(certifications, "certifications"):
        certifications = CertificationsResponse(certifications=[])

    lines = ["# Certifications", ""]

    for cert in certifications.certifications:
        lines.extend(_serialize_single_certification(cert))

    if certifications.certifications:
        return "\n".join(lines) + "\n"
    return ""


def update_resume_content_with_structured_data(
    current_content: str,
    personal_info: PersonalInfoResponse | None = None,
    education: EducationResponse | None = None,
    certifications: CertificationsResponse | None = None,
    experience: ExperienceResponse | None = None,
) -> str:
    """Update resume content with structured data by replacing specific sections.

    Args:
        current_content (str): Current resume Markdown content to update.
        personal_info (PersonalInfoResponse | None): Updated personal information to insert. If None, the existing info is preserved.
        education (EducationResponse | None): Updated education information to insert. If None, the existing info is preserved.
        certifications (CertificationsResponse | None): Updated certifications information to insert. If None, the existing info is preserved.
        experience (ExperienceResponse | None): Updated experience information to insert. If None, the existing info is preserved.

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
