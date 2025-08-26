from unittest.mock import patch

from resume_editor.app.api.routes.route_logic.resume_reconstruction import (
    build_complete_resume_from_sections,
    reconstruct_resume_markdown,
)
from resume_editor.app.api.routes.route_models import (
    CertificationsResponse,
    EducationResponse,
    ExperienceResponse,
    PersonalInfoResponse,
)


def test_reconstruct_resume_markdown_with_all_sections():
    """Test reconstructing a resume with all sections provided."""
    # Create mock data structures
    personal_info = PersonalInfoResponse(
        name="John Doe",
        email="john@example.com",
        phone="123-456-7890",
        location="New York, NY",
        website="https://johndoe.com",
    )

    education = EducationResponse(
        degrees=[
            {
                "school": "University of Example",
                "degree": "Bachelor of Science",
                "major": "Computer Science",
                "start_date": "2013-09-01",
                "end_date": "2017-05-01",
                "gpa": "3.8",
            },
        ],
    )

    experience = ExperienceResponse(
        roles=[
            {
                "basics": {
                    "company": "Tech Corp",
                    "title": "Software Engineer",
                    "start_date": "2017-06-01",
                    "end_date": "2021-01-01",
                    "location": "San Francisco, CA",
                },
                "summary": {"text": "Developed web applications"},
            },
        ],
        projects=[
            {
                "overview": {
                    "title": "Project Management System",
                    "url": "https://project.example.com",
                    "start_date": "2018-01-01",
                    "end_date": "2018-12-01",
                },
                "description": {
                    "text": "A system for managing projects",
                },
            },
        ],
    )

    certifications = CertificationsResponse(
        certifications=[
            {
                "name": "AWS Certified Developer",
                "issuer": "Amazon Web Services",
                "id": "12345",
                "issued_date": "2019-01-01",
                "expiry_date": "2022-01-01",
            },
        ],
    )

    # Mock the serialization functions to return specific content
    with (
        patch(
            "resume_editor.app.api.routes.route_logic.resume_serialization.serialize_personal_info_to_markdown",
        ) as mock_personal,
        patch(
            "resume_editor.app.api.routes.route_logic.resume_serialization.serialize_education_to_markdown",
        ) as mock_education,
        patch(
            "resume_editor.app.api.routes.route_logic.resume_serialization.serialize_experience_to_markdown",
        ) as mock_experience,
        patch(
            "resume_editor.app.api.routes.route_logic.resume_serialization.serialize_certifications_to_markdown",
        ) as mock_certifications,
    ):
        mock_personal.return_value = (
            "# Personal\n\n## Contact Information\nName: John Doe"
        )
        mock_education.return_value = (
            "# Education\n\n## Degrees\n\n### Degree\nSchool: University of Example"
        )
        mock_experience.return_value = """# Experience

## Projects

### Project

#### Overview
Title: Project Management System

## Roles

### Role

#### Basics
Company: Tech Corp"""
        mock_certifications.return_value = (
            "# Certifications\n\n## Certification\nName: AWS Certified Developer"
        )

        result = reconstruct_resume_markdown(
            personal_info=personal_info,
            education=education,
            experience=experience,
            certifications=certifications,
        )

        # Verify the result contains all sections in proper format
        assert result.startswith("# Personal")
        assert "# Education" in result
        assert "# Experience" in result
        assert "# Certifications" in result
        mock_experience.assert_called_once_with(experience)


