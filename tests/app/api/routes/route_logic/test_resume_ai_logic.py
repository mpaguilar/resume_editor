from unittest.mock import MagicMock, patch

import pytest

from resume_editor.app.api.routes.route_logic.resume_ai_logic import (
    _update_banner_in_raw_personal,
    handle_save_as_new_refinement,
    reconstruct_resume_with_new_introduction,
)
from resume_editor.app.api.routes.route_models import PersonalInfoResponse
from resume_editor.app.models.resume.personal import Banner
from resume_editor.app.models.resume_model import Resume as DatabaseResume



@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.create_resume_db")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.perform_pre_save_validation"
)
def test_handle_save_as_new_refinement_uses_user_provided_introduction(
    mock_validate: MagicMock,
    mock_create_resume: MagicMock,
) -> None:
    """
    Scenario: A user provides a custom introduction in the "Save as New" form.
    """
    # Setup
    params = MagicMock()
    params.db = MagicMock()
    params.user.id = 1
    params.resume.id = 1
    params.resume.content = "original"
    params.form_data.refined_content = "reconstructed"
    params.form_data.job_description = "A job description"
    params.form_data.introduction = "User provided introduction"
    params.form_data.new_resume_name = "New Resume from Test"

    mock_create_resume.return_value = MagicMock(spec=DatabaseResume)

    # Execution
    handle_save_as_new_refinement(params)

    # Assertions
    mock_validate.assert_called_once_with("reconstructed")
    create_params = mock_create_resume.call_args.kwargs["params"]
    assert create_params.content == "reconstructed"
    assert create_params.introduction == "User provided introduction"


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.create_resume_db")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.perform_pre_save_validation"
)
def test_handle_save_as_new_refinement_no_introduction(
    mock_validate: MagicMock,
    mock_create_resume: MagicMock,
) -> None:
    """
    Scenario: A user does not provide an introduction.
    """
    # Setup
    params = MagicMock()
    params.db = MagicMock()
    params.user.id = 42
    params.resume.id = 7
    params.resume.content = "original resume markdown"
    params.form_data.refined_content = "refined section content"
    params.form_data.new_resume_name = "New Resume Name"
    params.form_data.job_description = "JD text"
    params.form_data.introduction = None

    mock_create_resume.return_value = MagicMock(spec=DatabaseResume)

    # Execution
    handle_save_as_new_refinement(params)

    # Assertions
    mock_validate.assert_called_once_with("refined section content")
    create_params = mock_create_resume.call_args.kwargs["params"]
    assert create_params.content == "refined section content"
    assert create_params.introduction is None


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.create_resume_db")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.perform_pre_save_validation"
)
def test_handle_save_as_new_refinement_with_no_intro_or_jd(
    mock_validate: MagicMock,
    mock_create_resume: MagicMock,
) -> None:
    """
    Scenario: A user provides neither an introduction nor a job description.
    """
    # Setup
    params = MagicMock()
    params.db = MagicMock()
    params.user.id = 100
    params.resume.id = 55
    params.resume.content = "orig content"
    params.form_data.refined_content = "reconstructed"
    params.form_data.job_description = None
    params.form_data.introduction = None
    params.form_data.new_resume_name = "No Intro Resume"

    mock_create_resume.return_value = MagicMock(spec=DatabaseResume)

    # Execution
    handle_save_as_new_refinement(params)

    # Assertions
    mock_validate.assert_called_once_with("reconstructed")
    create_params = mock_create_resume.call_args.kwargs["params"]
    assert create_params.content == "reconstructed"
    assert create_params.introduction is None


def test_reconstruct_resume_with_new_introduction_none_introduction() -> None:
    """Test reconstruct_resume_with_new_introduction returns original content when introduction is None."""
    original_content = "# Personal\n## Banner\nOld banner\n# Experience\nSome content"

    result = reconstruct_resume_with_new_introduction(original_content, None)

    assert result == original_content


