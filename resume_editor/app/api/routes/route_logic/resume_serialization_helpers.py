import logging

from resume_writer.models.parsers import ParseContext
from resume_writer.models.resume import Resume as WriterResume

from resume_editor.app.api.routes.route_models import PersonalInfoResponse
from resume_editor.app.models.resume.experience import InclusionStatus
from resume_editor.app.models.resume.personal import Banner, Note

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


def _is_section_start(line: str, section_header: str) -> bool:
    """Check if line is the section header.

    Args:
        line (str): The line to check.
        section_header (str): The section header to match.

    Returns:
        bool: True if line matches section header.

    """
    return line.strip().lower() == section_header


def _is_next_section(line: str) -> bool:
    """Check if line is the start of a new section.

    Args:
        line (str): The line to check.

    Returns:
        bool: True if line starts a new section.

    """
    return line.strip().lower().startswith("# ")


def _scan_section_for_content(lines: list[str], section_header: str) -> bool:
    """Scan lines for content within a specific section.

    Args:
        lines (list[str]): The content lines to search.
        section_header (str): The section header to find.

    Returns:
        bool: True if content is found in the section.

    Notes:
        1. Iterate through lines to find the section header.
        2. Once inside the section, check for any non-empty lines before next section.
        3. Return True if content is found, False otherwise.

    """
    in_section = False

    for line in lines:
        if not in_section:
            in_section = _is_section_start(line, section_header)
        elif _is_next_section(line):
            break
        elif line.strip():
            return True

    return False


