import pytest

from resume_editor.app.api.routes.route_logic.resume_serialization import (
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