def test_reconstruct_resume_with_new_introduction_whitespace_introduction() -> None:
    """Test reconstruct_resume_with_new_introduction returns original content when introduction is whitespace."""
    original_content = "# Personal\n## Banner\nOld banner\n# Experience\nSome content"

    result = reconstruct_resume_with_new_introduction(original_content, "   \n\t  ")

    assert result == original_content


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic._update_banner_in_raw_personal")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic._extract_raw_section")
def test_reconstruct_resume_with_new_introduction_success(
    mock_extract_raw: MagicMock,
    mock_update_banner: MagicMock,
) -> None:
    """Test reconstruct_resume_with_new_introduction successfully replaces banner when introduction is provided."""
    original_content = "# Personal\nName: John Doe\n\n# Experience\nSome content"
    original_personal_section = "# Personal\nName: John Doe\n"
    new_introduction = "This is a new introduction"
    updated_personal_section = (
        "# Personal\nName: John Doe\n\n## Banner\nThis is a new introduction\n"
    )

    mock_extract_raw.return_value = original_personal_section
    mock_update_banner.return_value = updated_personal_section

    result = reconstruct_resume_with_new_introduction(
        original_content, new_introduction
    )

    # Verify raw extraction was called for the personal section
    mock_extract_raw.assert_called_once_with(original_content, "personal")

    # Verify banner update was called
    mock_update_banner.assert_called_once_with(
        original_personal_section, new_introduction
    )

    # Verify result uses str.replace correctly
    expected_content = original_content.replace(
        original_personal_section, updated_personal_section
    )
    assert result == expected_content


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic._update_banner_in_raw_personal")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic._extract_raw_section")
def test_reconstruct_resume_with_new_introduction_appends_when_no_personal_section(
    mock_extract_raw: MagicMock,
    mock_update_banner: MagicMock,
) -> None:
    """Test that a personal section is appended if one does not exist."""
    # Arrange
    original_content = "# Experience\nDeveloper at a company"
    new_introduction = "This is a new introduction"

    # When no personal section is found, _extract_raw_section returns an empty string.
    mock_extract_raw.return_value = ""

    # _update_banner_in_raw_personal will create a new personal section from scratch.
    updated_personal_section = (
        "# Personal\n\n## Banner\n\nThis is a new introduction\n"
    )
    mock_update_banner.return_value = updated_personal_section

    # Act
    result = reconstruct_resume_with_new_introduction(
        original_content, new_introduction
    )

    # Assert
    # Verify that the logic tried to find a personal section
    mock_extract_raw.assert_called_once_with(original_content, "personal")

    # Verify that the banner update logic was called with an empty string
    mock_update_banner.assert_called_once_with("", new_introduction)

    # Verify that the new personal section was appended to the original content
    expected_content = (
        original_content.rstrip() + "\n\n" + updated_personal_section.strip() + "\n"
    )
    assert result == expected_content


def test_update_banner_in_raw_personal_replaces_content_with_correct_spacing():
    """Test banner replacement provides correct spacing for Markdown."""
    raw_personal = "# Personal\n\n## Contact\n\n## Banner\nOld banner content\n\n## Websites\n"
    introduction = "* Point A\n* Point B"
    result = _update_banner_in_raw_personal(raw_personal, introduction)
    expected_output = "# Personal\n\n## Contact\n\n## Banner\n\n* Point A\n* Point B\n\n## Websites\n"

    assert result == expected_output


def test_update_banner_in_raw_personal_appends_content_with_correct_spacing():
    """Test banner appending provides correct spacing for Markdown."""
    raw_personal = "# Personal\n\n## Contact\nEmail: a@b.com\n"
    introduction = "* Point A\n* Point B"
    result = _update_banner_in_raw_personal(raw_personal, introduction)
    expected_output = (
        "# Personal\n\n## Contact\nEmail: a@b.com\n\n## Banner\n\n* Point A\n* Point B\n"
    )

    assert result == expected_output


def test_update_banner_in_raw_personal_preserves_paragraphs():
    """Test banner update preserves paragraphs in the introduction."""
    raw_personal = "# Personal\n\n## Banner\nOld content.\n"
    introduction = "Paragraph 1\n\nParagraph 2"
    result = _update_banner_in_raw_personal(raw_personal, introduction)
    expected_output = "# Personal\n\n## Banner\n\nParagraph 1\n\nParagraph 2\n"

    assert result == expected_output


@pytest.mark.parametrize(
    "raw_personal, expected_output_template",
    [
        (
            # Case 1: Banner exists and should be replaced
            """# Personal
## Banner
Old Banner
## Contact
email: a@b.com
""",
            """# Personal
## Banner

{intro}

## Contact
email: a@b.com
""",
        ),
        (
            # Case 2: Banner does not exist and should be appended
            """# Personal
## Contact
email: a@b.com
""",
            """# Personal
## Contact
email: a@b.com

## Banner

{intro}
""",
        ),
    ],
)
def test_update_banner_in_raw_personal_with_bullet_list(
    raw_personal, expected_output_template
):
    """Test that banner update handles multi-line bulleted lists correctly."""
    introduction = "- Strength 1\n- Strength 2"
    expected_output = expected_output_template.format(intro=introduction)

    result = _update_banner_in_raw_personal(raw_personal, introduction)

    assert result == expected_output
