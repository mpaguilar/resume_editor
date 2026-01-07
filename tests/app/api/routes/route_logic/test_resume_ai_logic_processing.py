from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from resume_editor.app.api.routes.html_fragments import RefineResultParams
from resume_editor.app.api.routes.route_logic.resume_ai_logic import (
    ProcessExperienceResultParams,
    _replace_resume_banner,
    process_refined_experience_result,
)
from resume_editor.app.api.routes.route_models import (
    ExperienceResponse,
    PersonalInfoResponse,
)
from resume_editor.app.models.resume.experience import (
    Project,
    ProjectOverview,
    Role,
    RoleBasics,
    RoleSummary,
)
from resume_editor.app.models.resume.personal import Banner
from resume_editor.app.models.resume_model import Resume as DatabaseResume


@pytest.fixture
def mock_resume() -> DatabaseResume:
    """Provides a mock resume with a dummy ID."""
    resume = MagicMock(spec=DatabaseResume)
    resume.id = 1
    return resume


@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic._replace_resume_banner"
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
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_education_info"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_experience_info"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_personal_info"
)
def test_process_refined_experience_result(
    mock_extract_personal: MagicMock,
    mock_extract_experience: MagicMock,
    mock_extract_education: MagicMock,
    mock_extract_certifications: MagicMock,
    mock_build_resume: MagicMock,
    mock_create_html: MagicMock,
    mock_replace_banner: MagicMock,
    mock_resume: DatabaseResume,
) -> None:
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

    reconstructed_resume = "fully reconstructed resume"
    resume_with_banner = "resume with banner added"
    mock_build_resume.return_value = reconstructed_resume
    mock_replace_banner.return_value = resume_with_banner
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

    # Check that build_complete_resume_from_sections was called with correct data
    mock_build_resume.assert_called_once()
    build_args = mock_build_resume.call_args.kwargs
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

    # Check that banner replacement was called
    mock_replace_banner.assert_called_once_with(
        resume_content=reconstructed_resume, introduction="intro"
    )

    # Check that the final HTML generator was called correctly
    mock_create_html.assert_called_once()
    html_params = mock_create_html.call_args.kwargs["params"]
    assert isinstance(html_params, RefineResultParams)
    assert html_params.refined_content == resume_with_banner
    assert html_params.introduction == "intro"
    assert html_params.limit_refinement_years == 5
    assert html_params.resume_id == mock_resume.id


@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic._replace_resume_banner"
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
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_education_info"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_experience_info"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_personal_info"
)
def test_process_refined_experience_result_out_of_bounds_index(
    mock_extract_personal: MagicMock,
    mock_extract_experience: MagicMock,
    mock_extract_education: MagicMock,
    mock_extract_certifications: MagicMock,
    mock_build_resume: MagicMock,
    mock_create_html: MagicMock,
    mock_replace_banner: MagicMock,
    mock_resume: DatabaseResume,
) -> None:
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
    mock_build_resume.return_value = "reconstructed content"
    mock_replace_banner.return_value = "reconstructed content with banner"
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
    mock_build_resume.assert_called_once()
    build_args = mock_build_resume.call_args.kwargs
    experience_arg = build_args["experience"]

    # The out-of-bounds index should be ignored, so the role is not updated.
    assert len(experience_arg.roles) == 1
    assert experience_arg.roles[0].basics.company == "Original Co"

    # Check banner was replaced
    mock_replace_banner.assert_called_once_with(
        resume_content="reconstructed content", introduction="An intro"
    )

    # Check call to HTML generator
    mock_create_html.assert_called_once()
    html_params = mock_create_html.call_args.kwargs["params"]
    assert isinstance(html_params, RefineResultParams)
    assert html_params.refined_content == "reconstructed content with banner"
    assert html_params.introduction == "An intro"
    assert html_params.resume_id == mock_resume.id


