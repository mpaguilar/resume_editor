import textwrap
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from resume_editor.app.api.routes.route_logic.resume_serialization import (
    _serialize_role_to_markdown,
    serialize_experience_to_markdown,
)
from resume_editor.app.api.routes.route_models import ExperienceResponse
from resume_editor.app.models.resume.experience import (
    InclusionStatus,
    Project,
    ProjectDescription,
    ProjectOverview,
    Role,
    RoleBasics,
    RoleSummary,
)


@pytest.fixture
def sample_experience_data():
    """Provides sample experience data for testing."""
    return {
        "roles": [
            {
                "basics": {
                    "company": "Include Corp",
                    "title": "Full-Stack Dev",
                    "start_date": datetime(2020, 1, 1),
                    "inclusion_status": InclusionStatus.INCLUDE,
                },
                "summary": {"text": "A summary."},
            },
            {
                "basics": {
                    "company": "Not Relevant Inc",
                    "title": "Backend Dev",
                    "start_date": datetime(2018, 1, 1),
                    "inclusion_status": InclusionStatus.NOT_RELEVANT,
                },
                "summary": {"text": "Another summary."},
            },
            {
                "basics": {
                    "company": "Omit Ltd",
                    "title": "Frontend Dev",
                    "start_date": datetime(2016, 1, 1),
                    "inclusion_status": InclusionStatus.OMIT,
                },
            },
        ],
        "projects": [
            {
                "overview": {
                    "title": "Include Project",
                    "inclusion_status": InclusionStatus.INCLUDE,
                },
                "description": {"text": "Project description."},
            },
            {
                "overview": {
                    "title": "Not Relevant Project",
                    "inclusion_status": InclusionStatus.NOT_RELEVANT,
                },
                "description": {"text": "Another project description."},
            },
            {
                "overview": {
                    "title": "Omit Project",
                    "inclusion_status": InclusionStatus.OMIT,
                },
                "description": {"text": "This project is omitted."},
            },
        ],
    }


def test_serialize_experience_with_inclusion_controls(sample_experience_data):
    """Test that inclusion controls are correctly applied during serialization."""
    experience = ExperienceResponse(**sample_experience_data)
    markdown = serialize_experience_to_markdown(experience)

    # Omitted items should not be present
    assert "Omit Ltd" not in markdown
    assert "Omit Project" not in markdown

    # Not Relevant role items should have basics, summary, and placeholder responsibilities
    assert "Not Relevant Inc" in markdown
    assert "Backend Dev" in markdown
    assert "Another summary." in markdown
    assert "(no relevant experience)" in markdown
    # Not Relevant project items should have overview only
    assert "Not Relevant Project" in markdown
    assert "Another project description." not in markdown

    # Included items should be fully present
    assert "Include Corp" in markdown
    assert "Full-Stack Dev" in markdown
    assert "A summary." in markdown
    assert "Include Project" in markdown
    assert "Project description." in markdown

    # Check that Inclusion Status field is not persisted
    assert "Inclusion Status" not in markdown


def test_serialize_empty_experience():
    """Test serializing an empty experience section returns an empty string."""
    assert serialize_experience_to_markdown(None) == ""
    assert serialize_experience_to_markdown(ExperienceResponse()) == ""


@pytest.mark.parametrize(
    "experience_data",
    [
        # All items are omitted
        pytest.param(
            {
                "roles": [
                    {
                        "basics": {
                            "company": "Omit Ltd",
                            "title": "Dev",
                            "start_date": datetime(2022, 1, 1),
                            "inclusion_status": InclusionStatus.OMIT,
                        },
                    },
                ],
                "projects": [
                    {
                        "overview": {
                            "title": "Omit Proj",
                            "inclusion_status": InclusionStatus.OMIT,
                        },
                        "description": {"text": "desc"},
                    },
                ],
            },
            id="all_omitted",
        ),
        # Malformed items (missing basics/overview)
        pytest.param(
            {
                "roles": [{"summary": {"text": "No basics"}}],
                "projects": [{"description": {"text": "No overview"}}],
            },
            id="malformed_data",
        ),
    ],
)
def test_serialize_experience_is_empty_if_no_content(experience_data):
    """Test serializing experience returns empty string if all content is filtered."""
    experience = ExperienceResponse(**experience_data)
    markdown = serialize_experience_to_markdown(experience)
    assert markdown == ""


