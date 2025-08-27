import logging

from resume_editor.app.api.routes.route_logic.resume_parsing import (
    validate_resume_content,
)

log = logging.getLogger(__name__)


def perform_pre_save_validation(
    markdown_content: str,
    original_content: str | None = None,
) -> None:
    """Perform comprehensive pre-save validation on resume content.

    Args:
        markdown_content (str): The updated resume Markdown content to validate.
        original_content (str | None): The original resume content for comparison.

    Returns:
        None: This function does not return any value.

    Raises:
        HTTPException: If validation fails with status code 422.

    Notes:
        1. Run the updated Markdown through the existing parser to ensure it's still valid.
        2. If any validation fails, raise an HTTPException with detailed error messages.
        3. This function performs validation checks on resume content before saving to ensure data integrity.
        4. Validation includes parsing the Markdown content to verify its structure and format.
        5. The function accesses the resume parsing module to validate the content structure.
    """
    validate_resume_content(markdown_content)
