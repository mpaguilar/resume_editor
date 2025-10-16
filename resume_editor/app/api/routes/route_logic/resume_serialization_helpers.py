import logging

from resume_writer.models.parsers import ParseContext
from resume_writer.models.resume import Resume as WriterResume

from resume_editor.app.api.routes.route_models import PersonalInfoResponse
from resume_editor.app.models.resume.experience import InclusionStatus

log = logging.getLogger(__name__)


def _parse_resume(resume_content: str) -> WriterResume:
    """Parse resume content using resume_writer.

    Args:
        resume_content (str): The Markdown content of the resume to parse.

    Returns:
        WriterResume: The parsed resume object.

    Raises:
        ValueError: If parsing fails.

    Notes:
        1. Splits content into lines.
        2. Creates a ParseContext.
        3. Attempts to parse the resume using WriterResume.parse.
        4. On any exception, logs and raises a ValueError.

    """
    log.debug("_parse_resume starting")
    try:
        lines = resume_content.splitlines()
        parse_context = ParseContext(lines, 1)
        parsed_resume = WriterResume.parse(parse_context)
        log.debug("_parse_resume returning")
        return parsed_resume
    except Exception as e:
        _msg = "Failed to parse resume content."
        log.exception(_msg)
        raise ValueError(_msg) from e


def _check_for_unparsed_content(
    resume_content: str,
    section_name: str,
    parsed_section: any,
) -> None:
    """Check for unparsed content in a resume section.

    Args:
        resume_content (str): The raw resume content.
        section_name (str): The name of the section to check (e.g., "personal").
        parsed_section (any): The result from the parser for this section.

    Raises:
        ValueError: If the section was not parsed but raw content exists.

    Notes:
        1. If 'parsed_section' is not empty, return.
        2. Iterate through 'resume_content' lines to find the section header.
        3. Once inside the section, check for any non-empty lines before the next top-level section.
        4. If any content is found, log a warning and raise a ValueError.

    """
    log.debug("_check_for_unparsed_content starting")
    if parsed_section:
        log.debug("_check_for_unparsed_content returning, parsed_section found")
        return

    lines = resume_content.splitlines()
    in_section = False
    content_found = False
    section_header = f"# {section_name.lower()}"

    for line in lines:
        stripped_line = line.strip()
        if stripped_line.lower() == section_header:
            in_section = True
            continue

        if in_section:
            if stripped_line.lower().startswith("# "):
                break  # Next section
            if stripped_line:
                content_found = True
                break
    if content_found:
        _msg = f"Failed to parse {section_name} info from resume content."
        log.warning(
            f"{section_name.capitalize()} section contains content that could not be parsed. "
            "The parser did not fail, but no data was found.",
        )
        raise ValueError(_msg)
    log.debug("_check_for_unparsed_content returning")


def _extract_data_from_personal_section(personal: any) -> dict:
    """Extract data from a parsed personal section into a dictionary.
    Args:
        personal (any): The parsed personal section from resume_writer.
    Returns:
        dict: A dictionary of personal information.
    Notes:
        1. If `personal` is None, returns an empty dictionary.
        2. Extracts contact info: name, email, phone, location.
        3. Extracts websites: website, github, linkedin, twitter.
        4. Extracts visa status: work_authorization, require_sponsorship.
        5. Extracts banner text.
        6. Extracts note text.
        7. Returns a dictionary containing all extracted data.

    """
    log.debug("_extract_data_from_personal_section starting")
    if not personal:
        log.debug("_extract_data_from_personal_section returning empty dict")
        return {}

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
    if banner and hasattr(banner, "text"):
        data["banner"] = banner.text

    note = getattr(personal, "note", None)
    if note and hasattr(note, "text"):
        data["note"] = note.text
    log.debug("_extract_data_from_personal_section returning")
    return data


