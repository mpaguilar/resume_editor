from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from resume_editor.app.api.routes.route_logic.resume_ai_logic import (
    handle_accept_refinement,
    handle_save_as_new_refinement,
)
from resume_editor.app.api.routes.route_logic.resume_crud import (
    ResumeCreateParams,
    ResumeUpdateParams,
)
from resume_editor.app.api.routes.route_models import RefineTargetSection
from resume_editor.app.models.resume_model import (
    Resume as DatabaseResume,
    ResumeData,
)


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.update_resume_db")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.perform_pre_save_validation"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.reconstruct_resume_from_refined_section"
)
def test_handle_accept_refinement_success(
    mock_reconstruct, mock_validate, mock_update, test_resume
):
    """Test handle_accept_refinement successfully updates a resume."""
    # Arrange
    db = MagicMock()
    refined_content = "refined"
    target_section = RefineTargetSection.PERSONAL
    introduction = "intro"
    mock_reconstruct.return_value = "updated content"
    mock_update.return_value = test_resume

    # Act
    result = handle_accept_refinement(
        db, test_resume, refined_content, target_section, introduction
    )

    # Assert
    assert result == test_resume
    mock_reconstruct.assert_called_once_with(
        original_resume_content=test_resume.content,
        refined_content=refined_content,
        target_section=target_section,
    )
    mock_validate.assert_called_once_with("updated content")
    expected_update_params = ResumeUpdateParams(
        content="updated content", introduction=introduction
    )
    mock_update.assert_called_once_with(
        db=db, resume=test_resume, params=expected_update_params
    )


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.update_resume_db")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.perform_pre_save_validation"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.reconstruct_resume_from_refined_section"
)
def test_handle_accept_refinement_failure_on_reconstruct(
    mock_reconstruct, mock_validate, mock_update, test_resume
):
    """Test handle_accept_refinement failure on reconstruction."""
    # Arrange
    db = MagicMock()
    mock_reconstruct.side_effect = ValueError("reconstruction failed")

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        handle_accept_refinement(
            db, test_resume, "refined", RefineTargetSection.PERSONAL, None
        )
    assert exc_info.value.status_code == 422
    assert "Failed to reconstruct" in exc_info.value.detail
    mock_validate.assert_not_called()
    mock_update.assert_not_called()


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.update_resume_db")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.perform_pre_save_validation"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.reconstruct_resume_from_refined_section"
)
def test_handle_accept_refinement_failure_on_validation(
    mock_reconstruct, mock_validate, mock_update, test_resume
):
    """Test handle_accept_refinement failure on validation."""
    # Arrange
    db = MagicMock()
    mock_reconstruct.return_value = "updated content"
    mock_validate.side_effect = ValueError("validation failed")

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        handle_accept_refinement(
            db, test_resume, "refined", RefineTargetSection.PERSONAL, None
        )
    assert exc_info.value.status_code == 422
    assert "Failed to reconstruct" in exc_info.value.detail
    assert "validation failed" in exc_info.value.detail
    mock_reconstruct.assert_called_once()
    mock_validate.assert_called_once_with("updated content")
    mock_update.assert_not_called()


from resume_editor.app.api.routes.route_models import SaveAsNewForm, SaveAsNewParams


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
    form_data = SaveAsNewForm(
        refined_content="refined",
        target_section=RefineTargetSection.PERSONAL,
        new_resume_name="New Resume",
        job_description="job desc",
        introduction="intro",
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
    form_data = SaveAsNewForm(
        refined_content="refined",
        target_section=RefineTargetSection.PERSONAL,
        new_resume_name="New",
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
    form_data = SaveAsNewForm(
        refined_content="refined",
        target_section=RefineTargetSection.PERSONAL,
        new_resume_name="New",
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