def test_serialize_experience_not_relevant_project_with_full_overview():
    """Test serializing a NOT_RELEVANT project with a complete overview."""
    experience = ExperienceResponse(
        roles=[],
        projects=[
            {
                "overview": {
                    "title": "Not Relevant Project Full",
                    "url": "http://example.com/not-relevant",
                    "url_description": "A link for not relevant project",
                    "start_date": "2022-02-01",
                    "end_date": "2022-03-01",
                    "inclusion_status": InclusionStatus.NOT_RELEVANT,
                },
                "description": {"text": "This description should be excluded."},
                "skills": {"skills": ["Skill E", "Skill F"]},
            },
        ],
    )
    markdown = serialize_experience_to_markdown(experience)

    assert "Title: Not Relevant Project Full" in markdown
    assert "Url: http://example.com/not-relevant" in markdown
    assert "Url Description: A link for not relevant project" in markdown
    assert "Start date: 02/2022" in markdown
    assert "End date: 03/2022" in markdown
    assert "This description should be excluded." not in markdown
    assert "Skill E" not in markdown
    assert "Skill F" not in markdown


def test_serialize_experience_not_relevant_role_with_full_basics():
    """Test serializing a NOT_RELEVANT role with complete basics."""
    experience = ExperienceResponse(
        roles=[
            {
                "basics": {
                    "company": "Not Relevant Company",
                    "title": "Not Relevant Title",
                    "start_date": "2021-01-01",
                    "end_date": "2021-12-31",
                    "location": "Not Relevant Location",
                    "agency_name": "Not Relevant Agency",
                    "job_category": "Not Relevant Category",
                    "employment_type": "Not Relevant Type",
                    "reason_for_change": "Not Relevant Reason",
                    "inclusion_status": InclusionStatus.NOT_RELEVANT,
                },
                "summary": {"text": "This summary should be included."},
                "responsibilities": {
                    "text": "These responsibilities should be ignored.",
                },
                "skills": {"skills": ["Skill G", "Skill H"]},
            },
        ],
        projects=[],
    )
    markdown = serialize_experience_to_markdown(experience)

    # Basics should always be present
    assert "Company: Not Relevant Company" in markdown
    assert "Title: Not Relevant Title" in markdown
    assert "Start date: 01/2021" in markdown
    assert "End date: 12/2021" in markdown
    assert "Location: Not Relevant Location" in markdown
    assert "Agency: Not Relevant Agency" in markdown
    assert "Job category: Not Relevant Category" in markdown
    assert "Employment type: Not Relevant Type" in markdown
    assert "Reason for change: Not Relevant Reason" in markdown

    # Summary and skills are now included
    assert "This summary should be included." in markdown
    assert "* Skill G" in markdown
    assert "* Skill H" in markdown

    # Responsibilities should be replaced with a placeholder
    assert "(no relevant experience)" in markdown
    assert "These responsibilities should be ignored." not in markdown


