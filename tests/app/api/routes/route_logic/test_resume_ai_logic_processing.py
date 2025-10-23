from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from resume_editor.app.api.routes.html_fragments import RefineResultParams
from resume_editor.app.api.routes.route_logic.resume_ai_logic import (
    ProcessExperienceResultParams,
    process_refined_experience_result,
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
from resume_editor.app.models.resume_model import Resume as DatabaseResume


@pytest.fixture
def mock_resume() -> DatabaseResume:
    """Provides a mock resume with a dummy ID."""
    resume = MagicMock(spec=DatabaseResume)
    resume.id = 1
    return resume


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
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_education_info"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_experience_info"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_personal_info"
)
def test_process_refined_experience_result(
    mock_extract_personal,
    mock_extract_experience,
    mock_extract_education,
    mock_extract_certifications,
    mock_build_complete,
    mock_create_html,
    mock_resume,
):
    """
    Test that process_refined_experience_result correctly reconstructs a full
    resume with refined roles and original projects.
    """
    # Arrange
    original_content = "original resume content"
    content_to_refine = "filtered resume content"

    # Mocks for extractors
    mock_personal = MagicMock()
    mock_education = MagicMock()
    mock_certifications = MagicMock()
    mock_extract_personal.return_value = mock_personal
    mock_extract_education.return_value = mock_education
    mock_extract_certifications.return_value = mock_certifications

    original_project = Project(overview=ProjectOverview(title="Original Project"))
    original_experience = ExperienceResponse(
        roles=[
            Role(
                basics=RoleBasics(
                    company="Company A", title="Dev", start_date=date(2020, 1, 1)
                )
            ),
            Role(
                basics=RoleBasics(
                    company="Company B", title="Sr. Dev", start_date=date(2022, 1, 1)
                )
            ),
        ],
        projects=[original_project],
    )

    # This is the filtered experience that was sent for refinement
    refinement_base_experience = ExperienceResponse(
        roles=[
            Role(
                basics=RoleBasics(
                    company="Company B", title="Sr. Dev", start_date=date(2022, 1, 1)
                )
            ),
        ],
        projects=[],  # Projects might be filtered out
    )

    mock_extract_experience.side_effect = [
        original_experience,  # First call on original_resume_content
        refinement_base_experience,  # Second call on resume_content_to_refine
    ]

    refined_role_data = Role(
        basics=RoleBasics(
            company="Company B Refined",
            title="Sr. Dev Refined",
            start_date=date(2022, 1, 1),
        )
    ).model_dump()
    refined_roles = {0: refined_role_data}  # Index 0 of the filtered list

    mock_build_complete.return_value = "fully reconstructed resume"
    mock_create_html.return_value = "final html"

    # Act
    params = ProcessExperienceResultParams(
        resume_id=mock_resume.id,
        original_resume_content=original_content,
        resume_content_to_refine=content_to_refine,
        refined_roles=refined_roles,
        job_description="job desc",
        introduction="intro",
        limit_refinement_years=5,
    )
    result = process_refined_experience_result(params)

    # Assert
    assert result == "final html"

    # Check extractors were called correctly
    mock_extract_personal.assert_called_once_with(original_content)
    mock_extract_education.assert_called_once_with(original_content)
    mock_extract_certifications.assert_called_once_with(original_content)
    assert mock_extract_experience.call_count == 2
    mock_extract_experience.assert_any_call(original_content)
    mock_extract_experience.assert_any_call(content_to_refine)

    # Check that `build_complete_resume_from_sections` was called with correct data
    mock_build_complete.assert_called_once()
    build_args = mock_build_complete.call_args.kwargs
    assert build_args["personal_info"] == mock_personal
    assert build_args["education"] == mock_education
    assert build_args["certifications"] == mock_certifications

    # Check experience object passed to builder
    experience_arg = build_args["experience"]
    assert isinstance(experience_arg, ExperienceResponse)
    assert len(experience_arg.roles) == 1
    assert (
        experience_arg.roles[0].basics.company == "Company B Refined"
    )  # The refined role
    assert len(experience_arg.projects) == 1
    assert (
        experience_arg.projects[0].overview.title == "Original Project"
    )  # The original project

    # Check that the final HTML generator was called correctly
    mock_create_html.assert_called_once()
    html_params = mock_create_html.call_args.kwargs["params"]
    assert isinstance(html_params, RefineResultParams)
    assert html_params.refined_content == "fully reconstructed resume"
    assert html_params.introduction == "intro"
    assert html_params.limit_refinement_years == 5
    assert html_params.resume_id == mock_resume.id


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
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_education_info"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_experience_info"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_personal_info"
)
def test_process_refined_experience_result_out_of_bounds_index(
    mock_extract_personal,
    mock_extract_experience,
    mock_extract_education,
    mock_extract_certifications,
    mock_build_complete,
    mock_create_html,
    mock_resume,
):
    """Test process_refined_experience_result ignores out-of-bounds indices."""
    # Arrange
    original_content = "original resume content"
    content_to_refine = "filtered resume content"

    # Mock extractors
    mock_extract_personal.return_value = MagicMock()
    mock_extract_education.return_value = MagicMock()
    mock_extract_certifications.return_value = MagicMock()

    original_experience = ExperienceResponse(roles=[], projects=[])
    # The filtered content has one role, which is the one we expect to see
    refinement_base_experience = ExperienceResponse(
        roles=[
            Role(
                basics=RoleBasics(
                    company="Original Co", title="Original Role", start_date=date(2022, 1, 1)
                )
            )
        ],
        projects=[],
    )
    mock_extract_experience.side_effect = [
        original_experience,
        refinement_base_experience,
    ]

    # Use an out-of-bounds index (e.g., 1, when there is only one role in filtered list)
    refined_role_llm = Role(
        basics=RoleBasics(
            company="Refined Co", title="Refined Role", start_date=date(2023, 1, 1)
        ),
        summary=RoleSummary(text="Refined Summary"),
    )
    refined_roles_from_llm = {1: refined_role_llm.model_dump(mode="json")}
    mock_build_complete.return_value = "reconstructed content"
    mock_create_html.return_value = "final html"

    # Act
    params = ProcessExperienceResultParams(
        resume_id=mock_resume.id,
        original_resume_content=original_content,
        resume_content_to_refine=content_to_refine,
        refined_roles=refined_roles_from_llm,
        job_description="A job",
        introduction="An intro",
        limit_refinement_years=None,
    )
    result = process_refined_experience_result(params)

    # Assert
    assert result == "final html"
    mock_build_complete.assert_called_once()
    build_args = mock_build_complete.call_args.kwargs
    experience_arg = build_args["experience"]

    # The out-of-bounds index should be ignored, so the role is not updated.
    assert len(experience_arg.roles) == 1
    assert experience_arg.roles[0].basics.company == "Original Co"

    # Check call to HTML generator
    mock_create_html.assert_called_once()
    html_params = mock_create_html.call_args.kwargs["params"]
    assert isinstance(html_params, RefineResultParams)
    assert html_params.refined_content == "reconstructed content"
    assert html_params.introduction == "An intro"
    assert html_params.resume_id == mock_resume.id
