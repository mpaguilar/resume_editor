from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from resume_editor.app.api.routes.route_logic.resume_ai_logic import (
    handle_save_as_new_refinement,
)
from resume_editor.app.api.routes.route_logic.resume_crud import ResumeCreateParams
from resume_editor.app.api.routes.route_models import RefineTargetSection
from resume_editor.app.models.resume_model import (
    Resume as DatabaseResume,
    ResumeData,
)




from resume_editor.app.api.routes.route_models import (
    SaveAsNewForm,
    SaveAsNewMetadata,
    SaveAsNewParams,
)


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.create_resume_db")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.perform_pre_save_validation"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.reconstruct_resume_from_refined_section"
)
def test_handle_save_as_new_refinement_success(
    mock_reconstruct, mock_validate, mock_create, test_user, test_resume
):
    """Test handle_save_as_new_refinement successfully creates a new resume."""
    # Arrange
    db = MagicMock()
    metadata = SaveAsNewMetadata(
        new_resume_name="New Resume",
        job_description="job desc",
        introduction="intro",
    )
    form_data = SaveAsNewForm(
        refined_content="refined",
        target_section=RefineTargetSection.PERSONAL,
        metadata=metadata,
    )
    params = SaveAsNewParams(db=db, user=test_user, resume=test_resume, form_data=form_data)

    mock_reconstruct.return_value = "updated content"
    resume_data = ResumeData(
        user_id=test_user.id, name=form_data.new_resume_name, content="updated content"
    )
    new_resume = DatabaseResume(data=resume_data)
    mock_create.return_value = new_resume

    # Act
    result = handle_save_as_new_refinement(params)

    # Assert
    assert result == new_resume
    mock_reconstruct.assert_called_once_with(
        original_resume_content=test_resume.content,
        refined_content=form_data.refined_content,
        target_section=form_data.target_section,
    )
    mock_validate.assert_called_once_with("updated content")
    expected_create_params = ResumeCreateParams(
        user_id=test_user.id,
        name=form_data.new_resume_name,
        content="updated content",
        is_base=False,
        parent_id=test_resume.id,
        job_description=form_data.job_description,
        introduction=form_data.introduction,
    )
    mock_create.assert_called_once_with(db=db, params=expected_create_params)


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.create_resume_db")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.perform_pre_save_validation"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.reconstruct_resume_from_refined_section"
)
def test_handle_save_as_new_refinement_failure_on_validation(
    mock_reconstruct, mock_validate, mock_create, test_user, test_resume
):
    """Test handle_save_as_new_refinement failure on validation."""
    # Arrange
    db = MagicMock()
    metadata = SaveAsNewMetadata(
        new_resume_name="New",
        job_description=None,
        introduction=None,
        limit_refinement_years=None,
    )
    form_data = SaveAsNewForm(
        refined_content="refined",
        target_section=RefineTargetSection.PERSONAL,
        metadata=metadata,
    )
    params = SaveAsNewParams(db=db, user=test_user, resume=test_resume, form_data=form_data)
    mock_reconstruct.return_value = "updated content"
    mock_validate.side_effect = ValueError("validation failed")

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        handle_save_as_new_refinement(params)
    assert exc_info.value.status_code == 422
    assert "Failed to reconstruct" in exc_info.value.detail
    assert "validation failed" in exc_info.value.detail
    mock_reconstruct.assert_called_once()
    mock_validate.assert_called_once_with("updated content")
    mock_create.assert_not_called()


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.create_resume_db")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.perform_pre_save_validation"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.reconstruct_resume_from_refined_section"
)
def test_handle_save_as_new_refinement_failure_on_reconstruction(
    mock_reconstruct, mock_validate, mock_create, test_user, test_resume
):
    """Test handle_save_as_new_refinement failure on reconstruction."""
    # Arrange
    db = MagicMock()
    metadata = SaveAsNewMetadata(
        new_resume_name="New",
        job_description=None,
        introduction=None,
        limit_refinement_years=None,
    )
    form_data = SaveAsNewForm(
        refined_content="refined",
        target_section=RefineTargetSection.PERSONAL,
        metadata=metadata,
    )
    params = SaveAsNewParams(db=db, user=test_user, resume=test_resume, form_data=form_data)
    mock_reconstruct.side_effect = ValueError("reconstruction failed")

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        handle_save_as_new_refinement(params)
    assert exc_info.value.status_code == 422
    assert "Failed to reconstruct" in exc_info.value.detail
    assert "reconstruction failed" in exc_info.value.detail
    mock_reconstruct.assert_called_once()
    mock_validate.assert_not_called()
    mock_create.assert_not_called()


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.create_resume_db")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.perform_pre_save_validation"
)
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
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_personal_info"
)
def test_handle_save_as_new_refinement_with_filtered_content(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certs,
    mock_build_complete,
    mock_validate,
    mock_create,
    test_user,
    test_resume,
):
    """
    Test handle_save_as_new_refinement with filtered experience content.

    This test ensures that when 'save as new' is used with a refined
    experience section, the system correctly uses the refined content for the
    experience section while preserving the other sections from the original
    resume.
    """
    # Arrange
    db = MagicMock()
    original_resume_content = "# Personal\n...\n# Experience\n..."
    refined_experience_only_content = "# Experience\n refined..."
    test_resume.content = original_resume_content

    metadata = SaveAsNewMetadata(
        new_resume_name="Filtered and Refined Resume",
        introduction=None,
        job_description=None,
        limit_refinement_years=None,
    )
    form_data = SaveAsNewForm(
        refined_content=refined_experience_only_content,
        target_section=RefineTargetSection.EXPERIENCE,
        metadata=metadata,
    )
    params = SaveAsNewParams(
        db=db, user=test_user, resume=test_resume, form_data=form_data
    )

    # Mock the return values of the extractors
    mock_personal_info = MagicMock()
    mock_education_info = MagicMock()
    mock_experience_info = MagicMock()
    mock_certs_info = MagicMock()
    mock_extract_personal.return_value = mock_personal_info
    mock_extract_education.return_value = mock_education_info
    mock_extract_experience.return_value = mock_experience_info
    mock_extract_certs.return_value = mock_certs_info

    # Mock the final reconstruction
    final_content = "Final Reconstructed Content"
    mock_build_complete.return_value = final_content
    mock_create.return_value = MagicMock(spec=DatabaseResume)

    # Act
    handle_save_as_new_refinement(params=params)

    # Assert
    # 1. Assert correct content was used for extraction
    mock_extract_personal.assert_called_once_with(original_resume_content)
    mock_extract_education.assert_called_once_with(original_resume_content)
    mock_extract_certs.assert_called_once_with(original_resume_content)
    mock_extract_experience.assert_called_once_with(refined_experience_only_content)

    # 2. Assert builder was called with the results of extraction
    mock_build_complete.assert_called_once_with(
        personal_info=mock_personal_info,
        education=mock_education_info,
        experience=mock_experience_info,
        certifications=mock_certs_info,
    )

    # 3. Assert validation was called with the reconstructed content
    mock_validate.assert_called_once_with(final_content)

    # 4. Assert that the new resume is created with the final reconstructed content
    mock_create.assert_called_once()
    create_params = mock_create.call_args.kwargs["params"]
    assert isinstance(create_params, ResumeCreateParams)
    assert create_params.content == final_content
    assert create_params.name == "Filtered and Refined Resume"
    assert create_params.is_base is False
    assert create_params.parent_id == test_resume.id
    assert create_params.job_description is None
    assert create_params.introduction is None
