from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from resume_editor.app.core.auth import get_current_user_from_cookie
from resume_editor.app.database.database import get_db
from resume_editor.app.main import create_app
from resume_editor.app.models.resume_model import Resume
from resume_editor.app.models.user import User


@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    return User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True,
    )


@pytest.fixture
def mock_resume():
    """Create a mock resume for testing."""
    return Resume(
        user_id=1,
        name="Test Resume",
        content="""# Personal

## Contact Information

Name: Test User
Email: test@example.com
Phone: 123-456-7890
Location: Test City, TS

## Websites

Website: https://testuser.com
GitHub: https://github.com/testuser
LinkedIn: https://linkedin.com/in/testuser
Twitter: https://twitter.com/testuser

## Visa Status

Work Authorization: US Citizen
Require sponsorship: No

## Banner

Experienced professional

## Note

Available for immediate hire

# Education

## Degrees

### Degree

School: University of Test
Degree: BS in Testing

# Experience

## Roles

### Role

#### Basics
Company: Test Corp
Title: Tester
Start date: 01/2022

## Projects

### Project

#### Overview
Title: A Test Project

#### Description
This is a test.

# Certifications

## Certification

Name: Certified Tester
""",
        is_active=True,
    )


@pytest.fixture
def authenticated_client(mock_user, mock_resume):
    """Create an authenticated test client with a mock database and resume."""
    app = create_app()

    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    def get_mock_db():
        yield mock_db

    def get_mock_current_user():
        return mock_user

    app.dependency_overrides[get_db] = get_mock_db
    app.dependency_overrides[get_current_user_from_cookie] = get_mock_current_user

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def test_edit_personal_info_form(authenticated_client):
    """Test the edit personal info form endpoint."""
    # Test the endpoint
    response = authenticated_client.get("/dashboard/resumes/1/edit/personal")
    assert response.status_code == 200
    assert "Edit Personal Information" in response.text
    # Check that the form has the correct hx-post attribute
    assert 'hx-post="/api/resumes/1/edit/personal"' in response.text


def test_edit_education_form(authenticated_client):
    """Test the edit education form endpoint."""
    # Test the endpoint
    response = authenticated_client.get("/dashboard/resumes/1/edit/education")
    assert response.status_code == 200
    assert "Edit Education" in response.text
    # Check that the form has the correct hx-post attribute
    assert 'hx-post="/api/resumes/1/edit/education"' in response.text


def test_edit_experience_form(authenticated_client):
    """Test the edit experience form endpoint."""
    # Test the endpoint
    response = authenticated_client.get("/dashboard/resumes/1/edit/experience")
    assert response.status_code == 200
    assert "Edit Experience" in response.text
    # Check that the form has the correct hx-post attribute
    assert 'hx-post="/api/resumes/1/edit/experience"' in response.text


def test_edit_projects_form(authenticated_client):
    """Test the edit projects form endpoint."""
    # Test the endpoint
    response = authenticated_client.get("/dashboard/resumes/1/edit/projects")
    assert response.status_code == 200
    assert "Edit Projects" in response.text
    # Check that the form has the correct hx-post attribute
    assert 'hx-post="/api/resumes/1/edit/projects"' in response.text


def test_edit_certifications_form(authenticated_client):
    """Test the edit certifications form endpoint."""
    # Test the endpoint
    response = authenticated_client.get("/dashboard/resumes/1/edit/certifications")
    assert response.status_code == 200
    assert "Edit Certifications" in response.text
    # Check that the form has the correct hx-post attribute
    assert 'hx-post="/api/resumes/1/edit/certifications"' in response.text


def test_get_personal_info(authenticated_client):
    """Test the get personal info endpoint."""
    # Test the endpoint
    response = authenticated_client.get("/api/resumes/1/personal")
    assert response.status_code == 200


def test_update_personal_info_structured(authenticated_client):
    """Test the update personal info structured endpoint."""
    # Test the endpoint
    response = authenticated_client.put(
        "/api/resumes/1/personal",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "123-456-7890",
            "location": "San Francisco, CA",
            "website": "https://johndoe.com",
            "github": "https://github.com/johndoe",
            "linkedin": "https://linkedin.com/in/johndoe",
            "twitter": "https://twitter.com/johndoe",
            "work_authorization": "US Citizen",
            "require_sponsorship": False,
            "banner": "Experienced professional",
            "note": "Available for immediate hire",
        },
    )
    assert response.status_code == 200


def test_get_education_info(authenticated_client):
    """Test the get education info endpoint."""
    # Test the endpoint
    response = authenticated_client.get("/api/resumes/1/education")
    assert response.status_code == 200


def test_update_education_info_structured(authenticated_client):
    """Test the update education info structured endpoint."""
    # Test the endpoint
    response = authenticated_client.put(
        "/api/resumes/1/education",
        json={
            "degrees": [
                {
                    "school": "University of Example",
                    "degree": "Bachelor of Science",
                    "major": "Computer Science",
                    "start_date": "2015-09-01",
                    "end_date": "2019-05-15",
                    "gpa": "3.9",
                },
            ],
        },
    )
    assert response.status_code == 200


def test_get_experience_info(authenticated_client):
    """Test the get experience info endpoint."""
    # Test the endpoint
    response = authenticated_client.get("/api/resumes/1/experience")
    assert response.status_code == 200


def test_update_experience_info_structured(authenticated_client):
    """Test the update experience info structured endpoint."""
    # Test the endpoint
    response = authenticated_client.put(
        "/api/resumes/1/experience",
        json={
            "roles": [
                {
                    "basics": {
                        "company": "Example Corp",
                        "title": "Software Engineer",
                        "start_date": "2020-01-01",
                        "end_date": "2022-12-31",
                    },
                    "summary": {
                        "text": "Developed web applications using Python and JavaScript",
                    },
                },
            ],
            "projects": [],
        },
    )
    assert response.status_code == 200


def test_get_projects_info(authenticated_client):
    """Test the get projects info endpoint."""
    # Test the endpoint
    response = authenticated_client.get("/api/resumes/1/projects")
    assert response.status_code == 200


def test_update_projects_info_structured(authenticated_client):
    """Test the update projects info structured endpoint."""
    # Test the endpoint
    response = authenticated_client.put(
        "/api/resumes/1/projects",
        json={
            "projects": [
                {
                    "overview": {
                        "title": "Resume Editor Application",
                        "url": "https://github.com/example/resume-editor",
                        "start_date": "2023-01-01",
                        "end_date": "2023-12-31",
                    },
                    "description": {
                        "text": "A web-based application for resume editing",
                    },
                },
            ],
        },
    )
    assert response.status_code == 200


def test_get_certifications_info(authenticated_client):
    """Test the get certifications info endpoint."""
    # Test the endpoint
    response = authenticated_client.get("/api/resumes/1/certifications")
    assert response.status_code == 200


def test_update_certifications_info_structured(authenticated_client):
    """Test the update certifications info structured endpoint."""
    # Test the endpoint
    response = authenticated_client.put(
        "/api/resumes/1/certifications",
        json={
            "certifications": [
                {
                    "name": "AWS Certified Solutions Architect",
                    "issuer": "Amazon Web Services",
                    "id": "ABC123XYZ",
                    "issued_date": "2022-01-01",
                    "expiry_date": "2025-01-01",
                },
            ],
        },
    )
    assert response.status_code == 200