@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.build_complete_resume_from_sections"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_certifications_info")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_experience_info")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_education_info")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_personal_info")
def test_replace_resume_banner_none_introduction(
    mock_extract_personal: MagicMock,
    mock_extract_education: MagicMock,
    mock_extract_experience: MagicMock,
    mock_extract_certifications: MagicMock,
    mock_build_resume: MagicMock,
) -> None:
    """Test _replace_resume_banner returns original content when introduction is None."""
    original_content = "# Personal\n## Banner\nOld banner\n# Experience\nSome content"
    
    result = _replace_resume_banner(original_content, None)
    
    assert result == original_content
    # No parsing should occur when introduction is None
    mock_extract_personal.assert_not_called()
    mock_extract_education.assert_not_called()
    mock_extract_experience.assert_not_called()
    mock_extract_certifications.assert_not_called()
    mock_build_resume.assert_not_called()


@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.build_complete_resume_from_sections"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_certifications_info")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_experience_info")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_education_info")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_personal_info")
def test_replace_resume_banner_whitespace_introduction(
    mock_extract_personal: MagicMock,
    mock_extract_education: MagicMock,
    mock_extract_experience: MagicMock,
    mock_extract_certifications: MagicMock,
    mock_build_resume: MagicMock,
) -> None:
    """Test _replace_resume_banner returns original content when introduction is whitespace."""
    original_content = "# Personal\n## Banner\nOld banner\n# Experience\nSome content"
    
    result = _replace_resume_banner(original_content, "   \n\t  ")
    
    assert result == original_content
    # No parsing should occur when introduction is whitespace
    mock_extract_personal.assert_not_called()
    mock_extract_education.assert_not_called()
    mock_extract_experience.assert_not_called()
    mock_extract_certifications.assert_not_called()
    mock_build_resume.assert_not_called()


@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.build_complete_resume_from_sections"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_certifications_info")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_experience_info")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_education_info")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_personal_info")
def test_replace_resume_banner_success(
    mock_extract_personal: MagicMock,
    mock_extract_education: MagicMock,
    mock_extract_experience: MagicMock,
    mock_extract_certifications: MagicMock,
    mock_build_resume: MagicMock,
) -> None:
    """Test _replace_resume_banner successfully replaces banner when introduction is provided."""
    original_content = "# Personal\nName: John Doe\n# Experience\nSome content"
    new_introduction = "This is a new introduction"
    
    # Set up mocks
    mock_personal = PersonalInfoResponse(name="John Doe")
    mock_extract_personal.return_value = mock_personal
    mock_extract_education.return_value = MagicMock()
    mock_extract_experience.return_value = MagicMock()
    mock_extract_certifications.return_value = MagicMock()
    mock_build_resume.return_value = "# Personal\n## Banner\nThis is a new introduction\nName: John Doe\n# Experience\nSome content"

    result = _replace_resume_banner(original_content, new_introduction)
    
    # Verify parsing functions were called
    mock_extract_personal.assert_called_once_with(original_content)
    mock_extract_education.assert_called_once_with(original_content)
    mock_extract_experience.assert_called_once_with(original_content)
    mock_extract_certifications.assert_called_once_with(original_content)
    
    # Verify personal info banner was updated
    assert mock_personal.banner == Banner(text=new_introduction)
    
    # Verify reconstruction was called with updated personal info
    mock_build_resume.assert_called_once_with(
        personal_info=mock_personal,
        education=mock_extract_education.return_value,
        experience=mock_extract_experience.return_value,
        certifications=mock_extract_certifications.return_value,
    )

    # Verify result
    assert result == mock_build_resume.return_value


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_personal_info")
def test_replace_resume_banner_malformed_content(mock_extract_personal: MagicMock) -> None:
    """Test _replace_resume_banner handles malformed resume content."""
    original_content = "This is not valid resume content"
    new_introduction = "This is a new introduction"
    
    # Make the extraction fail
    mock_extract_personal.side_effect = ValueError("Invalid resume format")
    
    # Should raise an exception due to malformed content
    with pytest.raises(ValueError):
        _replace_resume_banner(original_content, new_introduction)


