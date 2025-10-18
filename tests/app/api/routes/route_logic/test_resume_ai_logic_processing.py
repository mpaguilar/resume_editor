from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from resume_editor.app.api.routes.route_logic.resume_ai_logic import (
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
from resume_editor.app.models.resume_model import Resume as DatabaseResume, ResumeData


@pytest.fixture
def mock_resume() -> DatabaseResume:
    """Provides a mock resume with a dummy ID."""
    resume = MagicMock(spec=DatabaseResume)
    resume.id = 1
    return resume


@pytest.fixture
def mock_experience_info() -> ExperienceResponse:
    """Provides a mock ExperienceResponse object with roles and projects."""
    return ExperienceResponse(
        roles=[
            Role(
                basics=RoleBasics(
                    company="Old Company 1",
                    title="Old Role 1",
                    start_date=date(2018, 1, 1),
                )
            ),
            Role(
                basics=RoleBasics(
                    company="Old Company 2",
                    title="Old Role 2",
                    start_date=date(2022, 1, 1),
                )
            ),
        ],
        projects=[
            Project(
                overview=ProjectOverview(
                    title="Old Project 1", start_date=date(2018, 1, 1)
                )
            ),
            Project(
                overview=ProjectOverview(
                    title="Old Project 2", start_date=date(2022, 1, 1)
                )
            ),
        ],
    )


@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic._create_refine_result_html"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.serialize_experience_to_markdown"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_experience_info"
)
def test_process_refined_experience_result(
    mock_extract,
    mock_serialize,
    mock_create_html,
    mock_resume,
    mock_experience_info,
):
    """
    Test that roles are correctly updated.
    """
    # Arrange
    test_content = "some resume content"
    mock_extract.return_value = mock_experience_info
    refined_roles = {
        1: Role(
            basics=RoleBasics(
                company="Refined Company 2",
                title="Refined Role 2",
                start_date=date(2022, 1, 1),
            )
        ).model_dump()
    }
    mock_serialize.return_value = "serialized_markdown"

    # Act
    process_refined_experience_result(
        resume_id=mock_resume.id,
        resume_content_to_refine=test_content,
        refined_roles=refined_roles,
        job_description="job desc",
        introduction="intro",
    )

    # Assert
    mock_extract.assert_called_once_with(test_content)

    mock_serialize.assert_called_once()
    call_args = mock_serialize.call_args[0]
    experience_arg: ExperienceResponse = call_args[0]

    assert len(experience_arg.roles) == 2
    assert experience_arg.roles[0].basics.company == "Old Company 1"
    assert experience_arg.roles[1].basics.company == "Refined Company 2"
    assert len(experience_arg.projects) == 2  # Projects are preserved
    assert experience_arg.projects[0].overview.title == "Old Project 1"

    mock_create_html.assert_called_once_with(
        resume_id=mock_resume.id,
        target_section_val=RefineTargetSection.EXPERIENCE.value,
        refined_content="serialized_markdown",
        job_description="job desc",
        introduction="intro",
    )


@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic._create_refine_result_html"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.serialize_experience_to_markdown"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_experience_info"
)
def test_process_refined_experience_result_out_of_bounds_index(
    mock_extract_experience,
    mock_serialize_experience,
    mock_create_html,
):
    """Test process_refined_experience_result ignores out-of-bounds indices."""
    # Arrange
    resume_data = ResumeData(user_id=1, name="Test", content="Original content")
    resume = DatabaseResume(data=resume_data)
    resume.id = 1

    original_role = Role(
        basics=RoleBasics(
            company="Original Co", title="Original Role", start_date=date(2022, 1, 1)
        )
    )
    refined_role_llm = Role(
        basics=RoleBasics(
            company="Refined Co", title="Refined Role", start_date=date(2023, 1, 1)
        ),
        summary=RoleSummary(text="Refined Summary"),
    )
    # Use an out-of-bounds index (e.g., 1, when there is only one role)
    refined_roles_from_llm = {1: refined_role_llm.model_dump(mode="json")}

    original_experience = ExperienceResponse(roles=[original_role], projects=[])

    mock_extract_experience.return_value = original_experience
    mock_serialize_experience.return_value = "markdown content"
    mock_create_html.return_value = "final html"

    # Act
    result = process_refined_experience_result(
        resume_id=resume.id,
        resume_content_to_refine=resume.content,
        refined_roles=refined_roles_from_llm,
        job_description="A job",
        introduction="An intro",
    )

    # Assert
    assert result == "final html"

    mock_extract_experience.assert_called_once_with(resume.content)
    mock_serialize_experience.assert_called_once()
    experience_arg: ExperienceResponse = mock_serialize_experience.call_args[0][0]

    assert len(experience_arg.roles) == 1
    # The out-of-bounds index should be ignored, so the role is not updated.
    assert experience_arg.roles[0].basics.company == "Original Co"

    mock_create_html.assert_called_once_with(
        resume_id=resume.id,
        target_section_val=RefineTargetSection.EXPERIENCE.value,
        refined_content="markdown content",
        job_description="A job",
        introduction="An intro",
    )