def test_reconstruct_resume_markdown_with_some_sections():
    """Test reconstructing a resume with only some sections provided."""
    # Create mock data structures
    personal_info = PersonalInfoResponse(name="John Doe", email="john@example.com")

    experience = ExperienceResponse(
        roles=[
            {
                "basics": {
                    "company": "Tech Corp",
                    "title": "Software Engineer",
                    "start_date": "2017-06-01",
                    "end_date": "2021-01-01",
                },
                "summary": {"text": "Developed web applications"},
            },
        ],
        projects=[],
    )

    # Mock the serialization functions
    with (
        patch(
            "resume_editor.app.api.routes.route_logic.resume_serialization.serialize_personal_info_to_markdown",
        ) as mock_personal,
        patch(
            "resume_editor.app.api.routes.route_logic.resume_serialization.serialize_experience_to_markdown",
        ) as mock_experience,
        patch(
            "resume_editor.app.api.routes.route_logic.resume_serialization.serialize_education_to_markdown",
        ) as mock_education,
        patch(
            "resume_editor.app.api.routes.route_logic.resume_serialization.serialize_certifications_to_markdown",
        ) as mock_certifications,
    ):
        mock_personal.return_value = (
            "# Personal\n\n## Contact Information\nName: John Doe"
        )
        mock_experience.return_value = (
            "# Experience\n\n## Roles\n\n### Role\n\n#### Basics\nCompany: Tech Corp"
        )
        mock_education.return_value = ""
        mock_certifications.return_value = ""

        result = reconstruct_resume_markdown(
            personal_info=personal_info,
            education=None,
            experience=experience,
            certifications=None,
        )

        # Verify the result contains only provided sections
        assert result.startswith("# Personal")
        assert "# Experience" in result
        assert "Company: Tech Corp" in result
        assert "# Education" not in result
        assert "# Certifications" not in result


def test_reconstruct_resume_markdown_with_no_sections():
    """Test reconstructing a resume with no sections provided."""
    result = reconstruct_resume_markdown()

    # Should be an empty string
    assert result == ""


def test_build_complete_resume_from_sections():
    """Test building a complete resume from all sections."""
    # Create mock data structures
    personal_info = PersonalInfoResponse(name="John Doe", email="john@example.com")

    education = EducationResponse(
        degrees=[
            {
                "school": "University of Example",
                "degree": "Bachelor of Science",
                "major": "Computer Science",
                "start_date": "2013-09-01",
                "end_date": "2017-05-01",
                "gpa": "3.8",
            },
        ],
    )

    experience = ExperienceResponse(
        roles=[
            {
                "basics": {
                    "company": "Tech Corp",
                    "title": "Software Engineer",
                    "start_date": "2017-06-01",
                    "end_date": "2021-01-01",
                },
                "summary": {"text": "Developed web applications"},
            },
        ],
        projects=[
            {
                "overview": {
                    "title": "Project Management System",
                    "url": "https://project.example.com",
                    "start_date": "2018-01-01",
                    "end_date": "2018-12-01",
                },
                "description": {
                    "text": "A system for managing projects",
                },
            },
        ],
    )

    certifications = CertificationsResponse(
        certifications=[
            {
                "name": "AWS Certified Developer",
                "issuer": "Amazon Web Services",
                "id": "12345",
                "issued_date": "2019-01-01",
                "expiry_date": "2022-01-01",
            },
        ],
    )

    # Mock the serialization functions
    with (
        patch(
            "resume_editor.app.api.routes.route_logic.resume_serialization.serialize_personal_info_to_markdown",
        ) as mock_personal,
        patch(
            "resume_editor.app.api.routes.route_logic.resume_serialization.serialize_education_to_markdown",
        ) as mock_education,
        patch(
            "resume_editor.app.api.routes.route_logic.resume_serialization.serialize_experience_to_markdown",
        ) as mock_experience,
        patch(
            "resume_editor.app.api.routes.route_logic.resume_serialization.serialize_certifications_to_markdown",
        ) as mock_certifications,
    ):
        mock_personal.return_value = (
            "# Personal\n\n## Contact Information\nName: John Doe"
        )
        mock_education.return_value = (
            "# Education\n\n## Degrees\n\n### Degree\nSchool: University of Example"
        )
        mock_experience.return_value = """# Experience

## Projects

### Project

#### Overview
Title: Project Management System

## Roles

### Role

#### Basics
Company: Tech Corp"""
        mock_certifications.return_value = (
            "# Certifications\n\n## Certification\nName: AWS Certified Developer"
        )

        result = build_complete_resume_from_sections(
            personal_info=personal_info,
            education=education,
            experience=experience,
            certifications=certifications,
        )

        # Verify the result contains all sections
        assert result.startswith("# Personal")
        assert "# Education" in result
        assert "# Experience" in result
        assert "Project Management System" in result
        assert "Tech Corp" in result
        assert "# Certifications" in result