def test_serialize_experience_to_markdown_all_fields_from_main():
    """Test serializing experience with all possible fields to ensure coverage."""
    experience = ExperienceResponse(
        roles=[
            {
                "basics": {
                    "company": "Test Company",
                    "title": "Test Title",
                    "start_date": "2020-01-01",
                    "end_date": "2021-01-01",
                    "location": "Test Location",
                    "agency_name": "Test Agency",
                    "job_category": "Test Category",
                    "employment_type": "Test Type",
                    "reason_for_change": "Test Reason",
                    "inclusion_status": InclusionStatus.INCLUDE,
                },
                "summary": {"text": "Test Summary"},
                "responsibilities": {"text": "Test Responsibilities"},
                "skills": {"skills": ["Skill A", "Skill B"]},
            },
        ],
        projects=[
            {
                "overview": {
                    "title": "Test Project",
                    "url": "http://example.com",
                    "url_description": "Test URL Desc",
                    "start_date": "2022-01-01",
                    "end_date": "2023-01-01",
                    "inclusion_status": InclusionStatus.INCLUDE,
                },
                "description": {"text": "Test Description"},
                "skills": {"skills": ["Skill C", "Skill D"]},
            },
        ],
    )
    markdown = serialize_experience_to_markdown(experience)
    # Project assertions
    assert "#### Overview" in markdown
    assert "Title: Test Project" in markdown
    assert "Url: http://example.com" in markdown
    assert "Url Description: Test URL Desc" in markdown
    assert "Start date: 01/2022" in markdown
    assert "End date: 01/2023" in markdown
    assert "#### Description" in markdown
    assert "Test Description" in markdown
    assert "#### Skills" in markdown
    assert "* Skill C" in markdown

    # Role assertions
    assert "#### Basics" in markdown
    assert "Company: Test Company" in markdown
    assert "Title: Test Title" in markdown
    assert "Employment type: Test Type" in markdown
    assert "Job category: Test Category" in markdown
    assert "Agency: Test Agency" in markdown
    assert "Start date: 01/2020" in markdown
    assert "End date: 01/2021" in markdown
    assert "Reason for change: Test Reason" in markdown
    assert "Location: Test Location" in markdown
    assert "#### Summary" in markdown
    assert "Test Summary" in markdown
    assert "#### Responsibilities" in markdown
    assert "Test Responsibilities" in markdown
    assert "* Skill A" in markdown


def test_serialize_not_relevant_project_with_only_title():
    """Test serializing a NOT_RELEVANT project with only a title."""
    experience = ExperienceResponse(
        projects=[
            {
                "overview": {
                    "title": "A project",
                    "inclusion_status": InclusionStatus.NOT_RELEVANT,
                },
                "description": {"text": "A description to be ignored."},
            },
        ],
        roles=[],
    )
    markdown = serialize_experience_to_markdown(experience)
    expected_markdown = textwrap.dedent(
        """\
    # Experience

    ## Projects

    ### Project

    #### Overview

    Title: A project

    """,
    )
    assert markdown.strip() == expected_markdown.strip()


def test_serialize_not_relevant_role_with_only_basics():
    """Test serializing a NOT_RELEVANT role with basics and summary."""
    experience = ExperienceResponse(
        roles=[
            {
                "basics": {
                    "company": "A Company",
                    "title": "A Role",
                    "start_date": "2020-01-01",
                    "inclusion_status": InclusionStatus.NOT_RELEVANT,
                },
                "summary": {"text": "A summary to be included."},
            },
        ],
        projects=[],
    )
    markdown = serialize_experience_to_markdown(experience)
    expected_markdown = textwrap.dedent(
        """\
    # Experience

    ## Roles

    ### Role

    #### Basics

    Company: A Company
    Title: A Role
    Start date: 01/2020

    #### Summary

    A summary to be included.

    #### Responsibilities

    (no relevant experience)

    """,
    )
    assert markdown.strip() == expected_markdown.strip()


def test_serialize_experience_to_markdown_no_experience():
    """Test that an empty string is returned when no experience is provided."""
    # This covers the branch where experience has no roles and no projects
    experience_info = ExperienceResponse(roles=[], projects=[])
    result = serialize_experience_to_markdown(experience_info)
    assert result == ""


