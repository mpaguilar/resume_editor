from unittest.mock import Mock, patch

import pytest

from resume_editor.app.api.routes.route_logic.resume_serialization import (
    extract_personal_info,
    serialize_personal_info_to_markdown,
)
from resume_editor.app.api.routes.route_models import PersonalInfoResponse


@pytest.mark.parametrize(
    "personal_info, expected_output",
    [
        # Test case for no personal info, covers return ""
        (
            PersonalInfoResponse(),
            "",
        ),
        # Test case for None input
        (
            None,
            "",
        ),
        # Test case for only name
        (
            PersonalInfoResponse(name="John Doe"),
            "# Personal\n\n## Contact Information\n\nName: John Doe\n\n",
        ),
        # Test case for only email
        (
            PersonalInfoResponse(email="john.doe@example.com"),
            "# Personal\n\n## Contact Information\n\nEmail: john.doe@example.com\n\n",
        ),
        # Test case for phone but no name/email
        (
            PersonalInfoResponse(phone="123-456-7890"),
            "# Personal\n\n## Contact Information\n\nPhone: 123-456-7890\n\n",
        ),
        # Test case for only website
        (
            PersonalInfoResponse(website="https://johndoe.com"),
            "# Personal\n\n## Websites\n\nWebsite: https://johndoe.com\n\n",
        ),
        # Test case for only twitter
        (
            PersonalInfoResponse(twitter="@johndoe"),
            "# Personal\n\n## Websites\n\nTwitter: @johndoe\n\n",
        ),
        # Test case for github but no website/twitter
        (
            PersonalInfoResponse(github="https://github.com/johndoe"),
            "# Personal\n\n## Websites\n\nGitHub: https://github.com/johndoe\n\n",
        ),
        # Test case for only work_authorization
        (
            PersonalInfoResponse(work_authorization="Green Card"),
            "# Personal\n\n## Visa Status\n\nWork Authorization: Green Card\n\n",
        ),
        # Test case for only require_sponsorship
        (
            PersonalInfoResponse(require_sponsorship=True),
            "# Personal\n\n## Visa Status\n\nRequire sponsorship: Yes\n\n",
        ),
        # Test case for full personal info
        (
            PersonalInfoResponse(
                name="Jane Doe",
                email="jane.doe@example.com",
                phone="111-222-3333",
                location="New York, NY",
                website="https://janedoe.com",
                github="https://github.com/janedoe",
                linkedin="https://linkedin.com/in/janedoe",
                twitter="@janedoe",
                work_authorization="US Citizen",
                require_sponsorship=False,
                banner="Experienced Developer",
                note="Looking for new opportunities",
            ),
            (
                "# Personal\n\n"
                "## Contact Information\n\n"
                "Name: Jane Doe\n"
                "Email: jane.doe@example.com\n"
                "Phone: 111-222-3333\n"
                "Location: New York, NY\n\n"
                "## Websites\n\n"
                "GitHub: https://github.com/janedoe\n"
                "LinkedIn: https://linkedin.com/in/janedoe\n"
                "Website: https://janedoe.com\n"
                "Twitter: @janedoe\n\n"
                "## Visa Status\n\n"
                "Work Authorization: US Citizen\n"
                "Require sponsorship: No\n\n"
                "## Banner\n\n"
                "Experienced Developer\n\n"
                "## Note\n\n"
                "Looking for new opportunities\n\n"
            ),
        ),
    ],
)
def test_serialize_personal_info_to_markdown(personal_info, expected_output):
    """Test serialization of personal info to Markdown."""
    result = serialize_personal_info_to_markdown(personal_info)
    assert result == expected_output


class TestExtractPersonalInfo:
    """Test cases for personal info extraction functions."""

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_serialization.WriterResume.parse",
    )
    def test_extract_personal_info_no_personal_section(self, mock_parse):
        """Test personal info extraction when personal section is missing."""
        mock_resume = Mock()
        mock_resume.personal = None
        mock_parse.return_value = mock_resume

        response = extract_personal_info("any content")
        assert response == PersonalInfoResponse()

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_serialization.WriterResume.parse",
    )
    def test_extract_personal_info_no_contact_info(self, mock_parse):
        """Test personal info extraction when contact info is missing."""
        mock_personal = Mock()
        mock_personal.contact_info = None
        # To accurately simulate the parser's behavior for missing sections,
        # we configure the mock to raise an AttributeError when these are accessed.
        mock_personal.configure_mock(
            **{
                "websites": None,
                "visa_status": None,
                "banner": None,
                "note": None,
            },
        )
        # Use a spec to ensure only valid attributes of the real object are accessed
        mock_personal.spec = [
            "contact_info",
            "websites",
            "visa_status",
            "banner",
            "note",
        ]
        # Set attributes that should be absent to None explicitly.
        mock_personal.websites = None
        mock_personal.visa_status = None
        mock_personal.banner = None
        mock_personal.note = None

        mock_resume = Mock()
        mock_resume.personal = mock_personal
        mock_parse.return_value = mock_resume

        response = extract_personal_info("any content")
        # An empty response should be returned if no data is present
        assert response == PersonalInfoResponse()

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_serialization.WriterResume.parse",
    )
    def test_extract_personal_info_partial_data(self, mock_parse):
        """Test personal info extraction with partial data."""
        mock_contact_info = Mock()
        mock_contact_info.name = "John Doe"
        mock_contact_info.email = None
        mock_contact_info.phone = "123-456-7890"
        mock_contact_info.location = None
        mock_websites = Mock()
        mock_websites.website = None
        mock_websites.github = None
        mock_websites.linkedin = None
        mock_websites.twitter = None

        mock_personal = Mock()
        mock_personal.contact_info = mock_contact_info
        mock_personal.websites = mock_websites
        mock_personal.visa_status = None
        mock_personal.banner = None
        mock_personal.note = None

        mock_resume = Mock()
        mock_resume.personal = mock_personal
        mock_parse.return_value = mock_resume

        response = extract_personal_info("any content")
        assert response.name == "John Doe"
        assert response.email is None
        assert response.phone == "123-456-7890"
        assert response.location is None
        assert response.website is None

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_serialization.WriterResume.parse",
        side_effect=Exception("mock parse error"),
    )
    def test_extract_personal_info_parse_fails(self, mock_parse):
        """Test personal info extraction when parsing fails."""
        with pytest.raises(ValueError, match="Failed to parse personal info"):
            extract_personal_info("invalid content")
