import textwrap
from datetime import datetime
from unittest.mock import Mock

import pytest

from resume_editor.app.api.routes.route_logic.resume_reconstruction import (
    reconstruct_resume_markdown,
)
from resume_editor.app.api.routes.route_logic.resume_serialization import (
    extract_experience_info,
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
from resume_editor.app.models.resume.experience import (
    InclusionStatus,
    Project,
    ProjectDescription,
    ProjectOverview,
    Role,
    RoleBasics,
    RoleSummary,
)


@pytest.mark.parametrize(
    "personal_info, expected_output",
    [
        # Test case for no personal info, covers return ""
        (
            PersonalInfoResponse(),
            "",
        ),
        # Test case for only name
        (
            PersonalInfoResponse(name="John Doe"),
            "# Personal\n\n## Contact Information\n\nName: John Doe\n\n",
        ),
        # Test case for only email
        (
            PersonalInfoResponse(email="john.doe@example.com"),
            "# Personal\n\n## Contact Information\n\nEmail: john.doe@example.com\n\n",
        ),
        # Test case for phone but no name/email
        (
            PersonalInfoResponse(phone="123-456-7890"),
            "# Personal\n\n## Contact Information\n\nPhone: 123-456-7890\n\n",
        ),
        # Test case for only website
        (
            PersonalInfoResponse(website="https://johndoe.com"),
            "# Personal\n\n## Websites\n\nWebsite: https://johndoe.com\n\n",
        ),
        # Test case for only twitter
        (
            PersonalInfoResponse(twitter="@johndoe"),
            "# Personal\n\n## Websites\n\nTwitter: @johndoe\n\n",
        ),
        # Test case for github but no website/twitter
        (
            PersonalInfoResponse(github="https://github.com/johndoe"),
            "# Personal\n\n## Websites\n\nGitHub: https://github.com/johndoe\n\n",
        ),
        # Test case for only work_authorization
        (
            PersonalInfoResponse(work_authorization="Green Card"),
            "# Personal\n\n## Visa Status\n\nWork Authorization: Green Card\n\n",
        ),
        # Test case for only require_sponsorship
        (
            PersonalInfoResponse(require_sponsorship=True),
            "# Personal\n\n## Visa Status\n\nRequire sponsorship: Yes\n\n",
        ),
        # Test case for full personal info
        (
            PersonalInfoResponse(
                name="Jane Doe",
                email="jane.doe@example.com",
                phone="111-222-3333",
                location="New York, NY",
                website="https://janedoe.com",
                github="https://github.com/janedoe",
                linkedin="https://linkedin.com/in/janedoe",
                twitter="@janedoe",
                work_authorization="US Citizen",
                require_sponsorship=False,
                banner="Experienced Developer",
                note="Looking for new opportunities",
            ),
            (
                "# Personal\n\n"
                "## Contact Information\n\n"
                "Name: Jane Doe\n"
                "Email: jane.doe@example.com\n"
                "Phone: 111-222-3333\n"
                "Location: New York, NY\n\n"
                "## Websites\n\n"
                "GitHub: https://github.com/janedoe\n"
                "LinkedIn: https://linkedin.com/in/janedoe\n"
                "Website: https://janedoe.com\n"
                "Twitter: @janedoe\n\n"
                "## Visa Status\n\n"
                "Work Authorization: US Citizen\n"
                "Require sponsorship: No\n\n"
                "## Banner\n\n"
                "Experienced Developer\n\n"
                "## Note\n\n"
                "Looking for new opportunities\n\n"
            ),
        ),
    ],
)
def test_serialize_personal_info_to_markdown(personal_info, expected_output):
    """Test serialization of personal info to Markdown."""
    result = serialize_personal_info_to_markdown(personal_info)
    assert result == expected_output


def test_extract_experience_info_with_all_fields():
    """Test extracting experience info with all fields populated."""
    resume_content = textwrap.dedent("""\
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
    """)
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


def test_serialize_education_to_markdown_partial_data_with_degree():
    """Test serializing education to cover the 'degree' field presence."""
    education = EducationResponse(
        degrees=[
            {
                "school": "A University",
                "degree": "B.Sc.",
            },
        ],
    )
    markdown = serialize_education_to_markdown(education)
    assert "Degree: B.Sc." in markdown


def test_serialize_experience_to_markdown_all_fields():
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
    assert "#### Summary" in markdown
    assert "Test Summary" in markdown
    assert "#### Responsibilities" in markdown
    assert "Test Responsibilities" in markdown
    assert "* Skill A" in markdown


def test_serialize_certifications_to_markdown_with_issuer():
    """Test serializing certifications to cover the 'issuer' field presence."""
    certifications = CertificationsResponse(
        certifications=[
            {"name": "Cert Name", "issuer": "Cert Issuer", "id": "123"},
        ],
    )
    markdown = serialize_certifications_to_markdown(certifications)
    assert "Issuer: Cert Issuer" in markdown
    assert "Certification ID: 123" in markdown


def test_update_resume_content_with_structured_data_preserves_personal():
    """Test update_resume_content preserves personal info if not provided."""
    current_content = """# Personal
## Contact Information
Name: Original Name
"""
    updated_content = update_resume_content_with_structured_data(
        current_content,
        personal_info=None,
    )
    assert "Name: Original Name" in updated_content


def test_serialize_experience_to_markdown_no_experience():
    """Test that an empty string is returned when no experience is provided."""
    # This covers the branch where experience has no roles and no projects
    experience_info = ExperienceResponse(roles=[], projects=[])
    result = serialize_experience_to_markdown(experience_info)
    assert result == ""


def test_serialize_certifications_to_markdown_with_data():
    """Test that certifications are serialized correctly to markdown."""
    # This covers the main serialization logic for certifications
    certifications_info = CertificationsResponse(
        certifications=[
            {
                "name": "Certified Pythonista",
                "issuer": "Python Institute",
                "id": "12345",
                "issued_date": "2023-01-15T00:00:00",
                "expiry_date": "2025-01-15T00:00:00",
            },
            {
                "name": "Certified FastAPI Developer",
                "issuer": None,
                "id": "67890",
                "issued_date": "2024-02-20T00:00:00",
                "expiry_date": None,
            },
        ],
    )
    expected_markdown = """# Certifications

## Certification

Name: Certified Pythonista
Issuer: Python Institute
Issued: 01/2023
Expires: 01/2025
Certification ID: 12345

## Certification

Name: Certified FastAPI Developer
Issued: 02/2024
Certification ID: 67890

"""
    result = serialize_certifications_to_markdown(certifications_info)
    assert result == expected_markdown


def test_serialize_certifications_to_markdown_no_data():
    """Test that an empty string is returned for no certifications."""
    # This covers the branch where there are no certifications to serialize
    certifications_info = CertificationsResponse(certifications=[])
    result = serialize_certifications_to_markdown(certifications_info)
    assert result == ""


def test_extract_experience_info_various_configurations():
    """Test extracting experience info with various role and project configurations."""
    resume_content = textwrap.dedent("""\
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

    """)
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


def test_serialize_education_to_markdown_degree_without_school():
    """Test serializing education where a degree has no school but has a degree name."""
    mock_degree = Mock()
    mock_degree.school = None
    mock_degree.degree = "Ph.D. in Computer Science"
    mock_degree.major = None
    mock_degree.start_date = None
    mock_degree.end_date = None
    mock_degree.gpa = None

    mock_education = Mock()
    mock_education.degrees = [mock_degree]

    markdown = serialize_education_to_markdown(mock_education)
    expected = textwrap.dedent(
        """\
    # Education

    ## Degrees

    ### Degree

    Degree: Ph.D. in Computer Science

    """,
    )
    assert markdown == expected


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


def test_serialize_certifications_to_markdown_partial_fields():
    """Test serializing certifications with partial fields for coverage."""
    # Certification with name but no issuer
    mock_cert1 = Mock()
    mock_cert1.name = "Cert One"
    mock_cert1.issuer = None
    mock_cert1.issued = None
    mock_cert1.expires = None
    mock_cert1.certification_id = None

    # Certification with no name but with issuer
    mock_cert2 = Mock()
    mock_cert2.name = None
    mock_cert2.issuer = "Issuer Two"
    mock_cert2.issued = None
    mock_cert2.expires = None
    mock_cert2.certification_id = None

    mock_certs_response = Mock()
    mock_certs_response.certifications = [mock_cert1, mock_cert2]

    markdown = serialize_certifications_to_markdown(mock_certs_response)

    cert_sections = markdown.split("## Certification\n\n")
    cert1_markdown = cert_sections[1]
    assert "Name: Cert One" in cert1_markdown
    assert "Issuer: " not in cert1_markdown

    cert2_markdown = cert_sections[2]
    assert "Name: " not in cert2_markdown
    assert "Issuer: Issuer Two" in cert2_markdown


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
            }
        ],
        roles=[],
    )

    markdown = serialize_experience_to_markdown(experience)
    assert markdown == ""


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

    """
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

        """
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