def test_serialize_experience_project_partial_overview_no_url():
    """Test serializing a project with overview having no URL."""
    mock_experience = Mock()
    mock_overview = Mock(
        title="Project One",
        url=None,
        url_description="Desc for URL-less project",
        start_date=datetime(2023, 1, 1),
        end_date=None,
    )
    mock_project = Mock()
    mock_project.overview = mock_overview
    mock_project.description = Mock(text="Project one description")
    mock_project.skills = None
    mock_experience.projects = [mock_project]
    mock_experience.roles = []
    markdown = serialize_experience_to_markdown(mock_experience)
    assert "Title: Project One" in markdown
    assert "Url: " not in markdown
    assert "Url Description: Desc for URL-less project" in markdown


def test_serialize_experience_project_partial_overview_no_title():
    """Test serializing a project with overview having no title."""
    mock_experience = Mock()
    mock_overview = Mock(
        title=None,
        url="http://no-title.com",
        url_description=None,
        start_date=None,
        end_date=None,
    )
    mock_project = Mock()
    mock_project.overview = mock_overview
    mock_project.description = None
    mock_project.skills = None
    mock_experience.projects = [mock_project]
    mock_experience.roles = []
    markdown = serialize_experience_to_markdown(mock_experience)
    assert "Title: " not in markdown
    assert "Url: http://no-title.com" in markdown
    assert "#### Description" not in markdown


def test_serialize_experience_role_partial_basics_no_title():
    """Test serializing a role with basics having no title."""
    mock_experience = Mock()
    mock_basics = Mock(
        company="Company One",
        title=None,
        start_date=datetime(2022, 1, 1),
        end_date=None,
        employment_type="Full-time",
        job_category=None,
        agency_name=None,
        reason_for_change=None,
        location=None,
    )
    mock_role = Mock()
    mock_role.basics = mock_basics
    mock_role.summary = None
    mock_role.responsibilities = None
    mock_role.skills = None
    mock_experience.roles = [mock_role]
    mock_experience.projects = []
    markdown = serialize_experience_to_markdown(mock_experience)
    assert "Company: Company One" in markdown
    assert "Title: " not in markdown


def test_serialize_experience_role_partial_basics_no_company():
    """Test serializing a role with basics having no company."""
    mock_experience = Mock()
    mock_basics = Mock(
        company=None,
        title="No Company",
        start_date=datetime(2020, 1, 1),
        end_date=None,
        employment_type=None,
        job_category=None,
        agency_name=None,
        reason_for_change=None,
        location=None,
    )
    mock_role = Mock()
    mock_role.basics = mock_basics
    mock_role.summary = None
    mock_role.responsibilities = None
    mock_role.skills = None
    mock_experience.roles = [mock_role]
    mock_experience.projects = []
    markdown = serialize_experience_to_markdown(mock_experience)
    assert "Company: " not in markdown
    assert "Title: No Company" in markdown


def test_serialize_experience_role_partial_basics_no_start_date():
    """Test serializing a role with basics having no start date."""
    mock_experience = Mock()
    mock_basics = Mock(
        company="Company Four",
        title="No Start Date",
        start_date=None,
        end_date=datetime(2019, 1, 1),
        employment_type=None,
        job_category=None,
        agency_name=None,
        reason_for_change=None,
        location=None,
    )
    mock_role = Mock()
    mock_role.basics = mock_basics
    mock_role.summary = None
    mock_role.responsibilities = None
    mock_role.skills = None
    mock_experience.roles = [mock_role]
    mock_experience.projects = []
    markdown = serialize_experience_to_markdown(mock_experience)
    assert "Start date: " not in markdown
    assert "End date: 01/2019" in markdown


def test_serialize_experience_to_markdown_partial_project_overview():
    """Test serializing a project with a partial overview to improve coverage."""
    experience = ExperienceResponse(
        roles=[],
        projects=[
            {
                "overview": {
                    "title": "Partial Project",
                    "url": "http://partial.com",
                    "start_date": "2023-01-01",
                },
                "description": {"text": "A partial description."},
            },
        ],
    )
    markdown = serialize_experience_to_markdown(experience)
    expected = textwrap.dedent(
        """\
    # Experience

    ## Projects

    ### Project

    #### Overview

    Title: Partial Project
    Url: http://partial.com
    Start date: 01/2023

    #### Description

    A partial description.

    """,
    )
    assert markdown == expected


