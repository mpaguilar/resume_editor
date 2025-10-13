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
        ## Contact Information
        Name: John Doe
        Email: john.doe@example.com
        Phone: 123-456-7890
        Location: Some City, Some State

        ## Websites
        GitHub: johndoe
        LinkedIn: johndoe-li
        Website: https://johndoe.dev
        Twitter: @johndoe

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
    assert result.name == "John Doe"
    assert result.email == "john.doe@example.com"
    assert result.phone == "123-456-7890"
    assert result.location == "Some City, Some State"
    assert result.github == "johndoe"
    assert result.linkedin == "johndoe-li"
    assert result.website == "https://johndoe.dev"
    assert result.twitter == "@johndoe"
    assert result.work_authorization == "US Citizen"
    assert result.require_sponsorship is False
    assert result.banner == "This is a banner text."
    assert result.note == "This is a note."


@patch("resume_editor.app.api.routes.route_logic.resume_serialization._parse_resume")
def test_extract_personal_info_unparseable_check_raises_error(mock_parse_resume):
    """
    Test that the manual check for unparseable content raises an error.

    This test covers the case where the parser returns no personal info,
    but the raw markdown contains content that looks like it should have been parsed.
    """
    mock_parsed_resume = MagicMock()
    mock_parsed_resume.personal = None
    mock_parse_resume.return_value = mock_parsed_resume

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


@patch("resume_editor.app.api.routes.route_logic.resume_serialization._parse_resume")
def test_extract_personal_info_empty_section_manual_check(mock_parse_resume):
    """
    Test that the manual check for content correctly handles an empty section.
    This covers the case where the next line is another section header.
    """
    mock_parsed_resume = MagicMock()
    mock_parsed_resume.personal = None
    mock_parse_resume.return_value = mock_parsed_resume

    content = textwrap.dedent(
        """\
        # Personal

        # Education
        """
    )
    result = extract_personal_info(content)
    assert result == PersonalInfoResponse()


@patch(
    "resume_editor.app.api.routes.route_logic.resume_serialization._parse_resume",
    side_effect=ValueError("mocked error"),
)
def test_extract_personal_info_with_parsing_error(mock_parse_resume):
    """Test that extract_personal_info raises a ValueError when parsing fails."""
    with pytest.raises(ValueError, match="Failed to parse personal info from resume content."):
        extract_personal_info("some invalid content")
