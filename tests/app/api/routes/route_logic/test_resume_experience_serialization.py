import textwrap
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from resume_editor.app.api.routes.route_logic.resume_serialization import (
    extract_experience_info,
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


def test_extract_experience_info_from_markdown():
    """Test that experience data can be correctly extracted from Markdown."""
    markdown_content = """
# Experience

## Roles
### Role
#### Basics

Company: Test Corp
Title: Developer
Start date: 01/2020

#### Summary

This is a summary.

### Role
#### Basics

Company: Omitter Inc
Title: PM
Start date: 01/2019

## Projects
### Project
#### Overview

Title: A Project
#### Description

A description of the project.
"""
    experience = extract_experience_info(markdown_content)

    # Roles validation
    assert len(experience.roles) == 2
    # Included role
    assert experience.roles[0].basics.company == "Test Corp"
    assert experience.roles[0].basics.inclusion_status == InclusionStatus.INCLUDE
    assert experience.roles[0].summary is not None
    assert experience.roles[0].summary.text == "This is a summary."
    # Since inclusion status is not parsed, it should default to INCLUDE
    assert experience.roles[1].basics.company == "Omitter Inc"
    assert experience.roles[1].basics.inclusion_status == InclusionStatus.INCLUDE
    assert experience.roles[1].summary is None

    # Projects validation
    assert len(experience.projects) == 1
    assert experience.projects[0].overview.title == "A Project"
    # Since inclusion status is not parsed, it should default to INCLUDE
    assert experience.projects[0].overview.inclusion_status == InclusionStatus.INCLUDE
    assert experience.projects[0].description.text == "A description of the project."


def test_serialize_empty_experience():
    """Test serializing an empty experience section returns an empty string."""
    assert serialize_experience_to_markdown(None) == ""
    assert serialize_experience_to_markdown(ExperienceResponse()) == ""


def test_extract_experience_info_with_no_experience_section():
    """Test extracting experience from markdown with no experience section."""
    markdown_content = """
# Personal
## Contact Information
Name: John Doe
"""
    experience = extract_experience_info(markdown_content)
    assert experience.roles == []
    assert experience.projects == []


def test_extract_experience_info_with_invalid_markdown():
    """Test extracting experience from malformed markdown raises ValueError."""
    markdown_content = """
# Experience
### Role
Company: Test Corp
"""  # Invalid structure
    with pytest.raises(
        ValueError, match="Failed to parse experience info from resume content."
    ):
        extract_experience_info(markdown_content)


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


def test_extract_experience_info_with_all_fields():
    """Test extracting experience info with all fields populated."""
    resume_content = textwrap.dedent(
        """\
    # Experience

    ## Roles

    ### Role

    #### Basics

    Company: A Company
    Title: A Role
    Start date: 01/2020
    End date: 12/2020
    Location: A Location
    Agency: An Agency
    Job category: A Category
    Employment type: A Type
    Reason for change: A Reason

    #### Summary

    A summary.

    #### Responsibilities

    Some responsibilities.

    #### Skills

    * Skill 1
    * Skill 2

    ## Projects

    ### Project

    #### Overview

    Title: A Project
    Url: http://example.com
    Url Description: A link
    Start date: 02/2021
    End date: 03/2021

    #### Description

    A description.

    #### Skills

    * Skill 3
    * Skill 4
    """,
    )
    result = extract_experience_info(resume_content)

    # Validate roles
    assert len(result.roles) == 1
    role = result.roles[0]
    assert role.basics.company == "A Company"
    assert role.basics.title == "A Role"
    assert role.basics.start_date.year == 2020
    assert role.basics.location == "A Location"
    assert role.basics.agency_name == "An Agency"
    assert role.basics.job_category == "A Category"
    assert role.basics.employment_type == "A Type"
    assert role.basics.reason_for_change == "A Reason"
    assert role.summary.text == "A summary."
    assert role.responsibilities.text == "Some responsibilities."
    assert "Skill 1" in role.skills.skills
    assert "Skill 2" in role.skills.skills

    # Validate projects
    assert len(result.projects) == 1
    project = result.projects[0]
    assert project.overview.title == "A Project"
    assert project.overview.url == "http://example.com"
    assert project.overview.url_description == "A link"
    assert project.overview.start_date.year == 2021
    assert project.description.text == "A description."
    assert "Skill 3" in project.skills.skills
    assert "Skill 4" in project.skills.skills


def test_serialize_experience_to_markdown_no_experience():
    """Test that an empty string is returned when no experience is provided."""
    # This covers the branch where experience has no roles and no projects
    experience_info = ExperienceResponse(roles=[], projects=[])
    result = serialize_experience_to_markdown(experience_info)
    assert result == ""


def test_extract_experience_info_various_configurations():
    """Test extracting experience info with various role and project configurations."""
    resume_content = textwrap.dedent(
        """\
    # Experience

    ## Roles

    ### Role

    #### Basics

    Company: Basics Only Corp
    Title: Tester
    Start date: 01/2022

    ### Role

    #### Summary

    This role only has a summary.

    ### Role

    #### Responsibilities

    This role only has responsibilities.

    ### Role

    #### Skills
    * Skill A
    * Skill B

    ### Role


    ## Projects

    ### Project

    #### Overview

    Title: A Project without skills
    
    #### Description

    A description.

    """,
    )
    result = extract_experience_info(resume_content)

    # Role assertions
    assert len(result.roles) == 4

    # Role 1: Basics only
    assert result.roles[0].basics is not None
    assert result.roles[0].basics.company == "Basics Only Corp"
    assert result.roles[0].summary is None
    assert result.roles[0].responsibilities is None
    assert result.roles[0].skills is None

    # Role 2: Summary only
    assert result.roles[1].basics is None
    assert result.roles[1].summary is not None
    assert result.roles[1].summary.text == "This role only has a summary."
    assert result.roles[1].responsibilities is None
    assert result.roles[1].skills is None

    # Role 3: Responsibilities only
    assert result.roles[2].basics is None
    assert result.roles[2].summary is None
    assert result.roles[2].responsibilities is not None
    assert (
        result.roles[2].responsibilities.text == "This role only has responsibilities."
    )
    assert result.roles[2].skills is None

    # Role 4: Skills only
    assert result.roles[3].basics is None
    assert result.roles[3].summary is None
    assert result.roles[3].responsibilities is None
    assert result.roles[3].skills is not None
    assert result.roles[3].skills.skills == ["Skill A", "Skill B"]

    # The fifth role is empty and should be skipped.

    # Project assertions
    assert len(result.projects) == 1
    project = result.projects[0]
    assert project.overview.title == "A Project without skills"
    assert project.description.text == "A description."
    assert project.skills is None


def test_extract_experience_info_role_with_basics_and_skills_only():
    """Test extracting experience info for a role with basics and skills only."""
    resume_content = textwrap.dedent(
        """\
    # Experience

    ## Roles

    ### Role
    #### Basics
    Company: Skills Corp
    Title: Skill Master
    Start date: 02/2021

    #### Skills
    * Team Leadership
    * Project Management
    """,
    )
    result = extract_experience_info(resume_content)

    assert len(result.roles) == 1
    role = result.roles[0]

    assert role.basics is not None
    assert role.basics.company == "Skills Corp"
    assert role.summary is None
    assert role.responsibilities is None
    assert role.skills is not None
    assert "Team Leadership" in role.skills.skills
    assert "Project Management" in role.skills.skills


def test_extract_experience_info_with_empty_roles_list():
    """Test extracting experience info when the roles list is empty."""
    resume_content = textwrap.dedent(
        """\
    # Experience
    ## Roles

    """,
    )
    result = extract_experience_info(resume_content)
    assert result.roles == []
    assert result.projects == []


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


class TestExtractExperienceInfo:
    """Test cases for experience info extraction functions."""

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_serialization.WriterResume.parse",
    )
    def test_extract_experience_info_no_experience_or_roles(self, mock_parse):
        """Test experience info extraction when experience or roles are missing."""
        mock_resume = Mock()
        mock_resume.experience = None
        mock_parse.return_value = mock_resume

        response = extract_experience_info("any content")
        assert response.roles == []
        assert response.projects == []

        mock_experience = Mock()
        mock_experience.roles = None
        # Explicitly set projects to None to simulate an experience section with no projects
        mock_experience.projects = None
        mock_resume.experience = mock_experience
        response = extract_experience_info("any content")
        assert response.roles == []
        assert response.projects == []

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_serialization.WriterResume.parse",
    )
    def test_extract_experience_info_no_role_basics(self, mock_parse):
        """Test experience info extraction when a role has no basics."""
        mock_role = Mock()
        mock_role.basics = None
        # Ensure other attributes are also None to test empty role_dict
        mock_role.summary = None
        mock_role.responsibilities = None
        mock_role.skills = None

        mock_project = Mock()
        mock_project.overview = None
        # Ensure other attributes are also None to test empty project_dict
        mock_project.description = None
        mock_project.skills = None

        mock_experience = Mock()
        mock_experience.roles = [mock_role]
        mock_experience.projects = [mock_project]

        mock_resume = Mock()
        mock_resume.experience = mock_experience
        mock_parse.return_value = mock_resume

        response = extract_experience_info("any content")
        assert response.roles == []
        assert response.projects == []

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_serialization.WriterResume.parse",
    )
    def test_extract_experience_info_partial_data(self, mock_parse):
        """Test experience info extraction with partial data in a role."""
        mock_role_basics = Mock()
        mock_role_basics.company = "Test Co"
        mock_role_basics.title = "Engineer"
        mock_role_basics.start_date = datetime(2021, 1, 1)
        mock_role_basics.end_date = datetime(2022, 1, 1)
        mock_role_basics.location = None
        mock_role_basics.agency_name = None
        mock_role_basics.job_category = None
        mock_role_basics.employment_type = None
        mock_role_basics.reason_for_change = None

        mock_role = Mock()
        mock_role.basics = mock_role_basics
        mock_role.summary = None
        mock_role.responsibilities = None
        mock_role.skills = None

        mock_experience = Mock()
        mock_experience.roles = [mock_role]
        mock_experience.projects = []

        mock_resume = Mock()
        mock_resume.experience = mock_experience
        mock_parse.return_value = mock_resume

        response = extract_experience_info("any content")
        assert len(response.roles) == 1
        # The response model will contain a list of model objects, not dicts
        role = response.roles[0]
        assert role.basics.company == "Test Co"
        assert role.basics.title == "Engineer"
        assert role.basics.start_date == datetime(2021, 1, 1)
        assert role.basics.end_date == datetime(2022, 1, 1)
        assert role.basics.location is None
        assert role.summary is None

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_serialization.WriterResume.parse",
        side_effect=Exception("mock parse error"),
    )
    def test_extract_experience_info_parse_fails(self, mock_parse):
        """Test experience info extraction when parsing fails."""
        with pytest.raises(ValueError, match="Failed to parse experience info"):
            extract_experience_info("invalid content")


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
Start date: 01/2021
Location: Remote

"""
    assert markdown == expected
