import logging
from typing import Any

from fastapi import HTTPException
from resume_writer.models.parsers import ParseContext
from resume_writer.models.resume import Resume as WriterResume

log = logging.getLogger(__name__)


def parse_resume_to_writer_object(markdown_content: str) -> WriterResume:
    """Parse Markdown resume content into a resume_writer Resume object.

    Args:
        markdown_content (str): The Markdown content to parse.

    Returns:
        WriterResume: The parsed resume object from the resume_writer library.

    Raises:
        ValueError: If parsing results in no valid content.

    Notes:
        1. Splits the content into lines.
        2. Skips any lines before the first valid section header.
        3. Parses the content using the resume_writer's ParseContext and Resume.parse.
        4. Checks if any sections were successfully parsed; raises ValueError if not.
        5. Returns the parsed resume_writer Resume object.

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
    """Parse Markdown resume content using resume_writer parser.

    Args:
        markdown_content (str): The Markdown content to parse, expected to follow a valid resume format.

    Returns:
        dict[str, Any]: A dictionary representation of the parsed resume data structure,
                       including sections like personal info, experience, education, etc.
                       The structure matches the output of the resume_writer parser.

    Notes:
        1. Calls `parse_resume_to_writer_object` to perform parsing.
        2. Converts the returned resume object to a dictionary.
        3. Handles exceptions and raises an HTTPException on failure.
        4. Returns the dictionary representation.
        5. No disk, network, or database access is performed.

    """
    _msg = "parse_resume starting"
    log.debug(_msg)

    try:
        parsed_resume = parse_resume_to_writer_object(markdown_content)

        # Convert to dictionary
        resume_dict = vars(parsed_resume)

        _msg = "parse_resume returning successfully"
        log.debug(_msg)

        return resume_dict

    except Exception as e:
        _msg = f"Failed to parse resume content: {str(e)}"
        log.exception(_msg)
        raise HTTPException(status_code=422, detail=f"Invalid resume format: {str(e)}")


def parse_resume_content(markdown_content: str) -> dict[str, Any]:
    """Parse Markdown resume content and return structured data.

    Args:
        markdown_content (str): The Markdown content to parse, expected to follow a valid resume format.

    Returns:
        dict: A dictionary containing the structured resume data, including sections like personal info, experience, education, etc.
              The structure matches the expected output of the resume_writer parser.

    Notes:
        1. Use the parse_resume function to parse the provided markdown_content.
        2. Return the result of parse_resume as a dictionary.
        3. No disk, network, or database access is performed.

    """
    _msg = "parse_resume_content starting"
    log.debug(_msg)

    try:
        # Use our parse_resume function
        result = parse_resume(markdown_content)
        _msg = "parse_resume_content returning successfully"
        log.debug(_msg)
        return result
    except Exception as e:
        log.exception("Failed to parse resume")
        raise HTTPException(status_code=400, detail=f"Failed to parse resume: {str(e)}")


def validate_resume_content(content: str) -> None:
    """Validate resume Markdown content.

    Args:
        content (str): The Markdown content to validate, expected to be in a format compatible with resume_writer.

    Returns:
        None: The function returns nothing on success.

    Notes:
        1. Attempt to parse the provided content using the parse_resume function.
        2. If parsing fails, raise an HTTPException with status 422 and a descriptive message.
        3. No disk, network, or database access is performed.

    """
    _msg = "validate_resume_content starting"
    log.debug(_msg)

    try:
        parse_resume(content)
        _msg = "validate_resume_content returning successfully"
        log.debug(_msg)
    except Exception as e:
        _msg = f"Markdown validation failed: {str(e)}"
        log.exception(_msg)
        raise HTTPException(
            status_code=422,
            detail=f"Invalid Markdown format: {str(e)}",
        )