def test_serialize_experience_role_no_basics():
    """Test serializing a role that has no basics section returns empty string."""
    experience = ExperienceResponse(
        roles=[
            {
                "basics": None,
                "summary": {"text": "A role with no basics"},
            },
        ],
        projects=[],
    )
    markdown = serialize_experience_to_markdown(experience)
    assert markdown == ""


def test_serialize_experience_project_no_overview():
    """Test serializing a project that has no overview section returns empty string."""
    experience = ExperienceResponse(
        projects=[
            {
                "overview": None,
                "description": {"text": "A project description without overview"},
            },
        ],
        roles=[],
    )

    markdown = serialize_experience_to_markdown(experience)
    assert markdown == ""


def test_serialize_project_with_empty_overview_and_content():
    """Test serializing a project with an empty overview but still has content."""
    mock_overview = Mock(
        spec=ProjectOverview,
        title=None,
        url=None,
        url_description=None,
        start_date=None,
        end_date=None,
        inclusion_status=InclusionStatus.INCLUDE,
    )
    mock_description = Mock(spec=ProjectDescription, text="A sample description.")
    mock_project = Mock(
        spec=Project,
        overview=mock_overview,
        description=mock_description,
        skills=None,
    )
    mock_experience = Mock(spec=ExperienceResponse, projects=[mock_project], roles=[])

    markdown = serialize_experience_to_markdown(mock_experience)

    expected_markdown = textwrap.dedent(
        """\
    # Experience

    ## Projects

    ### Project

    #### Description

    A sample description.

    """,
    )
    assert markdown.strip() == expected_markdown.strip()


def test_serialize_role_with_no_content():
    """Test serializing a role that has no content should result in an empty string."""
    mock_role = Mock(spec=Role)

    mock_basics = Mock(spec=RoleBasics)
    attrs = {
        "company": None,
        "title": None,
        "employment_type": None,
        "job_category": None,
        "agency_name": None,
        "start_date": None,
        "end_date": None,
        "reason_for_change": None,
        "location": None,
        "inclusion_status": InclusionStatus.INCLUDE,
    }
    mock_basics.configure_mock(**attrs)

    mock_role.basics = mock_basics
    mock_role.summary = None
    mock_role.responsibilities = None
    mock_role.skills = None

    experience = ExperienceResponse(roles=[mock_role], projects=[])
    markdown = serialize_experience_to_markdown(experience)
    assert markdown == ""


def test_serialize_role_empty_basics_with_summary():
    """Test serializing a role with empty basics but that has a summary."""
    mock_role = Mock(spec=Role)
    mock_basics = Mock(spec=RoleBasics)
    attrs = {
        "company": None,
        "title": None,
        "employment_type": None,
        "job_category": None,
        "agency_name": None,
        "start_date": None,
        "end_date": None,
        "reason_for_change": None,
        "location": None,
        "inclusion_status": InclusionStatus.INCLUDE,
    }
    mock_basics.configure_mock(**attrs)

    mock_summary = Mock(spec=RoleSummary, text="This is a summary text.")
    mock_role.basics = mock_basics
    mock_role.summary = mock_summary
    mock_role.responsibilities = None
    mock_role.skills = None

    mock_experience = Mock(spec=ExperienceResponse, roles=[mock_role], projects=[])
    markdown = serialize_experience_to_markdown(mock_experience)
    expected_markdown = textwrap.dedent(
        """\
        # Experience

        ## Roles

        ### Role

        #### Summary

        This is a summary text.

        """,
    )
    assert markdown.strip() == expected_markdown.strip()