def _convert_writer_role_to_dict(role: any) -> dict:
    """Convert a resume_writer Role object to a dictionary.
    Args:
        role (any): The parsed role object from resume_writer.
    Returns:
        dict: A dictionary of role information.
    Notes:
        1. Extracts basics: company, title, dates, etc.
        2. Extracts summary text.
        3. Extracts responsibilities text.
        4. Extracts skills list.
        5. Returns a dictionary containing all extracted data.

    """
    log.debug("_convert_writer_role_to_dict starting")
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
        role_dict["responsibilities"] = {
            "text": responsibilities.text,
        }

    # Skills
    skills = getattr(role, "skills", None)
    if skills and hasattr(skills, "skills"):
        role_dict["skills"] = {"skills": skills.skills}

    log.debug("_convert_writer_role_to_dict returning")
    return role_dict


def _convert_writer_project_to_dict(project: any) -> dict:
    """Convert a resume_writer Project object to a dictionary.
    Args:
        project (any): The parsed project object from resume_writer.
    Returns:
        dict: A dictionary of project information.
    Notes:
        1. Extracts overview: title, url, dates, inclusion_status, etc.
        2. Extracts description text.
        3. Extracts skills list.
        4. Returns a dictionary containing all extracted data.

    """
    log.debug("_convert_writer_project_to_dict starting")
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
            "inclusion_status": getattr(
                project_overview,
                "inclusion_status",
                InclusionStatus.INCLUDE,
            ),
        }

    # Description
    description = getattr(project, "description", None)
    if description and hasattr(description, "text"):
        project_dict["description"] = {"text": description.text}

    # Skills
    skills = getattr(project, "skills", None)
    if skills and hasattr(skills, "skills"):
        project_dict["skills"] = {"skills": skills.skills}

    log.debug("_convert_writer_project_to_dict returning")
    return project_dict


def _add_contact_info_markdown(
    personal_info: PersonalInfoResponse,
    lines: list[str],
) -> None:
    """Adds contact info Markdown to a list of lines.
    Args:
        personal_info (PersonalInfoResponse): The personal info data.
        lines (list[str]): The list of lines to append to.
    Notes:
        1. Checks for name, email, phone, location.
        2. If any exist, adds a "Contact Information" section header.
        3. Appends each non-empty field.
        4. Adds a trailing blank line to the section.

    """
    log.debug("_add_contact_info_markdown starting")
    contact_fields = ["name", "email", "phone", "location"]
    if any(getattr(personal_info, field, None) for field in contact_fields):
        lines.extend(["## Contact Information", ""])
        if personal_info.name:
            lines.append(f"Name: {personal_info.name}")
        if personal_info.email:
            lines.append(f"Email: {personal_info.email}")
        if personal_info.phone:
            lines.append(f"Phone: {personal_info.phone}")
        if personal_info.location:
            lines.append(f"Location: {personal_info.location}")
        lines.append("")
    log.debug("_add_contact_info_markdown returning")


def _add_websites_markdown(
    personal_info: PersonalInfoResponse,
    lines: list[str],
) -> None:
    """Adds websites Markdown to a list of lines.
    Args:
        personal_info (PersonalInfoResponse): The personal info data.
        lines (list[str]): The list of lines to append to.
    Notes:
        1. Checks for github, linkedin, website, twitter.
        2. If any exist, adds a "Websites" section header.
        3. Appends each non-empty field.
        4. Adds a trailing blank line to the section.

    """
    log.debug("_add_websites_markdown starting")
    website_fields = ["github", "linkedin", "website", "twitter"]
    if any(getattr(personal_info, field, None) for field in website_fields):
        lines.extend(["## Websites", ""])
        if personal_info.github:
            lines.append(f"GitHub: {personal_info.github}")
        if personal_info.linkedin:
            lines.append(f"LinkedIn: {personal_info.linkedin}")
        if personal_info.website:
            lines.append(f"Website: {personal_info.website}")
        if personal_info.twitter:
            lines.append(f"Twitter: {personal_info.twitter}")
        lines.append("")
    log.debug("_add_websites_markdown returning")


