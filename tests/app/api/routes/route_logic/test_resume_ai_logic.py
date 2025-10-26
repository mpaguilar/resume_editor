from unittest.mock import MagicMock, patch

import pytest

from resume_editor.app.api.routes.route_logic.resume_ai_logic import (
    _replace_resume_banner,
    handle_save_as_new_refinement,
)
from resume_editor.app.api.routes.route_models import PersonalInfoResponse
from resume_editor.app.models.resume.personal import Banner
from resume_editor.app.models.resume_model import Resume as DatabaseResume


def test_replace_resume_banner_none_introduction() -> None:
    """Test _replace_resume_banner returns original content when introduction is None."""
    original_content = "# Personal\n## Banner\nOld banner\n# Experience\nSome content"

    result = _replace_resume_banner(original_content, None)

    assert result == original_content


def test_replace_resume_banner_whitespace_introduction() -> None:
    """Test _replace_resume_banner returns original content when introduction is whitespace."""
    original_content = "# Personal\n## Banner\nOld banner\n# Experience\nSome content"

    result = _replace_resume_banner(original_content, "   \n\t  ")

    assert result == original_content


@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_certifications_info"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_experience_info"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_education_info"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_personal_info")
def test_replace_resume_banner_success(
    mock_extract_personal: MagicMock,
    mock_extract_education: MagicMock,
    mock_extract_experience: MagicMock,
    mock_extract_certifications: MagicMock,
) -> None:
    """Test _replace_resume_banner successfully replaces banner when introduction is provided."""
    original_content = "# Personal\nName: John Doe\n# Experience\nSome content"
    new_introduction = "This is a new introduction"

    # Set up mocks
    mock_personal = PersonalInfoResponse(name="John Doe")
    mock_extract_personal.return_value = mock_personal
    mock_extract_education.return_value = None  # Mocking empty sections
    mock_extract_experience.return_value = None
    mock_extract_certifications.return_value = None

    result = _replace_resume_banner(original_content, new_introduction)

    # Verify parsing functions were called
    mock_extract_personal.assert_called_once_with(original_content)
    mock_extract_education.assert_called_once_with(original_content)
    mock_extract_experience.assert_called_once_with(original_content)
    mock_extract_certifications.assert_called_once_with(original_content)

    # Verify personal info banner was updated
    assert mock_personal.banner == Banner(text=new_introduction)

    # Verify result contains the correct, non-corrupted banner text
    expected_banner_markdown = "## Banner\n\nThis is a new introduction"
    assert expected_banner_markdown in result
    assert "text='This is a new introduction'" not in result
    # Check that other content is still present
    assert "# Personal" in result
    assert "Name: John Doe" in result


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_personal_info")
def test_replace_resume_banner_malformed_content(
    mock_extract_personal: MagicMock,
) -> None:
    """Test _replace_resume_banner handles malformed resume content."""
    original_content = "This is not valid resume content"
    new_introduction = "This is a new introduction"

    # Make the extraction fail
    mock_extract_personal.side_effect = ValueError("Invalid resume format")

    # Should raise an exception due to malformed content
    with pytest.raises(ValueError):
        _replace_resume_banner(original_content, new_introduction)


@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.reconstruct_resume_markdown",
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_certifications_info",
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_experience_info",
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_education_info",
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_personal_info")
def test_replace_resume_banner_personal_info_none(
    mock_extract_personal: MagicMock,
    mock_extract_education: MagicMock,
    mock_extract_experience: MagicMock,
    mock_extract_certifications: MagicMock,
    mock_reconstruct: MagicMock,
) -> None:
    """Test branch where personal_info is None to cover the False path of the condition."""
    original_content = (
        "# Personal\n(no personal info parsed)\n# Experience\nSome content"
    )
    new_introduction = "Intro text"

    mock_extract_personal.return_value = None
    mock_extract_education.return_value = MagicMock()
    mock_extract_experience.return_value = MagicMock()
    mock_extract_certifications.return_value = MagicMock()
    mock_reconstruct.return_value = "reconstructed content"

    result = _replace_resume_banner(original_content, new_introduction)

    # Verify reconstruct called with personal_info=None and other sections
    mock_reconstruct.assert_called_once_with(
        personal_info=None,
        education=mock_extract_education.return_value,
        experience=mock_extract_experience.return_value,
        certifications=mock_extract_certifications.return_value,
    )
    assert result == "reconstructed content"


