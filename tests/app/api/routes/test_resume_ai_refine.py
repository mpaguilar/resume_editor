from unittest.mock import ANY, AsyncMock, Mock, patch

import pytest
from fastapi import Request, Response
from fastapi.testclient import TestClient

from resume_editor.app.api.routes.route_models import (
    RefineTargetSection,
    SyncRefinementParams,
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


@patch("resume_editor.app.api.routes.resume_ai.handle_sync_refinement", new_callable=AsyncMock)
def test_refine_resume_delegates_for_non_experience_section(
    mock_handle_sync,
    client_with_auth_and_resume,
    test_resume,
    test_user,
):
    """Test that POST /refine delegates to handle_sync_refinement for non-experience sections."""
    # Arrange
    job_desc = "A cool job"
    target_section = "personal"
    gen_intro = "true"  # Form data will be a string
    
    mock_handle_sync.return_value = Response(status_code=204)

    # Act
    # Pass limit_refinement_years to ensure it is ignored for non-experience sections
    response = client_with_auth_and_resume.post(
        "/api/resumes/1/refine",
        data={
            "job_description": job_desc,
            "target_section": target_section,
            "generate_introduction": gen_intro,
            "limit_refinement_years": "5",
        },
    )

    # Assert
    assert response.status_code == 204
    mock_handle_sync.assert_called_once()
    call_kwargs = mock_handle_sync.call_args.kwargs
    assert "sync_params" in call_kwargs
    params_arg = call_kwargs["sync_params"]
    assert isinstance(params_arg, SyncRefinementParams)
    assert isinstance(params_arg.request, Request)
    assert params_arg.db is not None
    assert params_arg.user == test_user
    assert params_arg.resume == test_resume
    assert params_arg.job_description == job_desc
    assert params_arg.target_section == RefineTargetSection.PERSONAL
    assert params_arg.generate_introduction is True


@pytest.mark.parametrize(
    "limit_years, expected_limit_years",
    [(None, None), ("5", 5), ("", None)],
)
@pytest.mark.parametrize(
    "gen_intro, expected_gen_intro",
    [("true", True), (None, False)],  # None means the form field is absent
)
@patch("resume_editor.app.api.routes.resume_ai.templates.TemplateResponse")
def test_refine_resume_post_for_experience_returns_sse_loader(
    mock_template_response,
    limit_years,
    expected_limit_years,
    gen_intro,
    expected_gen_intro,
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
    if gen_intro is not None:
        form_data["generate_introduction"] = gen_intro
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
            "generate_introduction": expected_gen_intro,
            "limit_refinement_years": expected_limit_years,
        },
    )




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
