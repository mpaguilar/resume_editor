import logging

from resume_writer.models.parsers import ParseContext
from resume_writer.models.resume import Resume as WriterResume

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
        1. Splits the resume content into lines.
        2. Creates a ParseContext for parsing.
        3. Parses the resume using the resume_writer module.
        4. Retrieves the personal section from the parsed resume.
        5. Checks if contact information is present; if not, returns an empty response.
        6. Extracts contact info and websites from the parsed personal section.
        7. Maps the extracted data to the PersonalInfoResponse fields.
        8. Returns the populated response or an empty one if parsing fails.
        9. No network, disk, or database access is performed during this function.

    """
    try:
        lines = resume_content.splitlines()
        parse_context = ParseContext(lines, 1)
        parsed_resume = WriterResume.parse(parse_context)
        personal = parsed_resume.personal

        if not personal:
            return PersonalInfoResponse()

        data = {}

        contact_info = getattr(personal, "contact_info", None)
        if contact_info is not None:
            data["name"] = getattr(contact_info, "name", None)
            data["email"] = getattr(contact_info, "email", None)
            data["phone"] = getattr(contact_info, "phone", None)
            data["location"] = getattr(contact_info, "location", None)

        websites = getattr(personal, "websites", None)
        if websites is not None:
            data["website"] = getattr(websites, "website", None)
            data["github"] = getattr(websites, "github", None)
            data["linkedin"] = getattr(websites, "linkedin", None)
            data["twitter"] = getattr(websites, "twitter", None)

        visa_status = getattr(personal, "visa_status", None)
        if visa_status is not None:
            data["work_authorization"] = getattr(
                visa_status,
                "work_authorization",
                None,
            )
            data["require_sponsorship"] = getattr(
                visa_status,
                "require_sponsorship",
                None,
            )

        banner = getattr(personal, "banner", None)
        if banner is not None:
            data["banner"] = getattr(banner, "text", None)

        note = getattr(personal, "note", None)
        if note is not None:
            data["note"] = getattr(note, "text", None)

        return PersonalInfoResponse(**data)
    except Exception as e:
        # If parsing fails, re-raise the exception to be handled by the caller.
        _msg = "Failed to parse personal info from resume content."
        log.exception(_msg)
        raise ValueError(_msg) from e


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
        lines = resume_content.splitlines()
        parse_context = ParseContext(lines, 1)
        parsed_resume = WriterResume.parse(parse_context)
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
    except Exception as e:
        # If parsing fails, re-raise the exception to be handled by the caller.
        _msg = "Failed to parse education info from resume content."
        log.exception(_msg)
        raise ValueError(_msg) from e


def extract_experience_info(resume_content: str) -> ExperienceResponse:
    """
    Extract experience information from resume content.

    Args:
        resume_content (str): The Markdown content of the resume to parse.

    Returns:
        ExperienceResponse: Extracted experience information containing a list of roles and projects.

    Raises:
        ValueError: If parsing fails due to invalid or malformed resume content.

    Notes:
        1. Splits the resume content into lines.
        2. Creates a ParseContext for parsing.
        3. Parses the resume using the resume_writer module.
        4. Retrieves the experience section from the parsed resume.
        5. Checks if experience data is present; if not, returns an empty response.
        6. Loops through each role and extracts basics, summary, responsibilities and skills.
        7. Loops through each project and extracts overview, description, and skills.
        8. Maps the extracted data into a dictionary with nested structure.
        9. Returns a list of dictionaries wrapped in the ExperienceResponse model.
        10. If parsing fails, returns an empty response.
        11. No network, disk, or database access is performed during this function.

    """
    try:
        lines = resume_content.splitlines()
        parse_context = ParseContext(lines, 1)
        parsed_resume = WriterResume.parse(parse_context)
        experience = parsed_resume.experience

        if not experience:
            return ExperienceResponse(roles=[], projects=[])

        has_roles = bool(getattr(experience, "roles", None))
        has_projects = bool(getattr(experience, "projects", None))
        if not has_roles and not has_projects:
            # Check for content in the original markdown string.
            in_experience_section = False
            content_found = False
            for line in lines:
                stripped_line = line.strip()
                if stripped_line.lower() == "# experience":
                    in_experience_section = True
                    continue

                if in_experience_section and stripped_line:
                    # Headers for empty sections are not "content"
                    if stripped_line.lower() not in ["## roles", "## projects"]:
                        content_found = True
                    break  # Found first line of content or next section
            if content_found:
                raise ValueError(
                    "Experience section contains content that could not be parsed.",
                )

        roles_list = []
        if hasattr(experience, "roles") and experience.roles is not None:
            for role in experience.roles:
                role_dict = {}

                # Basics
                role_basics = getattr(role, "basics", None)
                if role_basics:
                    start_date = getattr(role_basics, "start_date", None)
                    end_date = getattr(role_basics, "end_date", None)
                    role_dict["basics"] = {
                        "company": getattr(role_basics, "company", None),
                        "title": getattr(role_basics, "title", None),
                        "start_date": start_date,
                        "end_date": end_date,
                        "location": getattr(role_basics, "location", None),
                        "agency_name": getattr(role_basics, "agency_name", None),
                        "job_category": getattr(role_basics, "job_category", None),
                        "employment_type": getattr(
                            role_basics,
                            "employment_type",
                            None,
                        ),
                        "reason_for_change": getattr(
                            role_basics,
                            "reason_for_change",
                            None,
                        ),
                    }

                # Summary
                summary = getattr(role, "summary", None)
                if summary and hasattr(summary, "summary"):
                    role_dict["summary"] = {"text": summary.summary}

                # Responsibilities
                responsibilities = getattr(role, "responsibilities", None)
                if responsibilities and hasattr(responsibilities, "text"):
                    role_dict["responsibilities"] = {"text": responsibilities.text}

                # Skills
                skills = getattr(role, "skills", None)
                if skills and hasattr(skills, "skills"):
                    role_dict["skills"] = {"skills": skills.skills}

                if role_dict:
                    roles_list.append(role_dict)

        projects_list = []
        if hasattr(experience, "projects") and experience.projects is not None:
            for project in experience.projects:
                project_dict = {}

                # Overview
                project_overview = getattr(project, "overview", None)
                if project_overview:
                    start_date = getattr(project_overview, "start_date", None)
                    end_date = getattr(project_overview, "end_date", None)
                    project_dict["overview"] = {
                        "title": getattr(project_overview, "title", None),
                        "url": getattr(project_overview, "url", None),
                        "url_description": getattr(
                            project_overview,
                            "url_description",
                            None,
                        ),
                        "start_date": start_date,
                        "end_date": end_date,
                    }

                # Description
                description = getattr(project, "description", None)
                if description and hasattr(description, "text"):
                    project_dict["description"] = {"text": description.text}

                # Skills
                skills = getattr(project, "skills", None)
                if skills and hasattr(skills, "skills"):
                    project_dict["skills"] = {"skills": skills.skills}

                if project_dict:
                    projects_list.append(project_dict)
        _ret = ExperienceResponse(roles=roles_list, projects=projects_list)
        return _ret
    except Exception as e:
        # If parsing fails, re-raise the exception to be handled by the caller.
        _msg = "Failed to parse experience info from resume content."
        log.exception(_msg)
        raise ValueError(_msg) from e


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
        lines = resume_content.splitlines()
        parse_context = ParseContext(lines, 1)
        parsed_resume = WriterResume.parse(parse_context)
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
    except Exception as e:
        # If parsing fails, re-raise the exception to be handled by the caller.
        _msg = "Failed to parse certifications info from resume content."
        log.exception(_msg)
        raise ValueError(_msg) from e


def serialize_personal_info_to_markdown(personal_info) -> str:
    """
    Serialize personal information to Markdown format.

    Args:
        personal_info: Personal information to serialize, containing name, email, phone, location, and website.

    Returns:
        str: Markdown formatted personal information section.

    Notes:
        1. Initializes an empty list of lines and adds a heading.
        2. Adds each field (name, email, phone, location) as a direct field if present.
        3. Adds a Websites section if website is present.
        4. Joins the lines with newlines.
        5. Returns the formatted string with a trailing newline.
        6. Returns an empty string if no personal data is present.
        7. No network, disk, or database access is performed during this function.

    """
    if not personal_info:
        personal_info = PersonalInfoResponse()

    lines = ["# Personal", ""]

    # Add contact information
    has_contact_info = any(
        [
            getattr(personal_info, "name", None),
            getattr(personal_info, "email", None),
            getattr(personal_info, "phone", None),
            getattr(personal_info, "location", None),
        ],
    )
    if has_contact_info:
        lines.append("## Contact Information")
        lines.append("")
        if getattr(personal_info, "name", None):
            lines.append(f"Name: {personal_info.name}")
        if getattr(personal_info, "email", None):
            lines.append(f"Email: {personal_info.email}")
        if getattr(personal_info, "phone", None):
            lines.append(f"Phone: {personal_info.phone}")
        if getattr(personal_info, "location", None):
            lines.append(f"Location: {personal_info.location}")
        lines.append("")

    # Add websites
    has_websites = any(
        [
            getattr(personal_info, "github", None),
            getattr(personal_info, "linkedin", None),
            getattr(personal_info, "website", None),
            getattr(personal_info, "twitter", None),
        ],
    )
    if has_websites:
        lines.append("## Websites")
        lines.append("")
        if getattr(personal_info, "github", None):
            lines.append(f"GitHub: {personal_info.github}")
        if getattr(personal_info, "linkedin", None):
            lines.append(f"LinkedIn: {personal_info.linkedin}")
        if getattr(personal_info, "website", None):
            lines.append(f"Website: {personal_info.website}")
        if getattr(personal_info, "twitter", None):
            lines.append(f"Twitter: {personal_info.twitter}")
        lines.append("")

    # Add visa status
    has_visa_status = any(
        [
            getattr(personal_info, "work_authorization", None),
            getattr(personal_info, "require_sponsorship", None) is not None,
        ],
    )
    if has_visa_status:
        lines.append("## Visa Status")
        lines.append("")
        if getattr(personal_info, "work_authorization", None):
            lines.append(f"Work Authorization: {personal_info.work_authorization}")
        if getattr(personal_info, "require_sponsorship", None) is not None:
            sponsorship = "Yes" if personal_info.require_sponsorship else "No"
            lines.append(f"Require sponsorship: {sponsorship}")
        lines.append("")

    # Add banner
    if getattr(personal_info, "banner", None):
        lines.append("## Banner")
        lines.append("")
        lines.append(str(personal_info.banner))
        lines.append("")

    # Add note
    if getattr(personal_info, "note", None):
        lines.append("## Note")
        lines.append("")
        lines.append(str(personal_info.note))
        lines.append("")

    # Only return content if there's more than just the main header
    if len(lines) > 2:
        return "\n".join(lines) + "\n"

    return ""


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
        3. Builds the overview content with title, URL, URL description, start date, and end date.
        4. Adds the overview section to the project content.
        5. If the inclusion status is not NOT_RELEVANT:
            a. Adds the description if present.
            b. Adds the skills if present.
        6. Returns the full project content as a list of lines.

    """
    overview = getattr(project, "overview", None)
    if not overview:
        return []

    inclusion_status = getattr(overview, "inclusion_status", InclusionStatus.INCLUDE)
    if inclusion_status == InclusionStatus.OMIT:
        return []

    project_content = []
    overview_content = []
    if getattr(overview, "title", None):
        overview_content.append(f"Title: {overview.title}")
    if getattr(overview, "url", None):
        overview_content.append(f"Url: {overview.url}")
    if getattr(overview, "url_description", None):
        overview_content.append(f"Url Description: {overview.url_description}")
    if getattr(overview, "start_date", None):
        overview_content.append(f"Start date: {overview.start_date.strftime('%m/%Y')}")
    if getattr(overview, "end_date", None):
        overview_content.append(f"End date: {overview.end_date.strftime('%m/%Y')}")

    if overview_content:
        project_content.extend(["#### Overview", ""])
        project_content.extend(overview_content)
        project_content.append("")

    if inclusion_status != InclusionStatus.NOT_RELEVANT:
        description = getattr(project, "description", None)
        if description:
            project_content.extend(["#### Description", "", description.text, ""])

        skills = getattr(project, "skills", None)
        if skills and hasattr(skills, "skills") and skills.skills:
            project_content.extend(["#### Skills", ""])
            project_content.extend([f"* {skill}" for skill in skills.skills])
            project_content.append("")

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
        1. Gets the basics from the role.
        2. Checks if the inclusion status is OMIT; if so, returns an empty list.
        3. Builds the basics content with company, title, employment type, job category, agency name, start date, end date, reason for change, and location.
        4. Adds the basics section to the role content.
        5. If the inclusion status is not NOT_RELEVANT:
            a. Adds the summary if present.
            b. Adds the responsibilities if present.
            c. Adds the skills if present.
        6. Returns the full role content as a list of lines.

    """
    basics = getattr(role, "basics", None)
    if not basics:
        return []

    inclusion_status = getattr(basics, "inclusion_status", InclusionStatus.INCLUDE)
    if inclusion_status == InclusionStatus.OMIT:
        return []

    role_content = []
    basics_content = []
    if getattr(basics, "company", None):
        basics_content.append(f"Company: {basics.company}")
    if getattr(basics, "title", None):
        basics_content.append(f"Title: {basics.title}")
    if getattr(basics, "employment_type", None):
        basics_content.append(f"Employment type: {basics.employment_type}")
    if getattr(basics, "job_category", None):
        basics_content.append(f"Job category: {basics.job_category}")
    if getattr(basics, "agency_name", None):
        basics_content.append(f"Agency: {basics.agency_name}")
    if getattr(basics, "start_date", None):
        basics_content.append(f"Start date: {basics.start_date.strftime('%m/%Y')}")
    if getattr(basics, "end_date", None):
        basics_content.append(f"End date: {basics.end_date.strftime('%m/%Y')}")
    if getattr(basics, "reason_for_change", None):
        basics_content.append(f"Reason for change: {basics.reason_for_change}")
    if getattr(basics, "location", None):
        basics_content.append(f"Location: {basics.location}")

    if basics_content:
        role_content.extend(["#### Basics", ""])
        role_content.extend(basics_content)
        role_content.append("")

    if inclusion_status != InclusionStatus.NOT_RELEVANT:
        summary = getattr(role, "summary", None)
        if summary:
            role_content.extend(["#### Summary", "", summary.text, ""])

        responsibilities = getattr(role, "responsibilities", None)
        if responsibilities:
            role_content.extend(
                [
                    "#### Responsibilities",
                    "",
                    responsibilities.text,
                    "",
                ],
            )

        skills = getattr(role, "skills", None)
        if skills and hasattr(skills, "skills") and skills.skills:
            role_content.extend(["#### Skills", ""])
            role_content.extend([f"* {skill}" for skill in skills.skills])
            role_content.append("")

    if role_content:
        return ["### Role", ""] + role_content
    return []


def serialize_experience_to_markdown(experience) -> str:
    """
    Serialize experience information to Markdown format.

    Args:
        experience: Experience information to serialize, containing a list of roles.

    Returns:
        str: Markdown formatted experience section.

    Notes:
        1. Checks if the experience list is empty.
        2. Initializes an empty list of lines and adds a heading.
        3. For each role in the list:
            a. Adds a subsection header.
            b. Adds each field (company, title, start_date, end_date, location, description) using proper subsection structure.
            c. Adds a blank line after each role.
        4. Joins the lines with newlines.
        5. Returns the formatted string with a trailing newline.
        6. Returns an empty string if no experience data is present or all is filtered out.
        7. No network, disk, or database access is performed during this function.

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
