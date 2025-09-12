import datetime
from enum import Enum
from unittest.mock import ANY, MagicMock, Mock, patch

import pytest
from cryptography.fernet import InvalidToken
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from openai import AuthenticationError
from sqlalchemy.orm import Session

from resume_editor.app.api.routes.route_models import (
    CertificationsResponse,
    EducationResponse,
    ExperienceResponse,
    PersonalInfoResponse,
    RefineAction,
    RefineTargetSection,
)
from resume_editor.app.core.auth import get_current_user_from_cookie
from resume_editor.app.core.config import get_settings
from resume_editor.app.database.database import get_db
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


REFINED_VALID_MINIMAL_RESUME_CONTENT = """# Personal

## Contact Information

Name: Refined Test Person

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
        content=VALID_MINIMAL_RESUME_CONTENT,
    )
    resume.id = 1
    return resume


@pytest.fixture
def app():
    """Fixture to create a new app for each test."""
    get_settings.cache_clear()
    _app = create_app()
    yield _app
    _app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    """Fixture to create a test client for each test."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def client_with_auth_and_resume(app, client, test_user, test_resume):
    """Fixture for a test client with an authenticated user and a resume."""
    mock_db = Mock()
    query_mock = Mock()
    filter_mock = Mock()
    filter_mock.first.return_value = test_resume
    filter_mock.all.return_value = [test_resume]
    query_mock.filter.return_value = filter_mock
    mock_db.query.return_value = query_mock

    def get_mock_db_with_resume():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db_with_resume
    app.dependency_overrides[get_current_user_from_cookie] = lambda: test_user
    return client


@pytest.fixture
def client_with_auth_no_resume(app, client, test_user):
    """Fixture for a test client with an authenticated user but no resume."""
    mock_db = Mock()
    query_mock = Mock()
    filter_mock = Mock()
    filter_mock.first.return_value = None
    filter_mock.all.return_value = []
    query_mock.filter.return_value = filter_mock
    mock_db.query.return_value = query_mock

    def get_mock_db_no_resume():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db_no_resume
    app.dependency_overrides[get_current_user_from_cookie] = lambda: test_user
    return client


@pytest.fixture
def client_with_last_resume(app, client, test_user, test_resume):
    """Fixture for deleting the last resume."""
    mock_db = Mock()
    query_mock = Mock()
    filter_mock = Mock()
    # For get_resume_by_id_and_user to find the resume to delete
    filter_mock.first.return_value = test_resume
    # For get_user_resumes which is called after deletion to rebuild the list
    filter_mock.all.return_value = []
    query_mock.filter.return_value = filter_mock
    mock_db.query.return_value = query_mock

    def get_mock_db_with_last_resume():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db_with_last_resume
    app.dependency_overrides[get_current_user_from_cookie] = lambda: test_user
    return client


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