def test_serialize_project_with_no_content():
    """Test serializing a project with no content results in an empty string."""
    mock_project = Mock(spec=Project)

    mock_overview = Mock(spec=ProjectOverview)
    attrs = {
        "title": None,
        "url": None,
        "url_description": None,
        "start_date": None,
        "end_date": None,
        "inclusion_status": InclusionStatus.INCLUDE,
    }
    mock_overview.configure_mock(**attrs)

    mock_project.overview = mock_overview
    mock_project.description = None
    mock_project.skills = None

    experience = ExperienceResponse(projects=[mock_project], roles=[])
    markdown = serialize_experience_to_markdown(experience)

    assert markdown == ""


def test_serialize_project_with_overview_and_skills_no_description():
    """Test serializing a project with overview and skills, but no description."""
    experience = ExperienceResponse(
        roles=[],
        projects=[
            {
                "overview": {
                    "title": "Skills Project",
                    "inclusion_status": InclusionStatus.INCLUDE,
                },
                "description": None,
                "skills": {"skills": ["API", "Testing"]},
            },
        ],
    )
    markdown = serialize_experience_to_markdown(experience)
    expected = textwrap.dedent(
        """\
        # Experience

        ## Projects

        ### Project

        #### Overview

        Title: Skills Project

        #### Skills

        * API
        * Testing

        """
    )
    assert "#### Description" not in markdown
    assert markdown.strip() == expected.strip()


def test_serialize_experience_to_markdown_partial_data():
    """Test serialization of partial experience information to Markdown."""
    experience = ExperienceResponse(
        roles=[
            {
                "basics": {
                    "company": "Partial Corp",
                    "title": "Partial Title",
                    "start_date": "2021-01-01",
                    "location": "Remote",
                },
            },
        ],
    )
    markdown = serialize_experience_to_markdown(experience)
    expected = """# Experience

## Roles

### Role

#### Basics

Company: Partial Corp
Title: Partial Title
Location: Remote
Start date: 01/2021

"""
    assert markdown == expected


def test_project_overview_missing_inclusion_status_defaults_to_include():
    """Test project with overview missing inclusion_status defaults to INCLUDE."""
    # This tests the defensive getattr() in _serialize_project_to_markdown
    mock_overview = SimpleNamespace(
        title="Default Include Project",
        url=None,
        url_description=None,
        start_date=None,
        end_date=None,
        # No inclusion_status
    )
    mock_project = Mock()
    mock_project.overview = mock_overview
    mock_project.description = Mock(text="Description is here")
    mock_project.skills = Mock(skills=["skill1"])

    mock_experience = Mock()
    mock_experience.projects = [mock_project]
    mock_experience.roles = []

    markdown = serialize_experience_to_markdown(mock_experience)

    assert "# Experience" in markdown
    assert "## Projects" in markdown
    assert "### Project" in markdown
    assert "#### Overview" in markdown
    assert "Title: Default Include Project" in markdown
    assert "#### Description" in markdown
    assert "Description is here" in markdown
    assert "#### Skills" in markdown
    assert "* skill1" in markdown


def test_serialize_project_with_empty_overview_and_default_include():
    """
    Test serializing a project with an empty overview and no inclusion status.

    It should default to INCLUDE and serialize the other content.
    """
    # Using SimpleNamespace to avoid having 'inclusion_status' attribute
    mock_overview = SimpleNamespace(
        title=None,
        url=None,
        url_description=None,
        start_date=None,
        end_date=None,
    )
    mock_description = Mock(spec=ProjectDescription, text="A sample description.")
    mock_project = Mock(
        spec=Project,
        overview=mock_overview,
        description=mock_description,
        skills=None,
    )
    mock_experience = Mock(spec=ExperienceResponse, projects=[mock_project], roles=[])

    markdown = serialize_experience_to_markdown(mock_experience)

    expected_markdown = textwrap.dedent(
        """\
    # Experience

    ## Projects

    ### Project

    #### Description

    A sample description.

    """
    )
    assert "Overview" not in markdown
    assert markdown.strip() == expected_markdown.strip()


