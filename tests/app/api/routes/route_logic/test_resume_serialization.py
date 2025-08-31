import textwrap

from resume_editor.app.api.routes.route_logic.resume_reconstruction import (
    reconstruct_resume_markdown,
)
from resume_editor.app.api.routes.route_logic.resume_serialization import (
    update_resume_content_with_structured_data,
)
from resume_editor.app.api.routes.route_models import (
    CertificationsResponse,
    EducationResponse,
    ExperienceResponse,
    PersonalInfoResponse,
)


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
