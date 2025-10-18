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
