import textwrap
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from resume_editor.app.api.routes.route_logic.resume_reconstruction import (
    reconstruct_resume_markdown,
)
from resume_editor.app.api.routes.route_logic.resume_serialization import (
    _serialize_role_to_markdown,
    extract_experience_info,
    serialize_experience_to_markdown,
    update_resume_content_with_structured_data,
)
from resume_editor.app.api.routes.route_models import (
    CertificationsResponse,
    EducationResponse,
    ExperienceResponse,
    PersonalInfoResponse,
)
from resume_editor.app.models.resume.experience import InclusionStatus


def test_update_resume_content_with_structured_data():
    """Test updating resume content with structured data."""
    current_content = textwrap.dedent(
        """\
        # Personal

        ## Contact Information
        Name: John Doe
        Email: john@example.com

        # Education

        ## Degrees

        ### Degree
        School: University of Example
        Degree: Bachelor of Science

        # Experience

        ## Roles

        ### Role

        #### Basics
        Company: Old Corp
        Title: Junior Developer
        Start date: 01/2020
    """,
    )

    personal_info = PersonalInfoResponse(
        name="Jane Smith",
        email="jane@example.com",
        phone="987-654-3210",
    )

    updated_content = update_resume_content_with_structured_data(
        current_content,
        personal_info=personal_info,
    )

    assert "Jane Smith" in updated_content
    assert "jane@example.com" in updated_content
    assert "987-654-3210" in updated_content
    assert "University of Example" in updated_content  # Should preserve other sections


def test_update_resume_content_with_structured_data_no_personal_info():
    """Test update_resume_content_with_structured_data preserves existing personal info."""
    current_content = """# Personal

## Contact Information

Name: John Doe
"""
    education_info = EducationResponse(degrees=[])
    experience_info = ExperienceResponse(roles=[], projects=[])
    certifications_info = CertificationsResponse(certifications=[])

    updated_content = update_resume_content_with_structured_data(
        current_content,
        personal_info=None,
        education=education_info,
        experience=experience_info,
        certifications=certifications_info,
    )

    assert "# Personal" in updated_content
    assert "Name: John Doe" in updated_content
    assert "# Education" not in updated_content
    assert "# Experience" not in updated_content
    assert "# Certifications" not in updated_content


def test_update_resume_content_with_all_sections():
    """Test updating resume content with all sections."""
    current_content = ""

    personal_info = PersonalInfoResponse(name="John Doe", email="john@example.com")
    education = EducationResponse(
        degrees=[{"school": "University", "degree": "BS"}],
    )
    experience = ExperienceResponse(
        roles=[
            {
                "basics": {
                    "company": "Tech Corp",
                    "title": "Engineer",
                    "start_date": "2020-01-01",
                },
            },
        ],
        projects=[
            {
                "overview": {"title": "Project A"},
                "description": {"text": "A project"},
            },
        ],
    )
    certifications = CertificationsResponse(
        certifications=[{"name": "Cert A", "issuer": "Issuer"}],
    )

    updated_content = update_resume_content_with_structured_data(
        current_content=current_content,
        personal_info=personal_info,
        education=education,
        experience=experience,
        certifications=certifications,
    )

    assert "# Personal" in updated_content
    assert "# Education" in updated_content
    assert "# Experience" in updated_content
    assert "# Certifications" in updated_content


def test_reconstruct_resume_markdown_with_empty_personal_info():
    """Test that an empty but non-None personal info section is not rendered."""
    personal_info = PersonalInfoResponse()  # This will serialize to an empty string
    education_info = EducationResponse(
        degrees=[
            {
                "school": "University of Testing",
                "degree": "B.Sc. in Testing",
            },
        ],
    )

    result = reconstruct_resume_markdown(
        personal_info=personal_info,
        education=education_info,
    )

    assert "# Personal" not in result
    assert "# Education" in result
    assert "University of Testing" in result


def test_serialize_experience_to_markdown_with_roles_and_projects():
    """Test serializing an experience section with both roles and projects."""
    experience = ExperienceResponse(
        roles=[
            {
                "basics": {
                    "company": "Tech Corp",
                    "title": "Engineer",
                    "start_date": "2020-01-01",
                },
                "summary": {"text": "A summary of the role."},
                "skills": {"skills": ["Python", "FastAPI"]},
            },
        ],
        projects=[
            {
                "overview": {"title": "Project A", "start_date": "2021-06-01"},
                "description": {"text": "A description of the project."},
                "skills": {"skills": ["HTML", "CSS"]},
            },
        ],
    )

    result = serialize_experience_to_markdown(experience)
    expected = textwrap.dedent(
        """\
        # Experience

        ## Projects

        ### Project

        #### Overview

        Title: Project A
        Start date: 06/2021

        #### Description

        A description of the project.

        #### Skills

        * HTML
        * CSS

        ## Roles

        ### Role

        #### Basics

        Company: Tech Corp
        Title: Engineer
        Start date: 01/2020

        #### Summary

        A summary of the role.

        #### Skills

        * Python
        * FastAPI

        """
    )
    assert result == expected


