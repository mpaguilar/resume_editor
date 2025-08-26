from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from resume_editor.app.api.routes.resume import get_db
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


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_edit_personal_info_form(
    fake_get_db,
    mock_get_current_user,
    mock_user,
    mock_resume,
):
    """Test the edit personal info form endpoint."""
    app = create_app()
    client = TestClient(app)

    # Setup mocks
    mock_get_current_user.return_value = mock_user
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    # Test the endpoint
    response = client.get("/dashboard/resumes/1/edit/personal")
    assert response.status_code == 200
    assert "Edit Personal Information" in response.text
    # Check that the form has the correct hx-post attribute
    assert 'hx-post="/api/resumes/1/edit/personal"' in response.text

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_edit_education_form(
    fake_get_db,
    mock_get_current_user,
    mock_user,
    mock_resume,
):
    """Test the edit education form endpoint."""
    app = create_app()
    client = TestClient(app)

    # Setup mocks
    mock_get_current_user.return_value = mock_user
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    # Test the endpoint
    response = client.get("/dashboard/resumes/1/edit/education")
    assert response.status_code == 200
    assert "Edit Education" in response.text
    # Check that the form has the correct hx-post attribute
    assert 'hx-post="/api/resumes/1/edit/education"' in response.text

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_edit_experience_form(
    fake_get_db,
    mock_get_current_user,
    mock_user,
    mock_resume,
):
    """Test the edit experience form endpoint."""
    app = create_app()
    client = TestClient(app)

    # Setup mocks
    mock_get_current_user.return_value = mock_user
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    # Test the endpoint
    response = client.get("/dashboard/resumes/1/edit/experience")
    assert response.status_code == 200
    assert "Edit Experience" in response.text
    # Check that the form has the correct hx-post attribute
    assert 'hx-post="/api/resumes/1/edit/experience"' in response.text

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_edit_projects_form(fake_get_db, mock_get_current_user, mock_user, mock_resume):
    """Test the edit projects form endpoint."""
    app = create_app()
    client = TestClient(app)

    # Setup mocks
    mock_get_current_user.return_value = mock_user
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    # Test the endpoint
    response = client.get("/dashboard/resumes/1/edit/projects")
    assert response.status_code == 200
    assert "Edit Projects" in response.text
    # Check that the form has the correct hx-post attribute
    assert 'hx-post="/api/resumes/1/edit/projects"' in response.text

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_edit_certifications_form(
    fake_get_db,
    mock_get_current_user,
    mock_user,
    mock_resume,
):
    """Test the edit certifications form endpoint."""
    app = create_app()
    client = TestClient(app)

    # Setup mocks
    mock_get_current_user.return_value = mock_user
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    # Test the endpoint
    response = client.get("/dashboard/resumes/1/edit/certifications")
    assert response.status_code == 200
    assert "Edit Certifications" in response.text
    # Check that the form has the correct hx-post attribute
    assert 'hx-post="/api/resumes/1/edit/certifications"' in response.text

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_update_personal_info(
    fake_get_db,
    mock_get_current_user,
    mock_user,
    mock_resume,
):
    """Test the update personal info endpoint."""
    app = create_app()
    client = TestClient(app)

    # Setup mocks
    mock_get_current_user.return_value = mock_user
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    # Test the endpoint
    response = client.post(
        "/api/resumes/1/edit/personal",
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
    assert "Personal information updated successfully!" in response.text

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_update_education(fake_get_db, mock_get_current_user, mock_user, mock_resume):
    """Test the update education endpoint."""
    app = create_app()
    client = TestClient(app)

    # Setup mocks
    mock_get_current_user.return_value = mock_user
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    # Test the endpoint
    response = client.post(
        "/api/resumes/1/edit/education",
        data={
            "school": "University of Example",
            "degree": "Bachelor of Science",
            "major": "Computer Science",
            "start_date": "2015-09-01",
            "end_date": "2019-05-15",
            "gpa": "3.9",
        },
    )
    assert response.status_code == 200
    assert "Education information updated successfully!" in response.text

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_update_experience(fake_get_db, mock_get_current_user, mock_user, mock_resume):
    """Test the update experience endpoint."""
    app = create_app()
    client = TestClient(app)

    # Setup mocks
    mock_get_current_user.return_value = mock_user
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    # Test the endpoint
    response = client.post(
        "/api/resumes/1/edit/experience",
        data={
            "company": "Example Corp",
            "title": "Software Engineer",
            "start_date": "2020-01-01",
            "end_date": "2022-12-31",
            "description": "Developed web applications using Python and JavaScript",
        },
    )
    assert response.status_code == 200
    assert "Experience information updated successfully!" in response.text

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_update_projects(fake_get_db, mock_get_current_user, mock_user, mock_resume):
    """Test the update projects endpoint."""
    app = create_app()
    client = TestClient(app)

    # Setup mocks
    mock_get_current_user.return_value = mock_user
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    # Test the endpoint
    response = client.post(
        "/api/resumes/1/edit/projects",
        data={
            "title": "Resume Editor Application",
            "description": "A web-based application for resume editing",
            "url": "https://github.com/example/resume-editor",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
        },
    )
    assert response.status_code == 200
    assert "Projects information updated successfully!" in response.text

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_update_certifications(
    fake_get_db,
    mock_get_current_user,
    mock_user,
    mock_resume,
):
    """Test the update certifications endpoint."""
    app = create_app()
    client = TestClient(app)

    # Setup mocks
    mock_get_current_user.return_value = mock_user
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    # Test the endpoint
    response = client.post(
        "/api/resumes/1/edit/certifications",
        data={
            "name": "AWS Certified Solutions Architect",
            "issuer": "Amazon Web Services",
            "id": "ABC123XYZ",
            "issued_date": "2022-01-01",
            "expiry_date": "2025-01-01",
        },
    )
    assert response.status_code == 200
    assert "Certifications information updated successfully!" in response.text

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_get_personal_info(fake_get_db, mock_get_current_user, mock_user, mock_resume):
    """Test the get personal info endpoint."""
    app = create_app()
    client = TestClient(app)

    # Setup mocks
    mock_get_current_user.return_value = mock_user
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    # Test the endpoint
    response = client.get("/api/resumes/1/personal")
    assert response.status_code == 200

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_update_personal_info_structured(
    fake_get_db,
    mock_get_current_user,
    mock_user,
    mock_resume,
):
    """Test the update personal info structured endpoint."""
    app = create_app()
    client = TestClient(app)

    # Setup mocks
    mock_get_current_user.return_value = mock_user
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    # Test the endpoint
    response = client.put(
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

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_get_education_info(fake_get_db, mock_get_current_user, mock_user, mock_resume):
    """Test the get education info endpoint."""
    app = create_app()
    client = TestClient(app)

    # Setup mocks
    mock_get_current_user.return_value = mock_user
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    # Test the endpoint
    response = client.get("/api/resumes/1/education")
    assert response.status_code == 200

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_update_education_info_structured(
    fake_get_db,
    mock_get_current_user,
    mock_user,
    mock_resume,
):
    """Test the update education info structured endpoint."""
    app = create_app()
    client = TestClient(app)

    # Setup mocks
    mock_get_current_user.return_value = mock_user
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    # Test the endpoint
    response = client.put(
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

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_get_experience_info(
    fake_get_db,
    mock_get_current_user,
    mock_user,
    mock_resume,
):
    """Test the get experience info endpoint."""
    app = create_app()
    client = TestClient(app)

    # Setup mocks
    mock_get_current_user.return_value = mock_user
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    # Test the endpoint
    response = client.get("/api/resumes/1/experience")
    assert response.status_code == 200

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_update_experience_info_structured(
    fake_get_db,
    mock_get_current_user,
    mock_user,
    mock_resume,
):
    """Test the update experience info structured endpoint."""
    app = create_app()
    client = TestClient(app)

    # Setup mocks
    mock_get_current_user.return_value = mock_user
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    # Test the endpoint
    response = client.put(
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

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_get_projects_info(fake_get_db, mock_get_current_user, mock_user, mock_resume):
    """Test the get projects info endpoint."""
    app = create_app()
    client = TestClient(app)

    # Setup mocks
    mock_get_current_user.return_value = mock_user
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    # Test the endpoint
    response = client.get("/api/resumes/1/projects")
    assert response.status_code == 200

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_update_projects_info_structured(
    fake_get_db,
    mock_get_current_user,
    mock_user,
    mock_resume,
):
    """Test the update projects info structured endpoint."""
    app = create_app()
    client = TestClient(app)

    # Setup mocks
    mock_get_current_user.return_value = mock_user
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    # Test the endpoint
    response = client.put(
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

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_get_certifications_info(
    fake_get_db,
    mock_get_current_user,
    mock_user,
    mock_resume,
):
    """Test the get certifications info endpoint."""
    app = create_app()
    client = TestClient(app)

    # Setup mocks
    mock_get_current_user.return_value = mock_user
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    # Test the endpoint
    response = client.get("/api/resumes/1/certifications")
    assert response.status_code == 200

    app.dependency_overrides.clear()


@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_update_certifications_info_structured(
    fake_get_db,
    mock_get_current_user,
    mock_user,
    mock_resume,
):
    """Test the update certifications info structured endpoint."""
    app = create_app()
    client = TestClient(app)

    # Setup mocks
    mock_get_current_user.return_value = mock_user
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    # Test the endpoint
    response = client.put(
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

    app.dependency_overrides.clear()
