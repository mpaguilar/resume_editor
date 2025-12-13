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
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.generate_introduction_from_resume"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.reconstruct_resume_from_refined_section",
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.perform_pre_save_validation",
)
def test_handle_save_as_new_refinement_with_intro_generation(
    mock_validate: MagicMock,
    mock_reconstruct: MagicMock,
    mock_get_llm_config: MagicMock,
    mock_generate_intro: MagicMock,
    mock_create_resume: MagicMock,
) -> None:
    """Verify handle_save_as_new_refinement integrates LLM introduction generation."""
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

    mock_reconstruct.return_value = "reconstructed content"
    mock_get_llm_config.return_value = ("endpoint", "model", "key")
    mock_generate_intro.return_value = "Generated intro text"
    new_resume = MagicMock(spec=DatabaseResume)
    mock_create_resume.return_value = new_resume

    # Act
    result = handle_save_as_new_refinement(params)

    # Assert reconstruction and intro generation flow
    mock_reconstruct.assert_called_once_with(
        original_resume_content="original resume markdown",
        refined_content="refined section content",
        target_section=params.form_data.target_section,
    )
    mock_get_llm_config.assert_called_once_with(params.db, params.user.id)
    mock_generate_intro.assert_called_once()
    mock_validate.assert_called_once_with("reconstructed content")

    # Assert DB create is called with correct content and introduction
    mock_create_resume.assert_called_once()
    kwargs = mock_create_resume.call_args.kwargs
    assert "db" in kwargs and kwargs["db"] is params.db
    create_params = kwargs["params"]
    assert create_params.content == "reconstructed content"
    assert create_params.introduction == "Generated intro text"
    assert create_params.name == "New Resume Name"
    assert create_params.job_description == "JD text"

    # Returned object
    assert result is new_resume


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.create_resume_db")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.generate_introduction_from_resume"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.reconstruct_resume_from_refined_section"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.perform_pre_save_validation"
)
def test_handle_save_as_new_refinement_without_job_description(
    mock_validate: MagicMock,
    mock_reconstruct: MagicMock,
    mock_get_llm_config: MagicMock,
    mock_generate_intro: MagicMock,
    mock_create_resume: MagicMock,
) -> None:
    """Verify handle_save_as_new_refinement skips intro generation when no job description is provided."""
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
    params.form_data.metadata.job_description = None

    mock_reconstruct.return_value = "reconstructed content"
    mock_create_resume.return_value = MagicMock(spec=DatabaseResume)

    # Act
    result = handle_save_as_new_refinement(params)

    # Assert flow and calls
    mock_reconstruct.assert_called_once()
    mock_get_llm_config.assert_not_called()
    mock_generate_intro.assert_not_called()
    mock_validate.assert_called_once_with("reconstructed content")

    # Ensure create called with empty introduction and reconstructed content
    create_params = mock_create_resume.call_args.kwargs["params"]
    assert create_params.content == "reconstructed content"
    assert create_params.introduction == ""
    assert result is mock_create_resume.return_value


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


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.reconstruct_resume_markdown")
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
    mock_reconstruct: MagicMock,
) -> None:
    """Test reconstruct_resume_with_new_introduction when personal_info is None."""
    original_content = "some content"
    new_introduction = "new intro"

    mock_extract_personal.return_value = None
    mock_extract_education.return_value = MagicMock()
    mock_extract_experience.return_value = MagicMock()
    mock_extract_certifications.return_value = MagicMock()
    mock_reconstruct.return_value = "reconstructed"

    result = reconstruct_resume_with_new_introduction(original_content, new_introduction)

    mock_reconstruct.assert_called_once_with(
        personal_info=None,
        education=mock_extract_education.return_value,
        experience=mock_extract_experience.return_value,
        certifications=mock_extract_certifications.return_value,
    )
    assert result == "reconstructed"


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.reconstruct_resume_markdown")
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
    mock_reconstruct: MagicMock,
) -> None:
    """Test reconstruct_resume_with_new_introduction handles reconstruction failure."""
    original_content = "some content"
    new_introduction = "new intro"

    mock_extract_personal.return_value = MagicMock()
    mock_extract_education.return_value = MagicMock()
    mock_extract_experience.return_value = MagicMock()
    mock_extract_certifications.return_value = MagicMock()
    mock_reconstruct.side_effect = RuntimeError("Reconstruction failed")

    with pytest.raises(RuntimeError, match="Reconstruction failed"):
        reconstruct_resume_with_new_introduction(original_content, new_introduction)
