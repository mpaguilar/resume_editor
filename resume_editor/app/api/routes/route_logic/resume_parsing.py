import logging
from typing import Any

from fastapi import HTTPException
from resume_writer.models.parsers import ParseContext
from resume_writer.models.resume import Resume as WriterResume

log = logging.getLogger(__name__)


def parse_resume(markdown_content: str) -> dict[str, Any]:
    """Parse Markdown resume content using resume_writer parser.

    Args:
        markdown_content (str): The Markdown content to parse, expected to follow a valid resume format.

    Returns:
        dict[str, Any]: A dictionary representation of the parsed resume data structure,
                       including sections like personal info, experience, education, etc.
                       The structure matches the output of the resume_writer parser.

    Notes:
        1. Split the markdown_content into lines.
        2. Identify the first valid section header by scanning lines for headers that start with "# " and not "##".
        3. Filter the lines to start from the first valid section header, if found.
        4. Create a ParseContext object from the filtered lines with an initial line number of 1.
        5. Use the WriterResume.parse method to parse the resume with the context.
        6. Convert the parsed resume object to a dictionary using vars().
        7. Return the dictionary representation.
        8. No disk, network, or database access is performed.

    """
    _msg = "parse_resume starting"
    log.debug(_msg)

    try:
        # Create parse context
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
        else:
            # If no valid headers, it's not a valid resume for our parser.
            # We can let it fail during parsing.
            pass

        parse_context = ParseContext(lines, 1)

        # Parse the resume
        parsed_resume = WriterResume.parse(parse_context)

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