@patch("resume_editor.app.api.routes.resume.validate_resume_content")
def test_update_resume_name_only_no_htmx(
    mock_validate, client_with_auth_and_resume, test_resume
):
    """Test updating only a resume's name without HTMX returns JSON."""
    response = client_with_auth_and_resume.put(
        "/api/resumes/1",
        data={"name": "Updated Name Only", "content": None},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name Only"
    mock_validate.assert_not_called()






def test_list_resumes_no_htmx(client_with_auth_and_resume, test_resume):
    """Test listing resumes without HTMX returns JSON."""
    response = client_with_auth_and_resume.get("/api/resumes/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == test_resume.id
    assert data[0]["name"] == test_resume.name


@patch("resume_editor.app.api.routes.resume._generate_resume_list_html")
def test_list_resumes_htmx_with_resumes(
    mock_gen_list_html, client_with_auth_and_resume, test_resume
):
    """Test listing resumes with HTMX when resumes exist."""
    mock_gen_list_html.return_value = "<html>List</html>"
    response = client_with_auth_and_resume.get(
        "/api/resumes/",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    assert response.text == "<html>List</html>"
    mock_gen_list_html.assert_called_once_with([test_resume])


@patch("resume_editor.app.api.routes.resume._generate_resume_list_html")
def test_list_resumes_htmx_no_resumes(
    mock_gen_list_html, client_with_auth_no_resume
):
    """Test listing resumes with HTMX when no resumes exist."""
    mock_gen_list_html.return_value = "No resumes"
    response = client_with_auth_no_resume.get(
        "/api/resumes/",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    assert response.text == "No resumes"
    mock_gen_list_html.assert_called_once_with([])


def test_parse_resume_endpoint_success(client):
    """Test successful parsing of resume content."""
    response = client.post(
        "/api/resumes/parse",
        json={"markdown_content": VALID_MINIMAL_RESUME_CONTENT},
    )
    assert response.status_code == 200
    data = response.json().get("resume_data", {})
    assert "personal" in data
    assert "education" in data
    assert "certifications" in data
    assert "experience" in data
    assert data["personal"]["name"] == "Test Person"


def test_parse_resume_endpoint_failure(client):
    """Test failure in parsing of resume content."""
    response = client.post(
        "/api/resumes/parse",
        json={"markdown_content": "this is not a valid resume"},
    )
    assert response.status_code == 400
    assert "Failed to parse resume" in response.json()["detail"]


# Test cases for not found resume
@pytest.mark.parametrize(
    "endpoint",
    [],
)
def test_get_info_not_found(client_with_auth_no_resume, endpoint):
    """Test GET endpoints return 404 for a non-existent resume."""
    response = client_with_auth_no_resume.get(endpoint)
    assert response.status_code == 404
    assert response.json() == {"detail": "Resume not found"}


@pytest.mark.parametrize(
    "endpoint, payload",
    [
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
    ],
)
def test_update_info_not_found(client_with_auth_no_resume, endpoint, payload):
    """Test PUT endpoints return 404 for a non-existent resume."""
    response = client_with_auth_no_resume.put(endpoint, json=payload)
    assert response.status_code == 404
    assert response.json() == {"detail": "Resume not found"}








def test_get_resume(client_with_auth_and_resume, test_resume):
    """Test getting a resume."""
    # Without HTMX (JSON)
    response = client_with_auth_and_resume.get(f"/api/resumes/{test_resume.id}")
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["id"] == test_resume.id
    assert json_response["name"] == test_resume.name
    assert json_response["content"] == test_resume.content




@patch("resume_editor.app.api.routes.resume.validate_resume_content")
@patch("resume_editor.app.api.routes.resume.create_resume_db")
def test_create_resume_no_htmx(
    mock_create_resume_db, mock_validate, client_with_auth_no_resume, test_user
):
    """Test creating a resume without HTMX returns a JSON response."""
    mock_validate.return_value = None
    created_resume = DatabaseResume(
        user_id=test_user.id,
        name="New Resume",
        content=VALID_MINIMAL_RESUME_CONTENT,
    )
    created_resume.id = 2
    mock_create_resume_db.return_value = created_resume

    response = client_with_auth_no_resume.post(
        "/api/resumes",
        json={"name": "New Resume", "content": VALID_MINIMAL_RESUME_CONTENT},
    )

    assert response.status_code == 200
    json_response = response.json()
    assert json_response["name"] == "New Resume"
    assert json_response["id"] == 2
    mock_validate.assert_called_once_with(VALID_MINIMAL_RESUME_CONTENT)
    mock_create_resume_db.assert_called_once()
    call_args = mock_create_resume_db.call_args[1]
    assert call_args["name"] == "New Resume"
    assert call_args["content"] == VALID_MINIMAL_RESUME_CONTENT


@patch("resume_editor.app.api.routes.resume.validate_resume_content")
@patch("resume_editor.app.api.routes.resume.create_resume_db")
def test_create_resume_htmx_redirect(
    mock_create_resume_db, mock_validate, client_with_auth_no_resume, test_user
):
    """Test creating a resume via HTMX returns a redirect response."""
    mock_validate.return_value = None
    created_resume = DatabaseResume(
        user_id=test_user.id,
        name="New Resume",
        content=VALID_MINIMAL_RESUME_CONTENT,
    )
    created_resume.id = 99
    mock_create_resume_db.return_value = created_resume

    response = client_with_auth_no_resume.post(
        "/api/resumes",
        json={"name": "New Resume", "content": VALID_MINIMAL_RESUME_CONTENT},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 200
    assert "HX-Redirect" in response.headers
    assert response.headers["HX-Redirect"] == "/resumes/99/edit"
    assert response.text == ""
    mock_create_resume_db.assert_called_once()


@patch("resume_editor.app.api.routes.resume.validate_resume_content")
def test_update_resume_no_htmx(
    mock_validate, client_with_auth_and_resume, test_resume
):
    """Test updating a resume without HTMX returns JSON success message."""
    mock_validate.return_value = None
    response = client_with_auth_and_resume.put(
        "/api/resumes/1",
        data={"name": "Updated Name", "content": test_resume.content},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"
    mock_validate.assert_called_once_with(test_resume.content)


@patch("resume_editor.app.api.routes.resume_ai._generate_resume_detail_html")
@patch("resume_editor.app.api.routes.resume_ai.update_resume_db")
@patch("resume_editor.app.api.routes.resume_ai.perform_pre_save_validation")
def test_accept_refined_resume_full(
    mock_validate,
    mock_update,
    mock_gen_html,
    client_with_auth_and_resume,
    test_resume,
):
    mock_validate.return_value = None
    mock_gen_html.return_value = "<div>Updated</div>"
    refined_content = REFINED_VALID_MINIMAL_RESUME_CONTENT

    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/accept",
        data={
            "refined_content": refined_content,
            "target_section": RefineTargetSection.FULL.value,
        },
    )

    assert response.status_code == 200
    assert response.text == "<div>Updated</div>"
    mock_validate.assert_called_once_with(refined_content, test_resume.content)
    mock_update.assert_called_once_with(
        db=ANY, resume=test_resume, content=refined_content
    )
    mock_gen_html.assert_called_once_with(test_resume)


@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_education_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume_ai._generate_resume_detail_html")
@patch("resume_editor.app.api.routes.resume_ai.update_resume_db")
@patch("resume_editor.app.api.routes.resume_ai.perform_pre_save_validation")
def test_accept_refined_resume_personal(
    mock_validate,
    mock_update,
    mock_gen_html,
    mock_extract_cert,
    mock_extract_exp,
    mock_extract_edu,
    mock_extract_pers,
    client_with_auth_and_resume,
    test_resume,
):
    refined_personal_content = "# Personal\n\n## Contact Information\n\nName: Refined Name"
    mock_validate.return_value = None
    mock_gen_html.return_value = "<div>Updated</div>"

    mock_extract_pers.return_value = PersonalInfoResponse(name="Refined Name")
    mock_extract_edu.return_value = EducationResponse(degrees=[])
    mock_extract_exp.return_value = ExperienceResponse(roles=[], projects=[])
    mock_extract_cert.return_value = CertificationsResponse(certifications=[])

    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/accept",
        data={
            "refined_content": refined_personal_content,
            "target_section": RefineTargetSection.PERSONAL.value,
        },
    )

    assert response.status_code == 200
    assert response.text == "<div>Updated</div>"
    mock_extract_pers.assert_called_once_with(refined_personal_content)
    mock_extract_edu.assert_called_once_with(test_resume.content)
    mock_extract_exp.assert_called_once_with(test_resume.content)
    mock_extract_cert.assert_called_once_with(test_resume.content)

    mock_validate.assert_called_once_with(ANY, test_resume.content)
    mock_update.assert_called_once_with(db=ANY, resume=test_resume, content=ANY)
    mock_gen_html.assert_called_once_with(test_resume)


@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
def test_accept_refined_resume_reconstruction_value_error(
    mock_extract_pers,
    client_with_auth_and_resume,
    test_resume,
):
    refined_content = "bad content"
    mock_extract_pers.side_effect = ValueError("Parsing failed")

    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/accept",
        data={
            "refined_content": refined_content,
            "target_section": RefineTargetSection.PERSONAL.value,
        },
    )

    assert response.status_code == 422
    assert (
        "Failed to reconstruct resume from refined section: Parsing failed"
        in response.json()["detail"]
    )


def test_save_refined_resume_as_new_no_name(
    client_with_auth_and_resume,
    test_resume,
):
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/save_as_new",
        data={
            "refined_content": "some content",
            "target_section": RefineTargetSection.FULL.value,
            "new_resume_name": "",  # empty name
        },
    )
    assert response.status_code == 400
    assert "New resume name is required" in response.json()["detail"]


@patch("resume_editor.app.api.routes.resume_ai.get_user_resumes")
@patch("resume_editor.app.api.routes.resume_ai.create_resume_db")
@patch("resume_editor.app.api.routes.resume_ai.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume_ai._generate_resume_list_html")
@patch("resume_editor.app.api.routes.resume_ai._generate_resume_detail_html")
def test_save_refined_resume_as_new_success(
    mock_gen_detail_html,
    mock_gen_list_html,
    mock_validate,
    mock_create,
    mock_get_resumes,
    client_with_auth_and_resume,
    test_resume,
    test_user,
):
    refined_content = REFINED_VALID_MINIMAL_RESUME_CONTENT
    new_resume_name = "Refined Resume"

    new_resume = DatabaseResume(
        user_id=test_user.id, name=new_resume_name, content=refined_content
    )
    new_resume.id = 2

    mock_validate.return_value = None
    mock_create.return_value = new_resume
    mock_get_resumes.return_value = [test_resume, new_resume]
    mock_gen_list_html.return_value = "sidebar"
    mock_gen_detail_html.return_value = "detail"

    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/save_as_new",
        data={
            "refined_content": refined_content,
            "target_section": RefineTargetSection.FULL.value,
            "new_resume_name": new_resume_name,
        },
    )

    assert response.status_code == 200
    assert "sidebar" in response.text
    assert "detail" in response.text
    assert 'hx-swap-oob="true"' in response.text

    mock_validate.assert_called_once_with(refined_content, test_resume.content)
    mock_create.assert_called_once_with(
        db=ANY,
        user_id=test_user.id,
        name=new_resume_name,
        content=refined_content,
    )
    mock_get_resumes.assert_called_once_with(ANY, test_user.id)
    mock_gen_list_html.assert_called_once_with(
        [test_resume, new_resume], selected_resume_id=new_resume.id
    )
    mock_gen_detail_html.assert_called_once_with(new_resume)


@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_education_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume_ai.get_user_resumes")
@patch("resume_editor.app.api.routes.resume_ai.create_resume_db")
@patch("resume_editor.app.api.routes.resume_ai.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume_ai._generate_resume_list_html")
@patch("resume_editor.app.api.routes.resume_ai._generate_resume_detail_html")
def test_save_refined_resume_as_new_partial_success(
    mock_gen_detail_html,
    mock_gen_list_html,
    mock_validate,
    mock_create,
    mock_get_resumes,
    mock_extract_cert,
    mock_extract_exp,
    mock_extract_edu,
    mock_extract_pers,
    client_with_auth_and_resume,
    test_resume,
    test_user,
):
    refined_personal_content = "# Personal\n\n## Contact Information\n\nName: Refined Name"
    new_resume_name = "Refined Resume"

    mock_extract_pers.return_value = PersonalInfoResponse(name="Refined Name")
    mock_extract_edu.return_value = EducationResponse(degrees=[])
    mock_extract_exp.return_value = ExperienceResponse(roles=[], projects=[])
    mock_extract_cert.return_value = CertificationsResponse(certifications=[])

    new_resume = DatabaseResume(
        user_id=test_user.id, name=new_resume_name, content="doesn't matter"
    )
    new_resume.id = 2

    mock_validate.return_value = None
    mock_create.return_value = new_resume
    mock_get_resumes.return_value = [test_resume, new_resume]
    mock_gen_list_html.return_value = "sidebar"
    mock_gen_detail_html.return_value = "detail"

    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/save_as_new",
        data={
            "refined_content": refined_personal_content,
            "target_section": RefineTargetSection.PERSONAL.value,
            "new_resume_name": new_resume_name,
        },
    )

    assert response.status_code == 200
    assert "sidebar" in response.text
    assert "detail" in response.text

    mock_extract_pers.assert_called_once_with(refined_personal_content)
    mock_extract_edu.assert_called_once_with(test_resume.content)
    mock_extract_exp.assert_called_once_with(test_resume.content)
    mock_extract_cert.assert_called_once_with(test_resume.content)

    mock_validate.assert_called_once_with(ANY, test_resume.content)

    mock_create.assert_called_once_with(
        db=ANY,
        user_id=test_user.id,
        name=new_resume_name,
        content=ANY,
    )

    mock_get_resumes.assert_called_once_with(ANY, test_user.id)
    mock_gen_list_html.assert_called_once_with(
        [test_resume, new_resume], selected_resume_id=new_resume.id
    )
    mock_gen_detail_html.assert_called_once_with(new_resume)


