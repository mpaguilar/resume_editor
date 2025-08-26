from enum import Enum
from unittest.mock import ANY, Mock, patch

import pytest
from cryptography.fernet import InvalidToken
from fastapi import HTTPException
from fastapi.testclient import TestClient

from resume_editor.app.api.routes.resume import (
    get_current_user,
    get_db,
)
from resume_editor.app.api.routes.route_models import (
    CertificationsResponse,
    EducationResponse,
    ExperienceResponse,
    PersonalInfoResponse,
    RefineAction,
    RefineTargetSection,
)
from resume_editor.app.main import create_app
from resume_editor.app.models.resume_model import Resume as DatabaseResume
from resume_editor.app.models.user import User as DBUser
from resume_editor.app.models.user_settings import UserSettings

# A sample resume content for testing purposes.
TEST_RESUME_CONTENT = """
# Personal
## Contact Information
name: Test User
email: test@example.com
"""


VALID_MINIMAL_RESUME_CONTENT = """# Personal
## Contact Information
Name: Test Person
# Education
## Degrees
### Degree
School: A School
# Certifications
## Certification
Name: A Cert
# Experience
## Roles
### Role
#### Basics
Company: A Company
Title: A Role
Start date: 01/2024
"""


@pytest.fixture
def test_user():
    """Fixture for a test user."""
    user = DBUser(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
    )
    user.id = 1
    return user


@pytest.fixture
def test_resume(test_user):
    """Fixture for a test resume."""
    resume = DatabaseResume(
        user_id=test_user.id,
        name="Test Resume",
        content=TEST_RESUME_CONTENT,
    )
    resume.id = 1
    return resume