@patch("resume_editor.app.api.routes.route_logic.resume_serialization._add_role_skills_markdown")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_serialization._add_role_responsibilities_markdown"
)
@patch("resume_editor.app.api.routes.route_logic.resume_serialization._add_role_summary_markdown")
@patch("resume_editor.app.api.routes.route_logic.resume_serialization._add_role_basics_markdown")
class TestSerializeRoleToMarkdown:
    def test_full_role_serialization(
        self,
        mock_add_basics,
        mock_add_summary,
        mock_add_responsibilities,
        mock_add_skills,
    ):
        """Test serializing a full role calls all helpers and handles content."""
        # Let one helper add content to test that the list is passed and used.
        mock_add_basics.side_effect = lambda basics, lines: lines.append(
            "basics content"
        )

        mock_role = Mock()
        mock_role.basics.inclusion_status = InclusionStatus.INCLUDE

        result = _serialize_role_to_markdown(mock_role)

        assert result == ["### Role", "", "basics content"]

        mock_add_basics.assert_called_once()
        assert mock_add_basics.call_args.args[0] is mock_role.basics

        mock_add_summary.assert_called_once()
        assert mock_add_summary.call_args.args[0] is mock_role.summary

        mock_add_responsibilities.assert_called_once()
        assert (
            mock_add_responsibilities.call_args.args[0] is mock_role.responsibilities
        )
        assert (
            mock_add_responsibilities.call_args.args[1] == InclusionStatus.INCLUDE
        )

        mock_add_skills.assert_called_once()
        assert mock_add_skills.call_args.args[0] is mock_role.skills

    def test_omit_inclusion_status(
        self,
        mock_add_basics,
        mock_add_summary,
        mock_add_responsibilities,
        mock_add_skills,
    ):
        """Test that a role with OMIT status is not serialized."""
        mock_role = Mock()
        mock_role.basics.inclusion_status = InclusionStatus.OMIT

        result = _serialize_role_to_markdown(mock_role)

        assert result == []
        mock_add_basics.assert_not_called()
        mock_add_summary.assert_not_called()
        mock_add_responsibilities.assert_not_called()
        mock_add_skills.assert_not_called()

    def test_no_basics(
        self,
        mock_add_basics,
        mock_add_summary,
        mock_add_responsibilities,
        mock_add_skills,
    ):
        """Test that a role without a 'basics' section is not serialized."""
        mock_role = Mock(spec=["summary", "responsibilities", "skills"])  # No 'basics'

        result = _serialize_role_to_markdown(mock_role)

        assert result == []
        mock_add_basics.assert_not_called()
        mock_add_summary.assert_not_called()
        mock_add_responsibilities.assert_not_called()
        mock_add_skills.assert_not_called()

    def test_no_content_generated(
        self,
        mock_add_basics,
        mock_add_summary,
        mock_add_responsibilities,
        mock_add_skills,
    ):
        """Test that if helpers generate no content, the result is empty."""
        # Mocks do nothing, so role_content stays empty
        mock_role = Mock()
        mock_role.basics.inclusion_status = InclusionStatus.INCLUDE

        result = _serialize_role_to_markdown(mock_role)

        assert result == []
        mock_add_basics.assert_called_once()
        mock_add_summary.assert_called_once()
        mock_add_responsibilities.assert_called_once()
        mock_add_skills.assert_called_once()

    def test_default_inclusion_status(
        self,
        mock_add_basics,
        mock_add_summary,
        mock_add_responsibilities,
        mock_add_skills,
    ):
        """Test inclusion_status defaults to INCLUDE if not present."""
        # Using SimpleNamespace to avoid having 'inclusion_status' attribute
        mock_basics = SimpleNamespace(company="Test Co")
        mock_role = Mock()
        mock_role.basics = mock_basics

        result = _serialize_role_to_markdown(mock_role)

        assert result == []
        mock_add_basics.assert_called_once()

        # Verify that inclusion_status was defaulted to INCLUDE for responsibilities call
        mock_add_responsibilities.assert_called_once()
        assert mock_add_responsibilities.call_args.args[1] == InclusionStatus.INCLUDE