def _find_content_in_section(lines: list[str], section_header: str) -> bool:
    """Check if any content exists in a section.

    Args:
        lines (list[str]): The content lines to search.
        section_header (str): The section header to find.

    Returns:
        bool: True if content is found in the section.

    Notes:
        1. Delegate to scanning function to check for content.

    """
    return _scan_section_for_content(lines, section_header)


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
        2. Search for content in the section using helper function.
        3. If any content is found, log a warning and raise a ValueError.

    """
    log.debug("_check_for_unparsed_content starting")
    if parsed_section:
        log.debug("_check_for_unparsed_content returning, parsed_section found")
        return

    lines = resume_content.splitlines()
    section_header = f"# {section_name.lower()}"
    content_found = _find_content_in_section(lines, section_header)

    if content_found:
        _msg = f"Failed to parse {section_name} info from resume content."
        log.warning(
            f"{section_name.capitalize()} section contains content that could not be parsed. "
            "The parser did not fail, but no data was found.",
        )
        raise ValueError(_msg)
    log.debug("_check_for_unparsed_content returning")


def _extract_contact_info(data: dict, personal: any) -> None:
    """Extract contact info from personal section.

    Args:
        data (dict): The dictionary to populate.
        personal (any): The parsed personal section.

    Notes:
        1. Gets contact_info attribute from personal.
        2. If contact_info exists, extracts name, email, phone, location.

    """
    contact_info = getattr(personal, "contact_info", None)
    if contact_info is not None:
        data["name"] = getattr(contact_info, "name", None)
        data["email"] = getattr(contact_info, "email", None)
        data["phone"] = getattr(contact_info, "phone", None)
        data["location"] = getattr(contact_info, "location", None)


def _extract_websites(data: dict, personal: any) -> None:
    """Extract websites from personal section.

    Args:
        data (dict): The dictionary to populate.
        personal (any): The parsed personal section.

    Notes:
        1. Gets websites attribute from personal.
        2. If websites exists, extracts website, github, linkedin, twitter.

    """
    websites = getattr(personal, "websites", None)
    if websites is not None:
        data["website"] = getattr(websites, "website", None)
        data["github"] = getattr(websites, "github", None)
        data["linkedin"] = getattr(websites, "linkedin", None)
        data["twitter"] = getattr(websites, "twitter", None)


def _extract_visa_status(data: dict, personal: any) -> None:
    """Extract visa status from personal section.

    Args:
        data (dict): The dictionary to populate.
        personal (any): The parsed personal section.

    Notes:
        1. Gets visa_status attribute from personal.
        2. If visa_status exists, extracts work_authorization and require_sponsorship.

    """
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


def _extract_banner_and_note(data: dict, personal: any) -> None:
    """Extract banner and note from personal section.

    Args:
        data (dict): The dictionary to populate.
        personal (any): The parsed personal section.

    Notes:
        1. Gets banner attribute and extracts text if it exists.
        2. Gets note attribute and extracts text if it exists.

    """
    banner = getattr(personal, "banner", None)
    if banner and hasattr(banner, "text"):
        data["banner"] = banner.text

    note = getattr(personal, "note", None)
    if note and hasattr(note, "text"):
        data["note"] = note.text


def _extract_data_from_personal_section(personal: any) -> dict:
    """Extract data from a parsed personal section into a dictionary.
    Args:
        personal (any): The parsed personal section from resume_writer.
    Returns:
        dict: A dictionary of personal information.
    Notes:
        1. If `personal` is None, returns an empty dictionary.
        2. Extracts contact info, websites, visa status, banner, and note.
        3. Returns a dictionary containing all extracted data.

    """
    log.debug("_extract_data_from_personal_section starting")
    if not personal:
        log.debug("_extract_data_from_personal_section returning empty dict")
        return {}

    data = {}

    _extract_contact_info(data, personal)
    _extract_websites(data, personal)
    _extract_visa_status(data, personal)
    _extract_banner_and_note(data, personal)

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


def _has_contact_info(personal_info: PersonalInfoResponse) -> bool:
    """Check if any contact info fields are present.

    Args:
        personal_info (PersonalInfoResponse): The personal info data.

    Returns:
        bool: True if any contact field exists.

    Notes:
        1. Checks name, email, phone, and location fields.
        2. Returns True if any field has a value.

    """
    contact_fields = ["name", "email", "phone", "location"]
    return any(getattr(personal_info, field, None) for field in contact_fields)


def _append_contact_fields(
    personal_info: PersonalInfoResponse, lines: list[str]
) -> None:
    """Append each contact field to lines if it exists.

    Args:
        personal_info (PersonalInfoResponse): The personal info data.
        lines (list[str]): The list of lines to append to.

    Notes:
        1. Checks each contact field and appends formatted line if present.

    """
    if personal_info.name:
        lines.append(f"Name: {personal_info.name}")
    if personal_info.email:
        lines.append(f"Email: {personal_info.email}")
    if personal_info.phone:
        lines.append(f"Phone: {personal_info.phone}")
    if personal_info.location:
        lines.append(f"Location: {personal_info.location}")


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
    if _has_contact_info(personal_info):
        lines.extend(["## Contact Information", ""])
        _append_contact_fields(personal_info, lines)
        lines.append("")
    log.debug("_add_contact_info_markdown returning")


def _has_website_info(personal_info: PersonalInfoResponse) -> bool:
    """Check if any website fields are present.

    Args:
        personal_info (PersonalInfoResponse): The personal info data.

    Returns:
        bool: True if any website field exists.

    Notes:
        1. Checks github, linkedin, website, and twitter fields.
        2. Returns True if any field has a value.

    """
    website_fields = ["github", "linkedin", "website", "twitter"]
    return any(getattr(personal_info, field, None) for field in website_fields)


def _append_website_fields(
    personal_info: PersonalInfoResponse, lines: list[str]
) -> None:
    """Append each website field to lines if it exists.

    Args:
        personal_info (PersonalInfoResponse): The personal info data.
        lines (list[str]): The list of lines to append to.

    Notes:
        1. Checks each website field and appends formatted line if present.

    """
    if personal_info.github:
        lines.append(f"GitHub: {personal_info.github}")
    if personal_info.linkedin:
        lines.append(f"LinkedIn: {personal_info.linkedin}")
    if personal_info.website:
        lines.append(f"Website: {personal_info.website}")
    if personal_info.twitter:
        lines.append(f"Twitter: {personal_info.twitter}")


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
    if _has_website_info(personal_info):
        lines.extend(["## Websites", ""])
        _append_website_fields(personal_info, lines)
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
        1. Checks if `personal_info.banner` has content.
        2. If the content is a string, it is used directly.
        3. If the content is a `Banner` object, the value of its `text` attribute is used.
        4. Any other type of content is ignored.
        5. If valid text is found, it adds a "Banner" section header and the text, followed by a blank line.

    """
    log.debug("_add_banner_markdown starting")
    if personal_info.banner:
        banner_text = None
        if isinstance(personal_info.banner, str):
            banner_text = personal_info.banner
        elif isinstance(personal_info.banner, Banner):
            banner_text = personal_info.banner.text

        if banner_text:
            lines.extend(["## Banner", "", banner_text, ""])

    log.debug("_add_banner_markdown returning")


