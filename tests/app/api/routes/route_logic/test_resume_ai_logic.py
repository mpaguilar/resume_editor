from unittest.mock import MagicMock, patch

import pytest

from resume_editor.app.api.routes.route_logic.resume_ai_logic import (
    _replace_resume_banner,
    handle_save_as_new_refinement,
    reconstruct_resume_with_new_introduction,
)
from resume_editor.app.api.routes.route_models import PersonalInfoResponse
from resume_editor.app.models.resume.personal import Banner
from resume_editor.app.models.resume_model import Resume as DatabaseResume


@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.reconstruct_resume_with_new_introduction"
)
def test_replace_resume_banner_is_wrapper(mock_reconstruct: MagicMock) -> None:
    """Test that _replace_resume_banner calls reconstruct_resume_with_new_introduction."""
    mock_reconstruct.return_value = "sentinel"
    content = "my content"
    intro = "my intro"

    result = _replace_resume_banner(content, intro)

    mock_reconstruct.assert_called_once_with(resume_content=content, introduction=intro)
    assert result == "sentinel"



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
def test_reconstruct_resume_with_new_introduction_success(
    mock_extract_personal: MagicMock,
    mock_extract_education: MagicMock,
    mock_extract_experience: MagicMock,
    mock_extract_certifications: MagicMock,
) -> None:
    """Test reconstruct_resume_with_new_introduction successfully replaces banner when introduction is provided."""
    original_content = "# Personal\nName: John Doe\n# Experience\nSome content"
    new_introduction = "This is a new introduction"

    # Set up mocks
    mock_personal = PersonalInfoResponse(name="John Doe")
    mock_extract_personal.return_value = mock_personal
    mock_extract_education.return_value = None
    mock_extract_experience.return_value = None
    mock_extract_certifications.return_value = None

    result = reconstruct_resume_with_new_introduction(
        original_content, new_introduction
    )

    # Verify parsing functions were called
    mock_extract_personal.assert_called_once_with(original_content)
    mock_extract_education.assert_called_once_with(original_content)
    mock_extract_experience.assert_called_once_with(original_content)
    mock_extract_certifications.assert_called_once_with(original_content)

    # Verify personal info banner was updated
    assert mock_personal.banner == Banner(text=new_introduction)

    # Verify result contains the new banner and other content is preserved
    expected_banner_markdown = "## Banner\n\nThis is a new introduction"
    assert expected_banner_markdown in result
    assert "Name: John Doe" in result


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_personal_info")
def test_reconstruct_resume_with_new_introduction_malformed_content(
    mock_extract_personal: MagicMock,
) -> None:
    """Test reconstruct_resume_with_new_introduction handles malformed resume content."""
    original_content = "This is not valid resume content"
    new_introduction = "This is a new introduction"

    mock_extract_personal.side_effect = ValueError("Invalid resume format")

    with pytest.raises(ValueError, match="Invalid resume format"):
        reconstruct_resume_with_new_introduction(original_content, new_introduction)


@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.build_complete_resume_from_sections"
)
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
def test_reconstruct_resume_with_new_introduction_personal_info_none(
    mock_extract_personal: MagicMock,
    mock_extract_education: MagicMock,
    mock_extract_experience: MagicMock,
    mock_extract_certifications: MagicMock,
    mock_build: MagicMock,
) -> None:
    """Test reconstruct_resume_with_new_introduction when personal_info is None."""
    original_content = "some content"
    new_introduction = "new intro"

    mock_extract_personal.return_value = None
    mock_extract_education.return_value = MagicMock()
    mock_extract_experience.return_value = MagicMock()
    mock_extract_certifications.return_value = MagicMock()
    mock_build.return_value = "reconstructed"

    result = reconstruct_resume_with_new_introduction(original_content, new_introduction)

    mock_build.assert_called_once_with(
        personal_info=None,
        education=mock_extract_education.return_value,
        experience=mock_extract_experience.return_value,
        certifications=mock_extract_certifications.return_value,
    )
    assert result == "reconstructed"


@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.build_complete_resume_from_sections"
)
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
def test_reconstruct_resume_with_new_introduction_reconstruct_failure(
    mock_extract_personal: MagicMock,
    mock_extract_education: MagicMock,
    mock_extract_experience: MagicMock,
    mock_extract_certifications: MagicMock,
    mock_build: MagicMock,
) -> None:
    """Test reconstruct_resume_with_new_introduction handles reconstruction failure."""
    original_content = "some content"
    new_introduction = "new intro"

    mock_extract_personal.return_value = MagicMock()
    mock_extract_education.return_value = MagicMock()
    mock_extract_experience.return_value = MagicMock()
    mock_extract_certifications.return_value = MagicMock()
    mock_build.side_effect = RuntimeError("Reconstruction failed")

    with pytest.raises(RuntimeError, match="Reconstruction failed"):
        reconstruct_resume_with_new_introduction(original_content, new_introduction)