@pytest.fixture
def client_with_auth_and_resume(test_user, test_resume):
    """Fixture for a test client with an authenticated user and a resume."""
    app = create_app()

    mock_db = Mock()
    query_mock = mock_db.query.return_value
    filter_mock = query_mock.filter.return_value
    filter_mock.first.return_value = test_resume
    filter_mock.all.return_value = [test_resume]

    def get_mock_db_with_resume():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db_with_resume
    app.dependency_overrides[get_current_user] = lambda: test_user
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def client_with_auth_no_resume(test_user):
    """Fixture for a test client with an authenticated user but no resume."""
    app = create_app()

    mock_db = Mock()
    query_mock = mock_db.query.return_value
    filter_mock = query_mock.filter.return_value
    filter_mock.first.return_value = None
    filter_mock.all.return_value = []

    def get_mock_db_no_resume():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db_no_resume
    app.dependency_overrides[get_current_user] = lambda: test_user
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def client_with_last_resume(test_user, test_resume):
    """Fixture for deleting the last resume."""
    app = create_app()

    mock_db = Mock()
    query_mock = mock_db.query.return_value
    filter_mock = query_mock.filter.return_value
    filter_mock.first.return_value = test_resume
    # After delete, get_user_resumes returns an empty list
    filter_mock.all.return_value = []

    def get_mock_db_with_last_resume():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db_with_last_resume
    app.dependency_overrides[get_current_user] = lambda: test_user
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_delete_resume_htmx_no_remaining_resumes(client_with_last_resume):
    """Test deleting the last resume with HTMX returns the correct message."""
    # The fixture simulates that no resumes are left after deletion.
    response = client_with_last_resume.delete(
        "/api/resumes/1",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    assert "No resumes found" in response.text


@patch("resume_editor.app.api.routes.resume.get_user_resumes")
def test_delete_resume_htmx_with_remaining_resumes(
    mock_get_user_resumes,
    client_with_auth_and_resume,
    test_user,
):
    """Test deleting a resume with HTMX when other resumes remain."""
    remaining_resume = DatabaseResume(
        user_id=test_user.id,
        name="Another Resume",
        content="...",
    )
    remaining_resume.id = 2
    mock_get_user_resumes.return_value = [remaining_resume]

    response = client_with_auth_and_resume.delete(
        "/api/resumes/1",
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 200
    assert "Another Resume" in response.text
    assert "Test Resume" not in response.text
    mock_get_user_resumes.assert_called_once()


def test_delete_resume_no_htmx(client_with_auth_and_resume):
    """Test deleting a resume without HTMX returns JSON success message."""
    response = client_with_auth_and_resume.delete("/api/resumes/1")
    assert response.status_code == 200
    assert response.json() == {"message": "Resume deleted successfully"}


def test_update_resume_no_htmx(client_with_auth_and_resume, test_resume):
    """Test updating a resume without HTMX returns JSON success message."""
    response = client_with_auth_and_resume.put(
        "/api/resumes/1",
        json={"name": "Updated Name"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"


@patch("resume_editor.app.api.routes.resume.get_user_resumes")
def test_update_resume_htmx_with_remaining_resumes(
    mock_get_user_resumes,
    client_with_auth_and_resume,
    test_user,
    test_resume,
):
    """Test updating a resume with HTMX when other resumes remain."""
    updated_resume = DatabaseResume(
        user_id=test_user.id,
        name="Updated Resume",
        content=test_resume.content,
    )
    updated_resume.id = test_resume.id
    other_resume = DatabaseResume(
        user_id=test_user.id,
        name="Another Resume",
        content="...",
    )
    other_resume.id = 2
    mock_get_user_resumes.return_value = [updated_resume, other_resume]

    response = client_with_auth_and_resume.put(
        f"/api/resumes/{test_resume.id}",
        json={"name": "Updated Resume"},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    assert "Updated Resume" in response.text
    assert "Another Resume" in response.text

    import re

    divs = re.findall(r'(<div class="resume-item.*?</div>)', response.text, re.DOTALL)
    assert len(divs) == 2
    selected_divs = [d for d in divs if "selected" in d]
    unselected_divs = [d for d in divs if "selected" not in d]
    assert len(selected_divs) == 1
    assert len(unselected_divs) == 1
    assert "Updated Resume" in selected_divs[0]
    assert "Another Resume" in unselected_divs[0]


def test_list_resumes_no_htmx(client_with_auth_and_resume, test_resume):
    """Test listing resumes without HTMX returns JSON."""
    response = client_with_auth_and_resume.get("/api/resumes/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == test_resume.id
    assert data[0]["name"] == test_resume.name


def test_list_resumes_htmx_with_resumes(client_with_auth_and_resume, test_resume):
    """Test listing resumes with HTMX when resumes exist."""
    response = client_with_auth_and_resume.get(
        "/api/resumes/",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    assert test_resume.name in response.text
    assert "No resumes found" not in response.text


def test_list_resumes_htmx_no_resumes(client_with_auth_no_resume):
    """Test listing resumes with HTMX when no resumes exist."""
    response = client_with_auth_no_resume.get(
        "/api/resumes/",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    assert "No resumes found" in response.text


# Test cases for not found resume
@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/resumes/999/personal",
        "/api/resumes/999/education",
        "/api/resumes/999/experience",
        "/api/resumes/999/projects",
        "/api/resumes/999/certifications",
    ],
)
def test_get_info_not_found(client_with_auth_no_resume, endpoint):
    """Test GET endpoints return 404 for a non-existent resume."""
    response = client_with_auth_no_resume.get(endpoint)
    assert response.status_code == 404
    assert response.json() == {"detail": "Resume not found"}


@pytest.mark.parametrize(
    "endpoint, payload",
    [
        ("/api/resumes/999/personal", {"name": "test"}),
        (
            "/api/resumes/999/education",
            {"degrees": [{"school": "test", "degree": "BSc"}]},
        ),
        (
            "/api/resumes/999/experience",
            {
                "roles": [
                    {
                        "basics": {
                            "company": "test",
                            "title": "t",
                            "start_date": "2023-01-01T00:00:00",
                        },
                    },
                ],
            },
        ),
        (
            "/api/resumes/999/projects",
            {
                "projects": [
                    {
                        "overview": {
                            "title": "A Project",
                            "start_date": "2023-01-01T00:00:00",
                            "url": None,
                            "url_description": None,
                            "end_date": None,
                        },
                        "description": {"text": "A description of the project."},
                        "skills": {"skills": ["Python"]},
                    },
                ],
            },
        ),
        ("/api/resumes/999/certifications", {"certifications": [{"name": "test"}]}),
    ],
)
def test_update_info_not_found(client_with_auth_no_resume, endpoint, payload):
    """Test PUT endpoints return 404 for a non-existent resume."""
    response = client_with_auth_no_resume.put(endpoint, json=payload)
    assert response.status_code == 404
    assert response.json() == {"detail": "Resume not found"}


# Test cases for successful requests
def test_get_personal_info_success(client_with_auth_and_resume):
    """Test successful retrieval of personal info."""
    with patch(
        "resume_editor.app.api.routes.resume.extract_personal_info",
    ) as mock_extract:
        from resume_editor.app.api.routes.route_models import PersonalInfoResponse

        mock_extract.return_value = PersonalInfoResponse(name="Test User")
        response = client_with_auth_and_resume.get("/api/resumes/1/personal")
        assert response.status_code == 200
        assert response.json() == {
            "name": "Test User",
            "email": None,
            "phone": None,
            "location": None,
            "website": None,
            "github": None,
            "linkedin": None,
            "twitter": None,
            "work_authorization": None,
            "require_sponsorship": None,
            "banner": None,
            "note": None,
        }
        mock_extract.assert_called_once_with(TEST_RESUME_CONTENT)


@patch("resume_editor.app.api.routes.resume.update_resume_db")
@patch("resume_editor.app.api.routes.resume.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume.extract_experience_info")
@patch("resume_editor.app.api.routes.resume.extract_education_info")
def test_update_personal_info_structured_success(
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_pre_save_validation,
    mock_update_resume_db,
    client_with_auth_and_resume,
    test_resume,
):
    """Test successful update of personal info."""
    from resume_editor.app.api.routes.route_models import (
        CertificationsResponse,
        EducationResponse,
        ExperienceResponse,
        PersonalInfoResponse,
    )

    mock_extract_education.return_value = EducationResponse(degrees=[])
    mock_extract_experience.return_value = ExperienceResponse(roles=[], projects=[])
    mock_extract_certifications.return_value = CertificationsResponse(certifications=[])
    mock_build_sections.return_value = "new updated content"
    payload = {"name": "new name", "email": "new@email.com"}

    response = client_with_auth_and_resume.put(
        "/api/resumes/1/personal",
        json=payload,
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["name"] == "new name"
    assert response_data["email"] == "new@email.com"

    mock_extract_education.assert_called_once_with(TEST_RESUME_CONTENT)
    mock_extract_experience.assert_called_once_with(TEST_RESUME_CONTENT)
    mock_extract_certifications.assert_called_once_with(TEST_RESUME_CONTENT)

    mock_build_sections.assert_called_once()
    call_kwargs = mock_build_sections.call_args.kwargs
    assert isinstance(call_kwargs["personal_info"], PersonalInfoResponse)
    assert call_kwargs["personal_info"].name == "new name"
    assert call_kwargs["education"] == mock_extract_education.return_value
    assert call_kwargs["experience"] == mock_extract_experience.return_value
    assert call_kwargs["certifications"] == mock_extract_certifications.return_value

    mock_pre_save_validation.assert_called_once_with(
        "new updated content",
        TEST_RESUME_CONTENT,
    )

    mock_update_resume_db.assert_called_once()
    assert mock_update_resume_db.call_args.args[1] == test_resume
    assert mock_update_resume_db.call_args.kwargs["content"] == "new updated content"


@patch("resume_editor.app.api.routes.resume.update_resume_db")
@patch("resume_editor.app.api.routes.resume.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume.extract_experience_info")
@patch("resume_editor.app.api.routes.resume.extract_education_info")
def test_update_personal_info_structured_validation_error(
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_pre_save_validation,
    mock_update_resume_db,
    client_with_auth_and_resume,
):
    """Test that a validation error during structured update is handled."""
    from fastapi import HTTPException

    from resume_editor.app.api.routes.route_models import (
        CertificationsResponse,
        EducationResponse,
        ExperienceResponse,
    )

    mock_extract_education.return_value = EducationResponse(degrees=[])
    mock_extract_experience.return_value = ExperienceResponse(roles=[], projects=[])
    mock_extract_certifications.return_value = CertificationsResponse(certifications=[])
    mock_build_sections.return_value = "new updated content"
    mock_pre_save_validation.side_effect = HTTPException(
        status_code=422,
        detail="Validation failed",
    )

    response = client_with_auth_and_resume.put(
        "/api/resumes/1/personal",
        json={"name": "new name"},
    )

    assert response.status_code == 422
    expected_detail = "Failed to update resume due to reconstruction/validation error: Validation failed"
    assert response.json()["detail"] == expected_detail
    mock_extract_education.assert_called_once()
    mock_extract_experience.assert_called_once()
    mock_extract_certifications.assert_called_once()
    mock_build_sections.assert_called_once()
    mock_pre_save_validation.assert_called_once()
    mock_update_resume_db.assert_not_called()


def test_get_education_info_success(client_with_auth_and_resume):
    """Test successful retrieval of education info."""
    with patch(
        "resume_editor.app.api.routes.resume.extract_education_info",
    ) as mock_extract:
        from resume_editor.app.api.routes.route_models import EducationResponse

        mock_extract.return_value = EducationResponse(degrees=[])
        response = client_with_auth_and_resume.get("/api/resumes/1/education")
        assert response.status_code == 200
        assert response.json() == {"degrees": []}
        mock_extract.assert_called_once_with(TEST_RESUME_CONTENT)


@patch("resume_editor.app.api.routes.resume.update_resume_db")
@patch("resume_editor.app.api.routes.resume.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume.extract_experience_info")
@patch("resume_editor.app.api.routes.resume.extract_personal_info")
def test_update_education_info_structured_success(
    mock_extract_personal,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_pre_save_validation,
    mock_update_resume_db,
    client_with_auth_and_resume,
    test_resume,
):
    """Test successful update of education info."""
    from resume_editor.app.api.routes.route_models import (
        CertificationsResponse,
        EducationResponse,
        ExperienceResponse,
        PersonalInfoResponse,
    )

    mock_extract_personal.return_value = PersonalInfoResponse(name="Test User")
    mock_extract_experience.return_value = ExperienceResponse(roles=[], projects=[])
    mock_extract_certifications.return_value = CertificationsResponse(certifications=[])
    mock_build_sections.return_value = "new updated content"
    payload = {"degrees": [{"school": "new school", "degree": "BSc"}]}

    response = client_with_auth_and_resume.put(
        "/api/resumes/1/education",
        json=payload,
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["degrees"][0]["school"] == "new school"

    mock_extract_personal.assert_called_once_with(TEST_RESUME_CONTENT)
    mock_extract_experience.assert_called_once_with(TEST_RESUME_CONTENT)
    mock_extract_certifications.assert_called_once_with(TEST_RESUME_CONTENT)

    mock_build_sections.assert_called_once()
    call_kwargs = mock_build_sections.call_args.kwargs
    assert isinstance(call_kwargs["education"], EducationResponse)
    assert call_kwargs["education"].degrees[0].school == "new school"
    assert call_kwargs["personal_info"] == mock_extract_personal.return_value
    assert call_kwargs["experience"] == mock_extract_experience.return_value
    assert call_kwargs["certifications"] == mock_extract_certifications.return_value

    mock_pre_save_validation.assert_called_once_with(
        "new updated content",
        TEST_RESUME_CONTENT,
    )

    mock_update_resume_db.assert_called_once()
    assert mock_update_resume_db.call_args.args[1] == test_resume
    assert mock_update_resume_db.call_args.kwargs["content"] == "new updated content"


def test_get_experience_info_success(client_with_auth_and_resume):
    """Test successful retrieval of experience info."""
    with patch(
        "resume_editor.app.api.routes.resume.extract_experience_info",
    ) as mock_extract:
        from resume_editor.app.api.routes.route_models import ExperienceResponse

        mock_extract.return_value = ExperienceResponse(roles=[])
        response = client_with_auth_and_resume.get("/api/resumes/1/experience")
        assert response.status_code == 200
        assert response.json() == {"roles": [], "projects": []}
        mock_extract.assert_called_once_with(TEST_RESUME_CONTENT)


@patch("resume_editor.app.api.routes.resume.update_resume_db")
@patch("resume_editor.app.api.routes.resume.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume.extract_personal_info")
@patch("resume_editor.app.api.routes.resume.extract_education_info")
@patch("resume_editor.app.api.routes.resume.extract_experience_info")
@patch("resume_editor.app.api.routes.resume.extract_certifications_info")
def test_update_experience_info_structured_success(
    mock_extract_certifications,
    mock_extract_experience,
    mock_extract_education,
    mock_extract_personal,
    mock_build_sections,
    mock_pre_save_validation,
    mock_update_resume_db,
    client_with_auth_and_resume,
    test_resume,
):
    """Test successful update of experience info."""
    from resume_editor.app.api.routes.route_models import (
        CertificationsResponse,
        EducationResponse,
        ExperienceResponse,
        PersonalInfoResponse,
    )

    mock_extract_personal.return_value = PersonalInfoResponse(name="Test User")
    mock_extract_education.return_value = EducationResponse(degrees=[])
    mock_extract_certifications.return_value = CertificationsResponse(certifications=[])
    mock_extract_experience.return_value = ExperienceResponse(roles=[], projects=[])
    mock_build_sections.return_value = "new updated content"
    payload = {
        "roles": [
            {
                "basics": {
                    "company": "new co",
                    "title": "new title",
                    "start_date": "2023-01-01T00:00:00",
                },
            },
        ],
        "projects": [],
    }

    response = client_with_auth_and_resume.put(
        "/api/resumes/1/experience",
        json=payload,
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["roles"][0]["basics"]["company"] == "new co"

    mock_extract_personal.assert_called_once_with(TEST_RESUME_CONTENT)
    mock_extract_education.assert_called_once_with(TEST_RESUME_CONTENT)
    mock_extract_certifications.assert_called_once_with(TEST_RESUME_CONTENT)
    mock_extract_experience.assert_called_once_with(TEST_RESUME_CONTENT)

    mock_build_sections.assert_called_once()
    call_kwargs = mock_build_sections.call_args.kwargs
    assert isinstance(call_kwargs["experience"], ExperienceResponse)
    assert call_kwargs["experience"].roles[0].basics.company == "new co"
    assert call_kwargs["personal_info"] == mock_extract_personal.return_value
    assert call_kwargs["education"] == mock_extract_education.return_value
    assert call_kwargs["certifications"] == mock_extract_certifications.return_value

    mock_pre_save_validation.assert_called_once_with(
        "new updated content",
        TEST_RESUME_CONTENT,
    )

    mock_update_resume_db.assert_called_once()
    assert mock_update_resume_db.call_args.args[1] == test_resume
    assert mock_update_resume_db.call_args.kwargs["content"] == "new updated content"


def test_get_projects_info_success(client_with_auth_and_resume):
    """Test successful retrieval of projects info."""
    with patch(
        "resume_editor.app.api.routes.resume.extract_experience_info",
    ) as mock_extract:
        from resume_editor.app.api.routes.route_models import ExperienceResponse

        mock_extract.return_value = ExperienceResponse(roles=[], projects=[])
        response = client_with_auth_and_resume.get("/api/resumes/1/projects")
        assert response.status_code == 200
        assert response.json() == {"projects": []}
        mock_extract.assert_called_once_with(TEST_RESUME_CONTENT)


@patch("resume_editor.app.api.routes.resume.update_resume_db")
@patch("resume_editor.app.api.routes.resume.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume.extract_personal_info")
@patch("resume_editor.app.api.routes.resume.extract_education_info")
@patch("resume_editor.app.api.routes.resume.extract_experience_info")
@patch("resume_editor.app.api.routes.resume.extract_certifications_info")
def test_update_projects_info_structured_success(
    mock_extract_certifications,
    mock_extract_experience,
    mock_extract_education,
    mock_extract_personal,
    mock_build_sections,
    mock_pre_save_validation,
    mock_update_resume_db,
    client_with_auth_and_resume,
    test_resume,
):
    """Test successful update of projects info."""
    from resume_editor.app.api.routes.route_models import (
        CertificationsResponse,
        EducationResponse,
        ExperienceResponse,
        PersonalInfoResponse,
    )

    mock_extract_personal.return_value = PersonalInfoResponse(name="Test User")
    mock_extract_education.return_value = EducationResponse(degrees=[])
    mock_extract_experience.return_value = ExperienceResponse(roles=[], projects=[])
    mock_extract_certifications.return_value = CertificationsResponse(certifications=[])
    mock_build_sections.return_value = "new updated content"
    payload = {
        "projects": [
            {
                "overview": {
                    "title": "new title",
                    "start_date": "2024-01-01T00:00:00",
                    "url": None,
                    "url_description": None,
                    "end_date": None,
                },
                "description": {"text": "A new project."},
                "skills": {"skills": ["Skill 1"]},
            },
        ],
    }

    response = client_with_auth_and_resume.put(
        "/api/resumes/1/projects",
        json=payload,
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["projects"][0]["overview"]["title"] == "new title"
    assert response_data["projects"][0]["description"]["text"] == "A new project."

    mock_extract_personal.assert_called_once_with(TEST_RESUME_CONTENT)
    mock_extract_education.assert_called_once_with(TEST_RESUME_CONTENT)
    mock_extract_experience.assert_called_once_with(TEST_RESUME_CONTENT)
    mock_extract_certifications.assert_called_once_with(TEST_RESUME_CONTENT)

    mock_build_sections.assert_called_once()
    call_kwargs = mock_build_sections.call_args.kwargs
    assert call_kwargs["experience"].projects[0].overview.title == "new title"
    assert call_kwargs["experience"].projects[0].description.text == "A new project."
    # The roles should be preserved from the extracted experience.
    assert call_kwargs["experience"].roles == []
    assert call_kwargs["personal_info"] == mock_extract_personal.return_value
    assert call_kwargs["education"] == mock_extract_education.return_value
    assert call_kwargs["certifications"] == mock_extract_certifications.return_value

    mock_pre_save_validation.assert_called_once_with(
        "new updated content",
        TEST_RESUME_CONTENT,
    )

    mock_update_resume_db.assert_called_once()
    assert mock_update_resume_db.call_args.args[1] == test_resume
    assert mock_update_resume_db.call_args.kwargs["content"] == "new updated content"


def test_get_certifications_info_success(client_with_auth_and_resume):
    """Test successful retrieval of certifications info."""
    with patch(
        "resume_editor.app.api.routes.resume.extract_certifications_info",
    ) as mock_extract:
        from resume_editor.app.api.routes.route_models import CertificationsResponse

        mock_extract.return_value = CertificationsResponse(certifications=[])
        response = client_with_auth_and_resume.get("/api/resumes/1/certifications")
        assert response.status_code == 200
        assert response.json() == {"certifications": []}
        mock_extract.assert_called_once_with(TEST_RESUME_CONTENT)


@patch("resume_editor.app.api.routes.resume.update_resume_db")
@patch("resume_editor.app.api.routes.resume.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume.extract_personal_info")
@patch("resume_editor.app.api.routes.resume.extract_education_info")
@patch("resume_editor.app.api.routes.resume.extract_experience_info")
def test_update_certifications_info_structured_success(
    mock_extract_experience,
    mock_extract_education,
    mock_extract_personal,
    mock_build_sections,
    mock_pre_save_validation,
    mock_update_resume_db,
    client_with_auth_and_resume,
    test_resume,
):
    """Test successful update of certifications info."""
    from resume_editor.app.api.routes.route_models import (
        CertificationsResponse,
        EducationResponse,
        ExperienceResponse,
        PersonalInfoResponse,
    )

    mock_extract_personal.return_value = PersonalInfoResponse(name="Test User")
    mock_extract_education.return_value = EducationResponse(degrees=[])
    mock_extract_experience.return_value = ExperienceResponse(roles=[], projects=[])
    mock_build_sections.return_value = "new updated content"
    payload = {"certifications": [{"name": "new cert"}]}

    response = client_with_auth_and_resume.put(
        "/api/resumes/1/certifications",
        json=payload,
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["certifications"][0]["name"] == "new cert"

    mock_extract_personal.assert_called_once_with(TEST_RESUME_CONTENT)
    mock_extract_education.assert_called_once_with(TEST_RESUME_CONTENT)
    mock_extract_experience.assert_called_once_with(TEST_RESUME_CONTENT)

    mock_build_sections.assert_called_once()
    call_kwargs = mock_build_sections.call_args.kwargs
    assert isinstance(call_kwargs["certifications"], CertificationsResponse)
    assert call_kwargs["certifications"].certifications[0].name == "new cert"
    assert call_kwargs["personal_info"] == mock_extract_personal.return_value
    assert call_kwargs["education"] == mock_extract_education.return_value
    assert call_kwargs["experience"] == mock_extract_experience.return_value

    mock_pre_save_validation.assert_called_once_with(
        "new updated content",
        TEST_RESUME_CONTENT,
    )

    mock_update_resume_db.assert_called_once()
    assert mock_update_resume_db.call_args.args[1] == test_resume
    assert mock_update_resume_db.call_args.kwargs["content"] == "new updated content"


def test_get_resume(client_with_auth_and_resume, test_resume):
    """Test getting a resume with and without HTMX."""
    # Without HTMX (JSON)
    response = client_with_auth_and_resume.get(f"/api/resumes/{test_resume.id}")
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["id"] == test_resume.id
    assert json_response["name"] == test_resume.name
    assert json_response["content"] == test_resume.content

    # With HTMX (HTML)
    response = client_with_auth_and_resume.get(
        f"/api/resumes/{test_resume.id}",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    assert test_resume.name in response.text
    assert test_resume.content in response.text


@patch("resume_editor.app.api.routes.resume.get_user_resumes")
def test_create_resume(
    mock_get_user_resumes,
    client_with_auth_no_resume,
    test_user,
    test_resume,
):
    """Test creating a resume with and without HTMX."""
    app = client_with_auth_no_resume.app
    db_mock = next(app.dependency_overrides[get_db]())

    created_resume = DatabaseResume(
        user_id=test_user.id,
        name="New Resume",
        content=VALID_MINIMAL_RESUME_CONTENT,
    )
    created_resume.id = 2

    def mock_add(obj):
        obj.id = created_resume.id

    db_mock.add.side_effect = mock_add
    db_mock.commit.return_value = None

    def do_refresh(obj):
        obj.id = created_resume.id
        obj.name = created_resume.name
        obj.content = created_resume.content
        return None

    db_mock.refresh.side_effect = do_refresh

    # Test JSON response
    response = client_with_auth_no_resume.post(
        "/api/resumes/",
        json={"name": "New Resume", "content": VALID_MINIMAL_RESUME_CONTENT},
    )
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["name"] == "New Resume"
    assert json_response["id"] == 2

    # Test HTMX response
    mock_get_user_resumes.return_value = [test_resume, created_resume]
    response = client_with_auth_no_resume.post(
        "/api/resumes/",
        json={"name": "New Resume", "content": VALID_MINIMAL_RESUME_CONTENT},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    assert "New Resume" in response.text
    assert test_resume.name in response.text
    mock_get_user_resumes.assert_called_once()


@patch("resume_editor.app.api.routes.resume.update_resume_db")
@patch("resume_editor.app.api.routes.resume.extract_education_info")
def test_update_personal_info_reconstruction_error(
    mock_extract_education,
    mock_update_resume_db,
    client_with_auth_and_resume,
):
    """Test that a reconstruction error during structured update is handled."""
    mock_extract_education.side_effect = ValueError("Parsing failed")
    payload = {"name": "new name", "email": "new@email.com"}

    response = client_with_auth_and_resume.put(
        "/api/resumes/1/personal",
        json=payload,
    )

    assert response.status_code == 422
    assert "Parsing failed" in response.json()["detail"]
    mock_update_resume_db.assert_not_called()


@patch("resume_editor.app.api.routes.resume.ats_render")
@patch("resume_editor.app.api.routes.resume.plain_render")
@patch("resume_editor.app.api.routes.resume.basic_render")
@patch("resume_editor.app.api.routes.resume.Document")
def test_export_resume_docx(
    mock_docx_doc,
    mock_basic_render,
    mock_plain_render,
    mock_ats_render,
    client_with_auth_and_resume,
    test_resume,
):
    """Test DOCX export for all formats."""
    # Test ATS format
    response_ats = client_with_auth_and_resume.get(
        "/api/resumes/1/export/docx?format=ats",
    )
    assert response_ats.status_code == 200
    assert (
        response_ats.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert (
        response_ats.headers["content-disposition"]
        == f'attachment; filename="{test_resume.name}_ats.docx"'
    )
    mock_ats_render.assert_called_once()
    mock_plain_render.assert_not_called()
    mock_basic_render.assert_not_called()
    mock_ats_render.reset_mock()

    # Test PLAIN format
    response_plain = client_with_auth_and_resume.get(
        "/api/resumes/1/export/docx?format=plain",
    )
    assert response_plain.status_code == 200
    assert (
        response_plain.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert (
        response_plain.headers["content-disposition"]
        == f'attachment; filename="{test_resume.name}_plain.docx"'
    )
    mock_ats_render.assert_not_called()
    mock_plain_render.assert_called_once()
    mock_basic_render.assert_not_called()
    mock_plain_render.reset_mock()

    # Test EXECUTIVE format
    response_exec = client_with_auth_and_resume.get(
        "/api/resumes/1/export/docx?format=executive",
    )
    assert response_exec.status_code == 200
    assert (
        response_exec.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert (
        response_exec.headers["content-disposition"]
        == f'attachment; filename="{test_resume.name}_executive.docx"'
    )
    mock_ats_render.assert_not_called()
    mock_plain_render.assert_not_called()
    mock_basic_render.assert_called_once()

    # Check if settings were modified for executive
    settings_arg = mock_basic_render.call_args[0][2]
    assert settings_arg.executive_summary is True
    assert settings_arg.skills_matrix is True


def test_export_resume_docx_invalid_format(client_with_auth_and_resume):
    """Test DOCX export with an invalid format."""
    response = client_with_auth_and_resume.get(
        "/api/resumes/1/export/docx?format=invalid_format",
    )
    assert response.status_code == 422


def test_export_resume_docx_not_found(client_with_auth_no_resume):
    """Test DOCX export for a resume that is not found."""
    response = client_with_auth_no_resume.get(
        "/api/resumes/999/export/docx?format=plain",
    )
    assert response.status_code == 404


@patch("resume_editor.app.api.routes.resume.plain_render")
@patch("resume_editor.app.api.routes.resume.Document")
def test_export_resume_docx_with_leading_content(
    mock_doc,
    mock_plain_render,
    client_with_auth_and_resume,
    test_resume,
):
    """Test docx export with leading content before the first valid header."""
    test_resume.content = (
        "Some junk text\n## A subheading\n# Invalid Header\n" + TEST_RESUME_CONTENT
    )

    response = client_with_auth_and_resume.get(
        "/api/resumes/1/export/docx?format=plain",
    )
    assert response.status_code == 200
    mock_plain_render.assert_called_once()
    # Ensure the parser still managed to get the right content
    parsed_resume = mock_plain_render.call_args[0][1]
    assert parsed_resume.personal.contact_info.name == "Test User"


@patch("resume_editor.app.api.routes.resume.plain_render")
@patch("resume_editor.app.api.routes.resume.Document")
def test_export_resume_docx_unparseable_content(
    mock_doc,
    mock_plain_render,
    client_with_auth_and_resume,
    test_resume,
):
    """Test that docx export fails for unparseable Markdown content."""
    # This content has no valid headers, so parsing will fail.
    test_resume.content = "this is not a valid resume"

    response = client_with_auth_and_resume.get(
        "/api/resumes/1/export/docx?format=plain",
    )

    assert response.status_code == 422
    assert "Invalid resume format" in response.json()["detail"]
    mock_plain_render.assert_not_called()


def test_export_resume_markdown_success(client_with_auth_and_resume, test_resume):
    """Test successful export of a resume as Markdown."""
    response = client_with_auth_and_resume.get(
        f"/api/resumes/{test_resume.id}/export/markdown",
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/markdown; charset=utf-8"
    assert (
        response.headers["content-disposition"]
        == f'attachment; filename="{test_resume.name}.md"'
    )
    assert response.text == test_resume.content


def test_export_resume_markdown_not_found(client_with_auth_no_resume):
    """Test exporting a non-existent resume returns 404."""
    response = client_with_auth_no_resume.get("/api/resumes/999/export/markdown")
    assert response.status_code == 404


@patch("resume_editor.app.api.routes.resume.update_resume_db")
@patch("resume_editor.app.api.routes.resume.extract_personal_info")
def test_update_education_info_reconstruction_error(
    mock_extract_personal,
    mock_update_resume_db,
    client_with_auth_and_resume,
):
    """Test that a reconstruction error during education update is handled."""
    mock_extract_personal.side_effect = ValueError("Parsing failed")
    payload = {"degrees": [{"school": "new school", "degree": "BSc"}]}

    response = client_with_auth_and_resume.put(
        "/api/resumes/1/education",
        json=payload,
    )

    assert response.status_code == 422
    assert "Parsing failed" in response.json()["detail"]
    mock_update_resume_db.assert_not_called()


@patch("resume_editor.app.api.routes.resume.update_resume_db")
@patch("resume_editor.app.api.routes.resume.extract_personal_info")
def test_update_experience_info_reconstruction_error(
    mock_extract_personal,
    mock_update_resume_db,
    client_with_auth_and_resume,
):
    """Test that a reconstruction error during experience update is handled."""
    mock_extract_personal.side_effect = ValueError("Parsing failed")
    payload = {
        "roles": [
            {
                "basics": {
                    "company": "new co",
                    "title": "new title",
                    "start_date": "2023-01-01T00:00:00",
                },
            },
        ],
    }

    response = client_with_auth_and_resume.put(
        "/api/resumes/1/experience",
        json=payload,
    )

    assert response.status_code == 422
    assert "Parsing failed" in response.json()["detail"]
    mock_update_resume_db.assert_not_called()


@patch("resume_editor.app.api.routes.resume.update_resume_db")
@patch("resume_editor.app.api.routes.resume.extract_personal_info")
def test_update_projects_info_reconstruction_error(
    mock_extract_personal,
    mock_update_resume_db,
    client_with_auth_and_resume,
):
    """Test that a reconstruction error during projects update is handled."""
    mock_extract_personal.side_effect = ValueError("Parsing failed")
    payload = {
        "projects": [
            {
                "overview": {
                    "title": "new title",
                    "start_date": "2024-01-01T00:00:00",
                    "url": None,
                    "url_description": None,
                    "end_date": None,
                },
                "description": {"text": "A new project."},
                "skills": {"skills": ["Skill 1"]},
            },
        ],
    }

    response = client_with_auth_and_resume.put(
        "/api/resumes/1/projects",
        json=payload,
    )

    assert response.status_code == 422
    assert "Parsing failed" in response.json()["detail"]
    mock_update_resume_db.assert_not_called()


@patch("resume_editor.app.api.routes.resume.update_resume_db")
@patch("resume_editor.app.api.routes.resume.extract_personal_info")
def test_update_certifications_info_reconstruction_error(
    mock_extract_personal,
    mock_update_resume_db,
    client_with_auth_and_resume,
):
    """Test that a reconstruction error during certifications update is handled."""
    mock_extract_personal.side_effect = ValueError("Parsing failed")
    payload = {"certifications": [{"name": "new cert"}]}

    response = client_with_auth_and_resume.put(
        "/api/resumes/1/certifications",
        json=payload,
    )

    assert response.status_code == 422
    assert "Parsing failed" in response.json()["detail"]
    mock_update_resume_db.assert_not_called()


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.resume.Document")
async def test_export_resume_docx_unhandled_format_safeguard(mock_doc):
    """Test that the case _ safeguard is hit for unhandled DocxFormat members."""
    from resume_editor.app.api.routes.resume import (
        export_resume_docx,
    )

    class PatchedDocxFormat(str, Enum):
        ATS = "ats"
        PLAIN = "plain"
        EXECUTIVE = "executive"
        UNHANDLED = "unhandled"

    mock_resume = Mock(spec=DatabaseResume)
    mock_resume.name = "Test Resume"
    mock_resume.content = VALID_MINIMAL_RESUME_CONTENT

    with patch(
        "resume_editor.app.api.routes.resume.DocxFormat",
        PatchedDocxFormat,
    ):
        with pytest.raises(HTTPException) as excinfo:
            await export_resume_docx(
                format=PatchedDocxFormat.UNHANDLED,
                resume=mock_resume,
            )
        assert excinfo.value.status_code == 400
        assert excinfo.value.detail == "Invalid format specified"


@patch("resume_editor.app.api.routes.resume.refine_resume_section_with_llm")
@patch("resume_editor.app.api.routes.resume.decrypt_data")
@patch("resume_editor.app.api.routes.resume.get_user_settings")
def test_refine_resume_success_with_key(
    mock_get_user_settings,
    mock_decrypt_data,
    mock_refine_llm,
    client_with_auth_and_resume,
    test_user,
):
    """Test successful resume refinement when user has settings and API key."""
    # Arrange
    mock_db_session = next(
        client_with_auth_and_resume.app.dependency_overrides[get_db](),
    )

    mock_settings = UserSettings(
        user_id=test_user.id,
        llm_endpoint="http://llm.test",
        encrypted_api_key="key",
    )
    mock_get_user_settings.return_value = mock_settings
    mock_decrypt_data.return_value = "decrypted_key"
    mock_refine_llm.return_value = "refined"

    # Act
    response = client_with_auth_and_resume.post(
        "/api/resumes/1/refine",
        data={"job_description": "job", "target_section": "experience"},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"refined_content": "refined"}
    mock_get_user_settings.assert_called_once_with(mock_db_session, test_user.id)
    mock_decrypt_data.assert_called_once_with("key")
    mock_refine_llm.assert_called_once_with(
        resume_content=TEST_RESUME_CONTENT,
        job_description="job",
        target_section="experience",
        llm_endpoint="http://llm.test",
        api_key="decrypted_key",
    )


@patch("resume_editor.app.api.routes.resume.refine_resume_section_with_llm")
@patch("resume_editor.app.api.routes.resume.get_user_settings")
def test_refine_resume_no_settings(
    mock_get_user_settings,
    mock_refine_llm,
    client_with_auth_and_resume,
    test_user,
):
    """Test resume refinement when user has no settings."""
    # Arrange
    mock_db_session = next(
        client_with_auth_and_resume.app.dependency_overrides[get_db](),
    )
    mock_get_user_settings.return_value = None
    mock_refine_llm.return_value = "refined"

    # Act
    response = client_with_auth_and_resume.post(
        "/api/resumes/1/refine",
        data={"job_description": "job", "target_section": "experience"},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"refined_content": "refined"}
    mock_get_user_settings.assert_called_once_with(mock_db_session, test_user.id)
    mock_refine_llm.assert_called_once_with(
        resume_content=TEST_RESUME_CONTENT,
        job_description="job",
        target_section="experience",
        llm_endpoint=None,
        api_key=None,
    )


@patch("resume_editor.app.api.routes.resume.refine_resume_section_with_llm")
@patch("resume_editor.app.api.routes.resume.get_user_settings")
def test_refine_resume_no_api_key(
    mock_get_user_settings,
    mock_refine_llm,
    client_with_auth_and_resume,
    test_user,
):
    """Test resume refinement when user settings exist but have no API key."""
    # Arrange
    mock_settings = UserSettings(user_id=test_user.id, llm_endpoint="http://llm.test")
    mock_settings.encrypted_api_key = None
    mock_get_user_settings.return_value = mock_settings
    mock_refine_llm.return_value = "refined"

    # Act
    response = client_with_auth_and_resume.post(
        "/api/resumes/1/refine",
        data={"job_description": "job", "target_section": "experience"},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"refined_content": "refined"}
    mock_refine_llm.assert_called_once_with(
        resume_content=TEST_RESUME_CONTENT,
        job_description="job",
        target_section="experience",
        llm_endpoint="http://llm.test",
        api_key=None,
    )


@patch("resume_editor.app.api.routes.resume.refine_resume_section_with_llm")
@patch("resume_editor.app.api.routes.resume.get_user_settings")
def test_refine_resume_llm_failure(
    mock_get_user_settings,
    mock_refine_llm,
    client_with_auth_and_resume,
):
    """Test resume refinement when the LLM call fails."""
    # Arrange
    mock_get_user_settings.return_value = None
    mock_refine_llm.side_effect = Exception("LLM call failed")

    # Act
    response = client_with_auth_and_resume.post(
        "/api/resumes/1/refine",
        data={"job_description": "job", "target_section": "experience"},
    )

    # Assert
    assert response.status_code == 500
    assert response.json() == {"detail": "LLM refinement failed: LLM call failed"}


@patch("resume_editor.app.api.routes.resume.refine_resume_section_with_llm")
@patch("resume_editor.app.api.routes.resume.decrypt_data")
@patch("resume_editor.app.api.routes.resume.get_user_settings")
def test_refine_resume_decryption_failure(
    mock_get_user_settings,
    mock_decrypt_data,
    mock_refine_llm,
    client_with_auth_and_resume,
    test_user,
):
    """Test resume refinement when API key decryption fails."""
    # Arrange
    mock_settings = UserSettings(
        user_id=test_user.id,
        llm_endpoint="http://llm.test",
        encrypted_api_key="key",
    )
    mock_get_user_settings.return_value = mock_settings
    mock_decrypt_data.side_effect = InvalidToken

    # Act
    response = client_with_auth_and_resume.post(
        "/api/resumes/1/refine",
        data={"job_description": "job", "target_section": "experience"},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Invalid API key. Please update your settings.",
    }
    mock_get_user_settings.assert_called_once()
    mock_decrypt_data.assert_called_once_with("key")
    mock_refine_llm.assert_not_called()


def test_refine_resume_invalid_section(client_with_auth_and_resume, test_resume):
    """Test that providing an invalid section to the refine endpoint fails."""
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine",
        data={"job_description": "job", "target_section": "invalid_section"},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["detail"][0]["type"] == "enum"
    assert body["detail"][0]["input"] == "invalid_section"
    assert "Input should be" in body["detail"][0]["msg"]


@patch("resume_editor.app.api.routes.resume.refine_resume_section_with_llm")
@patch("resume_editor.app.api.routes.resume.get_user_settings", return_value=None)
def test_refine_resume_htmx_response(
    mock_get_user_settings,
    mock_refine_llm,
    client_with_auth_and_resume,
):
    """Test that the /refine endpoint returns HTML for an HTMX request."""
    # Arrange
    mock_refine_llm.return_value = "## <Refined> Experience"

    # Act
    response = client_with_auth_and_resume.post(
        "/api/resumes/1/refine",
        data={"job_description": "job", "target_section": "experience"},
        headers={"HX-Request": "true"},
    )

    # Assert
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "AI Refinement Suggestion" in response.text
    assert "## &lt;Refined&gt; Experience" in response.text
    assert 'hx-post="/api/resumes/1/refine/accept"' in response.text
    # Ensure the textarea is editable
    assert "readonly" not in response.text


@patch("resume_editor.app.api.routes.resume.refine_resume_section_with_llm")
@patch("resume_editor.app.api.routes.resume.get_user_settings", return_value=None)
def test_refine_resume_no_htmx_response(
    mock_get_user_settings,
    mock_refine_llm,
    client_with_auth_and_resume,
):
    """Test that the /refine endpoint returns JSON for a non-HTMX request."""
    # Arrange
    mock_refine_llm.return_value = "## Refined Experience"

    # Act
    response = client_with_auth_and_resume.post(
        "/api/resumes/1/refine",
        data={"job_description": "job", "target_section": "experience"},
    )

    # Assert
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {"refined_content": "## Refined Experience"}


@patch("resume_editor.app.api.routes.resume.get_user_resumes")
@patch("resume_editor.app.api.routes.resume.create_resume_db")
@patch("resume_editor.app.api.routes.resume.update_resume_db")
@patch("resume_editor.app.api.routes.resume.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume.extract_experience_info")
@patch("resume_editor.app.api.routes.resume.extract_education_info")
@patch("resume_editor.app.api.routes.resume.extract_personal_info")
def test_accept_refined_resume_overwrite_personal(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_pre_save,
    mock_update_db,
    mock_create_db,
    mock_get_resumes,
    client_with_auth_and_resume,
    test_resume,
):
    """Test accepting a 'personal' refinement and overwriting the existing resume."""
    # Arrange
    refined_content = "# Personal\nname: Refined"
    mock_extract_personal.return_value = PersonalInfoResponse(name="Refined")
    mock_build_sections.return_value = "reconstructed content"
    mock_get_resumes.return_value = [test_resume]

    # Act
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/accept",
        data={
            "refined_content": refined_content,
            "target_section": RefineTargetSection.PERSONAL.value,
            "action": RefineAction.OVERWRITE.value,
        },
    )

    # Assert
    assert response.status_code == 200
    mock_extract_personal.assert_called_once_with(refined_content)
    mock_extract_education.assert_called_once_with(test_resume.content)
    mock_extract_experience.assert_called_once_with(test_resume.content)
    mock_extract_certifications.assert_called_once_with(test_resume.content)
    mock_build_sections.assert_called_once()
    assert mock_build_sections.call_args.kwargs["personal_info"].name == "Refined"
    mock_pre_save.assert_called_once_with("reconstructed content", test_resume.content)
    mock_update_db.assert_called_once()
    assert mock_update_db.call_args.kwargs["content"] == "reconstructed content"
    mock_create_db.assert_not_called()


@patch("resume_editor.app.api.routes.resume.get_user_resumes")
@patch("resume_editor.app.api.routes.resume.create_resume_db")
@patch("resume_editor.app.api.routes.resume.update_resume_db")
@patch("resume_editor.app.api.routes.resume.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume.extract_experience_info")
@patch("resume_editor.app.api.routes.resume.extract_education_info")
@patch("resume_editor.app.api.routes.resume.extract_personal_info")
def test_accept_refined_resume_overwrite_education(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_pre_save,
    mock_update_db,
    mock_create_db,
    mock_get_resumes,
    client_with_auth_and_resume,
    test_resume,
):
    """Test accepting an 'education' refinement and overwriting the resume."""
    refined_content = "# Education\n..."
    mock_extract_education.return_value = EducationResponse(degrees=[])
    client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/accept",
        data={
            "refined_content": refined_content,
            "target_section": RefineTargetSection.EDUCATION.value,
            "action": RefineAction.OVERWRITE.value,
        },
    )
    mock_extract_education.assert_called_once_with(refined_content)
    mock_extract_personal.assert_called_once_with(test_resume.content)


@patch("resume_editor.app.api.routes.resume.get_user_resumes")
@patch("resume_editor.app.api.routes.resume.create_resume_db")
@patch("resume_editor.app.api.routes.resume.update_resume_db")
@patch("resume_editor.app.api.routes.resume.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume.extract_experience_info")
@patch("resume_editor.app.api.routes.resume.extract_education_info")
@patch("resume_editor.app.api.routes.resume.extract_personal_info")
def test_accept_refined_resume_overwrite_experience(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_pre_save,
    mock_update_db,
    mock_create_db,
    mock_get_resumes,
    client_with_auth_and_resume,
    test_resume,
):
    """Test accepting an 'experience' refinement and overwriting the resume."""
    refined_content = "# Experience\n..."
    mock_extract_experience.return_value = ExperienceResponse(roles=[], projects=[])
    client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/accept",
        data={
            "refined_content": refined_content,
            "target_section": RefineTargetSection.EXPERIENCE.value,
            "action": RefineAction.OVERWRITE.value,
        },
    )
    mock_extract_experience.assert_called_once_with(refined_content)
    mock_extract_personal.assert_called_once_with(test_resume.content)


@patch("resume_editor.app.api.routes.resume.get_user_resumes")
@patch("resume_editor.app.api.routes.resume.create_resume_db")
@patch("resume_editor.app.api.routes.resume.update_resume_db")
@patch("resume_editor.app.api.routes.resume.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume.extract_experience_info")
@patch("resume_editor.app.api.routes.resume.extract_education_info")
@patch("resume_editor.app.api.routes.resume.extract_personal_info")
def test_accept_refined_resume_overwrite_certifications(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_pre_save,
    mock_update_db,
    mock_create_db,
    mock_get_resumes,
    client_with_auth_and_resume,
    test_resume,
):
    """Test accepting a 'certifications' refinement and overwriting the resume."""
    refined_content = "# Certifications\n..."
    mock_extract_certifications.return_value = CertificationsResponse(certifications=[])
    client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/accept",
        data={
            "refined_content": refined_content,
            "target_section": RefineTargetSection.CERTIFICATIONS.value,
            "action": RefineAction.OVERWRITE.value,
        },
    )
    mock_extract_certifications.assert_called_once_with(refined_content)
    mock_extract_personal.assert_called_once_with(test_resume.content)


@patch("resume_editor.app.api.routes.resume.get_user_resumes")
@patch("resume_editor.app.api.routes.resume.create_resume_db")
@patch("resume_editor.app.api.routes.resume.update_resume_db")
@patch("resume_editor.app.api.routes.resume.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume.extract_experience_info")
@patch("resume_editor.app.api.routes.resume.extract_education_info")
@patch("resume_editor.app.api.routes.resume.extract_personal_info")
def test_accept_refined_resume_overwrite_full(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_pre_save,
    mock_update_db,
    mock_create_db,
    mock_get_resumes,
    client_with_auth_and_resume,
    test_resume,
):
    """Test accepting a 'full' refinement and overwriting the existing resume."""
    # Arrange
    refined_content = "# Personal\nname: Full Refined"
    mock_get_resumes.return_value = [test_resume]

    # Act
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/accept",
        data={
            "refined_content": refined_content,
            "target_section": RefineTargetSection.FULL.value,
            "action": RefineAction.OVERWRITE.value,
        },
    )

    # Assert
    assert response.status_code == 200
    mock_extract_personal.assert_not_called()
    mock_extract_education.assert_not_called()
    mock_extract_experience.assert_not_called()
    mock_extract_certifications.assert_not_called()
    mock_build_sections.assert_not_called()

    mock_pre_save.assert_called_once_with(refined_content, test_resume.content)
    mock_update_db.assert_called_once()
    assert mock_update_db.call_args.kwargs["content"] == refined_content
    mock_create_db.assert_not_called()
    mock_get_resumes.assert_called_once()


@patch("resume_editor.app.api.routes.resume.get_user_resumes")
@patch("resume_editor.app.api.routes.resume.create_resume_db")
@patch("resume_editor.app.api.routes.resume.update_resume_db")
@patch("resume_editor.app.api.routes.resume.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume.extract_experience_info")
@patch("resume_editor.app.api.routes.resume.extract_education_info")
@patch("resume_editor.app.api.routes.resume.extract_personal_info")
def test_accept_refined_resume_save_as_new(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_pre_save,
    mock_update_db,
    mock_create_db,
    mock_get_resumes,
    client_with_auth_and_resume,
    test_user,
    test_resume,
):
    """Test accepting a 'full' refinement and saving it as a new resume."""
    # Arrange
    refined_content = "# Personal\n..."
    new_resume = DatabaseResume(
        user_id=test_user.id,
        name="New Name",
        content=refined_content,
    )
    new_resume.id = 2
    mock_create_db.return_value = new_resume
    mock_get_resumes.return_value = [test_resume, new_resume]

    # Act
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/accept",
        data={
            "refined_content": refined_content,
            "target_section": RefineTargetSection.FULL.value,
            "action": RefineAction.SAVE_AS_NEW.value,
            "new_resume_name": "New Name",
        },
    )

    # Assert
    assert response.status_code == 200
    mock_pre_save.assert_called_once_with(refined_content, test_resume.content)
    mock_build_sections.assert_not_called()
    mock_extract_personal.assert_not_called()
    mock_extract_education.assert_not_called()
    mock_extract_experience.assert_not_called()
    mock_extract_certifications.assert_not_called()
    mock_update_db.assert_not_called()
    mock_create_db.assert_called_once_with(
        db=ANY,
        user_id=test_user.id,
        name="New Name",
        content=refined_content,
    )
    mock_get_resumes.assert_called_once()
    assert "New Name" in response.text

    import re

    divs = re.findall(r'(<div class="resume-item.*?</div>)', response.text, re.DOTALL)
    assert len(divs) == 2
    selected_divs = [d for d in divs if "selected" in d]
    assert len(selected_divs) == 1
    assert "New Name" in selected_divs[0]
    assert 'onclick="selectResume(2, this)"' in selected_divs[0]


@patch("resume_editor.app.api.routes.resume.get_user_resumes")
@patch("resume_editor.app.api.routes.resume.create_resume_db")
@patch("resume_editor.app.api.routes.resume.update_resume_db")
@patch("resume_editor.app.api.routes.resume.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume.extract_experience_info")
@patch("resume_editor.app.api.routes.resume.extract_education_info")
@patch("resume_editor.app.api.routes.resume.extract_personal_info")
def test_accept_refined_resume_save_as_new_partial(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_pre_save,
    mock_update_db,
    mock_create_db,
    mock_get_resumes,
    client_with_auth_and_resume,
    test_user,
    test_resume,
):
    """Test accepting a partial refinement and saving it as a new resume."""
    # Arrange
    refined_content = "# Personal\nname: Refined New"
    reconstructed_content = "reconstructed content for new resume"

    mock_extract_personal.return_value = PersonalInfoResponse(name="Refined New")
    mock_build_sections.return_value = reconstructed_content

    new_resume = DatabaseResume(
        user_id=test_user.id, name="New Name", content=reconstructed_content
    )
    new_resume.id = 2
    mock_create_db.return_value = new_resume
    mock_get_resumes.return_value = [test_resume, new_resume]

    # Act
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/accept",
        data={
            "refined_content": refined_content,
            "target_section": RefineTargetSection.PERSONAL.value,
            "action": RefineAction.SAVE_AS_NEW.value,
            "new_resume_name": "New Name",
        },
    )

    # Assert
    assert response.status_code == 200
    mock_extract_personal.assert_called_once_with(refined_content)
    mock_extract_education.assert_called_once_with(test_resume.content)
    mock_build_sections.assert_called_once()
    mock_pre_save.assert_called_once_with(reconstructed_content, test_resume.content)
    mock_update_db.assert_not_called()
    mock_create_db.assert_called_once_with(
        db=ANY,
        user_id=test_user.id,
        name="New Name",
        content=reconstructed_content,
    )


@patch("resume_editor.app.api.routes.resume.extract_personal_info")
def test_accept_refined_resume_reconstruction_error(
    mock_extract_personal,
    client_with_auth_and_resume,
    test_resume,
):
    """Test that an error during reconstruction is handled."""
    # Arrange
    mock_extract_personal.side_effect = ValueError("test error")
    refined_content = "# Personal\nname: Refined"

    # Act
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/accept",
        data={
            "refined_content": refined_content,
            "target_section": RefineTargetSection.PERSONAL.value,
            "action": RefineAction.OVERWRITE.value,
        },
    )

    # Assert
    assert response.status_code == 422
    assert "Failed to reconstruct" in response.json()["detail"]


def test_accept_refined_resume_save_as_new_no_name(
    client_with_auth_and_resume, test_resume
):
    """Test that saving as new without a name fails."""
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/accept",
        data={
            "refined_content": "...",
            "target_section": RefineTargetSection.FULL.value,
            "action": RefineAction.SAVE_AS_NEW.value,
        },
    )
    assert response.status_code == 400
    assert "New resume name is required" in response.json()["detail"]


def test_accept_refined_resume_invalid_action(client_with_auth_and_resume, test_resume):
    """Test that providing an invalid action to the accept endpoint fails."""
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/accept",
        data={
            "refined_content": "content",
            "target_section": "full",
            "action": "invalid_action",
        },
    )
    assert response.status_code == 422
    body = response.json()
    assert body["detail"][0]["type"] == "enum"
    assert body["detail"][0]["input"] == "invalid_action"
    assert "Input should be 'overwrite' or 'save_as_new'" in body["detail"][0]["msg"]


def test_accept_refined_resume_invalid_section(
    client_with_auth_and_resume, test_resume
):
    """Test that providing an invalid section to the accept endpoint fails."""
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/accept",
        data={
            "refined_content": "content",
            "target_section": "invalid_section",
            "action": "overwrite",
        },
    )
    assert response.status_code == 422
    body = response.json()
    assert body["detail"][0]["type"] == "enum"
    assert body["detail"][0]["input"] == "invalid_section"
    assert (
        "Input should be 'full', 'personal', 'education', 'experience' or 'certifications'"
        in body["detail"][0]["msg"]
    )


def test_generate_resume_list_html_empty():
    """Test that _generate_resume_list_html returns the correct message for an empty list."""
    from resume_editor.app.api.routes.resume import _generate_resume_list_html

    html = _generate_resume_list_html([], None)
    assert "No resumes found" in html
    assert "Create your first resume" in html


def test_generate_resume_list_html_no_selection():
    """Test that _generate_resume_list_html correctly handles no selection."""
    from resume_editor.app.api.routes.resume import _generate_resume_list_html

    r1 = DatabaseResume(user_id=1, name="R1", content="")
    r1.id = 1
    r2 = DatabaseResume(user_id=1, name="R2", content="")
    r2.id = 2
    resumes = [r1, r2]
    html = _generate_resume_list_html(resumes, None)
    assert "R1" in html
    assert "R2" in html
    assert "selected" not in html


def test_generate_resume_list_html_with_selection():
    """Test that _generate_resume_list_html correctly marks an item as selected."""
    from resume_editor.app.api.routes.resume import _generate_resume_list_html
    import re

    r1 = DatabaseResume(user_id=1, name="R1", content="c1")
    r1.id = 1
    r2 = DatabaseResume(user_id=1, name="R2", content="c2")
    r2.id = 2
    resumes = [r1, r2]
    html = _generate_resume_list_html(resumes, 2)

    divs = re.findall(r'(<div class="resume-item.*?</div>)', html, re.DOTALL)
    assert len(divs) == 2
    selected_divs = [d for d in divs if "selected" in d]
    unselected_divs = [d for d in divs if "selected" not in d]
    assert len(selected_divs) == 1
    assert len(unselected_divs) == 1
    assert "R2" in selected_divs[0]
    assert "R1" in unselected_divs[0]
