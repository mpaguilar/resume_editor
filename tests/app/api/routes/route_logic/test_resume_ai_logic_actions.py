from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from resume_editor.app.api.routes.route_logic.resume_ai_logic import (
    handle_save_as_new_refinement,
)
from resume_editor.app.api.routes.route_logic.resume_crud import ResumeCreateParams
from resume_editor.app.api.routes.route_models import (
    RefinementContext,
    SaveAsNewForm,
    SaveAsNewParams,
)
from resume_editor.app.models.resume_model import (
    Resume as DatabaseResume,
    ResumeData,
)


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.create_resume_db")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.perform_pre_save_validation"
)
def test_handle_save_as_new_refinement_success(
    mock_validate,
    mock_create,
    test_user,
    test_resume,
):
    """Test handle_save_as_new_refinement successfully creates a new resume."""
    # Arrange
    db = MagicMock()
    context = RefinementContext(
        job_description="job desc",
        introduction="new intro",
        limit_refinement_years=None,
    )
    form_data = SaveAsNewForm(
        refined_content="full refined content",
        new_resume_name="New Resume",
        context=context,
    )
    params = SaveAsNewParams(
        db=db, user=test_user, resume=test_resume, form_data=form_data
    )

    resume_data = ResumeData(
        user_id=test_user.id,
        name=form_data.new_resume_name,
        content=form_data.refined_content,
        introduction=context.introduction,
    )
    new_resume = DatabaseResume(data=resume_data)
    mock_create.return_value = new_resume

    # Act
    result = handle_save_as_new_refinement(params)

    # Assert
    assert result == new_resume
    mock_validate.assert_called_once_with(form_data.refined_content)
    expected_create_params = ResumeCreateParams(
        user_id=test_user.id,
        name=form_data.new_resume_name,
        content=form_data.refined_content,
        is_base=False,
        parent_id=test_resume.id,
        job_description=context.job_description,
        introduction=context.introduction,
    )
    mock_create.assert_called_once_with(db=db, params=expected_create_params)


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.create_resume_db")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.perform_pre_save_validation"
)
def test_handle_save_as_new_refinement_failure_on_validation(
    mock_validate,
    mock_create,
    test_user,
    test_resume,
):
    """Test handle_save_as_new_refinement failure on validation."""
    # Arrange
    db = MagicMock()
    context = RefinementContext(
        job_description=None,
        introduction=None,
        limit_refinement_years=None,
    )
    form_data = SaveAsNewForm(
        refined_content="full refined content",
        new_resume_name="New",
        context=context,
    )
    params = SaveAsNewParams(
        db=db, user=test_user, resume=test_resume, form_data=form_data
    )
    mock_validate.side_effect = ValueError("validation failed")

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        handle_save_as_new_refinement(params)
    assert exc_info.value.status_code == 422
    assert "Failed to validate refined resume content" in exc_info.value.detail
    assert "validation failed" in exc_info.value.detail
    mock_validate.assert_called_once_with("full refined content")
    mock_create.assert_not_called()