def test_serialize_role_to_markdown_not_relevant_full():
    """Test that a 'not relevant' role with full data is serialized correctly."""
    # 1. Construct a mock Role object with sample data for all sections
    # Using SimpleNamespace to mock the object structure
    mock_role = SimpleNamespace(
        basics=SimpleNamespace(
            company="Test Corp",
            title="Tester",
            start_date=datetime(2022, 1, 1),
            end_date=None,
            location="Remote",
            agency_name=None,
            job_category=None,
            employment_type=None,
            reason_for_change=None,
            inclusion_status=InclusionStatus.NOT_RELEVANT,
        ),
        summary=SimpleNamespace(text="This summary should be visible."),
        responsibilities=SimpleNamespace(
            text="These responsibilities should be replaced."
        ),
        skills=SimpleNamespace(skills=["Python", "Testing"]),
    )

    # 3. Call _serialize_role_to_markdown
    result_lines = _serialize_role_to_markdown(mock_role)
    result = "\n".join(result_lines)

    # 4. Assert conditions
    # Basics and Summary content should be present
    assert "Company: Test Corp" in result
    assert "Title: Tester" in result
    assert "#### Summary" in result
    assert "This summary should be visible." in result

    # Responsibilities header and placeholder text should be present
    assert "#### Responsibilities" in result
    assert "(no relevant experience)" in result

    # Original responsibilities text should NOT be present
    assert "These responsibilities should be replaced." not in result

    # Skills content should be present
    assert "#### Skills" in result
    assert "* Python" in result
    assert "* Testing" in result


def test_serialize_role_to_markdown_include_full():
    """Test that an 'include' role with full data is serialized correctly."""
    mock_role = SimpleNamespace(
        basics=SimpleNamespace(
            company="Test Corp",
            title="Tester",
            start_date=datetime(2022, 1, 1),
            end_date=None,
            location="Remote",
            agency_name=None,
            job_category=None,
            employment_type=None,
            reason_for_change=None,
            inclusion_status=InclusionStatus.INCLUDE,
        ),
        summary=SimpleNamespace(text="This is a summary."),
        responsibilities=SimpleNamespace(text="These are responsibilities."),
        skills=SimpleNamespace(skills=["Python", "Testing"]),
    )

    result_lines = _serialize_role_to_markdown(mock_role)
    result = "\n".join(result_lines)

    assert "Company: Test Corp" in result
    assert "Title: Tester" in result
    assert "#### Summary" in result
    assert "This is a summary." in result
    assert "#### Responsibilities" in result
    assert "These are responsibilities." in result
    assert "(no relevant experience)" not in result
    assert "#### Skills" in result
    assert "* Python" in result


def test_serialize_role_to_markdown_omit():
    """Test that an 'omit' role returns an empty list."""
    mock_role = SimpleNamespace(basics=SimpleNamespace(inclusion_status=InclusionStatus.OMIT))
    result_lines = _serialize_role_to_markdown(mock_role)
    assert result_lines == []


def test_serialize_role_to_markdown_no_basics():
    """Test serializing a role with no 'basics' attribute returns an empty list."""
    mock_role = SimpleNamespace(summary=SimpleNamespace(text="summary"))
    result_lines = _serialize_role_to_markdown(mock_role)
    assert result_lines == []


def test_serialize_role_to_markdown_empty_role_content():
    """Test serializing a role that results in no content returns an empty list."""
    mock_role = SimpleNamespace(
        basics=SimpleNamespace(
            company=None,
            title=None,
            start_date=None,
            end_date=None,
            location=None,
            agency_name=None,
            job_category=None,
            employment_type=None,
            reason_for_change=None,
            inclusion_status=InclusionStatus.INCLUDE,
        ),
        summary=None,
        responsibilities=None,
        skills=None,
    )
    result_lines = _serialize_role_to_markdown(mock_role)
    assert result_lines == []


def test_serialize_experience_with_roles_only():
    """Test serializing an experience section with only roles."""
    experience = ExperienceResponse(
        roles=[
            {
                "basics": {
                    "company": "Big Firm",
                    "title": "Analyst",
                    "start_date": "2018-05-01",
                }
            }
        ],
        projects=[],
    )
    result = serialize_experience_to_markdown(experience)
    expected = textwrap.dedent(
        """\
        # Experience

        ## Roles

        ### Role

        #### Basics

        Company: Big Firm
        Title: Analyst
        Start date: 05/2018

        """
    )
    assert result == expected


def test_serialize_experience_with_projects_only():
    """Test serializing an experience section with only projects."""
    experience = ExperienceResponse(
        roles=[],
        projects=[
            {
                "overview": {"title": "Side Project"},
                "description": {"text": "A fun project."},
            }
        ],
    )
    result = serialize_experience_to_markdown(experience)
    expected = textwrap.dedent(
        """\
        # Experience

        ## Projects

        ### Project

        #### Overview

        Title: Side Project

        #### Description

        A fun project.

        """
    )
    assert result == expected


def test_serialize_experience_empty():
    """Test serializing an empty experience section."""
    experience = ExperienceResponse(roles=[], projects=[])
    result = serialize_experience_to_markdown(experience)
    assert result == ""


