from unittest.mock import ANY, patch

import pytest
from fastapi import HTTPException

from resume_editor.app.api.routes.route_models import SaveAsNewParams


@patch("resume_editor.app.api.routes.resume_ai.handle_accept_refinement")
@pytest.mark.parametrize(
    "target_section",
    [
        "personal",
        "education",
        "experience",
        "certifications",
    ],
)
@pytest.mark.parametrize(
    "intro_value, expected_intro",
    [(None, None), ("", ""), ("This is an introduction.", "This is an introduction.")],
)
def test_accept_refined_resume_overwrite_partial(
    mock_handle_accept,
    target_section,
    intro_value,
    expected_intro,
    client_with_auth_and_resume,
    test_resume,
):
    """Test accepting a partial refinement and overwriting the existing resume."""
    from resume_editor.app.api.routes.route_models import RefineTargetSection

    # Arrange
    refined_content = f"# {target_section.capitalize()}\n..."
    mock_handle_accept.return_value = test_resume

    form_data = {
        "refined_content": refined_content,
        "target_section": target_section,
    }
    if intro_value is not None:
        form_data["introduction"] = intro_value

    # Act
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/accept",
        data=form_data,
    )

    # Assert
    assert response.status_code == 200
    assert response.headers["HX-Redirect"] == "/dashboard"
    assert not response.content

    mock_handle_accept.assert_called_once_with(
        db=ANY,
        resume=test_resume,
        refined_content=refined_content,
        target_section=RefineTargetSection(target_section),
        introduction=expected_intro,
    )




@patch("resume_editor.app.api.routes.resume_ai.handle_accept_refinement")
@pytest.mark.parametrize("intro_value, expected_intro", [(None, None), ("", "")])
def test_accept_refined_resume_overwrite_full(
    mock_handle_accept,
    intro_value,
    expected_intro,
    client_with_auth_and_resume,
    test_resume,
):
    """Test 'full' refinement overwrites content."""
    from resume_editor.app.api.routes.route_models import RefineTargetSection

    # Arrange
    refined_content = "# Personal\nname: Full Refined"
    mock_handle_accept.return_value = test_resume

    form_data = {
        "refined_content": refined_content,
        "target_section": RefineTargetSection.FULL.value,
    }
    if intro_value is not None:
        form_data["introduction"] = intro_value

    # Act
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/accept",
        data=form_data,
    )

    # Assert
    assert response.status_code == 200
    assert response.headers["HX-Redirect"] == "/dashboard"
    assert not response.content

    mock_handle_accept.assert_called_once_with(
        db=ANY,
        resume=test_resume,
        refined_content=refined_content,
        target_section=RefineTargetSection.FULL,
        introduction=expected_intro,
    )


