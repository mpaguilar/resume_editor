import textwrap
from unittest.mock import MagicMock, patch

import pytest

from resume_editor.app.api.routes.route_logic.resume_serialization import (
    extract_personal_info,
)
from resume_editor.app.api.routes.route_models import PersonalInfoResponse


def test_extract_personal_info_all_fields():
    """Test extracting personal info with all fields present."""
    content = textwrap.dedent(
        """\
        # Personal
        ## Visa Status
        Work Authorization: US Citizen
        Require sponsorship: No

        ## Banner
        This is a banner text.

        ## Note
        This is a note.
        """
    )
    result = extract_personal_info(content)
    assert result.work_authorization == "US Citizen"
    assert result.require_sponsorship is False
    assert result.banner == "This is a banner text."
    assert result.note == "This is a note."


@patch("resume_editor.app.api.routes.route_logic.resume_serialization.WriterResume")
def test_extract_personal_info_unparseable_check_raises_error(mock_writer_resume):
    """
    Test that the manual check for unparseable content raises an error.

    This test covers the case where the parser returns no personal info,
    but the raw markdown contains content that looks like it should have been parsed.
    """
    mock_parsed_resume = MagicMock()
    mock_parsed_resume.personal = None
    mock_writer_resume.parse.return_value = mock_parsed_resume

    content = textwrap.dedent(
        """\
        Junk before
        # Personal
        some unparseable content
        # Education
        """
    )
    with pytest.raises(
        ValueError, match="Failed to parse personal info from resume content."
    ):
        extract_personal_info(content)


@patch("resume_editor.app.api.routes.route_logic.resume_serialization.WriterResume")
def test_extract_personal_info_empty_section_manual_check(mock_writer_resume):
    """
    Test that the manual check for content correctly handles an empty section.
    This covers the case where the next line is another section header.
    """
    mock_parsed_resume = MagicMock()
    mock_parsed_resume.personal = None
    mock_writer_resume.parse.return_value = mock_parsed_resume

    content = textwrap.dedent(
        """\
        # Personal

        # Education
        """
    )
    result = extract_personal_info(content)
    assert result == PersonalInfoResponse()
