from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from resume_editor.app.api.routes.resume import get_resume_for_user
from resume_editor.app.api.routes.route_logic.resume_validation import (
    perform_pre_save_validation,
)
from resume_editor.app.core.auth import get_current_user_from_cookie
from resume_editor.app.main import create_app
from resume_editor.app.models.resume_model import Resume as DatabaseResume
from resume_editor.app.models.user import User


@pytest.fixture
def app():
    """Fixture to create a new app for each test."""
    _app = create_app()
    yield _app
    _app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    """Fixture to create a test client for each test."""
    with TestClient(app) as client:
        yield client


def test_perform_pre_save_validation_success():
    """Test that pre-save validation passes with valid content."""
    content = """# Personal
## Contact Information
Name: John Doe"""
    with patch(
        "resume_editor.app.api.routes.route_logic.resume_validation.validate_resume_content"
    ) as mock_validate:
        mock_validate.return_value = None
        perform_pre_save_validation(content)
        mock_validate.assert_called_once_with(content)


def test_perform_pre_save_validation_failure():
    """Test that pre-save validation raises HTTPException with invalid content."""
    content = "Invalid content"
    with patch(
        "resume_editor.app.api.routes.route_logic.resume_validation.validate_resume_content"
    ) as mock_validate:
        mock_validate.side_effect = HTTPException(status_code=422, detail="Invalid")
        with pytest.raises(HTTPException) as exc_info:
            perform_pre_save_validation(content)
        assert exc_info.value.status_code == 422
        assert "Invalid" in exc_info.value.detail


@patch("resume_editor.app.api.routes.resume.validate_resume_content")
def test_create_resume_with_invalid_markdown_raises_422(mock_validate, app, client):
    """Test creating a resume with invalid Markdown raises a 422 error."""
    mock_validate.side_effect = HTTPException(
        status_code=422, detail="Invalid Markdown format"
    )
    mock_user = User(id=1, username="test", email="email@email.com", hashed_password="hp")
    app.dependency_overrides[
        get_current_user_from_cookie
    ] = lambda: mock_user

    response = client.post(
        "/api/resumes", data={"name": "test", "content": "invalid"}
    )
    assert response.status_code == 422
    assert "Invalid Markdown format" in response.json()["detail"]


@patch("resume_editor.app.api.routes.resume.create_resume_db")
@patch("resume_editor.app.api.routes.resume.validate_resume_content")
def test_create_resume_with_valid_markdown_succeeds(
    mock_validate, mock_create_db, app, client
):
    """Test creating a resume with valid Markdown succeeds."""
    mock_user = User(id=1, username="test", email="email@email.com", hashed_password="hp")
    app.dependency_overrides[
        get_current_user_from_cookie
    ] = lambda: mock_user

    mock_resume = DatabaseResume(
        user_id=1, name="Test Resume", content="# Valid Markdown"
    )
    mock_resume.id = 1
    mock_create_db.return_value = mock_resume

    response = client.post(
        "/api/resumes",
        data={"name": "Test Resume", "content": "# Valid Markdown"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Test Resume"
    mock_validate.assert_called_once_with("# Valid Markdown")


@patch("resume_editor.app.api.routes.resume.validate_resume_content")
def test_update_resume_with_invalid_markdown_raises_422(mock_validate, app, client):
    """Test updating a resume with invalid Markdown raises a 422 error."""
    mock_validate.side_effect = HTTPException(
        status_code=422, detail="Invalid Markdown format"
    )
    # Mock the dependency that provides the resume to the route
    app.dependency_overrides[get_resume_for_user] = lambda: Mock()
    mock_user = User(id=1, username="test", email="email@email.com", hashed_password="hp")
    app.dependency_overrides[
        get_current_user_from_cookie
    ] = lambda: mock_user

    response = client.put(
        "/api/resumes/1", data={"name": "test", "content": "invalid"}
    )
    assert response.status_code == 422
    assert "Invalid Markdown format" in response.json()["detail"]


@patch("resume_editor.app.api.routes.resume.update_resume_db")
@patch("resume_editor.app.api.routes.resume.validate_resume_content")
def test_update_resume_with_valid_markdown_succeeds(
    mock_validate, mock_update_db, app, client
):
    """Test updating a resume with valid Markdown succeeds."""
    mock_resume = DatabaseResume(user_id=1, name="Test", content="Valid")
    mock_resume.id = 1

    app.dependency_overrides[get_resume_for_user] = lambda: mock_resume
    mock_update_db.return_value = mock_resume
    mock_user = User(id=1, username="test", email="email@email.com", hashed_password="hp")
    app.dependency_overrides[
        get_current_user_from_cookie
    ] = lambda: mock_user

    response = client.put("/api/resumes/1", data={"name": "Test", "content": "Valid"})

    assert response.status_code == 200
    mock_validate.assert_called_once_with("Valid")
