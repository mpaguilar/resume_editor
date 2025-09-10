from unittest.mock import patch

import pytest
from fastapi import HTTPException

from resume_editor.app.api.routes.route_logic.resume_parsing import (
    parse_resume,
    validate_resume_content,
)


def test_parse_resume_success():
    """Test that parse_resume successfully parses valid markdown."""
    valid_markdown_with_indent = """
    # Personal
    ## Contact Information
    Name: Testy McTestface
    """

    # Test with leading whitespace
    result_with_indent = parse_resume(valid_markdown_with_indent)
    assert result_with_indent["personal"] is not None
    assert result_with_indent["personal"].name == "Testy McTestface"

    # Test without leading whitespace
    valid_markdown_no_indent = """
# Personal
## Contact Information
Name: Another Person
"""
    result_no_indent = parse_resume(valid_markdown_no_indent)
    assert result_no_indent["personal"] is not None
    assert result_no_indent["personal"].name == "Another Person"


@patch(
    "resume_editor.app.api.routes.route_logic.resume_parsing.extract_personal_info"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_parsing.extract_education_info"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_parsing.extract_experience_info"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_parsing.extract_certifications_info"
)
def test_parse_resume_failure(
    mock_extract_cert,
    mock_extract_exp,
    mock_extract_edu,
    mock_extract_personal,
):
    """Test that parse_resume raises ValueError on failure."""
    mock_extract_personal.side_effect = ValueError("Parsing failed")
    with pytest.raises(ValueError):
        parse_resume("invalid markdown")


def test_validate_resume_content_success():
    """Test that validate_resume_content passes with valid markdown."""
    valid_markdown = """
# Personal
## Contact Information
Name: Testy McTestface
"""
    # This should not raise an exception
    validate_resume_content(valid_markdown)


@patch("resume_editor.app.api.routes.route_logic.resume_parsing.parse_resume")
def test_validate_resume_content_failure(mock_parse_resume):
    """Test that validate_resume_content raises HTTPException with invalid markdown."""
    mock_parse_resume.side_effect = ValueError("Parsing failed")
    with pytest.raises(HTTPException) as exc_info:
        validate_resume_content("invalid markdown")
    assert exc_info.value.status_code == 422
    assert "Invalid Markdown format: Parsing failed" in exc_info.value.detail
