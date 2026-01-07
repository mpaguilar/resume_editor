from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from resume_editor.app.api.routes.html_fragments import RefineResultParams
from resume_editor.app.api.routes.route_logic.resume_ai_logic import (
    ProcessExperienceResultParams,
    _extract_raw_section,
    _replace_resume_banner,
    _update_banner_in_raw_personal,
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


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.serialize_experience_to_markdown")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic._update_banner_in_raw_personal")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic._extract_raw_section")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic._create_refine_result_html")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_experience_info")
def test_process_refined_experience_result(
    mock_extract_experience: MagicMock,
    mock_create_html: MagicMock,
    mock_extract_raw: MagicMock,
    mock_update_banner: MagicMock,
    mock_serialize_experience: MagicMock,
    mock_resume: DatabaseResume,
) -> None:
    """
    Test that process_refined_experience_result correctly reconstructs a full
    resume with refined roles and original projects, using raw sections for
    Personal, Education, and Certifications.
    """
    # Arrange
    original_content = """# Personal
Name: Test User

# Education
School: Test University

# Certifications
Name: Azure (AI-102)
Issuer: Microsoft

# Experience
Company: Old Co
"""
    content_to_refine = "filtered resume content"

    # Mock raw extraction to simulate extracting sections with specific content
    def extract_raw_side_effect(content, section):
        if section == "certifications":
            return "# Certifications\nName: Azure (AI-102)\nIssuer: Microsoft\n"
        if section == "education":
            return "# Education\nSchool: Test University\n"
        if section == "personal":
            return "# Personal\nName: Test User\n"
        return ""
    mock_extract_raw.side_effect = extract_raw_side_effect

    # Mock banner update
    mock_update_banner.return_value = "# Personal\n## Banner\nintro\nName: Test User\n"

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

    mock_serialize_experience.return_value = "serialized experience"
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

    assert mock_extract_experience.call_count == 2
    mock_extract_experience.assert_any_call(original_content)
    mock_extract_experience.assert_any_call(content_to_refine)
    
    # Check raw extraction
    assert mock_extract_raw.call_count == 3
    mock_extract_raw.assert_any_call(original_content, "personal")
    mock_extract_raw.assert_any_call(original_content, "education")
    mock_extract_raw.assert_any_call(original_content, "certifications")

    # Check banner update
    mock_update_banner.assert_called_once_with("# Personal\nName: Test User\n", "intro")

    # Check experience object passed to serializer
    mock_serialize_experience.assert_called_once()
    experience_arg = mock_serialize_experience.call_args.args[0]
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
    # The content should be the concatenation of sections
    # The code appends a newline to raw sections and joins with a newline, resulting in double newlines
    expected_content = "# Personal\n## Banner\nintro\nName: Test User\n\n# Education\nSchool: Test University\n\n# Certifications\nName: Azure (AI-102)\nIssuer: Microsoft\n\nserialized experience"
    assert html_params.refined_content == expected_content
    # Verify the ID is preserved in the final content
    assert "Name: Azure (AI-102)" in html_params.refined_content
    assert html_params.introduction == "intro"
    assert html_params.limit_refinement_years == 5
    assert html_params.resume_id == mock_resume.id


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.serialize_experience_to_markdown")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic._update_banner_in_raw_personal")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic._extract_raw_section")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic._create_refine_result_html")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_experience_info")
def test_process_refined_experience_result_out_of_bounds_index(
    mock_extract_experience: MagicMock,
    mock_create_html: MagicMock,
    mock_extract_raw: MagicMock,
    mock_update_banner: MagicMock,
    mock_serialize_experience: MagicMock,
    mock_resume: DatabaseResume,
) -> None:
    """Test process_refined_experience_result ignores out-of-bounds indices."""
    # Arrange
    original_content = "original resume content"
    content_to_refine = "filtered resume content"

    # Mock raw extraction
    mock_extract_raw.return_value = ""
    mock_update_banner.return_value = ""

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
    
    mock_serialize_experience.return_value = "serialized experience"
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
    
    # Check experience object passed to serializer
    mock_serialize_experience.assert_called_once()
    experience_arg = mock_serialize_experience.call_args.args[0]

    # The out-of-bounds index should be ignored, so the role is not updated.
    assert len(experience_arg.roles) == 1
    assert experience_arg.roles[0].basics.company == "Original Co"

    # Check call to HTML generator
    mock_create_html.assert_called_once()
    html_params = mock_create_html.call_args.kwargs["params"]
    assert isinstance(html_params, RefineResultParams)
    assert html_params.introduction == "An intro"
    assert html_params.resume_id == mock_resume.id


def test_extract_raw_section_preserves_formatting():
    """
    Input: A resume string with specific formatting in Certifications (e.g., IDs in parentheses).
    Action: Call `_extract_raw_section` for "certifications".
    Assertion: The returned string matches the input section exactly, including IDs.
    """
    resume_content = """# Personal
Name: Test User

# Certifications
## AWS Certified Solutions Architect
Issuer: AWS
(ID: 12345-ABC)
Issued: 2023-01-01

# Experience
## Developer
"""
    expected_certifications = """# Certifications
## AWS Certified Solutions Architect
Issuer: AWS
(ID: 12345-ABC)
Issued: 2023-01-01
"""
    
    extracted = _extract_raw_section(resume_content, "certifications")
    
    # Verify content matches
    assert extracted.strip() == expected_certifications.strip()
    # Verify specific formatting is preserved
    assert "(ID: 12345-ABC)" in extracted