def test_serialize_experience_with_omitted_items():
    """Test that items with OMIT status are not serialized."""
    experience = ExperienceResponse(
        roles=[
            {
                "basics": {
                    "company": "Visible Corp",
                    "title": "Visible Role",
                    "start_date": "2020-01-01",
                },
            },
            {
                "basics": {
                    "company": "Invisible Corp",
                    "title": "Omitted Role",
                    "start_date": "2019-01-01",
                    "inclusion_status": InclusionStatus.OMIT,
                },
            },
        ],
        projects=[
            {
                "overview": {
                    "title": "Omitted Project",
                    "inclusion_status": InclusionStatus.OMIT,
                },
            },
            {"overview": {"title": "Visible Project"}},
        ],
    )

    result = serialize_experience_to_markdown(experience)

    assert "Visible Corp" in result
    assert "Visible Project" in result
    assert "Invisible Corp" not in result
    assert "Omitted Project" not in result
    assert "Omitted Role" not in result


def test_serialize_experience_with_empty_text_fields():
    """Test that sections with empty text are not serialized."""
    experience = ExperienceResponse(
        roles=[
            {
                "basics": {
                    "company": "Tech Corp",
                    "title": "Engineer",
                    "start_date": "2020-01-01",
                },
                "summary": {"text": "A summary."},
                "responsibilities": {"text": ""},  # Empty text
            },
            {
                "basics": {
                    "company": "Another Corp",
                    "title": "Old Engineer",
                    "start_date": "2018-01-01",
                },
                "summary": {"text": "  "},  # Whitespace only is not stripped, but this is ok.
            },
        ],
        projects=[
            {
                "overview": {"title": "Project A"},
                "description": {"text": "A real description."},
            },
            {
                "overview": {"title": "Project B"},
                "description": {"text": None},
            },
        ],
    )

    result = serialize_experience_to_markdown(experience)
    roles_section = result.split("## Roles")[1]
    role_blocks = roles_section.split("### Role")

    tech_corp_block = [b for b in role_blocks if "Tech Corp" in b][0]
    another_corp_block = [b for b in role_blocks if "Another Corp" in b][0]

    # Tech Corp should have summary, but not responsibilities (empty text)
    assert "#### Summary" in tech_corp_block
    assert "A summary." in tech_corp_block
    assert "#### Responsibilities" not in tech_corp_block

    # Another Corp should have summary (whitespace is content)
    assert "#### Summary" in another_corp_block

    # Project B should not have description (None)
    projects_section = result.split("## Projects")[1]
    project_b_text = projects_section.split("Project B")[1]
    assert "#### Description" not in project_b_text


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


def test_serialize_experience_with_not_relevant_items():
    """Test that items with NOT_RELEVANT status are serialized correctly."""
    experience = ExperienceResponse(
        roles=[
            {
                "basics": {
                    "company": "Not Relevant Corp",
                    "title": "Not Relevant Role",
                    "start_date": "2020-01-01",
                    "inclusion_status": InclusionStatus.NOT_RELEVANT,
                },
                "summary": {"text": "This summary should now be included."},
                "responsibilities": {"text": "This text should be ignored."},
                "skills": {"skills": ["included skill"]},
            },
        ],
        projects=[
            {
                "overview": {
                    "title": "Not Relevant Project",
                    "inclusion_status": InclusionStatus.NOT_RELEVANT,
                },
                "description": {"text": "This description should be ignored."},
            },
        ],
    )

    result = serialize_experience_to_markdown(experience)

    # Role assertions
    assert "Not Relevant Corp" in result
    assert "Not Relevant Role" in result
    assert "#### Basics" in result

    # Summary and skills should now be included
    assert "#### Summary" in result
    assert "This summary should now be included." in result
    assert "#### Skills" in result
    assert "included skill" in result

    # Responsibilities should be a placeholder
    assert "#### Responsibilities" in result
    assert "(no relevant experience)" in result
    assert "This text should be ignored." not in result

    # Project assertions (unchanged behavior)
    assert "Not Relevant Project" in result
    assert "#### Overview" in result
    assert "#### Description" not in result
    assert "This description should be ignored." not in result


def test_serialize_experience_with_not_relevant_role_minimal():
    """Test that a NOT_RELEVANT role with minimal data serializes correctly."""
    experience = ExperienceResponse(
        roles=[
            {
                "basics": {
                    "company": "Minimal Corp",
                    "title": "Minimalist",
                    "start_date": "2022-01-01",
                    "inclusion_status": InclusionStatus.NOT_RELEVANT,
                },
                "summary": None,
                "responsibilities": {"text": "This should be ignored."},
                "skills": None,
            },
        ],
        projects=[],
    )
    result = serialize_experience_to_markdown(experience)
    expected = textwrap.dedent(
        """\
        # Experience

        ## Roles

        ### Role

        #### Basics

        Company: Minimal Corp
        Title: Minimalist
        Start date: 01/2022

        #### Responsibilities

        (no relevant experience)

        """
    )
    assert result == expected