@patch("resume_editor.app.api.routes.resume_ai.handle_save_as_new_refinement")
@pytest.mark.parametrize(
    "intro_value, expected_intro",
    [(None, None), ("", ""), ("This is a new introduction.", "This is a new introduction.")],
)
def test_save_refined_resume_as_new_full(
    mock_handle_save,
    intro_value,
    expected_intro,
    client_with_auth_and_resume,
    test_user,
    test_resume,
):
    """Test accepting a 'full' refinement and saving it as a new resume."""
    from resume_editor.app.api.routes.route_models import RefineTargetSection

    # Arrange
    refined_content = "# Personal\n..."
    mock_handle_save.return_value = test_resume

    form_data = {
        "refined_content": refined_content,
        "target_section": RefineTargetSection.FULL.value,
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
    assert params_arg.form_data.target_section == RefineTargetSection.FULL
    assert params_arg.form_data.new_resume_name == "New Name"
    assert params_arg.form_data.job_description == "A job description"
    assert params_arg.form_data.introduction == expected_intro


@patch("resume_editor.app.api.routes.resume_ai.handle_save_as_new_refinement")
@pytest.mark.parametrize(
    "intro_value, expected_intro",
    [(None, None), ("", ""), ("The new intro.", "The new intro.")],
)
def test_save_refined_resume_as_new_partial_with_job_desc(
    mock_handle_save,
    intro_value,
    expected_intro,
    client_with_auth_and_resume,
    test_user,
    test_resume,
):
    """Test accepting a partial refinement with job desc and saving it as new."""
    from resume_editor.app.api.routes.route_models import RefineTargetSection

    # Arrange
    refined_content = "# Personal\nname: Refined New"
    mock_handle_save.return_value = test_resume

    form_data = {
        "refined_content": refined_content,
        "target_section": RefineTargetSection.PERSONAL.value,
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
    assert params_arg.form_data.target_section == RefineTargetSection.PERSONAL
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
    from resume_editor.app.api.routes.route_models import RefineTargetSection

    # Arrange
    refined_content = "# Personal\nname: Refined New"
    mock_handle_save.return_value = test_resume

    form_data = {
        "refined_content": refined_content,
        "target_section": RefineTargetSection.PERSONAL.value,
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
    assert params_arg.form_data.target_section == RefineTargetSection.PERSONAL
    assert params_arg.form_data.new_resume_name == "New Name"
    assert params_arg.form_data.job_description is None
    assert params_arg.form_data.introduction == expected_intro


@patch("resume_editor.app.api.routes.resume_ai.handle_save_as_new_refinement")
def test_save_refined_resume_as_new_reconstruction_error(
    mock_handle_save,
    client_with_auth_and_resume,
    test_resume,
):
    """Test that a reconstruction error is handled when saving a new refined resume."""
    from resume_editor.app.api.routes.route_models import RefineTargetSection

    # Arrange
    mock_handle_save.side_effect = HTTPException(
        status_code=422, detail="Failed to reconstruct"
    )
    refined_content = "# Personal\nname: Refined New"

    # Act
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/save_as_new",
        data={
            "refined_content": refined_content,
            "target_section": RefineTargetSection.FULL.value,
            "new_resume_name": "New Name",
            "job_description": "A job description",
        },
    )

    # Assert
    assert response.status_code == 422
    assert "Failed to reconstruct" in response.json()["detail"]


@patch("resume_editor.app.api.routes.resume_ai.handle_accept_refinement")
def test_accept_refined_resume_reconstruction_error(
    mock_handle_accept,
    client_with_auth_and_resume,
    test_resume,
):
    """Test that an error during reconstruction is handled."""
    from resume_editor.app.api.routes.route_models import RefineTargetSection

    # Arrange
    mock_handle_accept.side_effect = HTTPException(
        status_code=422, detail="Failed to reconstruct"
    )
    refined_content = "# Personal\nname: Refined"

    # Act
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/accept",
        data={
            "refined_content": refined_content,
            "target_section": RefineTargetSection.PERSONAL.value,
        },
    )

    # Assert
    assert response.status_code == 422
    assert "Failed to reconstruct" in response.json()["detail"]


def test_save_refined_resume_as_new_no_name(
    client_with_auth_and_resume,
    test_resume,
):
    """Test that saving as new without a name fails."""
    from resume_editor.app.api.routes.route_models import RefineTargetSection

    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/save_as_new",
        data={
            "refined_content": "...",
            "target_section": RefineTargetSection.FULL.value,
            "new_resume_name": "",
        },
    )
    assert response.status_code == 400
    assert "New resume name is required" in response.json()["detail"]


def test_accept_refined_resume_invalid_section(
    client_with_auth_and_resume,
    test_resume,
):
    """Test that providing an invalid section to the accept endpoint fails."""
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/accept",
        data={
            "refined_content": "content",
            "target_section": "invalid_section",
        },
    )
    assert response.status_code == 422
    body = response.json()
    assert body["detail"][0]["type"] == "enum"
    assert body["detail"][0]["input"] == "invalid_section"
    assert (
        "Input should be 'full', 'personal', 'education', 'experience' or 'certifications'"
        in body["detail"][0]["msg"]
    )


def test_discard_refined_resume(client_with_auth_and_resume, test_resume):
    """Test the discard endpoint returns an HX-Redirect to the resume view page."""
    # Act
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/discard"
    )

    # Assert
    assert response.status_code == 200
    assert response.headers["HX-Redirect"] == f"/resumes/{test_resume.id}/view"
    assert not response.content