def _add_visa_status_markdown(
    personal_info: PersonalInfoResponse,
    lines: list[str],
) -> None:
    """Adds visa status Markdown to a list of lines.
    Args:
        personal_info (PersonalInfoResponse): The personal info data.
        lines (list[str]): The list of lines to append to.
    Notes:
        1. Checks for work_authorization or require_sponsorship.
        2. If any exist, adds a "Visa Status" section header.
        3. Appends each field if it has a value.
        4. Adds a trailing blank line to the section.

    """
    log.debug("_add_visa_status_markdown starting")
    if (
        personal_info.work_authorization
        or personal_info.require_sponsorship is not None
    ):
        lines.extend(["## Visa Status", ""])
        if personal_info.work_authorization:
            lines.append(f"Work Authorization: {personal_info.work_authorization}")
        if personal_info.require_sponsorship is not None:
            sponsorship = "Yes" if personal_info.require_sponsorship else "No"
            lines.append(f"Require sponsorship: {sponsorship}")
        lines.append("")
    log.debug("_add_visa_status_markdown returning")


def _add_banner_markdown(personal_info: PersonalInfoResponse, lines: list[str]) -> None:
    """Adds banner Markdown to a list of lines.
    Args:
        personal_info (PersonalInfoResponse): The personal info data.
        lines (list[str]): The list of lines to append to.
    Notes:
        1. Checks for banner text.
        2. If it exists, adds a "Banner" section header and the text.
        3. Adds a trailing blank line to the section.

    """
    log.debug("_add_banner_markdown starting")
    if personal_info.banner:
        lines.extend(["## Banner", "", str(personal_info.banner), ""])
    log.debug("_add_banner_markdown returning")


def _add_note_markdown(personal_info: PersonalInfoResponse, lines: list[str]) -> None:
    """Adds note Markdown to a list of lines.
    Args:
        personal_info (PersonalInfoResponse): The personal info data.
        lines (list[str]): The list of lines to append to.
    Notes:
        1. Checks for note text.
        2. If it exists, adds a "Note" section header and the text.
        3. Adds a trailing blank line to the section.

    """
    log.debug("_add_note_markdown starting")
    if personal_info.note:
        lines.extend(["## Note", "", str(personal_info.note), ""])
    log.debug("_add_note_markdown returning")


def _add_project_overview_markdown(overview: any, lines: list[str]) -> None:
    """Adds project overview Markdown to a list of lines.
    Args:
        overview (any): The parsed project overview from resume_writer.
        lines (list[str]): The list of lines to append to.
    Notes:
        1. Checks for title, url, url_description, start_date, end_date.
        2. If any exist, adds an "Overview" section header.
        3. Appends each non-empty field.
        4. Adds a trailing blank line to the section.

    """
    log.debug("_add_project_overview_markdown starting")
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
        lines.extend(["#### Overview", ""])
        lines.extend(overview_content)
        lines.append("")
    log.debug("_add_project_overview_markdown returning")


def _add_project_description_markdown(description: any, lines: list[str]) -> None:
    """Adds project description Markdown to a list of lines.
    Args:
        description (any): The parsed project description from resume_writer.
        lines (list[str]): The list of lines to append to.
    Notes:
        1. Checks for description text.
        2. If it exists, adds a "Description" section header and the text.
        3. Adds a trailing blank line to the section.

    """
    log.debug("_add_project_description_markdown starting")
    if description and getattr(description, "text", None):
        lines.extend(["#### Description", "", description.text, ""])
    log.debug("_add_project_description_markdown returning")


def _add_project_skills_markdown(skills: any, lines: list[str]) -> None:
    """Adds project skills Markdown to a list of lines.
    Args:
        skills (any): The parsed project skills from resume_writer.
        lines (list[str]): The list of lines to append to.
    Notes:
        1. Checks for a list of skills.
        2. If it exists, adds a "Skills" section header and the skills as a bulleted list.
        3. Adds a trailing blank line to the section.

    """
    log.debug("_add_project_skills_markdown starting")
    if skills and hasattr(skills, "skills") and skills.skills:
        lines.extend(["#### Skills", ""])
        lines.extend([f"* {skill}" for skill in skills.skills])
        lines.append("")
    log.debug("_add_project_skills_markdown returning")