def test_update_banner_in_raw_personal_replaces_existing():
    """
    Input: Raw personal section with an existing banner.
    Action: Call `_update_banner_in_raw_personal` with new text.
    Assertion: The banner text is updated, but other fields (Name, Email) remain untouched.
    """
    raw_personal = """# Personal
Name: John Doe
Email: john@example.com

## Banner
Old banner text.
It has multiple lines.

## Websites
GitHub: https://github.com/johndoe
"""
    new_intro = "New banner text."
    
    updated = _update_banner_in_raw_personal(raw_personal, new_intro)
    
    assert "Name: John Doe" in updated
    assert "Email: john@example.com" in updated
    assert "GitHub: https://github.com/johndoe" in updated
    assert "Old banner text." not in updated
    assert "New banner text." in updated
    assert "## Banner" in updated


def test_update_banner_in_raw_personal_appends_new():
    """
    Input: Raw personal section without a banner.
    Action: Call `_update_banner_in_raw_personal`.
    Assertion: The banner is appended correctly.
    """
    raw_personal = """# Personal
Name: Jane Doe
"""
    new_intro = "This is a new banner."
    
    updated = _update_banner_in_raw_personal(raw_personal, new_intro)
    
    assert "Name: Jane Doe" in updated
    assert "## Banner" in updated
    assert "This is a new banner." in updated
    # Ensure it's at the end
    assert updated.strip().endswith("This is a new banner.")


def test_update_banner_in_raw_personal_no_change_if_none():
    """Test that no changes are made if introduction is None or empty."""
    raw_personal = "# Personal\nName: Test"
    assert _update_banner_in_raw_personal(raw_personal, None) == raw_personal
    assert _update_banner_in_raw_personal(raw_personal, "") == raw_personal
    assert _update_banner_in_raw_personal(raw_personal, "   ") == raw_personal


def test_extract_raw_section_not_found():
    """Test extracting a section that does not exist."""
    content = "# Personal\nName: Me"
    assert _extract_raw_section(content, "Education") == ""


def test_extract_raw_section_at_end_no_trailing_newline():
    """Test extracting a section at the end of the file without trailing newline."""
    content = "# Personal\nName: Me\n# Education\nSchool: My School"
    expected = "# Education\nSchool: My School\n"
    assert _extract_raw_section(content, "Education") == expected


def test_extract_raw_section_with_trailing_blank_line():
    """Test extracting a section that ends with a blank line."""
    content = "# Personal\nName: Me\n\n# Next"
    expected = "# Personal\nName: Me\n"
    assert _extract_raw_section(content, "Personal") == expected


def test_update_banner_in_raw_personal_banner_at_end():
    """Test replacing banner when it is the last subsection."""
    raw_personal = "# Personal\nName: Me\n\n## Banner\nOld Text"
    new_intro = "New Text"
    result = _update_banner_in_raw_personal(raw_personal, new_intro)

    assert "New Text" in result
    assert "Old Text" not in result
    assert result.endswith("\n")
    # Ensure structure is correct
    assert "## Banner\n\nNew Text\n" in result


def test_update_banner_in_raw_personal_append_with_trailing_newline():
    """Test appending banner when the section ends with a blank line."""
    # "A\n\n".splitlines() -> ["A", ""]
    raw_personal = "# Personal\nName: Me\n\n"
    new_intro = "Intro"
    result = _update_banner_in_raw_personal(raw_personal, new_intro)

    # Should not add an extra blank line before ## Banner because one exists
    # Expected: "# Personal\nName: Me\n\n## Banner\n\nIntro\n"
    assert result == "# Personal\nName: Me\n\n## Banner\n\nIntro\n"


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.serialize_experience_to_markdown")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic._update_banner_in_raw_personal")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic._extract_raw_section")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic._create_refine_result_html")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_experience_info")
def test_process_refined_experience_result_no_introduction(
    mock_extract_experience: MagicMock,
    mock_create_html: MagicMock,
    mock_extract_raw: MagicMock,
    mock_update_banner: MagicMock,
    mock_serialize_experience: MagicMock,
    mock_resume: DatabaseResume,
) -> None:
    """Test process_refined_experience_result when introduction is None."""
    # Arrange
    original_content = "original resume content"
    content_to_refine = "filtered resume content"

    mock_extract_raw.return_value = "raw section"
    mock_update_banner.return_value = "raw personal"

    mock_extract_experience.return_value = ExperienceResponse(roles=[], projects=[])

    mock_serialize_experience.return_value = "serialized experience"
    mock_create_html.return_value = "final html"

    # Act
    params = ProcessExperienceResultParams(
        resume_id=mock_resume.id,
        original_resume_content=original_content,
        resume_content_to_refine=content_to_refine,
        refined_roles={},
        job_description="job desc",
        introduction=None,  # No introduction
        limit_refinement_years=None,
    )
    result = process_refined_experience_result(params)

    # Assert
    assert result == "final html"
    
    # Banner update should be called with None
    mock_update_banner.assert_called_once_with("raw section", None)
