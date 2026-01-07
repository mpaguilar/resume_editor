from unittest.mock import ANY, AsyncMock, Mock, patch

import pytest
from fastapi import Request, Response
from fastapi.testclient import TestClient

from resume_editor.app.api.routes.route_models import (
    RefineForm,
)
from resume_editor.app.core.auth import get_current_user_from_cookie
from resume_editor.app.core.config import get_settings
from resume_editor.app.database.database import get_db
from resume_editor.app.main import create_app
from resume_editor.app.models.resume_model import Resume as DatabaseResume, ResumeData
from resume_editor.app.models.user import User as DBUser, UserData


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
        data=UserData(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            id_=1,
        )
    )
    return user


@pytest.fixture
def test_resume(test_user):
    """Fixture for a test resume."""
    resume_data = ResumeData(
        user_id=test_user.id,
        name="Test Resume",
        content=VALID_MINIMAL_RESUME_CONTENT,
    )
    resume = DatabaseResume(data=resume_data)
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


def test_refine_resume_delegates_for_non_experience_section():
    """This test is no longer valid as non-experience sections are not refined."""
    assert True


@pytest.mark.parametrize(
    "limit_years, expected_limit_years",
    [(None, None), ("5", 5), ("", None)],
)
@patch("resume_editor.app.api.routes.resume_ai.templates.TemplateResponse")
def test_refine_resume_post_for_experience_returns_sse_loader(
    mock_template_response,
    limit_years,
    expected_limit_years,
    client_with_auth_and_resume,
):
    """Test that POST /refine for 'experience' returns the SSE loader partial."""
    # Arrange
    job_desc = "A cool job"
    mock_template_response.return_value = "sse loader html"
    form_data = {
        "job_description": job_desc,
        "target_section": "experience",
    }
    if limit_years is not None:
        form_data["limit_refinement_years"] = limit_years

    # Act
    response = client_with_auth_and_resume.post(
        "/api/resumes/1/refine",
        data=form_data,
    )

    # Assert
    assert response.status_code == 200
    assert response.text == '"sse loader html"'
    mock_template_response.assert_called_once_with(
        ANY,
        "partials/resume/_refine_sse_loader.html",
        {
            "resume_id": 1,
            "job_description": job_desc,
            "limit_refinement_years": expected_limit_years,
        },
    )




@patch("resume_editor.app.api.routes.resume_ai.templates.TemplateResponse")
def test_refine_resume_invalid_section_returns_sse_loader(
    mock_template_response, client_with_auth_and_resume, test_resume
):
    """Test that providing an invalid section to the refine endpoint still returns the SSE loader partial."""
    # Arrange
    job_desc = "job"
    invalid_section = "invalid_section"
    mock_template_response.return_value = "sse loader html"
    form_data = {"job_description": job_desc, "target_section": invalid_section}

    # Act
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine",
        data=form_data,
    )

    # Assert
    assert response.status_code == 200
    assert response.text == '"sse loader html"'
    mock_template_response.assert_called_once_with(
        ANY,
        "partials/resume/_refine_sse_loader.html",
        {
            "resume_id": test_resume.id,
            "job_description": job_desc,
            "limit_refinement_years": None,
        },
    )