@patch("resume_editor.app.api.routes.resume_ai.create_resume_db")
@patch("resume_editor.app.api.routes.resume_ai.perform_pre_save_validation")
def test_save_refined_resume_as_new_reconstruction_error(
    mock_validate,
    mock_create,
    client_with_auth_and_resume,
    test_resume,
):
    mock_validate.side_effect = HTTPException(status_code=422, detail="Validation failed")

    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/save_as_new",
        data={
            "refined_content": "some content",
            "target_section": RefineTargetSection.FULL.value,
            "new_resume_name": "New Name",
        },
    )

    assert response.status_code == 422
    assert (
        "Failed to reconstruct resume from refined section: Validation failed"
        in response.json()["detail"]
    )
    mock_create.assert_not_called()










# --- Tests for form-based submissions from test_resume_route ---


def setup_dependency_overrides(
    app: FastAPI, mock_db: MagicMock, mock_user: DBUser | None
):
    """Setup dependency overrides for the FastAPI app."""

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    if mock_user:

        def get_mock_current_user():
            return mock_user

        app.dependency_overrides[get_current_user_from_cookie] = get_mock_current_user
    else:

        def raise_unauthorized():
            from fastapi import HTTPException

            raise HTTPException(status_code=401, detail="Not authenticated")

        app.dependency_overrides[get_current_user_from_cookie] = raise_unauthorized