def _add_role_basics_markdown(basics: any, lines: list[str]) -> None:
    """Adds role basics Markdown to a list of lines.
    Args:
        basics (any): The parsed role basics from resume_writer.
        lines (list[str]): The list of lines to append to.
    Notes:
        1. Defines mappings for string and date fields to their labels.
        2. Iterates through the field mappings to collect basics info.
        3. Formats date fields to 'MM/YYYY'.
        4. If any data is collected, adds a "Basics" section header.
        5. Appends each non-empty field.
        6. Adds a trailing blank line.

    """
    log.debug("_add_role_basics_markdown starting")
    basics_content = []

    string_fields = {
        "company": "Company",
        "title": "Title",
        "employment_type": "Employment type",
        "job_category": "Job category",
        "agency_name": "Agency",
        "reason_for_change": "Reason for change",
        "location": "Location",
    }
    date_fields = {
        "start_date": "Start date",
        "end_date": "End date",
    }

    for attr, label in string_fields.items():
        value = getattr(basics, attr, None)
        if value:
            basics_content.append(f"{label}: {value}")

    for attr, label in date_fields.items():
        value = getattr(basics, attr, None)
        if value:
            basics_content.append(f"{label}: {value.strftime('%m/%Y')}")

    if basics_content:
        lines.extend(["#### Basics", ""])
        lines.extend(basics_content)
        lines.append("")
    log.debug("_add_role_basics_markdown returning")


def _add_role_summary_markdown(summary: any, lines: list[str]) -> None:
    """Adds role summary Markdown to a list of lines.
    Args:
        summary (any): The parsed role summary from resume_writer.
        lines (list[str]): The list of lines to append to.
    Notes:
        1. Checks for summary text.
        2. If present, adds a "Summary" section header and the text.
        3. Adds a trailing blank line.

    """
    log.debug("_add_role_summary_markdown starting")
    if summary and getattr(summary, "text", None):
        lines.extend(["#### Summary", "", summary.text, ""])
    log.debug("_add_role_summary_markdown returning")


def _add_role_responsibilities_markdown(
    responsibilities: any,
    inclusion_status: InclusionStatus,
    lines: list[str],
) -> None:
    """Adds role responsibilities Markdown to a list of lines.
    Args:
        responsibilities (any): The parsed role responsibilities from resume_writer.
        inclusion_status (InclusionStatus): The inclusion status of the role.
        lines (list[str]): The list of lines to append to.
    Notes:
        1. If inclusion_status is `NOT_RELEVANT`, appends a placeholder.
        2. If inclusion_status is `INCLUDE` and responsibilities text exists, appends the text.
        3. Adds section header and trailing blank line as appropriate.

    """
    log.debug("_add_role_responsibilities_markdown starting")
    if inclusion_status == InclusionStatus.NOT_RELEVANT:
        lines.extend(
            [
                "#### Responsibilities",
                "",
                "(no relevant experience)",
                "",
            ],
        )
    elif inclusion_status == InclusionStatus.INCLUDE:
        if responsibilities and getattr(responsibilities, "text", None):
            lines.extend(
                [
                    "#### Responsibilities",
                    "",
                    responsibilities.text,
                    "",
                ],
            )
    log.debug("_add_role_responsibilities_markdown returning")


def _add_role_skills_markdown(skills: any, lines: list[str]) -> None:
    """Adds role skills Markdown to a list of lines.
    Args:
        skills (any): The parsed role skills from resume_writer.
        lines (list[str]): The list of lines to append to.
    Notes:
        1. Checks for a list of skills.
        2. If it exists and is not empty, adds a "Skills" section header.
        3. Appends the skills as a bulleted list.
        4. Adds a trailing blank line.

    """
    log.debug("_add_role_skills_markdown starting")
    if skills and hasattr(skills, "skills") and skills.skills:
        lines.extend(["#### Skills", ""])
        lines.extend([f"* {skill}" for skill in skills.skills])
        lines.append("")
    log.debug("_add_role_skills_markdown returning")