def _add_note_markdown(personal_info: PersonalInfoResponse, lines: list[str]) -> None:
    """Adds note Markdown to a list of lines.
    Args:
        personal_info (PersonalInfoResponse): The personal info data.
        lines (list[str]): The list of lines to append to.
    Notes:
        1. Checks if `personal_info.note` has content.
        2. If the content is a string, it is used directly.
        3. If the content is a `Note` object, the value of its `text` attribute is used.
        4. Any other type of content is ignored.
        5. If valid text is found, it adds a "Note" section header and the text, followed by a blank line.

    """
    log.debug("_add_note_markdown starting")
    if personal_info.note:
        note_text = None
        if isinstance(personal_info.note, str):
            note_text = personal_info.note
        elif isinstance(personal_info.note, Note):
            note_text = personal_info.note.text

        if note_text:
            lines.extend(["## Note", "", note_text, ""])
    log.debug("_add_note_markdown returning")


def _format_overview_string_field(overview: any, field: str, label: str) -> str | None:
    """Format a string field from overview if it exists.

    Args:
        overview (any): The parsed project overview.
        field (str): The attribute name to get.
        label (str): The display label.

    Returns:
        str | None: Formatted field string or None if not present.

    """
    value = getattr(overview, field, None)
    return f"{label}: {value}" if value else None


def _format_overview_date_field(overview: any, field: str, label: str) -> str | None:
    """Format a date field from overview if it exists.

    Args:
        overview (any): The parsed project overview.
        field (str): The attribute name to get.
        label (str): The display label.

    Returns:
        str | None: Formatted date string or None if not present.

    """
    value = getattr(overview, field, None)
    return f"{label}: {value.strftime('%m/%Y')}" if value else None


def _collect_overview_fields(overview: any) -> list[str]:
    """Collect all non-empty overview fields.

    Args:
        overview (any): The parsed project overview from resume_writer.

    Returns:
        list[str]: List of formatted field strings.

    Notes:
        1. Collects string fields using helper.
        2. Collects date fields using helper.
        3. Returns combined list of non-None values.

    """
    fields = [
        _format_overview_string_field(overview, "title", "Title"),
        _format_overview_string_field(overview, "url", "Url"),
        _format_overview_string_field(overview, "url_description", "Url Description"),
        _format_overview_date_field(overview, "start_date", "Start date"),
        _format_overview_date_field(overview, "end_date", "End date"),
    ]

    return [f for f in fields if f is not None]


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
    overview_content = _collect_overview_fields(overview)

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


def _collect_string_basics(basics: any) -> list[str]:
    """Collect formatted string fields from role basics.

    Args:
        basics (any): The parsed role basics from resume_writer.

    Returns:
        list[str]: List of formatted string field lines.

    Notes:
        1. Defines mapping of attribute names to display labels.
        2. Iterates through mapping and collects non-empty fields.

    """
    string_fields = {
        "company": "Company",
        "title": "Title",
        "employment_type": "Employment type",
        "job_category": "Job category",
        "agency_name": "Agency",
        "reason_for_change": "Reason for change",
        "location": "Location",
    }
    result = []

    for attr, label in string_fields.items():
        value = getattr(basics, attr, None)
        if value:
            result.append(f"{label}: {value}")

    return result


def _collect_date_basics(basics: any) -> list[str]:
    """Collect formatted date fields from role basics.

    Args:
        basics (any): The parsed role basics from resume_writer.

    Returns:
        list[str]: List of formatted date field lines.

    Notes:
        1. Defines mapping of date attribute names to display labels.
        2. Formats dates to 'MM/YYYY' format.

    """
    date_fields = {
        "start_date": "Start date",
        "end_date": "End date",
    }
    result = []

    for attr, label in date_fields.items():
        value = getattr(basics, attr, None)
        if value:
            result.append(f"{label}: {value.strftime('%m/%Y')}")

    return result


def _add_role_basics_markdown(basics: any, lines: list[str]) -> None:
    """Adds role basics Markdown to a list of lines.
    Args:
        basics (any): The parsed role basics from resume_writer.
        lines (list[str]): The list of lines to append to.
    Notes:
        1. Collects string and date fields using helper functions.
        2. If any data is collected, adds a "Basics" section header.
        3. Appends each non-empty field.
        4. Adds a trailing blank line.

    """
    log.debug("_add_role_basics_markdown starting")
    basics_content = _collect_string_basics(basics) + _collect_date_basics(basics)

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
