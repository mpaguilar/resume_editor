import textwrap
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from resume_editor.app.api.routes.route_logic.resume_serialization import (
    extract_experience_info,
)
from resume_editor.app.models.resume.experience import InclusionStatus


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


@patch("resume_editor.app.api.routes.route_logic.resume_serialization.WriterResume")
def test_extract_experience_info_with_summary(mock_writer_resume):
    """Test that experience info with a summary is extracted correctly."""
    # Arrange
    mock_role = MagicMock()
    # The writer object has attributes that are themselves MagicMocks.
    mock_role.basics.company = "Test Co"
    mock_role.basics.title = "Tester"
    mock_role.basics.start_date = datetime(2022, 1, 1)
    mock_role.basics.end_date = None
    mock_role.basics.location = None
    mock_role.basics.agency_name = None
    mock_role.basics.job_category = None
    mock_role.basics.employment_type = None
    mock_role.basics.reason_for_change = None

    # This is the key: The parser from resume_writer returns an object
    # that has a 'summary' attribute.
    mock_summary = MagicMock()
    mock_summary.summary = "This is a test summary."
    mock_role.summary = mock_summary

    mock_role.responsibilities = None
    mock_role.skills = None

    mock_experience = MagicMock()
    mock_experience.roles = [mock_role]
    mock_experience.projects = []

    mock_parsed_resume = MagicMock()
    mock_parsed_resume.experience = mock_experience

    mock_writer_resume.parse.return_value = mock_parsed_resume

    resume_content = "# Experience"

    # Act
    experience_response = extract_experience_info(resume_content)

    # Assert
    assert len(experience_response.roles) == 1
    role = experience_response.roles[0]
    assert role.summary is not None
    assert role.summary.text == "This is a test summary."


def test_extract_experience_info_with_unparseable_content():
    """Test that extract_experience_info raises an error for unparseable content."""
    unparseable_content = textwrap.dedent(
        """\
        # Experience
        This is some random text that does not follow the format.
        """
    )
    with pytest.raises(
        ValueError, match="Failed to parse experience info from resume content."
    ):
        extract_experience_info(unparseable_content)


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
