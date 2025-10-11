from unittest.mock import patch

import pytest

from resume_editor.app.llm.orchestration import (
    _get_section_content,
)


FULL_RESUME = """# Personal
name: Test Person

# Education
school: Test University

# Experience
company: Test Company

# Certifications
name: Test Cert
"""


@pytest.mark.parametrize(
    "section_name, extractor, serializer, expected_output",
    [
        (
            "personal",
            "extract_personal_info",
            "serialize_personal_info_to_markdown",
            "personal section",
        ),
        (
            "education",
            "extract_education_info",
            "serialize_education_to_markdown",
            "education section",
        ),
        (
            "experience",
            "extract_experience_info",
            "serialize_experience_to_markdown",
            "experience section",
        ),
        (
            "certifications",
            "extract_certifications_info",
            "serialize_certifications_to_markdown",
            "certifications section",
        ),
    ],
)
def test_get_section_content(section_name, extractor, serializer, expected_output):
    """Test that _get_section_content correctly calls extract and serialize for each section."""
    with (
        patch(
            f"resume_editor.app.llm.orchestration.{extractor}",
        ) as mock_extract,
        patch(
            f"resume_editor.app.llm.orchestration.{serializer}",
            return_value=expected_output,
        ) as mock_serialize,
    ):
        result = _get_section_content(FULL_RESUME, section_name)

        mock_extract.assert_called_once_with(FULL_RESUME)
        mock_serialize.assert_called_once_with(mock_extract.return_value)
        assert result == expected_output


def test_get_section_content_full():
    """Test that _get_section_content returns the full resume for 'full' section."""
    assert _get_section_content(FULL_RESUME, "full") == FULL_RESUME


def test_get_section_content_invalid():
    """Test that _get_section_content raises ValueError for an invalid section."""
    with pytest.raises(ValueError, match="Invalid section name: invalid"):
        _get_section_content(FULL_RESUME, "invalid")











