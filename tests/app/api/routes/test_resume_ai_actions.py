from unittest.mock import ANY, patch

import pytest
from fastapi import HTTPException


@patch("resume_editor.app.api.routes.resume_ai.update_resume_db")
@patch("resume_editor.app.api.routes.resume_ai.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume_ai.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume_ai.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_education_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
@pytest.mark.parametrize(
    "intro_value, expected_intro",
    [(None, None), ("", ""), ("This is an introduction.", "This is an introduction.")],
)
def test_accept_refined_resume_overwrite_personal(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_pre_save,
    mock_update_db,
    intro_value,
    expected_intro,
    client_with_auth_and_resume,
    test_resume,
):
    """Test accepting a 'personal' refinement and overwriting the existing resume."""
    from resume_editor.app.api.routes.route_models import (
        PersonalInfoResponse,
        RefineTargetSection,
    )

    # Arrange
    refined_content = "# Personal\nname: Refined"
    mock_extract_personal.return_value = PersonalInfoResponse(name="Refined")
    mock_build_sections.return_value = "reconstructed content"
    mock_update_db.return_value = test_resume

    form_data = {
        "refined_content": refined_content,
        "target_section": RefineTargetSection.PERSONAL.value,
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
    mock_extract_personal.assert_called_once_with(refined_content)
    mock_extract_education.assert_called_once_with(test_resume.content)
    mock_extract_experience.assert_called_once_with(test_resume.content)
    mock_extract_certifications.assert_called_once_with(test_resume.content)
    mock_build_sections.assert_called_once()
    assert mock_build_sections.call_args.kwargs["personal_info"].name == "Refined"
    mock_pre_save.assert_called_once_with("reconstructed content", test_resume.content)
    mock_update_db.assert_called_once()
    assert mock_update_db.call_args.kwargs["content"] == "reconstructed content"
    assert mock_update_db.call_args.kwargs["introduction"] == expected_intro


@patch("resume_editor.app.api.routes.resume_ai.update_resume_db")
@patch("resume_editor.app.api.routes.resume_ai.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume_ai.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume_ai.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_education_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
@pytest.mark.parametrize("intro_value, expected_intro", [(None, None), ("", "")])
def test_accept_refined_resume_overwrite_education_no_intro(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_pre_save,
    mock_update_db,
    intro_value,
    expected_intro,
    client_with_auth_and_resume,
    test_resume,
):
    """Test accepting 'education' refinement with no introduction or empty introduction."""
    from resume_editor.app.api.routes.route_models import (
        EducationResponse,
        RefineTargetSection,
    )

    refined_content = "# Education\n..."
    mock_extract_education.return_value = EducationResponse(degrees=[])
    mock_update_db.return_value = test_resume

    form_data = {
        "refined_content": refined_content,
        "target_section": RefineTargetSection.EDUCATION.value,
    }
    if intro_value is not None:
        form_data["introduction"] = intro_value

    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/accept",
        data=form_data,
    )
    assert response.status_code == 200
    assert response.headers["HX-Redirect"] == "/dashboard"
    assert not response.content
    mock_extract_education.assert_called_once_with(refined_content)
    mock_extract_personal.assert_called_once_with(test_resume.content)
    mock_build_sections.assert_called_once()
    mock_pre_save.assert_called_once()
    mock_update_db.assert_called_once()
    assert mock_update_db.call_args.kwargs["introduction"] == expected_intro


@patch("resume_editor.app.api.routes.resume_ai.update_resume_db")
@patch("resume_editor.app.api.routes.resume_ai.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume_ai.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume_ai.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_education_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
@pytest.mark.parametrize("intro_value, expected_intro", [(None, None), ("", "")])
def test_accept_refined_resume_overwrite_experience_no_intro(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_pre_save,
    mock_update_db,
    intro_value,
    expected_intro,
    client_with_auth_and_resume,
    test_resume,
):
    """Test accepting an 'experience' refinement with no introduction."""
    from resume_editor.app.api.routes.route_models import (
        ExperienceResponse,
        RefineTargetSection,
    )

    refined_content = "# Experience\n..."
    mock_extract_experience.return_value = ExperienceResponse(roles=[], projects=[])
    mock_update_db.return_value = test_resume

    form_data = {
        "refined_content": refined_content,
        "target_section": RefineTargetSection.EXPERIENCE.value,
    }
    if intro_value is not None:
        form_data["introduction"] = intro_value

    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/accept",
        data=form_data,
    )

    assert response.status_code == 200
    assert response.headers["HX-Redirect"] == "/dashboard"
    assert not response.content
    mock_extract_experience.assert_called_once_with(refined_content)
    mock_extract_personal.assert_called_once_with(test_resume.content)
    mock_build_sections.assert_called_once()
    mock_pre_save.assert_called_once()
    mock_update_db.assert_called_once()
    assert mock_update_db.call_args.kwargs["introduction"] == expected_intro


@patch("resume_editor.app.api.routes.resume_ai.update_resume_db")
@patch("resume_editor.app.api.routes.resume_ai.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume_ai.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume_ai.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_education_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
@pytest.mark.parametrize("intro_value, expected_intro", [(None, None), ("", "")])
def test_accept_refined_resume_overwrite_certifications_no_intro(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_pre_save,
    mock_update_db,
    intro_value,
    expected_intro,
    client_with_auth_and_resume,
    test_resume,
):
    """Test 'certifications' refinement with no or empty introduction."""
    from resume_editor.app.api.routes.route_models import (
        CertificationsResponse,
        RefineTargetSection,
    )

    refined_content = "# Certifications\n..."
    mock_extract_certifications.return_value = CertificationsResponse(certifications=[])
    mock_update_db.return_value = test_resume

    form_data = {
        "refined_content": refined_content,
        "target_section": RefineTargetSection.CERTIFICATIONS.value,
    }
    if intro_value is not None:
        form_data["introduction"] = intro_value

    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/accept",
        data=form_data,
    )
    assert response.status_code == 200
    assert response.headers["HX-Redirect"] == "/dashboard"
    assert not response.content
    mock_extract_certifications.assert_called_once_with(refined_content)
    mock_extract_personal.assert_called_once_with(test_resume.content)
    mock_build_sections.assert_called_once()
    mock_pre_save.assert_called_once()
    mock_update_db.assert_called_once()
    assert mock_update_db.call_args.kwargs["introduction"] == expected_intro


@patch("resume_editor.app.api.routes.resume_ai.update_resume_db")
@patch("resume_editor.app.api.routes.resume_ai.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume_ai.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume_ai.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_education_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
@pytest.mark.parametrize("intro_value, expected_intro", [(None, None), ("", "")])
def test_accept_refined_resume_overwrite_full_no_intro(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_pre_save,
    mock_update_db,
    intro_value,
    expected_intro,
    client_with_auth_and_resume,
    test_resume,
):
    """Test 'full' refinement with no or empty introduction."""
    from resume_editor.app.api.routes.route_models import RefineTargetSection

    # Arrange
    refined_content = "# Personal\nname: Full Refined"
    mock_update_db.return_value = test_resume

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
    mock_extract_personal.assert_not_called()
    mock_extract_education.assert_not_called()
    mock_extract_experience.assert_not_called()
    mock_extract_certifications.assert_not_called()
    mock_build_sections.assert_not_called()

    mock_pre_save.assert_called_once_with(refined_content, test_resume.content)
    mock_update_db.assert_called_once()
    assert mock_update_db.call_args.kwargs["content"] == refined_content
    assert mock_update_db.call_args.kwargs["introduction"] == expected_intro


@patch("resume_editor.app.api.routes.resume_ai.create_resume_db")
@patch("resume_editor.app.api.routes.resume_ai.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume_ai.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume_ai.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_education_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
@pytest.mark.parametrize(
    "intro_value, expected_intro",
    [(None, None), ("", ""), ("This is a new introduction.", "This is a new introduction.")],
)
def test_save_refined_resume_as_new_full(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_pre_save,
    mock_create_db,
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
    mock_create_db.return_value = None  # Not used

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
    assert response.headers["HX-Redirect"] == "/dashboard"
    assert not response.content

    mock_pre_save.assert_called_once_with(refined_content, test_resume.content)
    mock_build_sections.assert_not_called()
    mock_extract_personal.assert_not_called()
    mock_extract_education.assert_not_called()
    mock_extract_experience.assert_not_called()
    mock_extract_certifications.assert_not_called()
    mock_create_db.assert_called_once_with(
        db=ANY,
        user_id=test_user.id,
        name="New Name",
        content=refined_content,
        is_base=False,
        parent_id=test_resume.id,
        job_description="A job description",
        introduction=expected_intro,
    )


@patch("resume_editor.app.api.routes.resume_ai.create_resume_db")
@patch("resume_editor.app.api.routes.resume_ai.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume_ai.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume_ai.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_education_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
@pytest.mark.parametrize(
    "intro_value, expected_intro",
    [(None, None), ("", ""), ("The new intro.", "The new intro.")],
)
def test_save_refined_resume_as_new_partial_with_job_desc(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_pre_save,
    mock_create_db,
    intro_value,
    expected_intro,
    client_with_auth_and_resume,
    test_user,
    test_resume,
):
    """Test accepting a partial refinement with job desc and saving it as new."""
    from resume_editor.app.api.routes.route_models import (
        PersonalInfoResponse,
        RefineTargetSection,
    )

    # Arrange
    refined_content = "# Personal\nname: Refined New"
    reconstructed_content = "reconstructed content for new resume"

    mock_extract_personal.return_value = PersonalInfoResponse(name="Refined New")
    mock_build_sections.return_value = reconstructed_content

    mock_create_db.return_value = None  # Not used

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
    assert response.headers["HX-Redirect"] == "/dashboard"
    assert not response.content
    mock_extract_personal.assert_called_once_with(refined_content)
    mock_extract_education.assert_called_once_with(test_resume.content)
    mock_build_sections.assert_called_once()
    mock_pre_save.assert_called_once_with(reconstructed_content, test_resume.content)
    mock_create_db.assert_called_once_with(
        db=ANY,
        user_id=test_user.id,
        name="New Name",
        content=reconstructed_content,
        is_base=False,
        parent_id=test_resume.id,
        job_description="A job description",
        introduction=expected_intro,
    )


@patch("resume_editor.app.api.routes.resume_ai.create_resume_db")
@patch("resume_editor.app.api.routes.resume_ai.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume_ai.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume_ai.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_education_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
@pytest.mark.parametrize("intro_value, expected_intro", [(None, None), ("", "")])
def test_save_refined_resume_as_new_no_intro_no_jd(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_pre_save,
    mock_create_db,
    intro_value,
    expected_intro,
    client_with_auth_and_resume,
    test_user,
    test_resume,
):
    """Test saving as new with no/empty intro and no job description."""
    from resume_editor.app.api.routes.route_models import (
        PersonalInfoResponse,
        RefineTargetSection,
    )

    # Arrange
    refined_content = "# Personal\nname: Refined New"
    reconstructed_content = "reconstructed content for new resume"

    mock_extract_personal.return_value = PersonalInfoResponse(name="Refined New")
    mock_build_sections.return_value = reconstructed_content

    mock_create_db.return_value = None  # Not used

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
    assert response.headers["HX-Redirect"] == "/dashboard"
    assert not response.content
    mock_extract_personal.assert_called_once_with(refined_content)
    mock_extract_education.assert_called_once_with(test_resume.content)
    mock_build_sections.assert_called_once()
    mock_pre_save.assert_called_once_with(reconstructed_content, test_resume.content)
    mock_create_db.assert_called_once_with(
        db=ANY,
        user_id=test_user.id,
        name="New Name",
        content=reconstructed_content,
        is_base=False,
        parent_id=test_resume.id,
        job_description=None,  # Expect None
        introduction=expected_intro,
    )


@patch("resume_editor.app.api.routes.resume_ai.perform_pre_save_validation")
def test_save_refined_resume_as_new_reconstruction_error(
    mock_pre_save,
    client_with_auth_and_resume,
    test_resume,
):
    """Test that a reconstruction error is handled when saving a new refined resume."""
    from resume_editor.app.api.routes.route_models import RefineTargetSection

    # Arrange
    mock_pre_save.side_effect = HTTPException(status_code=422, detail="Invalid")
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


@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
def test_accept_refined_resume_reconstruction_error(
    mock_extract_personal,
    client_with_auth_and_resume,
    test_resume,
):
    """Test that an error during reconstruction is handled."""
    from resume_editor.app.api.routes.route_models import RefineTargetSection

    # Arrange
    mock_extract_personal.side_effect = ValueError("test error")
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


@patch("resume_editor.app.api.routes.resume_ai._generate_resume_detail_html")
def test_discard_refined_resume(
    mock_generate_html, client_with_auth_and_resume, test_resume
):
    """Test the discard endpoint returns the original resume detail HTML."""
    # Arrange
    mock_generate_html.return_value = "<div>Original Detail HTML</div>"

    # Act
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/discard"
    )

    # Assert
    assert response.status_code == 200
    assert response.text == "<div>Original Detail HTML</div>"
    mock_generate_html.assert_called_once_with(test_resume)