@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.reconstruct_resume_markdown",
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_certifications_info",
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_experience_info",
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_education_info",
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_personal_info")
def test_replace_resume_banner_reconstruct_failure(
    mock_extract_personal: MagicMock,
    mock_extract_education: MagicMock,
    mock_extract_experience: MagicMock,
    mock_extract_certifications: MagicMock,
    mock_reconstruct: MagicMock,
) -> None:
    """Test exception handling path when reconstruction fails."""
    original_content = "# Personal\nName: Jane\n# Experience\nSome content"
    new_introduction = "New intro"

    # Provide valid parsed sections
    mock_extract_personal.return_value = PersonalInfoResponse(name="Jane")
    mock_extract_education.return_value = MagicMock()
    mock_extract_experience.return_value = MagicMock()
    mock_extract_certifications.return_value = MagicMock()

    # Force reconstruction to fail to hit the except block
    mock_reconstruct.side_effect = RuntimeError("reconstruction failed")

    with pytest.raises(RuntimeError):
        _replace_resume_banner(original_content, new_introduction)


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.create_resume_db")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic._replace_resume_banner",
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.reconstruct_resume_from_refined_section",
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.perform_pre_save_validation",
)
def test_handle_save_as_new_refinement_uses_banner_replacement_with_intro(
    mock_validate: MagicMock,
    mock_reconstruct: MagicMock,
    mock_replace_banner: MagicMock,
    mock_create_resume: MagicMock,
) -> None:
    """Verify handle_save_as_new_refinement integrates banner replacement when introduction is provided."""
    # Arrange params
    params = MagicMock()
    params.db = MagicMock()
    params.user = MagicMock()
    params.user.id = 42
    params.resume = MagicMock()
    params.resume.id = 7
    params.resume.content = "original resume markdown"
    params.form_data = MagicMock()
    params.form_data.refined_content = "refined section content"
    params.form_data.target_section = MagicMock()
    params.form_data.metadata = MagicMock()
    params.form_data.metadata.new_resume_name = "New Resume Name"
    params.form_data.metadata.job_description = "JD text"
    params.form_data.metadata.introduction = "Intro text"

    mock_reconstruct.return_value = "reconstructed content"
    mock_replace_banner.return_value = "final content"
    new_resume = MagicMock(spec=DatabaseResume)
    mock_create_resume.return_value = new_resume

    # Act
    result = handle_save_as_new_refinement(params)

    # Assert reconstruction and banner replacement flow
    mock_reconstruct.assert_called_once_with(
        original_resume_content="original resume markdown",
        refined_content="refined section content",
        target_section=params.form_data.target_section,
    )
    mock_replace_banner.assert_called_once_with(
        resume_content="reconstructed content",
        introduction="Intro text",
    )
    mock_validate.assert_called_once_with("final content")

    # Assert DB create is called with final content and introduction
    mock_create_resume.assert_called_once()
    kwargs = mock_create_resume.call_args.kwargs
    assert "db" in kwargs and kwargs["db"] is params.db
    create_params = kwargs["params"]
    assert create_params.content == "final content"
    assert create_params.introduction == "Intro text"
    assert create_params.name == "New Resume Name"
    assert create_params.job_description == "JD text"

    # Returned object
    assert result is new_resume


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.create_resume_db")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic._replace_resume_banner",
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.reconstruct_resume_from_refined_section",
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.perform_pre_save_validation",
)
def test_handle_save_as_new_refinement_uses_banner_replacement_with_none_intro(
    mock_validate: MagicMock,
    mock_reconstruct: MagicMock,
    mock_replace_banner: MagicMock,
    mock_create_resume: MagicMock,
) -> None:
    """Verify handle_save_as_new_refinement calls banner replacement with None introduction."""
    # Arrange params
    params = MagicMock()
    params.db = MagicMock()
    params.user = MagicMock()
    params.user.id = 100
    params.resume = MagicMock()
    params.resume.id = 55
    params.resume.content = "orig content"
    params.form_data = MagicMock()
    params.form_data.refined_content = "refined"
    params.form_data.target_section = MagicMock()
    params.form_data.metadata = MagicMock()
    params.form_data.metadata.new_resume_name = "Name"
    params.form_data.metadata.job_description = "JD"
    params.form_data.metadata.introduction = None

    mock_reconstruct.return_value = "reconstructed"
    mock_replace_banner.return_value = "final"
    mock_create_resume.return_value = MagicMock(spec=DatabaseResume)

    # Act
    result = handle_save_as_new_refinement(params)

    # Assert flow and calls
    mock_replace_banner.assert_called_once_with(
        resume_content="reconstructed",
        introduction=None,
    )
    mock_validate.assert_called_once_with("final")

    # Ensure create called with introduction None and final content
    create_params = mock_create_resume.call_args.kwargs["params"]
    assert create_params.content == "final"
    assert create_params.introduction is None
    assert result is mock_create_resume.return_value
