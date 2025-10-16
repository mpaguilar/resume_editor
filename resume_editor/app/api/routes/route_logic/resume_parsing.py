import logging
from typing import Any

from fastapi import HTTPException
from resume_writer.models.parsers import ParseContext
from resume_writer.models.resume import Resume as WriterResume

from resume_editor.app.api.routes.route_logic.resume_serialization import (
    extract_certifications_info,
    extract_education_info,
    extract_experience_info,
    extract_personal_info,
)

log = logging.getLogger(__name__)


def parse_resume_to_writer_object(markdown_content: str) -> WriterResume:
    """Parse Markdown resume content into a resume_writer Resume object.

    Args:
        markdown_content (str): The Markdown content to parse, expected to follow a valid resume format.

    Returns:
        WriterResume: The parsed resume object from the resume_writer library, containing structured data for personal info, experience, education, certifications, etc.

    Raises:
        ValueError: If the parsed content contains no valid resume sections (e.g., no personal, education, experience, or certifications data).

    Notes:
        1. Split the input Markdown content into individual lines.
        2. Skip any lines before the first valid top-level section header (i.e., lines starting with "# " but not "##").
        3. Identify valid section headers by checking against the keys in WriterResume.expected_blocks().
        4. If a valid header is found, truncate the lines list to start from that header.
        5. Create a ParseContext object using the processed lines and indentation level 1.
        6. Use the Resume.parse method to parse the content into a WriterResume object.
        7. Check if any of the main resume sections (personal, education, experience, certifications) were successfully parsed.
        8. Raise ValueError if no valid sections were parsed.
        9. Return the fully parsed WriterResume object.

    """
    lines = markdown_content.split("\n")

    # To make parsing more robust, skip any content before the first valid section header
    first_valid_line_index = -1
    valid_headers = WriterResume.expected_blocks().keys()

    for i, line in enumerate(lines):
        stripped_line = line.strip()
        if stripped_line.startswith("# ") and not stripped_line.startswith("##"):
            # Extract header name
            header_name = stripped_line[2:].lower()
            if header_name in valid_headers:
                first_valid_line_index = i
                break

    if first_valid_line_index != -1:
        lines = lines[first_valid_line_index:]

    parse_context = ParseContext(lines, 1)
    parsed_resume = WriterResume.parse(parse_context)

    # Check if parsing resulted in any content
    if not any(
        [
            parsed_resume.personal,
            parsed_resume.education,
            parsed_resume.experience,
            parsed_resume.certifications,
        ],
    ):
        raise ValueError("No valid resume sections found in content.")

    return parsed_resume


def parse_resume(markdown_content: str) -> dict[str, Any]:
    """Parse Markdown resume content using resume_writer parser and return a dictionary.

    Args:
        markdown_content (str): The Markdown content to parse, expected to follow a valid resume format.

    Returns:
        dict[str, Any]: A dictionary representation of the parsed resume data, including:
            - personal: Personal information (e.g., name, email, phone).
            - experience: List of work experience entries.
            - education: List of educational qualifications.
            - certifications: List of certifications.
            - Any other sections supported by resume_writer.

    Raises:
        HTTPException: If parsing fails due to invalid format or content, with status 422 and a descriptive message.

    Notes:
        1. Log the start of the parsing process.
        2. Call a series of extraction functions to get serializable Pydantic models.
        3. Construct a dictionary from these models.
        4. Log successful completion.
        5. Return the dictionary representation.
        6. No disk, network, or database access is performed.

    """
    _msg = "parse_resume starting"
    log.debug(_msg)

    try:
        personal_info = extract_personal_info(markdown_content)
        education_info = extract_education_info(markdown_content)
        experience_info = extract_experience_info(markdown_content)
        certifications_info = extract_certifications_info(markdown_content)

        resume_dict = {
            "personal": personal_info,
            "education": education_info,
            "experience": experience_info,
            "certifications": certifications_info,
        }
        personal_empty = not personal_info or not any(
            v for v in personal_info.model_dump().values() if v
        )
        education_empty = not education_info or not education_info.degrees
        experience_empty = not experience_info or (
            not experience_info.roles and not experience_info.projects
        )
        certifications_empty = (
            not certifications_info or not certifications_info.certifications
        )

        if (
            personal_empty
            and education_empty
            and experience_empty
            and certifications_empty
        ):
            raise ValueError("No valid resume content could be parsed.")

        _msg = "parse_resume returning successfully"
        log.debug(_msg)

        return resume_dict

    except ValueError as e:
        _msg = f"Failed to parse resume content: {str(e)}"
        log.exception(_msg)
        raise ValueError(f"Invalid resume format: {str(e)}") from e


def parse_resume_content(markdown_content: str) -> dict[str, Any]:
    """Parse Markdown resume content and return structured data as a dictionary.

    Args:
        markdown_content (str): The Markdown content to parse, expected to follow a valid resume format.

    Returns:
        dict: A dictionary containing the structured resume data, including:
            - personal: Personal information (e.g., name, email, phone).
            - experience: List of work experience entries.
            - education: List of educational qualifications.
            - certifications: List of certifications.
            - Any other sections supported by resume_writer.

    Raises:
        HTTPException: If parsing fails due to invalid format or content, with status 400 and a descriptive message.

    Notes:
        1. Log the start of the parsing process.
        2. Use the parse_resume function to parse the provided markdown_content.
        3. Return the result of parse_resume as a dictionary.
        4. Log successful completion.
        5. No disk, network, or database access is performed.

    """
    _msg = "parse_resume_content starting"
    log.debug(_msg)

    try:
        # Use our parse_resume function
        result = parse_resume(markdown_content)
        # This check is flawed because empty sections can be valid.
        # The lower-level parsing functions are responsible for validation.

        _msg = "parse_resume_content returning successfully"
        log.debug(_msg)
        return result
    except ValueError as e:
        log.exception("Failed to parse resume")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse resume: {str(e)}",
        ) from e


def validate_resume_content(content: str) -> None:
    """Validate resume Markdown content for proper format.

    Args:
        content (str): The Markdown content to validate, expected to be in a format compatible with resume_writer.

    Returns:
        None: The function returns nothing if validation passes.

    Raises:
        HTTPException: If parsing fails due to invalid format, with status 422 and a descriptive message.

    Notes:
        1. Log the start of the validation process.
        2. Attempt to parse the provided content using the parse_resume function.
        3. If parsing fails, raise an HTTPException with a descriptive error message.
        4. Log successful completion if no exception is raised.
        5. No disk, network, or database access is performed.

    """
    _msg = "validate_resume_content starting"
    log.debug(_msg)

    try:
        parse_resume(content)
        _msg = "validate_resume_content returning successfully"
        log.debug(_msg)
    except ValueError as e:
        _msg = f"Markdown validation failed: {str(e)}"
        log.exception(_msg)
        raise HTTPException(
            status_code=422,
            detail=f"Invalid Markdown format: {str(e)}",
        ) from e
