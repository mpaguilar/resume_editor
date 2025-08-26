import textwrap
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from resume_editor.app.api.routes.route_logic.resume_serialization import (
    extract_certifications_info,
    extract_education_info,
    extract_experience_info,
    extract_personal_info,
    serialize_certifications_to_markdown,
    serialize_education_to_markdown,
    serialize_experience_to_markdown,
    serialize_personal_info_to_markdown,
    update_resume_content_with_structured_data,
)
from resume_editor.app.api.routes.route_models import (
    CertificationsResponse,
    EducationResponse,
    ExperienceResponse,
    PersonalInfoResponse,
)
from resume_editor.app.models.resume.experience import InclusionStatus


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

    # Not Relevant items should have basics/overview only
    assert "Not Relevant Inc" in markdown
    assert "Backend Dev" in markdown
    assert "Another summary." not in markdown
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
    assert experience.roles[0].summary.text == "This is a summary."
    # Since inclusion status is not parsed, it should default to INCLUDE
    assert experience.roles[1].basics.company == "Omitter Inc"
    assert experience.roles[1].basics.inclusion_status == InclusionStatus.INCLUDE
    assert experience.roles[1].summary is None

    # Projects validation
    assert len(experience.projects) == 1
    assert experience.projects[0].overview.title == "A Project"
    # Since inclusion status is not parsed, it should default to INCLUDE
    assert (
        experience.projects[0].overview.inclusion_status == InclusionStatus.INCLUDE
    )
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
    with pytest.raises(ValueError, match="Failed to parse experience info"):
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
                        }
                    }
                ],
                "projects": [
                    {
                        "overview": {
                            "title": "Omit Proj",
                            "inclusion_status": InclusionStatus.OMIT,
                        },
                        "description": {"text": "desc"},
                    }
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


class TestResumeSerialization:
    """Test cases for resume serialization functions."""

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_serialization.WriterResume.parse",
    )
    def test_extract_personal_info_no_personal_section(self, mock_parse):
        """Test personal info extraction when personal section is missing."""
        mock_resume = Mock()
        mock_resume.personal = None
        mock_parse.return_value = mock_resume

        response = extract_personal_info("any content")
        assert response == PersonalInfoResponse()

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_serialization.WriterResume.parse",
    )
    def test_extract_personal_info_no_contact_info(self, mock_parse):
        """Test personal info extraction when contact info is missing."""
        mock_personal = Mock()
        mock_personal.contact_info = None
        # To accurately simulate the parser's behavior for missing sections,
        # we configure the mock to raise an AttributeError when these are accessed.
        mock_personal.configure_mock(
            **{
                "websites": None,
                "visa_status": None,
                "banner": None,
                "note": None,
            },
        )
        # Use a spec to ensure only valid attributes of the real object are accessed
        mock_personal.spec = [
            "contact_info",
            "websites",
            "visa_status",
            "banner",
            "note",
        ]
        # Set attributes that should be absent to None explicitly.
        mock_personal.websites = None
        mock_personal.visa_status = None
        mock_personal.banner = None
        mock_personal.note = None

        mock_resume = Mock()
        mock_resume.personal = mock_personal
        mock_parse.return_value = mock_resume

        response = extract_personal_info("any content")
        # An empty response should be returned if no data is present
        assert response == PersonalInfoResponse()

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_serialization.WriterResume.parse",
    )
    def test_extract_personal_info_partial_data(self, mock_parse):
        """Test personal info extraction with partial data."""
        mock_contact_info = Mock()
        mock_contact_info.name = "John Doe"
        mock_contact_info.email = None
        mock_contact_info.phone = "123-456-7890"
        mock_contact_info.location = None
        mock_websites = Mock()
        mock_websites.website = None
        mock_websites.github = None
        mock_websites.linkedin = None
        mock_websites.twitter = None

        mock_personal = Mock()
        mock_personal.contact_info = mock_contact_info
        mock_personal.websites = mock_websites
        mock_personal.visa_status = None
        mock_personal.banner = None
        mock_personal.note = None

        mock_resume = Mock()
        mock_resume.personal = mock_personal
        mock_parse.return_value = mock_resume

        response = extract_personal_info("any content")
        assert response.name == "John Doe"
        assert response.email is None
        assert response.phone == "123-456-7890"
        assert response.location is None
        assert response.website is None

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_serialization.WriterResume.parse",
        side_effect=Exception("mock parse error"),
    )
    def test_extract_personal_info_parse_fails(self, mock_parse):
        """Test personal info extraction when parsing fails."""
        with pytest.raises(ValueError, match="Failed to parse personal info"):
            extract_personal_info("invalid content")

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_serialization.WriterResume.parse",
    )
    def test_extract_education_info_no_education_section(self, mock_parse):
        """Test education info extraction when education section is missing."""
        mock_resume = Mock()
        mock_resume.education = None
        mock_parse.return_value = mock_resume

        response = extract_education_info("any content")
        assert response.degrees == []

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_serialization.WriterResume.parse",
    )
    def test_extract_education_info_no_degrees(self, mock_parse):
        """Test education info extraction when degrees are missing."""
        mock_education = Mock()
        mock_education.degrees = None
        mock_resume = Mock()
        mock_resume.education = mock_education
        mock_parse.return_value = mock_resume

        response = extract_education_info("any content")
        assert response.degrees == []

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_serialization.WriterResume.parse",
    )
    def test_extract_education_info_partial_data(self, mock_parse):
        """Test education info extraction with partial data in a degree."""
        mock_degree = Mock()
        mock_degree.school = "Partial Uni"
        mock_degree.degree = None
        mock_degree.major = "Partial Major"
        mock_degree.start_date = None
        mock_degree.end_date = Mock()
        mock_degree.end_date.isoformat.return_value = "2022-01-01T00:00:00"
        mock_degree.gpa = None

        mock_education = Mock()
        mock_education.degrees = [mock_degree]
        mock_resume = Mock()
        mock_resume.education = mock_education
        mock_parse.return_value = mock_resume

        response = extract_education_info("any content")
        assert len(response.degrees) == 1
        degree = response.degrees[0]
        assert degree.school == "Partial Uni"
        assert degree.degree is None
        assert degree.major == "Partial Major"
        assert degree.start_date is None
        assert degree.end_date.isoformat() == "2022-01-01T00:00:00"
        assert degree.gpa is None

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_serialization.WriterResume.parse",
        side_effect=Exception("mock parse error"),
    )
    def test_extract_education_info_parse_fails(self, mock_parse):
        """Test education info extraction when parsing fails."""
        with pytest.raises(ValueError, match="Failed to parse education info"):
            extract_education_info("invalid content")

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

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_serialization.WriterResume.parse",
    )
    def test_extract_certifications_info_no_certifications(self, mock_parse):
        """Test certifications extraction when certifications section is missing."""
        mock_resume = Mock()
        mock_resume.certifications = None
        mock_parse.return_value = mock_resume

        response = extract_certifications_info("any content")
        assert response.certifications == []

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_serialization.WriterResume.parse",
    )
    def test_extract_certifications_info_partial_data(self, mock_parse):
        """Test certifications extraction with partial data in a certification."""
        mock_cert = Mock()
        mock_cert.name = "Test Cert"
        mock_cert.issuer = None
        mock_cert.certification_id = "123"
        mock_cert.issued = None
        mock_cert.expires = None

        # The Certifications object is iterable
        mock_resume = Mock(certifications=[mock_cert])
        mock_parse.return_value = mock_resume

        response = extract_certifications_info("any content")
        assert len(response.certifications) == 1
        cert = response.certifications[0]
        assert cert.name == "Test Cert"
        assert cert.issuer is None
        assert cert.certification_id == "123"
        assert cert.issued is None
        assert cert.expires is None

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_serialization.WriterResume.parse",
        side_effect=Exception("mock parse error"),
    )
    def test_extract_certifications_info_parse_fails(self, mock_parse):
        """Test certifications extraction when parsing fails."""
        with pytest.raises(ValueError, match="Failed to parse certifications info"):
            extract_certifications_info("invalid content")

    def test_serialize_personal_info_to_markdown(self):
        """Test serialization of personal information to Markdown."""
        personal_info = PersonalInfoResponse(
            name="John Doe",
            email="john@example.com",
            phone="123-456-7890",
            location="New York, NY",
            website="https://johndoe.com",
        )

        markdown = serialize_personal_info_to_markdown(personal_info)
        expected = """# Personal

## Contact Information

Name: John Doe
Email: john@example.com
Phone: 123-456-7890
Location: New York, NY

## Websites

Website: https://johndoe.com

"""
        assert "# Personal" in markdown
        assert "Name: John Doe" in markdown
        assert "Website: https://johndoe.com" in markdown

    def test_serialize_personal_info_to_markdown_partial_data(self):
        """Test serialization of partial personal information to Markdown."""
        personal_info = PersonalInfoResponse(name="John Doe", email="john@example.com")

        markdown = serialize_personal_info_to_markdown(personal_info)
        assert "# Personal" in markdown
        assert "Name: John Doe" in markdown
        assert "Email: john@example.com" in markdown
        assert "Websites" not in markdown

    def test_serialize_personal_info_to_markdown_empty_data(self):
        """Test serialization of empty personal information to Markdown."""
        personal_info = PersonalInfoResponse()
        markdown = serialize_personal_info_to_markdown(personal_info)
        assert markdown == ""

    def test_serialize_personal_info_to_markdown_another_partial_data(self):
        """Test serialization of different partial personal information to Markdown."""
        personal_info = PersonalInfoResponse(name="John Doe", phone="123-456-7890")

        markdown = serialize_personal_info_to_markdown(personal_info)
        assert "# Personal" in markdown
        assert "Name: John Doe" in markdown
        assert "Phone: 123-456-7890" in markdown
        assert "Websites" not in markdown

    # Tests for uncovered lines in serialize_personal_info_to_markdown
    def test_serialize_personal_info_to_markdown_none_input(self):
        """Test serialize_personal_info_to_markdown with None input - covers line 292."""
        result = serialize_personal_info_to_markdown(None)
        assert result == ""

    # Tests for uncovered lines in serialize_education_to_markdown
    def test_serialize_education_to_markdown_none_input(self):
        """Test serialize_education_to_markdown with None input - covers line 402."""
        result = serialize_education_to_markdown(None)
        assert result == ""

    def test_serialize_education_to_markdown(self):
        """Test serialization of education information to Markdown."""
        education = EducationResponse(
            degrees=[
                {
                    "school": "University of Example",
                    "degree": "Bachelor of Science",
                    "major": "Computer Science",
                    "start_date": "2016-09-01",
                    "end_date": "2020-05-15",
                    "gpa": "3.8",
                },
            ],
        )

        markdown = serialize_education_to_markdown(education)
        expected = """# Education

## Degrees

### Degree

School: University of Example
Degree: Bachelor of Science
Major: Computer Science
Start date: 09/2016
End date: 05/2020
GPA: 3.8

"""
        assert markdown == expected

    # Tests for uncovered lines in serialize_experience_to_markdown
    def test_serialize_experience_to_markdown_none_input(self):
        """Test serialize_experience_to_markdown with None input."""
        result = serialize_experience_to_markdown(None)
        assert result == ""

    def test_serialize_education_to_markdown_empty(self):
        """Test serialization of empty education information to Markdown."""
        education = EducationResponse(degrees=[])
        markdown = serialize_education_to_markdown(education)
        assert markdown == ""

    def test_serialize_education_to_markdown_partial_data(self):
        """Test serialization of partial education information to Markdown."""
        education = EducationResponse(
            degrees=[
                {
                    "school": "Partial University",
                    "degree": None,
                    "major": "Partial Major",
                    "start_date": "2018-01-01",
                    "end_date": None,
                    "gpa": None,
                },
            ],
        )

        markdown = serialize_education_to_markdown(education)
        expected = """# Education

## Degrees

### Degree

School: Partial University
Major: Partial Major
Start date: 01/2018

"""
        assert markdown == expected

    def test_serialize_education_to_markdown_partial_data_no_major(self):
        """Test serialization of partial education information without major."""
        education = EducationResponse(
            degrees=[
                {
                    "school": "A University",
                    "degree": "BS",
                    "major": None,
                    "start_date": "2018-01-01",
                    "end_date": None,
                    "gpa": None,
                },
            ],
        )

        markdown = serialize_education_to_markdown(education)
        expected = """# Education

## Degrees

### Degree

School: A University
Degree: BS
Start date: 01/2018

"""
        assert markdown == expected

    def test_serialize_experience_to_markdown(self):
        """Test serialization of experience information to Markdown."""
        experience = ExperienceResponse(
            roles=[
                {
                    "basics": {
                        "company": "Tech Corp",
                        "title": "Software Engineer",
                        "start_date": "2020-06-01",
                        "end_date": "2023-12-31",
                        "location": "San Francisco, CA",
                    },
                    "summary": {"text": "Developed web applications"},
                },
            ],
        )

        markdown = serialize_experience_to_markdown(experience)
        expected = """# Experience

## Roles

### Role

#### Basics

Company: Tech Corp
Title: Software Engineer
Start date: 06/2020
End date: 12/2023
Location: San Francisco, CA

#### Summary

Developed web applications

"""
        assert markdown == expected

    def test_serialize_experience_to_markdown_empty(self):
        """Test serialization of empty experience information to Markdown."""
        experience = ExperienceResponse(roles=[])
        markdown = serialize_experience_to_markdown(experience)
        assert markdown == ""

    def test_serialize_experience_to_markdown_partial_data(self):
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

    def test_serialize_experience_to_markdown_partial_data_no_location(self):
        """Test serialization of partial experience information without location."""
        experience = ExperienceResponse(
            roles=[
                {
                    "basics": {
                        "company": "Some Company",
                        "title": "Intern",
                        "start_date": "2021-01-01",
                    },
                },
            ],
        )
        markdown = serialize_experience_to_markdown(experience)
        expected = """# Experience

## Roles

### Role

#### Basics

Company: Some Company
Title: Intern
Start date: 01/2021

"""
        assert markdown == expected

    def test_serialize_certifications_to_markdown(self):
        """Test serialization of certifications information to Markdown."""
        certifications = CertificationsResponse(
            certifications=[
                {
                    "name": "AWS Certified Solutions Architect",
                    "issuer": "Amazon Web Services",
                    "id": "1234567890",
                    "issued_date": "2022-01-15",
                    "expiry_date": "2025-01-15",
                },
            ],
        )

        markdown = serialize_certifications_to_markdown(certifications)
        expected = """# Certifications

## Certification

Name: AWS Certified Solutions Architect
Issuer: Amazon Web Services
Issued: 01/2022
Expires: 01/2025
Certification ID: 1234567890

"""
        assert markdown == expected

    # Tests for uncovered lines in serialize_certifications_to_markdown
    def test_serialize_certifications_to_markdown_none_input(self):
        """Test serialize_certifications_to_markdown with None input."""
        result = serialize_certifications_to_markdown(None)
        assert result == ""

    def test_serialize_certifications_to_markdown_empty(self):
        """Test serialization of empty certifications information to Markdown."""
        certifications = CertificationsResponse(certifications=[])
        markdown = serialize_certifications_to_markdown(certifications)
        assert markdown == ""

    def test_serialize_certifications_to_markdown_partial_data(self):
        """Test serialization of partial certifications information to Markdown."""
        certifications = CertificationsResponse(
            certifications=[
                {
                    "name": "Partial Certification",
                    "issuer": None,
                    "id": "PART-123",
                    "issued_date": None,
                    "expiry_date": "2025-12-31",
                },
            ],
        )
        markdown = serialize_certifications_to_markdown(certifications)
        expected = """# Certifications

## Certification

Name: Partial Certification
Expires: 12/2025
Certification ID: PART-123

"""
        assert markdown == expected

    def test_serialize_certifications_to_markdown_partial_data_no_issuer(self):
        """Test serialization of partial certifications information without issuer."""
        certifications = CertificationsResponse(
            certifications=[
                {
                    "name": "A Certification",
                    "issuer": None,
                    "id": "PART-123",
                    "issued_date": None,
                    "expiry_date": "2025-12-31",
                },
            ],
        )
        markdown = serialize_certifications_to_markdown(certifications)
        expected = """# Certifications

## Certification

Name: A Certification
Expires: 12/2025
Certification ID: PART-123

"""
        assert markdown == expected

    def test_update_resume_content_with_structured_data(self):
        """Test updating resume content with structured data."""
        current_content = textwrap.dedent("""\
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
        """)

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
        assert (
            "University of Example" in updated_content
        )  # Should preserve other sections

    def test_update_resume_content_with_structured_data_no_personal_info(self):
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

    def test_update_resume_content_with_all_sections(self):
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

    def test_serialize_experience_not_relevant_project_with_full_overview(self):
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

    def test_serialize_experience_not_relevant_role_with_full_basics(self):
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
                    "summary": {"text": "This summary should be excluded."},
                    "responsibilities": {
                        "text": "These responsibilities should be excluded."
                    },
                    "skills": {"skills": ["Skill G", "Skill H"]},
                },
            ],
            projects=[],
        )
        markdown = serialize_experience_to_markdown(experience)

        assert "Company: Not Relevant Company" in markdown
        assert "Title: Not Relevant Title" in markdown
        assert "Start date: 01/2021" in markdown
        assert "End date: 12/2021" in markdown
        assert "Location: Not Relevant Location" in markdown
        assert "Agency: Not Relevant Agency" in markdown
        assert "Job category: Not Relevant Category" in markdown
        assert "Employment type: Not Relevant Type" in markdown
        assert "Reason for change: Not Relevant Reason" in markdown
        assert "This summary should be excluded." not in markdown
        assert "These responsibilities should be excluded." not in markdown
        assert "Skill G" not in markdown
        assert "Skill H" not in markdown

    def test_serialize_experience_to_markdown_all_fields(self):
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
            }
        ],
        roles=[],
    )
    markdown = serialize_experience_to_markdown(experience)
    expected_markdown = textwrap.dedent("""\
    # Experience

    ## Projects

    ### Project

    #### Overview

    Title: A project

    """)
    assert markdown.strip() == expected_markdown.strip()


def test_serialize_not_relevant_role_with_only_basics():
    """Test serializing a NOT_RELEVANT role with only basics."""
    experience = ExperienceResponse(
        roles=[
            {
                "basics": {
                    "company": "A Company",
                    "title": "A Role",
                    "start_date": "2020-01-01",
                    "inclusion_status": InclusionStatus.NOT_RELEVANT,
                },
                "summary": {"text": "A summary to be ignored."},
            }
        ],
        projects=[],
    )
    markdown = serialize_experience_to_markdown(experience)
    expected_markdown = textwrap.dedent("""\
    # Experience

    ## Roles

    ### Role

    #### Basics

    Company: A Company
    Title: A Role
    Start date: 01/2020

    """)
    assert markdown.strip() == expected_markdown.strip()
