import datetime
from enum import Enum
from unittest.mock import ANY, MagicMock, Mock, patch

import pytest
from bs4 import BeautifulSoup
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
    RefineTargetSection,
)
from resume_editor.app.api.dependencies import get_resume_for_user
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
def test_refined_resume(test_user):
    """Fixture for a test refined resume."""
    resume = DatabaseResume(
        user_id=test_user.id,
        name="Refined Test Resume",
        content=REFINED_VALID_MINIMAL_RESUME_CONTENT,
        is_base=False,
        parent_id=1,
    )
    resume.id = 2
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
    filter_mock = mock_db.query.return_value.filter.return_value
    filter_mock.first.return_value = test_resume
    filter_mock.order_by.return_value.all.return_value = [test_resume]

    def get_mock_db_with_resume():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db_with_resume
    app.dependency_overrides[get_current_user_from_cookie] = lambda: test_user
    return client


@pytest.fixture
def client_with_auth_no_resume(app, client, test_user):
    """Fixture for a test client with an authenticated user but no resume."""
    mock_db = Mock()
    filter_mock = mock_db.query.return_value.filter.return_value
    filter_mock.first.return_value = None
    filter_mock.order_by.return_value.all.return_value = []

    def get_mock_db_no_resume():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db_no_resume
    app.dependency_overrides[get_current_user_from_cookie] = lambda: test_user
    return client


