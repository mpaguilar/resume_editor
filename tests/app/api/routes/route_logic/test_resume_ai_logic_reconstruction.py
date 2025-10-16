from unittest.mock import MagicMock, patch

import pytest

from resume_editor.app.api.routes.route_logic.resume_ai_logic import (
    process_refined_experience_result,
    reconstruct_resume_from_refined_section,
)
from resume_editor.app.api.routes.route_models import (
    ExperienceResponse,
    RefineTargetSection,
)
from resume_editor.app.models.resume.experience import (
    Project,
    ProjectOverview,
    Role,
    RoleBasics,
    RoleSummary,
)
from resume_editor.app.models.resume_model import (
    Resume as DatabaseResume,
    ResumeData,
)


@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic._create_refine_result_html"
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
def test_process_refined_experience_result(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_create_html,
):
    """Test process_refined_experience_result successfully reconstructs and generates HTML."""
    # Arrange
    resume_data = ResumeData(user_id=1, name="Test", content="Original content")
    resume = DatabaseResume(data=resume_data)
    resume.id = 1

    refined_role1 = Role(
        basics=RoleBasics(
            company="Refined Co", title="Refined Role", start_date="2023-01-01"
        ),
        summary=RoleSummary(text="Refined Summary"),
    )
    refined_roles = {0: refined_role1.model_dump(mode="json")}

    job_description = "A job"
    introduction = "An intro"

    mock_project = Project(overview=ProjectOverview(title="My Project"))
    mock_original_experience = ExperienceResponse(roles=[], projects=[mock_project])

    mock_extract_personal.return_value = "personal"
    mock_extract_education.return_value = "education"
    mock_extract_experience.return_value = mock_original_experience
    mock_extract_certifications.return_value = "certifications"
    mock_build_sections.return_value = "updated content"
    mock_create_html.return_value = "final html"

    # Act
    result = process_refined_experience_result(
        resume, refined_roles, job_description, introduction
    )

    # Assert
    assert result == "final html"

    mock_extract_personal.assert_called_once_with(resume.content)
    mock_extract_education.assert_called_once_with(resume.content)
    mock_extract_experience.assert_called_once_with(resume.content)
    mock_extract_certifications.assert_called_once_with(resume.content)

    mock_build_sections.assert_called_once()
    call_args = mock_build_sections.call_args.kwargs
    assert call_args["personal_info"] == "personal"
    assert call_args["education"] == "education"
    assert call_args["certifications"] == "certifications"

    reconstructed_experience = call_args["experience"]
    assert len(reconstructed_experience.roles) == 1
    assert reconstructed_experience.roles[0].summary.text == "Refined Summary"
    assert reconstructed_experience.projects == mock_original_experience.projects

    mock_create_html.assert_called_once_with(
        resume.id,
        "experience",
        "updated content",
        job_description=job_description,
        introduction=introduction,
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
@pytest.mark.parametrize(
    "target_section",
    [
        RefineTargetSection.PERSONAL,
        RefineTargetSection.EDUCATION,
        RefineTargetSection.EXPERIENCE,
        RefineTargetSection.CERTIFICATIONS,
    ],
)
def test_reconstruct_resume_from_refined_section_partial(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    target_section,
):
    """Test partial reconstruction for each section."""
    original_content = "original"
    refined_content = "refined"
    mock_build_sections.return_value = "reconstructed"

    result = reconstruct_resume_from_refined_section(
        original_content, refined_content, target_section
    )

    assert result == "reconstructed"

    if target_section == RefineTargetSection.PERSONAL:
        mock_extract_personal.assert_called_once_with(refined_content)
        mock_extract_education.assert_called_once_with(original_content)
        mock_extract_experience.assert_called_once_with(original_content)
        mock_extract_certifications.assert_called_once_with(original_content)
    elif target_section == RefineTargetSection.EDUCATION:
        mock_extract_personal.assert_called_once_with(original_content)
        mock_extract_education.assert_called_once_with(refined_content)
        mock_extract_experience.assert_called_once_with(original_content)
        mock_extract_certifications.assert_called_once_with(original_content)
    elif target_section == RefineTargetSection.EXPERIENCE:
        mock_extract_personal.assert_called_once_with(original_content)
        mock_extract_education.assert_called_once_with(original_content)
        mock_extract_experience.assert_called_once_with(refined_content)
        mock_extract_certifications.assert_called_once_with(original_content)
    elif target_section == RefineTargetSection.CERTIFICATIONS:
        mock_extract_personal.assert_called_once_with(original_content)
        mock_extract_education.assert_called_once_with(original_content)
        mock_extract_experience.assert_called_once_with(original_content)
        mock_extract_certifications.assert_called_once_with(refined_content)

    mock_build_sections.assert_called_once()


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
def test_reconstruct_resume_from_refined_section_full(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
):
    """Test 'full' reconstruction directly returns refined content."""
    original_content = "original"
    refined_content = "refined"
    result = reconstruct_resume_from_refined_section(
        original_content, refined_content, RefineTargetSection.FULL
    )

    assert result == refined_content
    mock_extract_personal.assert_not_called()
    mock_extract_education.assert_not_called()
    mock_extract_experience.assert_not_called()
    mock_extract_certifications.assert_not_called()
    mock_build_sections.assert_not_called()
