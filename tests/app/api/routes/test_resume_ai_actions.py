from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from resume_editor.app.api.dependencies import get_resume_for_user
from resume_editor.app.api.routes.route_models import SaveAsNewParams
from resume_editor.app.core.auth import get_current_user_from_cookie
from resume_editor.app.database.database import get_db
from resume_editor.app.main import create_app




@patch("resume_editor.app.api.routes.resume_ai.handle_save_as_new_refinement")
@pytest.mark.parametrize(
    "intro_value, expected_intro",
    [
        (None, None),
        ("", ""),
        ("This is a new introduction.", "This is a new introduction."),
    ],
)
def test_save_refined_resume_as_new(
    mock_handle_save,
    intro_value,
    expected_intro,
    client_with_auth_and_resume,
    test_user,
    test_resume,
):
    """Test accepting a refinement and saving it as a new resume."""
    # Arrange
    refined_content = "# Personal\n..."
    mock_handle_save.return_value = test_resume

    form_data = {
        "refined_content": refined_content,
        "new_resume_name": "New Name",
        "job_description": "A job description",
    }
    if intro_value is not None:
        form_data["introduction"] = intro_value

    # Act
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/save_as_new",
        data=form_data,
    )

    # Assert
    assert response.status_code == 200
    assert response.headers["HX-Redirect"] == f"/resumes/{test_resume.id}/view"
    assert not response.content

    mock_handle_save.assert_called_once()
    call_args, _ = mock_handle_save.call_args
    assert len(call_args) == 1
    params_arg = call_args[0]
    assert isinstance(params_arg, SaveAsNewParams)
    assert params_arg.user == test_user
    assert params_arg.resume == test_resume
    assert params_arg.form_data.refined_content == refined_content
    assert params_arg.form_data.new_resume_name == "New Name"
    assert params_arg.form_data.job_description == "A job description"
    assert params_arg.form_data.introduction == expected_intro




@patch("resume_editor.app.api.routes.resume_ai.handle_save_as_new_refinement")
@pytest.mark.parametrize("intro_value, expected_intro", [(None, None), ("", "")])
def test_save_refined_resume_as_new_no_intro_no_jd(
    mock_handle_save,
    intro_value,
    expected_intro,
    client_with_auth_and_resume,
    test_user,
    test_resume,
):
    """Test saving as new with no/empty intro and no job description."""
    # Arrange
    refined_content = "# Personal\nname: Refined New"
    mock_handle_save.return_value = test_resume

    form_data = {
        "refined_content": refined_content,
        "new_resume_name": "New Name",
        # No job_description
    }
    if intro_value is not None:
        form_data["introduction"] = intro_value

    # Act
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/save_as_new",
        data=form_data,
    )

    # Assert
    assert response.status_code == 200
    assert response.headers["HX-Redirect"] == f"/resumes/{test_resume.id}/view"
    assert not response.content

    mock_handle_save.assert_called_once()
    call_args, _ = mock_handle_save.call_args
    assert len(call_args) == 1
    params_arg = call_args[0]
    assert isinstance(params_arg, SaveAsNewParams)
    assert params_arg.user == test_user
    assert params_arg.resume == test_resume
    assert params_arg.form_data.refined_content == refined_content
    assert params_arg.form_data.new_resume_name == "New Name"
    assert params_arg.form_data.job_description is None
    assert params_arg.form_data.introduction == expected_intro


@patch("resume_editor.app.api.routes.resume_ai.handle_save_as_new_refinement")
def test_save_refined_resume_as_new_validation_error(
    mock_handle_save,
    client_with_auth_and_resume,
    test_resume,
):
    """Test that a validation error is handled when saving a new refined resume."""
    # Arrange
    mock_handle_save.side_effect = HTTPException(
        status_code=422, detail="Failed to validate"
    )
    refined_content = "# Personal\nname: Refined New"

    # Act
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/save_as_new",
        data={
            "refined_content": refined_content,
            "new_resume_name": "New Name",
            "job_description": "A job description",
        },
    )

    # Assert
    assert response.status_code == 422
    assert "Failed to validate" in response.json()["detail"]




@patch("resume_editor.app.api.routes.resume_ai.handle_save_as_new_refinement")
def test_save_refined_resume_as_new_no_name(
    mock_handle_save, client_with_auth_and_resume, test_resume
):
    """Test that saving as new without a name fails."""
    # Arrange
    mock_handle_save.side_effect = HTTPException(
        status_code=400, detail="New resume name is required"
    )

    # Act
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/save_as_new",
        data={
            "refined_content": "...",
            "new_resume_name": "",
        },
    )

    # Assert
    assert response.status_code == 400
    assert "New resume name is required" in response.json()["detail"]




def test_discard_refined_resume(client_with_auth_and_resume, test_resume):
    """Test the discard endpoint issues a 303 redirect to the edit page."""
    # Act
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/discard", follow_redirects=False
    )

    # Assert
    assert response.status_code == 303
    assert response.headers["location"] == f"/resumes/{test_resume.id}/edit"


@patch("resume_editor.app.api.routes.resume_ai.handle_save_as_new_refinement")
def test_save_refined_resume_as_new_e2e_form_post(
    mock_handle_save,
    test_user,
    test_resume,
):
    """
    Test the save_as_new endpoint with a real form post to ensure
    dot-notation form fields are correctly parsed into nested models.
    """
    # Arrange
    app = create_app()
    client = TestClient(app)

    mock_db_session = Mock()
    mock_handle_save.return_value = test_resume

    def get_mock_db():
        yield mock_db_session

    def get_mock_current_user():
        return test_user

    def get_mock_resume():
        return test_resume

    app.dependency_overrides[get_db] = get_mock_db
    app.dependency_overrides[
        get_current_user_from_cookie
    ] = get_mock_current_user
    app.dependency_overrides[get_resume_for_user] = get_mock_resume

    form_data = {
        "refined_content": "# Some Content",
        "new_resume_name": "My New Resume",
        "job_description": "A Great Job",
        "introduction": "A custom user-edited intro",
        "limit_refinement_years": 5,
    }

    # Act
    try:
        response = client.post(
            f"/api/resumes/{test_resume.id}/refine/save_as_new",
            data=form_data,
        )

        # Assert
        assert response.status_code == 200
        assert response.headers["HX-Redirect"] == f"/resumes/{test_resume.id}/view"
        assert not response.content

        mock_handle_save.assert_called_once()
        call_args, _ = mock_handle_save.call_args
        params_arg = call_args[0]

        assert isinstance(params_arg, SaveAsNewParams)
        assert params_arg.form_data.new_resume_name == "My New Resume"
        assert (
            params_arg.form_data.introduction
            == "A custom user-edited intro"
        )
        assert params_arg.form_data.job_description == "A Great Job"
        assert params_arg.form_data.limit_refinement_years == 5
        assert params_arg.form_data.refined_content == "# Some Content"

    finally:
        # Cleanup
        app.dependency_overrides.clear()