def test_delete_resume_htmx_redirects(client_with_auth_and_resume):
    """Test deleting a resume with HTMX returns an HX-Redirect header."""
    response = client_with_auth_and_resume.delete(
        "/api/resumes/1",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    assert response.text == ""
    assert response.headers["HX-Redirect"] == "/dashboard"


def test_delete_resume_no_htmx(client_with_auth_and_resume):
    """Test deleting a resume without HTMX returns JSON success message."""
    response = client_with_auth_and_resume.delete("/api/resumes/1")
    assert response.status_code == 200
    assert response.json() == {"message": "Resume deleted successfully"}


def test_delete_resume_not_found(client_with_auth_no_resume):
    """Test deleting a non-existent or unauthorized resume returns 404."""
    response = client_with_auth_no_resume.delete("/api/resumes/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Resume not found"}


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


@patch("resume_editor.app.api.routes.resume.validate_resume_content")
@patch("resume_editor.app.api.routes.resume.get_user_resumes")
@patch("resume_editor.app.api.routes.resume._generate_resume_list_html")
@patch("resume_editor.app.api.routes.resume._generate_resume_detail_html")
@pytest.mark.parametrize(
    "sort_by_param, expected_sort_by_val",
    [(None, None), ("name_desc", "name_desc")],
)
def test_update_resume_htmx(
    mock_gen_detail_html,
    mock_gen_list_html,
    mock_get_resumes,
    mock_validate,
    client_with_auth_and_resume,
    test_resume,
    test_user,
    sort_by_param,
    expected_sort_by_val,
):
    """Test updating a resume with HTMX returns HTML for list and detail."""
    mock_validate.return_value = None
    mock_get_resumes.return_value = [test_resume]
    mock_gen_list_html.return_value = "list_html"
    mock_gen_detail_html.return_value = "detail_html"

    updated_name = "Updated Resume Name"
    updated_content = "Updated content"
    form_data = {"name": updated_name, "content": updated_content}
    if sort_by_param:
        form_data["sort_by"] = sort_by_param

    response = client_with_auth_and_resume.put(
        f"/api/resumes/{test_resume.id}",
        data=form_data,
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 200
    soup = BeautifulSoup(response.content, "html.parser")

    # The OOB swap for the list is still present
    list_div = soup.find("div", {"id": "resume-list", "hx-swap-oob": "true"})
    assert list_div
    assert list_div.text == "list_html"

    # Check the contents of the detail view
    detail_div = soup.find("div", {"id": "resume-detail"})
    assert detail_div is not None
    assert detail_div.text == "detail_html"

    mock_validate.assert_called_once_with(updated_content)

    mock_get_resumes.assert_called_once_with(
        db=ANY, user_id=test_user.id, sort_by=expected_sort_by_val
    )

    mock_gen_list_html.assert_called_once_with(
        base_resumes=[test_resume],
        refined_resumes=[],
        selected_resume_id=test_resume.id,
        sort_by=expected_sort_by_val,
        wrap_in_div=False,
    )

    mock_gen_detail_html.assert_called_once_with(resume=test_resume)


@patch("resume_editor.app.api.routes.resume.validate_resume_content")
def test_update_resume_from_editor(
    mock_validate, client_with_auth_and_resume, test_resume
):
    """Test updating a resume with HTMX from the editor page returns 200 OK."""
    mock_validate.return_value = None
    updated_name = "Updated From Editor"
    updated_content = "some new content from editor"

    response = client_with_auth_and_resume.put(
        f"/api/resumes/{test_resume.id}",
        data={
            "name": updated_name,
            "content": updated_content,
            "from_editor": "true",
        },
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 200
    assert response.text == ""
    mock_validate.assert_called_once_with(updated_content)






def test_list_resumes_no_htmx(client_with_auth_and_resume, test_resume):
    """Test listing resumes without HTMX returns JSON."""
    response = client_with_auth_and_resume.get("/api/resumes/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == test_resume.id
    assert data[0]["name"] == test_resume.name


def test_list_resumes_htmx_with_base_resume(client_with_auth_and_resume, test_resume):
    """Test listing resumes with HTMX renders correctly with only a base resume."""
    response = client_with_auth_and_resume.get(
        "/api/resumes/",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    soup = BeautifulSoup(response.text, "html.parser")

    assert "Base Resumes" in response.text
    assert "Applied Resumes" in response.text
    assert "Test Resume" in response.text
    assert "No applied resumes found" in response.text

    button = soup.find("button", class_="bg-red-500")
    assert button is not None
    assert button["hx-delete"] == f"/api/resumes/{test_resume.id}"


def test_list_resumes_htmx_with_selection(client_with_auth_and_resume, test_resume):
    """Test listing resumes with HTMX and a selected ID."""
    response = client_with_auth_and_resume.get(
        f"/api/resumes/?selected_id={test_resume.id}",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    soup = BeautifulSoup(response.text, "html.parser")
    selected_item = soup.find("div", class_="selected")
    assert selected_item is not None
    assert f"ID: {test_resume.id}" in selected_item.text


def test_list_resumes_htmx_no_resumes(client_with_auth_no_resume):
    """Test listing resumes with HTMX when no resumes exist."""
    response = client_with_auth_no_resume.get(
        "/api/resumes/",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    assert "No resumes found" in response.text


@pytest.fixture
def client_with_auth_refined_only(app, client, test_user, test_refined_resume):
    """Fixture for a test client with an authenticated user and only a refined resume."""
    mock_db = Mock()
    filter_mock = mock_db.query.return_value.filter.return_value
    filter_mock.first.return_value = test_refined_resume
    filter_mock.order_by.return_value.all.return_value = [test_refined_resume]

    def get_mock_db_with_resume():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db_with_resume
    app.dependency_overrides[get_current_user_from_cookie] = lambda: test_user
    return client


def test_list_resumes_htmx_with_refined_resume(
    client_with_auth_refined_only, test_refined_resume
):
    """Test listing resumes with HTMX renders correctly with only a refined resume."""
    response = client_with_auth_refined_only.get(
        "/api/resumes/",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200

    assert "Base Resumes" in response.text
    assert "Applied Resumes" in response.text
    assert "No base resumes found" in response.text
    assert "Refined Test Resume" in response.text
    assert f"Parent: {test_refined_resume.parent_id}" in response.text

    soup = BeautifulSoup(response.text, "html.parser")
    button = soup.find("button", class_="bg-red-500")
    assert button is not None
    assert button["hx-delete"] == f"/api/resumes/{test_refined_resume.id}"


@pytest.fixture
def client_with_auth_both_resumes(
    app, client, test_user, test_resume, test_refined_resume
):
    """Fixture for a test client with an authenticated user and both resume types."""
    mock_db = Mock()
    filter_mock = mock_db.query.return_value.filter.return_value
    filter_mock.first.return_value = test_resume
    filter_mock.order_by.return_value.all.return_value = [
        test_resume,
        test_refined_resume,
    ]

    def get_mock_db_with_resume():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db_with_resume
    app.dependency_overrides[get_current_user_from_cookie] = lambda: test_user
    return client


def test_list_resumes_htmx_with_both_resumes(
    client_with_auth_both_resumes, test_resume, test_refined_resume
):
    """Test listing resumes with HTMX renders correctly with both resume types."""
    response = client_with_auth_both_resumes.get(
        "/api/resumes/",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200

    assert "Base Resumes" in response.text
    assert "Applied Resumes" in response.text
    assert "Test Resume" in response.text
    assert "Refined Test Resume" in response.text
    assert "No base resumes found" not in response.text
    assert "No applied resumes found" not in response.text

    soup = BeautifulSoup(response.text, "html.parser")
    buttons = soup.find_all("button", class_="bg-red-500")
    assert len(buttons) == 2
    delete_urls = {b["hx-delete"] for b in buttons}
    assert f"/api/resumes/{test_resume.id}" in delete_urls
    assert f"/api/resumes/{test_refined_resume.id}" in delete_urls


@patch("resume_editor.app.api.routes.resume.get_user_resumes")
def test_list_resumes_with_sort_by(
    mock_get_user_resumes, client_with_auth_no_resume, test_user
):
    """Test that list_resumes passes the sort_by parameter correctly."""
    mock_get_user_resumes.return_value = []

    response = client_with_auth_no_resume.get("/api/resumes/?sort_by=name_asc")

    assert response.status_code == 200
    mock_get_user_resumes.assert_called_once_with(
        db=ANY, user_id=test_user.id, sort_by="name_asc"
    )


@patch("resume_editor.app.api.routes.resume.get_user_resumes")
def test_list_resumes_with_default_sort(
    mock_get_user_resumes, client_with_auth_no_resume, test_user
):
    """Test that list_resumes uses default sorting when sort_by is not provided."""
    mock_get_user_resumes.return_value = []

    response = client_with_auth_no_resume.get("/api/resumes/")

    assert response.status_code == 200
    mock_get_user_resumes.assert_called_once_with(db=ANY, user_id=test_user.id, sort_by=None)


def test_list_resumes_invalid_sort_by(client_with_auth_no_resume):
    """Test that list_resumes returns 422 for invalid sort_by."""
    response = client_with_auth_no_resume.get("/api/resumes/?sort_by=invalid_sort")
    assert response.status_code == 422


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

    # With HTMX (HTML)
    response_htmx = client_with_auth_and_resume.get(
        f"/api/resumes/{test_resume.id}", headers={"HX-Request": "true"}
    )
    assert response_htmx.status_code == 200
    soup = BeautifulSoup(response_htmx.content, "html.parser")

    # Check the export form
    export_form = soup.find("form", id=f"export-form-{test_resume.id}")
    assert export_form is not None
    assert export_form.get("method") == "GET"
    assert export_form.get("action") == f"/api/resumes/{test_resume.id}/download"

    # Check for Markdown download button
    markdown_button = export_form.find(
        "button", {"formaction": f"/api/resumes/{test_resume.id}/export/markdown"}
    )
    assert markdown_button is not None
    assert markdown_button.text.strip() == "Download Markdown"

    # Check for DOCX download button
    docx_button = export_form.find("button", string=lambda t: t and "Download DOCX" in t)
    assert docx_button is not None
    assert docx_button.get("formaction") is None
    assert docx_button.text.strip() == "Download DOCX"

    # Check for date inputs
    assert export_form.find("input", {"name": "start_date"}) is not None
    assert export_form.find("input", {"name": "end_date"}) is not None

    # Check for select dropdowns
    render_format_select = export_form.find("select", {"name": "render_format"})
    assert render_format_select is not None
    assert render_format_select.find("option", {"value": "plain"})
    assert render_format_select.find("option", {"value": "ats"})

    settings_name_select = export_form.find("select", {"name": "settings_name"})
    assert settings_name_select is not None
    assert settings_name_select.find("option", {"value": "general"})
    assert settings_name_select.find("option", {"value": "executive_summary"})




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




def test_get_resume_htmx_renders_edit_button_for_all_resumes(
    app, client, test_user, test_resume, test_refined_resume
):
    """
    Test that the get_resume endpoint, when called via HTMX, renders an 'Edit'
    button for both base and refined resumes.
    """
    resumes = [test_resume, test_refined_resume]
    app.dependency_overrides[get_current_user_from_cookie] = lambda: test_user

    for resume_obj in resumes:
        # Mock the dependency to return the specific resume for this iteration.
        app.dependency_overrides[get_resume_for_user] = lambda: resume_obj

        response = client.get(
            f"/api/resumes/{resume_obj.id}", headers={"HX-Request": "true"}
        )

        assert response.status_code == 200
        soup = BeautifulSoup(response.content, "html.parser")

        # Check for a link with "Edit" text pointing to the correct editor page.
        edit_link = soup.find("a", string=lambda t: t and "Edit" in t.strip())

        assert edit_link is not None, f"Edit link missing for resume id {resume_obj.id}"
        assert edit_link.get("href") == f"/resumes/{resume_obj.id}/edit"

    app.dependency_overrides.clear()


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






