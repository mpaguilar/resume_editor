from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from resume_editor.app.api.routes.resume import (
    get_current_user,
    get_db,
)
from resume_editor.app.main import create_app
from resume_editor.app.models.resume_model import Resume as DatabaseResume
from resume_editor.app.models.user import User as DBUser

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
