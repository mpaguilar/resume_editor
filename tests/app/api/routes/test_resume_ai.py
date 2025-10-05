from unittest.mock import ANY, AsyncMock, MagicMock, Mock, patch
import logging
import asyncio
import pytest
from cryptography.fernet import InvalidToken
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from openai import AuthenticationError

from resume_editor.app.core.auth import get_current_user_from_cookie
from resume_editor.app.core.config import get_settings
from resume_editor.app.database.database import get_db
from resume_editor.app.main import create_app
from resume_editor.app.models.resume_model import Resume as DatabaseResume
from resume_editor.app.models.user import User as DBUser
from resume_editor.app.models.user_settings import UserSettings

_real_asyncio_sleep = asyncio.sleep

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


VALID_RESUME_TWO_ROLES = """# Personal

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

### Role

#### Basics

Company: B Company
Title: B Role
Start date: 01/2023

## Projects

### Project

#### Overview

Title: A Cool Project
#### Description

A project description.
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




@patch("resume_editor.app.api.routes.resume_ai.refine_resume_section_with_llm")
@patch("resume_editor.app.api.routes.resume_ai.decrypt_data")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings")
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
        llm_model_name="test-model",
    )
    mock_get_user_settings.return_value = mock_settings
    mock_decrypt_data.return_value = "decrypted_key"
    mock_refine_llm.return_value = ("refined content", "this is an intro")

    # Act
    response = client_with_auth_and_resume.post(
        "/api/resumes/1/refine",
        data={
            "job_description": "job",
            "target_section": "personal",
            "generate_introduction": "true",
        },
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "refined_content": "refined content",
        "introduction": "this is an intro",
    }
    mock_get_user_settings.assert_called_once_with(mock_db_session, test_user.id)
    mock_decrypt_data.assert_called_once_with("key")
    mock_refine_llm.assert_called_once_with(
        resume_content=VALID_MINIMAL_RESUME_CONTENT,
        job_description="job",
        target_section="personal",
        llm_endpoint="http://llm.test",
        api_key="decrypted_key",
        llm_model_name="test-model",
        generate_introduction=True,
    )


@patch("resume_editor.app.api.routes.resume_ai.refine_resume_section_with_llm")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings")
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
    mock_refine_llm.return_value = ("refined content", "this is an intro")

    # Act
    response = client_with_auth_and_resume.post(
        "/api/resumes/1/refine",
        data={
            "job_description": "job",
            "target_section": "personal",
            "generate_introduction": "true",
        },
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "refined_content": "refined content",
        "introduction": "this is an intro",
    }
    mock_get_user_settings.assert_called_once_with(mock_db_session, test_user.id)
    mock_refine_llm.assert_called_once_with(
        resume_content=VALID_MINIMAL_RESUME_CONTENT,
        job_description="job",
        target_section="personal",
        llm_endpoint=None,
        api_key=None,
        llm_model_name=None,
        generate_introduction=True,
    )


@patch("resume_editor.app.api.routes.resume_ai.refine_resume_section_with_llm")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings")
def test_refine_resume_no_api_key(
    mock_get_user_settings,
    mock_refine_llm,
    client_with_auth_and_resume,
    test_user,
):
    """Test resume refinement when user settings exist but have no API key."""
    # Arrange
    mock_settings = UserSettings(
        user_id=test_user.id,
        llm_endpoint="http://llm.test",
        llm_model_name="test-model",
    )
    mock_settings.encrypted_api_key = None
    mock_get_user_settings.return_value = mock_settings
    mock_refine_llm.return_value = ("refined content", "this is an intro")

    # Act
    response = client_with_auth_and_resume.post(
        "/api/resumes/1/refine",
        data={
            "job_description": "job",
            "target_section": "personal",
            "generate_introduction": "true",
        },
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "refined_content": "refined content",
        "introduction": "this is an intro",
    }
    mock_refine_llm.assert_called_once_with(
        resume_content=VALID_MINIMAL_RESUME_CONTENT,
        job_description="job",
        target_section="personal",
        llm_endpoint="http://llm.test",
        api_key=None,
        llm_model_name="test-model",
        generate_introduction=True,
    )


@patch("resume_editor.app.api.routes.resume_ai.refine_resume_section_with_llm")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
def test_refine_resume_success_with_gen_intro_unchecked(
    mock_get_user_settings,
    mock_refine_llm,
    client_with_auth_and_resume,
    test_user,
):
    """Test successful resume refinement when generate_introduction is unchecked (not sent)."""
    # Arrange
    mock_db_session = next(
        client_with_auth_and_resume.app.dependency_overrides[get_db](),
    )
    mock_refine_llm.return_value = ("refined content", None)

    # Act
    response = client_with_auth_and_resume.post(
        "/api/resumes/1/refine",
        data={"job_description": "job", "target_section": "personal"},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"refined_content": "refined content", "introduction": None}
    mock_get_user_settings.assert_called_once_with(mock_db_session, test_user.id)
    mock_refine_llm.assert_called_once_with(
        resume_content=VALID_MINIMAL_RESUME_CONTENT,
        job_description="job",
        target_section="personal",
        llm_endpoint=None,
        api_key=None,
        llm_model_name=None,
        generate_introduction=False,
    )


@patch("resume_editor.app.api.routes.resume_ai.refine_resume_section_with_llm")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
def test_refine_resume_llm_failure(
    mock_get_user_settings,
    mock_refine_llm,
    client_with_auth_and_resume,
):
    """Test resume refinement when the LLM call fails."""
    # Arrange
    mock_refine_llm.side_effect = Exception("LLM call failed")

    # Act
    response = client_with_auth_and_resume.post(
        "/api/resumes/1/refine",
        data={
            "job_description": "job",
            "target_section": "personal",
            "generate_introduction": "true",
        },
    )

    # Assert
    assert response.status_code == 500
    assert response.json() == {"detail": "LLM refinement failed: LLM call failed"}


@patch("resume_editor.app.api.routes.resume_ai.refine_resume_section_with_llm")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
def test_refine_resume_llm_failure_htmx(
    mock_get_user_settings,
    mock_refine_llm,
    client_with_auth_and_resume,
):
    """Test resume refinement HTMX request when the LLM call fails."""
    # Arrange
    mock_refine_llm.side_effect = Exception("LLM call failed")

    # Act
    response = client_with_auth_and_resume.post(
        "/api/resumes/1/refine",
        data={
            "job_description": "job",
            "target_section": "personal",
            "generate_introduction": "true",
        },
        headers={"HX-Request": "true"},
    )

    # Assert
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "An unexpected error occurred during refinement" in response.text
    assert "LLM call failed" in response.text


@patch("resume_editor.app.api.routes.resume_ai.refine_resume_section_with_llm")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
def test_refine_resume_llm_auth_failure(
    mock_get_user_settings,
    mock_refine_llm,
    client_with_auth_and_resume,
):
    """Test resume refinement when the LLM call fails with an auth error."""
    # Arrange
    mock_refine_llm.side_effect = AuthenticationError(
        message="Invalid API key",
        response=Mock(),
        body=None,
    )

    # Act
    response = client_with_auth_and_resume.post(
        "/api/resumes/1/refine",
        data={
            "job_description": "job",
            "target_section": "personal",
            "generate_introduction": "true",
        },
    )

    # Assert
    assert response.status_code == 401
    assert response.json() == {
        "detail": "LLM authentication failed. Please check your API key in settings.",
    }


@patch("resume_editor.app.api.routes.resume_ai.refine_resume_section_with_llm")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
def test_refine_resume_llm_auth_failure_htmx(
    mock_get_user_settings,
    mock_refine_llm,
    client_with_auth_and_resume,
):
    """Test resume refinement HTMX request when LLM auth fails."""
    # Arrange
    mock_refine_llm.side_effect = AuthenticationError(
        message="auth failed", response=Mock(), body=None
    )

    # Act
    response = client_with_auth_and_resume.post(
        "/api/resumes/1/refine",
        data={
            "job_description": "job",
            "target_section": "personal",
            "generate_introduction": "true",
        },
        headers={"HX-Request": "true"},
    )

    # Assert
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert (
        "LLM authentication failed. Please check your API key in settings."
        in response.text
    )


@pytest.mark.parametrize("target_section", ["personal"])
@patch("resume_editor.app.api.routes.resume_ai.decrypt_data")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings")
def test_refine_resume_decryption_failure(
    mock_get_user_settings,
    mock_decrypt_data,
    target_section,
    client_with_auth_and_resume,
    test_user,
):
    """Test resume refinement when API key decryption fails."""
    # Arrange
    mock_settings = UserSettings(
        user_id=test_user.id,
        llm_endpoint="http://llm.test",
        encrypted_api_key="key",
        llm_model_name="test-model",
    )
    mock_get_user_settings.return_value = mock_settings
    mock_decrypt_data.side_effect = InvalidToken

    # Act
    response = client_with_auth_and_resume.post(
        "/api/resumes/1/refine",
        data={
            "job_description": "job",
            "target_section": target_section,
            "generate_introduction": "true",
        },
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Invalid API key. Please update your settings.",
    }
    mock_get_user_settings.assert_called_once()
    mock_decrypt_data.assert_called_once_with("key")


@patch("resume_editor.app.api.routes.resume_ai.templates.TemplateResponse")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
def test_refine_resume_post_for_experience_returns_sse_loader(
    mock_get_user_settings,
    mock_template_response,
    client_with_auth_and_resume,
):
    """Test that POST /refine for 'experience' returns the SSE loader partial."""
    # Arrange
    job_desc = "A cool job"
    mock_template_response.return_value = "sse loader html"

    # Act
    response = client_with_auth_and_resume.post(
        "/api/resumes/1/refine",
        data={
            "job_description": job_desc,
            "target_section": "experience",
            "generate_introduction": "true",
        },
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
            "generate_introduction": True,
        },
    )


@patch("resume_editor.app.api.routes.resume_ai.templates.TemplateResponse")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
def test_refine_resume_post_for_experience_gen_intro_false(
    mock_get_user_settings,
    mock_template_response,
    client_with_auth_and_resume,
):
    """Test POST /refine for 'experience' with generate_introduction false."""
    # Arrange
    job_desc = "A cool job"
    mock_template_response.return_value = "sse loader html"

    # Act
    response = client_with_auth_and_resume.post(
        "/api/resumes/1/refine",
        data={"job_description": job_desc, "target_section": "experience"},
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
            "generate_introduction": False,
        },
    )


@pytest.mark.parametrize("target_section", ["personal"])
@patch("resume_editor.app.api.routes.resume_ai.decrypt_data")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings")
def test_refine_resume_decryption_failure_htmx(
    mock_get_user_settings,
    mock_decrypt_data,
    target_section,
    client_with_auth_and_resume,
    test_user,
):
    """Test resume refinement HTMX request when API key decryption fails."""
    # Arrange
    mock_settings = UserSettings(user_id=test_user.id, encrypted_api_key="key")
    mock_get_user_settings.return_value = mock_settings
    mock_decrypt_data.side_effect = InvalidToken

    # Act
    response = client_with_auth_and_resume.post(
        "/api/resumes/1/refine",
        data={
            "job_description": "job",
            "target_section": target_section,
            "generate_introduction": "true",
        },
        headers={"HX-Request": "true"},
    )

    # Assert
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Invalid API key. Please update your settings." in response.text


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


@patch("resume_editor.app.api.routes.resume_ai._create_refine_result_html")
@patch("resume_editor.app.api.routes.resume_ai.refine_resume_section_with_llm")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
def test_refine_resume_htmx_response(
    mock_get_user_settings,
    mock_refine_llm,
    mock_create_result_html,
    client_with_auth_and_resume,
):
    """Test that the /refine endpoint returns HTML for an HTMX request."""
    # Arrange
    mock_refine_llm.return_value = ("refined content", "this is an intro")
    mock_create_result_html.return_value = "<html>refine result</html>"

    # Act
    response = client_with_auth_and_resume.post(
        "/api/resumes/1/refine",
        data={
            "job_description": "job",
            "target_section": "personal",
            "generate_introduction": "true",
        },
        headers={"HX-Request": "true"},
    )

    # Assert
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert response.text == "<html>refine result</html>"
    mock_create_result_html.assert_called_once_with(
        resume_id=1,
        target_section_val="personal",
        refined_content="refined content",
        job_description="job",
        introduction="this is an intro",
    )


@patch("resume_editor.app.api.routes.resume_ai.refine_resume_section_with_llm")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
def test_refine_resume_no_htmx_response(
    mock_get_user_settings,
    mock_refine_llm,
    client_with_auth_and_resume,
):
    """Test that the /refine endpoint returns JSON for a non-HTMX request."""
    # Arrange
    mock_refine_llm.return_value = ("## Refined Experience", "intro")

    # Act
    response = client_with_auth_and_resume.post(
        "/api/resumes/1/refine",
        data={
            "job_description": "job",
            "target_section": "personal",
            "generate_introduction": "true",
        },
    )

    # Assert
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {
        "refined_content": "## Refined Experience",
        "introduction": "intro",
    }


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.resume_ai._create_refine_result_html")
@patch("resume_editor.app.api.routes.resume_ai.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume_ai.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_education_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
@patch("resume_editor.app.api.routes.resume_ai.async_refine_experience_section")
@patch(
    "resume_editor.app.api.routes.resume_ai.decrypt_data",
    return_value="decrypted_key",
)
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings")
async def test_refine_resume_stream_happy_path(
    mock_get_user_settings,
    mock_decrypt_data,
    mock_async_refine_experience,
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_create_refine_result_html,
    client_with_auth_and_resume,
    test_user,
    test_resume,
):
    """Test successful SSE refinement via the new GET stream endpoint."""
    # This test mocks the orchestrator, so the original resume content just needs
    # to be consistent for the reconstruction step.
    test_resume.content = VALID_RESUME_TWO_ROLES

    from resume_editor.app.api.routes.route_models import ExperienceResponse
    from resume_editor.app.models.resume.experience import (
        Project,
        ProjectOverview,
        Role,
        RoleBasics,
        RoleSummary,
    )

    mock_settings = UserSettings(
        user_id=test_user.id,
        llm_endpoint="http://llm.test",
        encrypted_api_key="key",
        llm_model_name="test-model",
    )
    mock_get_user_settings.return_value = mock_settings

    # Mock extractors to return valid data, including projects
    mock_project = Project(overview=ProjectOverview(title="A Cool Project"))
    mock_original_experience = ExperienceResponse(roles=[], projects=[mock_project])
    mock_extract_personal.return_value = MagicMock()
    mock_extract_education.return_value = MagicMock()
    mock_extract_experience.return_value = mock_original_experience
    mock_extract_certifications.return_value = MagicMock()
    mock_build_sections.return_value = "reconstructed content"

    # Mock the async generator from refine_experience_section
    refined_role1 = Role(
        basics=RoleBasics(
            company="Refined Company 1",
            title="Refined Role 1",
            start_date="2024-01-01",
        ),
        summary=RoleSummary(text="Refined Summary 1"),
    )
    refined_role1_data = refined_role1.model_dump(mode="json")
    refined_role2 = Role(
        basics=RoleBasics(
            company="Refined Company 2",
            title="Refined Role 2",
            start_date="2023-01-01",
        ),
        summary=RoleSummary(text="Refined Summary 2"),
    )
    refined_role2_data = refined_role2.model_dump(mode="json")

    async def mock_async_generator():
        yield {"status": "in_progress", "message": "doing stuff"}
        yield {"status": "introduction_generated", "data": "Generated Intro"}
        # Yield out of order to ensure sorting logic is tested
        yield {
            "status": "role_refined",
            "data": refined_role2_data,
            "original_index": 1,
        }
        yield {
            "status": "role_refined",
            "data": refined_role1_data,
            "original_index": 0,
        }

    mock_async_refine_experience.return_value = mock_async_generator()
    mock_create_refine_result_html.return_value = "<html>final refined html</html>"

    # Act
    with client_with_auth_and_resume.stream(
        "GET",
        "/api/resumes/1/refine/stream?job_description=a%20new%20job&generate_introduction=true",
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        text_content = response.read().decode("utf-8")

    # Assert
    events = text_content.strip().split("\n\n")
    # Expected: progress, introduction, done, close
    assert len(events) == 4, f"Expected 4 events, got {len(events)}: {events}"

    assert "event: progress" in events[0]
    assert "data: <li>doing stuff</li>" in events[0]
    assert "event: introduction_generated" in events[1]
    assert 'id="introduction-container"' in events[1]
    assert "event: done" in events[2]
    assert "data: <html>final refined html</html>" in events[2]
    assert "event: close" in events[3]

    # Assert mocks
    mock_async_refine_experience.assert_called_once_with(
        resume_content=VALID_RESUME_TWO_ROLES,
        job_description="a new job",
        llm_endpoint="http://llm.test",
        api_key="decrypted_key",
        llm_model_name="test-model",
        generate_introduction=True,
    )
    mock_extract_personal.assert_called_once_with(VALID_RESUME_TWO_ROLES)
    mock_extract_education.assert_called_once_with(VALID_RESUME_TWO_ROLES)
    mock_extract_experience.assert_called_once_with(VALID_RESUME_TWO_ROLES)
    mock_extract_certifications.assert_called_once_with(VALID_RESUME_TWO_ROLES)
    mock_build_sections.assert_called_once()
    reconstruct_kwargs = mock_build_sections.call_args.kwargs
    reconstructed_experience = reconstruct_kwargs["experience"]
    reconstructed_roles = reconstructed_experience.roles

    assert len(reconstructed_roles) == 2
    assert reconstructed_roles[0].summary.text == "Refined Summary 1"
    assert reconstructed_roles[1].summary.text == "Refined Summary 2"
    assert reconstructed_experience.projects == mock_original_experience.projects

    mock_create_refine_result_html.assert_called_once_with(
        1,
        "experience",
        "reconstructed content",
        job_description="a new job",
        introduction="Generated Intro",
    )

    mock_create_refine_result_html.assert_called_once_with(
        1,
        "experience",
        "reconstructed content",
        job_description="a new job",
        introduction="Generated Intro",
    )


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.resume_ai._create_refine_result_html")
@patch("resume_editor.app.api.routes.resume_ai.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume_ai.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_education_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
@patch("resume_editor.app.api.routes.resume_ai.async_refine_experience_section")
@patch(
    "resume_editor.app.api.routes.resume_ai.decrypt_data",
    return_value="decrypted_key",
)
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings")
async def test_refine_resume_stream_happy_path_gen_intro_false(
    mock_get_user_settings,
    mock_decrypt_data,
    mock_async_refine_experience,
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_create_refine_result_html,
    client_with_auth_and_resume,
    test_user,
    test_resume,
):
    """Test successful SSE refinement when generate_introduction is false."""
    test_resume.content = VALID_RESUME_TWO_ROLES

    from resume_editor.app.api.routes.route_models import ExperienceResponse
    from resume_editor.app.models.resume.experience import (
        Project,
        ProjectOverview,
        Role,
        RoleBasics,
        RoleSummary,
    )

    mock_settings = UserSettings(
        user_id=test_user.id,
        llm_endpoint="http://llm.test",
        encrypted_api_key="key",
        llm_model_name="test-model",
    )
    mock_get_user_settings.return_value = mock_settings

    mock_project = Project(overview=ProjectOverview(title="A Cool Project"))
    mock_original_experience = ExperienceResponse(roles=[], projects=[mock_project])
    mock_extract_experience.return_value = mock_original_experience
    mock_build_sections.return_value = "reconstructed content"

    refined_role1 = Role(
        basics=RoleBasics(
            company="Refined Company 1",
            title="Refined Role 1",
            start_date="2024-01-01",
        ),
        summary=RoleSummary(text="Refined Summary 1"),
    )
    refined_role1_data = refined_role1.model_dump(mode="json")

    async def mock_async_generator():
        yield {
            "status": "role_refined",
            "data": refined_role1_data,
            "original_index": 0,
        }

    mock_async_refine_experience.return_value = mock_async_generator()
    mock_create_refine_result_html.return_value = "<html>final refined html</html>"

    with client_with_auth_and_resume.stream(
        "GET",
        "/api/resumes/1/refine/stream?job_description=a%20new%20job&generate_introduction=false",
    ) as response:
        assert response.status_code == 200

    mock_async_refine_experience.assert_called_once_with(
        resume_content=VALID_RESUME_TWO_ROLES,
        job_description="a new job",
        llm_endpoint="http://llm.test",
        api_key="decrypted_key",
        llm_model_name="test-model",
        generate_introduction=False,
    )

    mock_create_refine_result_html.assert_called_once_with(
        1,
        "experience",
        "reconstructed content",
        job_description="a new job",
        introduction=None,
    )








@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.resume_ai.async_refine_experience_section")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
async def test_refine_resume_stream_introduction_is_none(
    mock_get_user_settings,
    mock_async_refine_experience,
    client_with_auth_and_resume,
):
    """Test that an introduction_generated event with None data is handled."""

    async def mock_generator():
        yield {"status": "introduction_generated", "data": None}
        yield {"status": "in_progress", "message": "doing stuff"}

    mock_async_refine_experience.return_value = mock_generator()

    with client_with_auth_and_resume.stream(
        "GET",
        "/api/resumes/1/refine/stream?job_description=job&generate_introduction=true",
    ) as response:
        assert response.status_code == 200
        text_content = response.read().decode("utf-8")

    events = text_content.strip().split("\n\n")

    # The empty introduction event should be ignored.
    # The stream continues and since no roles are refined, it sends an error.
    # Expected events: progress, error (since no roles are refined), and close.
    assert len(events) == 3
    assert "event: progress" in events[0]
    assert "data: <li>doing stuff</li>" in events[0]
    assert "event: error" in events[1]
    assert "Refinement finished, but no roles were found to refine." in events[1]
    assert "event: close" in events[2]




@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.resume_ai.async_refine_experience_section")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
async def test_refine_resume_stream_orchestration_error(
    mock_get_user_settings,
    mock_async_refine_experience,
    client_with_auth_and_resume,
):
    """Test that an error raised by the orchestrator is handled in the SSE stream."""

    # Mock the async generator to raise an error
    mock_async_refine_experience.side_effect = ValueError("Orchestration failed")

    # Act
    with client_with_auth_and_resume.stream(
        "GET",
        "/api/resumes/1/refine/stream?job_description=a%20new%20job",
    ) as response:
        # Assert
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        text_content = response.read().decode("utf-8")

    events = text_content.strip().split("\n\n")
    assert len(events) == 2  # error event, and close event

    error_event = events[0]
    assert "event: error" in error_event
    assert (
        "data: <div role='alert' class='text-red-500 p-2'>Refinement failed: Orchestration failed</div>"
        in error_event
    )

    close_event = events[1]
    assert "event: close" in close_event
    assert "data: stream complete" in close_event

    mock_async_refine_experience.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "malformed_event",
    [
        {"status": "processing", "message": "unhandled status"},  # Unknown status
        {"status": "role_refined", "data": {"some": "data"}},  # Missing index
        {"status": "role_refined", "original_index": 0},  # Missing data
        {"status": "role_refined", "data": None, "original_index": 0},
        {"status": "role_refined", "data": {"some": "data"}, "original_index": None},
    ],
)
@patch("resume_editor.app.api.routes.resume_ai.async_refine_experience_section")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
async def test_refine_resume_stream_malformed_events(
    mock_get_user_settings,
    mock_async_refine_experience,
    malformed_event,
    client_with_auth_and_resume,
):
    """Test SSE stream handles unknown or malformed events gracefully."""

    async def mock_async_generator():
        yield malformed_event

    mock_async_refine_experience.return_value = mock_async_generator()

    # Act
    with client_with_auth_and_resume.stream(
        "GET",
        "/api/resumes/1/refine/stream?job_description=a%20new%20job",
    ) as response:
        # Assert
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        text_content = response.read().decode("utf-8")

    # The generator should not add any roles, so an error event for "no roles"
    # should be yielded, followed by the close event.
    events = text_content.strip().split("\n\n")
    assert len(events) == 2, f"Expected 2 events, got {len(events)}: {events}"
    assert "event: error" in events[0]
    assert "Refinement finished, but no roles were found to refine." in events[0]
    assert "text-yellow-500" in events[0]
    assert "event: close" in events[1]

    mock_async_refine_experience.assert_called_once()


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.resume_ai.async_refine_experience_section")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
async def test_refine_resume_stream_empty_generator(
    mock_get_user_settings,
    mock_async_refine_experience,
    client_with_auth_and_resume,
):
    """Test SSE stream with an empty generator from the LLM service."""

    # Mock the async generator to be empty
    async def mock_empty_async_generator():
        return
        yield  # pylint: disable=unreachable

    mock_async_refine_experience.return_value = mock_empty_async_generator()

    # Act
    with client_with_auth_and_resume.stream(
        "GET",
        "/api/resumes/1/refine/stream?job_description=a%20new%20job",
    ) as response:
        # Assert
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        text_content = response.read().decode("utf-8")

    events = text_content.strip().split("\n\n")
    assert len(events) == 2, f"Expected 2 events, but got {len(events)}: {events}"
    assert "event: error" in events[0]
    assert "Refinement finished, but no roles were found to refine." in events[0]
    assert "text-yellow-500" in events[0]
    assert "event: close" in events[1]

    mock_async_refine_experience.assert_called_once()


@pytest.mark.asyncio
@patch("resume_editor.app.llm.orchestration.analyze_job_description", new_callable=AsyncMock)
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
async def test_refine_resume_stream_no_roles_in_resume(
    mock_get_user_settings,
    mock_analyze_job,
    client_with_auth_and_resume,
    test_resume,
):
    """Test SSE stream when the resume has no roles in the experience section."""
    from resume_editor.app.llm.models import JobAnalysis

    # Arrange
    resume_with_no_roles = """# Personal
Name: Test

# Experience
## Projects
### Project
#### Overview
Title: A project
#### Description
A project with no roles.
"""
    test_resume.content = resume_with_no_roles
    mock_analyze_job.return_value = (
        JobAnalysis(key_skills=[], primary_duties=[], themes=[]),
        None,
    )

    # Act
    with client_with_auth_and_resume.stream(
        "GET", "/api/resumes/1/refine/stream?job_description=job"
    ) as response:
        assert response.status_code == 200
        text_content = response.read().decode("utf-8")

    # Assert
    events = text_content.strip().split("\n\n")
    assert len(events) == 4, f"Expected 4 events, got {len(events)}: {events}"

    assert "event: progress" in events[0] and "Parsing resume..." in events[0]
    assert "event: progress" in events[1] and "Analyzing job description..." in events[1]
    assert "event: error" in events[2]
    # This message comes from sse_generator when refined_roles is empty.
    # The orchestrator returns early in this case, leading to an empty refined_roles dict.
    assert "Refinement finished, but no roles were found to refine" in events[2]
    assert "text-yellow-500" in events[2]
    assert "event: close" in events[3]
    mock_analyze_job.assert_called_once()


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.resume_ai.async_refine_experience_section")
@patch("resume_editor.app.api.routes.resume_ai.decrypt_data", side_effect=InvalidToken)
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings")
async def test_refine_resume_stream_invalid_token(
    mock_get_user_settings,
    mock_decrypt_data,
    mock_async_refine_experience,
    client_with_auth_and_resume,
    test_user,
):
    """Test SSE stream reports error on API key decryption failure."""
    mock_settings = UserSettings(user_id=test_user.id, encrypted_api_key="key")
    mock_get_user_settings.return_value = mock_settings

    with client_with_auth_and_resume.stream(
        "GET", "/api/resumes/1/refine/stream?job_description=job"
    ) as response:
        assert response.status_code == 200
        text_content = response.read().decode("utf-8")

    events = text_content.strip().split("\n\n")
    assert len(events) == 2
    assert "event: error" in events[0]
    assert "Invalid API key. Please update your settings." in events[0]
    assert "text-red-500" in events[0]
    assert "event: close" in events[1]
    mock_async_refine_experience.assert_not_called()


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.resume_ai.async_refine_experience_section")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
async def test_refine_resume_stream_auth_error(
    mock_get_user_settings,
    mock_async_refine_experience,
    client_with_auth_and_resume,
):
    """Test SSE stream reports error on LLM authentication failure within sse_generator."""
    mock_async_refine_experience.side_effect = AuthenticationError(
        message="auth error", response=Mock(), body=None
    )

    with client_with_auth_and_resume.stream(
        "GET", "/api/resumes/1/refine/stream?job_description=job"
    ) as response:
        assert response.status_code == 200
        text_content = response.read().decode("utf-8")

    events = text_content.strip().split("\n\n")
    assert len(events) == 2
    assert "event: error" in events[0]
    assert "LLM authentication failed. Please check your API key." in events[0]
    assert "text-red-500" in events[0]
    assert "event: close" in events[1]




@pytest.mark.asyncio
@pytest.mark.parametrize(
    "exception,expected_message_part",
    [
        (ValueError("value error"), "Refinement failed: value error"),
        (Exception("generic error"), "An unexpected error occurred."),
    ],
)
@patch("resume_editor.app.api.routes.resume_ai.async_refine_experience_section")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
async def test_refine_resume_stream_errors_in_generator(
    mock_get_user_settings,
    mock_async_refine_experience,
    exception,
    expected_message_part,
    client_with_auth_and_resume,
):
    """
    Test that the SSE stream correctly handles exceptions raised from the
    orchestration function, which are caught inside the sse_generator.
    """
    mock_async_refine_experience.side_effect = exception

    with client_with_auth_and_resume.stream(
        "GET", "/api/resumes/1/refine/stream?job_description=job"
    ) as response:
        assert response.status_code == 200
        text_content = response.read().decode("utf-8")

    events = text_content.strip().split("\n\n")
    assert len(events) == 2
    assert "event: error" in events[0]
    assert expected_message_part in events[0]
    assert "text-red-500" in events[0]
    assert "event: close" in events[1]


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.resume_ai.async_refine_experience_section")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
async def test_refine_resume_stream_client_disconnect(
    mock_get_user_settings,
    mock_async_refine_experience,
    client_with_auth_and_resume,
    caplog,
):
    """Test that the SSE stream handles a ClientDisconnect gracefully."""
    from starlette.middleware.base import ClientDisconnect

    async def mock_generator_with_disconnect():
        raise ClientDisconnect()
        yield  # Make it a generator

    mock_async_refine_experience.return_value = mock_generator_with_disconnect()

    with caplog.at_level(logging.WARNING):
        with client_with_auth_and_resume.stream(
            "GET",
            "/api/resumes/1/refine/stream?job_description=job",
        ) as response:
            assert response.status_code == 200
            # The generator should yield the close event from the finally block
            # even when the client disconnects.
            content = response.read()
            assert b"event: close" in content

    assert "Client disconnected from SSE stream for resume 1." in caplog.text
    mock_async_refine_experience.assert_called_once()


@patch("resume_editor.app.api.routes.resume_ai.refine_resume_section_with_llm")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
def test_refine_resume_json_decode_error_htmx(
    mock_get_user_settings,
    mock_refine_llm,
    client_with_auth_and_resume,
):
    """Test resume refinement HTMX request when the LLM call fails with a ValueError."""
    # Arrange
    mock_refine_llm.side_effect = ValueError(
        "The AI service returned an unexpected response. Please try again."
    )

    # Act
    response = client_with_auth_and_resume.post(
        "/api/resumes/1/refine",
        data={
            "job_description": "job",
            "target_section": "personal",
            "generate_introduction": "true",
        },
        headers={"HX-Request": "true"},
    )

    # Assert
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Refinement failed:" in response.text
    assert (
        "The AI service returned an unexpected response. Please try again."
        in response.text
    )


@patch("resume_editor.app.api.routes.resume_ai.refine_resume_section_with_llm")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
def test_refine_resume_json_decode_error_non_htmx(
    mock_get_user_settings,
    mock_refine_llm,
    client_with_auth_and_resume,
):
    """Test resume refinement non-HTMX request when the LLM call fails with a ValueError."""
    # Arrange
    error_message = "The AI service returned an unexpected response. Please try again."
    mock_refine_llm.side_effect = ValueError(error_message)

    # Act
    response = client_with_auth_and_resume.post(
        "/api/resumes/1/refine",
        data={
            "job_description": "job",
            "target_section": "personal",
            "generate_introduction": "true",
        },
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": error_message}




@patch("resume_editor.app.api.routes.resume_ai._generate_resume_detail_html")
@patch("resume_editor.app.api.routes.resume_ai.update_resume_db")
@patch("resume_editor.app.api.routes.resume_ai.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume_ai.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume_ai.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_education_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
def test_accept_refined_resume_overwrite_personal(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_pre_save,
    mock_update_db,
    mock_gen_detail_html,
    client_with_auth_and_resume,
    test_resume,
):
    """Test accepting a 'personal' refinement and overwriting the existing resume."""
    from resume_editor.app.api.routes.route_models import (
        PersonalInfoResponse,
        RefineTargetSection,
    )

    # Arrange
    refined_content = "# Personal\nname: Refined"
    intro_text = "This is an introduction."
    mock_extract_personal.return_value = PersonalInfoResponse(name="Refined")
    mock_build_sections.return_value = "reconstructed content"
    mock_gen_detail_html.return_value = "<html>Detail View</html>"
    mock_update_db.return_value = test_resume

    # Act
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/accept",
        data={
            "refined_content": refined_content,
            "target_section": RefineTargetSection.PERSONAL.value,
            "introduction": intro_text,
        },
    )

    # Assert
    assert response.status_code == 200
    assert response.text == "<html>Detail View</html>"
    mock_extract_personal.assert_called_once_with(refined_content)
    mock_extract_education.assert_called_once_with(test_resume.content)
    mock_extract_experience.assert_called_once_with(test_resume.content)
    mock_extract_certifications.assert_called_once_with(test_resume.content)
    mock_build_sections.assert_called_once()
    assert mock_build_sections.call_args.kwargs["personal_info"].name == "Refined"
    mock_pre_save.assert_called_once_with("reconstructed content", test_resume.content)
    mock_update_db.assert_called_once()
    assert mock_update_db.call_args.kwargs["content"] == "reconstructed content"
    assert mock_update_db.call_args.kwargs["introduction"] == intro_text
    mock_gen_detail_html.assert_called_once_with(test_resume)


@patch("resume_editor.app.api.routes.resume_ai._generate_resume_detail_html")
@patch("resume_editor.app.api.routes.resume_ai.update_resume_db")
@patch("resume_editor.app.api.routes.resume_ai.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume_ai.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume_ai.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_education_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
def test_accept_refined_resume_overwrite_education(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_pre_save,
    mock_update_db,
    mock_gen_detail_html,
    client_with_auth_and_resume,
    test_resume,
):
    """Test accepting an 'education' refinement and overwriting the resume."""
    from resume_editor.app.api.routes.route_models import (
        EducationResponse,
        RefineTargetSection,
    )

    refined_content = "# Education\n..."
    mock_extract_education.return_value = EducationResponse(degrees=[])
    mock_gen_detail_html.return_value = "<html>Detail View</html>"
    mock_update_db.return_value = test_resume

    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/accept",
        data={
            "refined_content": refined_content,
            "target_section": RefineTargetSection.EDUCATION.value,
        },
    )
    assert response.status_code == 200
    assert response.text == "<html>Detail View</html>"
    mock_extract_education.assert_called_once_with(refined_content)
    mock_extract_personal.assert_called_once_with(test_resume.content)
    mock_gen_detail_html.assert_called_once_with(test_resume)


@patch("resume_editor.app.api.routes.resume_ai._generate_resume_detail_html")
@patch("resume_editor.app.api.routes.resume_ai.update_resume_db")
@patch("resume_editor.app.api.routes.resume_ai.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume_ai.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume_ai.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_education_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
def test_accept_refined_resume_overwrite_experience(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_pre_save,
    mock_update_db,
    mock_gen_detail_html,
    client_with_auth_and_resume,
    test_resume,
):
    """Test accepting an 'experience' refinement and overwriting the resume."""
    from resume_editor.app.api.routes.route_models import (
        ExperienceResponse,
        RefineTargetSection,
    )

    refined_content = "# Experience\n..."
    mock_extract_experience.return_value = ExperienceResponse(roles=[], projects=[])
    mock_gen_detail_html.return_value = "<html>Detail View</html>"
    mock_update_db.return_value = test_resume

    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/accept",
        data={
            "refined_content": refined_content,
            "target_section": RefineTargetSection.EXPERIENCE.value,
        },
    )

    assert response.status_code == 200
    assert response.text == "<html>Detail View</html>"
    mock_extract_experience.assert_called_once_with(refined_content)
    mock_extract_personal.assert_called_once_with(test_resume.content)
    mock_gen_detail_html.assert_called_once_with(test_resume)


@patch("resume_editor.app.api.routes.resume_ai._generate_resume_detail_html")
@patch("resume_editor.app.api.routes.resume_ai.update_resume_db")
@patch("resume_editor.app.api.routes.resume_ai.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume_ai.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume_ai.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_education_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
def test_accept_refined_resume_overwrite_certifications(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_pre_save,
    mock_update_db,
    mock_gen_detail_html,
    client_with_auth_and_resume,
    test_resume,
):
    """Test accepting a 'certifications' refinement and overwriting the resume."""
    from resume_editor.app.api.routes.route_models import (
        CertificationsResponse,
        RefineTargetSection,
    )

    refined_content = "# Certifications\n..."
    mock_extract_certifications.return_value = CertificationsResponse(certifications=[])
    mock_gen_detail_html.return_value = "<html>Detail View</html>"
    mock_update_db.return_value = test_resume

    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/accept",
        data={
            "refined_content": refined_content,
            "target_section": RefineTargetSection.CERTIFICATIONS.value,
        },
    )
    assert response.status_code == 200
    assert response.text == "<html>Detail View</html>"
    mock_extract_certifications.assert_called_once_with(refined_content)
    mock_extract_personal.assert_called_once_with(test_resume.content)
    mock_gen_detail_html.assert_called_once_with(test_resume)


@patch("resume_editor.app.api.routes.resume_ai._generate_resume_detail_html")
@patch("resume_editor.app.api.routes.resume_ai.update_resume_db")
@patch("resume_editor.app.api.routes.resume_ai.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume_ai.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume_ai.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_education_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
def test_accept_refined_resume_overwrite_full(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_pre_save,
    mock_update_db,
    mock_gen_detail_html,
    client_with_auth_and_resume,
    test_resume,
):
    """Test accepting a 'full' refinement and overwriting the existing resume."""
    from resume_editor.app.api.routes.route_models import RefineTargetSection

    # Arrange
    refined_content = "# Personal\nname: Full Refined"
    mock_gen_detail_html.return_value = "<html>Detail View</html>"
    mock_update_db.return_value = test_resume

    # Act
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/accept",
        data={
            "refined_content": refined_content,
            "target_section": RefineTargetSection.FULL.value,
        },
    )

    # Assert
    assert response.status_code == 200
    assert response.text == "<html>Detail View</html>"
    mock_extract_personal.assert_not_called()
    mock_extract_education.assert_not_called()
    mock_extract_experience.assert_not_called()
    mock_extract_certifications.assert_not_called()
    mock_build_sections.assert_not_called()

    mock_pre_save.assert_called_once_with(refined_content, test_resume.content)
    mock_update_db.assert_called_once()
    assert mock_update_db.call_args.kwargs["content"] == refined_content
    mock_gen_detail_html.assert_called_once_with(test_resume)


@patch("resume_editor.app.api.routes.resume_ai._generate_resume_list_html")
@patch("resume_editor.app.api.routes.resume_ai._generate_resume_detail_html")
@patch("resume_editor.app.api.routes.resume_ai.get_user_resumes")
@patch("resume_editor.app.api.routes.resume_ai.create_resume_db")
@patch("resume_editor.app.api.routes.resume_ai.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume_ai.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume_ai.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_education_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
def test_save_refined_resume_as_new_full(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_pre_save,
    mock_create_db,
    mock_get_resumes,
    mock_gen_detail_html,
    mock_gen_list_html,
    client_with_auth_and_resume,
    test_user,
    test_resume,
):
    """Test accepting a 'full' refinement and saving it as a new resume."""
    from resume_editor.app.api.routes.route_models import RefineTargetSection

    # Arrange
    refined_content = "# Personal\n..."
    intro_text = "This is a new introduction."
    new_resume = DatabaseResume(
        user_id=test_user.id,
        name="New Name",
        content=refined_content,
        is_base=False,
        parent_id=test_resume.id,
        introduction=intro_text,
    )
    new_resume.id = 2
    mock_create_db.return_value = new_resume
    mock_get_resumes.return_value = [test_resume, new_resume]
    mock_gen_detail_html.return_value = "<html>New Detail</html>"
    mock_gen_list_html.return_value = "<html>Sidebar</html>"

    # Act
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/save_as_new",
        data={
            "refined_content": refined_content,
            "target_section": RefineTargetSection.FULL.value,
            "new_resume_name": "New Name",
            "job_description": "A job description",
            "introduction": intro_text,
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
    mock_create_db.assert_called_once_with(
        db=ANY,
        user_id=test_user.id,
        name="New Name",
        content=refined_content,
        is_base=False,
        parent_id=test_resume.id,
        job_description="A job description",
        introduction=intro_text,
    )
    mock_get_resumes.assert_called_once()
    mock_gen_detail_html.assert_called_once_with(new_resume)
    mock_gen_list_html.assert_called_once_with(
        base_resumes=[test_resume],
        refined_resumes=[new_resume],
        selected_resume_id=new_resume.id,
    )

    assert '<div id="left-sidebar-content" hx-swap-oob="true">' in response.text
    assert "<html>Sidebar</html>" in response.text
    assert "<html>New Detail</html>" in response.text


@patch("resume_editor.app.api.routes.resume_ai._generate_resume_list_html")
@patch("resume_editor.app.api.routes.resume_ai._generate_resume_detail_html")
@patch("resume_editor.app.api.routes.resume_ai.get_user_resumes")
@patch("resume_editor.app.api.routes.resume_ai.create_resume_db")
@patch("resume_editor.app.api.routes.resume_ai.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume_ai.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume_ai.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_education_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
def test_save_refined_resume_as_new_partial_with_job_desc(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_pre_save,
    mock_create_db,
    mock_get_resumes,
    mock_gen_detail_html,
    mock_gen_list_html,
    client_with_auth_and_resume,
    test_user,
    test_resume,
):
    """Test accepting a partial refinement with job desc and saving it as new."""
    from resume_editor.app.api.routes.route_models import (
        PersonalInfoResponse,
        RefineTargetSection,
    )

    # Arrange
    refined_content = "# Personal\nname: Refined New"
    reconstructed_content = "reconstructed content for new resume"
    intro_text = "The new intro."

    mock_extract_personal.return_value = PersonalInfoResponse(name="Refined New")
    mock_build_sections.return_value = reconstructed_content

    new_resume = DatabaseResume(
        user_id=test_user.id,
        name="New Name",
        content=reconstructed_content,
        is_base=False,
        parent_id=test_resume.id,
        introduction=intro_text,
    )
    new_resume.id = 2
    mock_create_db.return_value = new_resume
    mock_get_resumes.return_value = [test_resume, new_resume]
    mock_gen_detail_html.return_value = "<html>New Detail</html>"
    mock_gen_list_html.return_value = "<html>Sidebar</html>"

    # Act
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/save_as_new",
        data={
            "refined_content": refined_content,
            "target_section": RefineTargetSection.PERSONAL.value,
            "new_resume_name": "New Name",
            "job_description": "A job description",
            "introduction": intro_text,
        },
    )

    # Assert
    assert response.status_code == 200
    mock_extract_personal.assert_called_once_with(refined_content)
    mock_extract_education.assert_called_once_with(test_resume.content)
    mock_build_sections.assert_called_once()
    mock_pre_save.assert_called_once_with(reconstructed_content, test_resume.content)
    mock_create_db.assert_called_once_with(
        db=ANY,
        user_id=test_user.id,
        name="New Name",
        content=reconstructed_content,
        is_base=False,
        parent_id=test_resume.id,
        job_description="A job description",
        introduction=intro_text,
    )
    mock_gen_detail_html.assert_called_once_with(new_resume)
    mock_gen_list_html.assert_called_once_with(
        base_resumes=[test_resume],
        refined_resumes=[new_resume],
        selected_resume_id=new_resume.id,
    )

    assert '<div id="left-sidebar-content" hx-swap-oob="true">' in response.text
    assert "<html>Sidebar</html>" in response.text
    assert "<html>New Detail</html>" in response.text


@patch("resume_editor.app.api.routes.resume_ai._generate_resume_list_html")
@patch("resume_editor.app.api.routes.resume_ai._generate_resume_detail_html")
@patch("resume_editor.app.api.routes.resume_ai.get_user_resumes")
@patch("resume_editor.app.api.routes.resume_ai.create_resume_db")
@patch("resume_editor.app.api.routes.resume_ai.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume_ai.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume_ai.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_education_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
def test_save_refined_resume_as_new_partial_without_job_desc(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_pre_save,
    mock_create_db,
    mock_get_resumes,
    mock_gen_detail_html,
    mock_gen_list_html,
    client_with_auth_and_resume,
    test_user,
    test_resume,
):
    """Test accepting a partial refinement without job desc and saving as new."""
    from resume_editor.app.api.routes.route_models import (
        PersonalInfoResponse,
        RefineTargetSection,
    )

    # Arrange
    refined_content = "# Personal\nname: Refined New"
    reconstructed_content = "reconstructed content for new resume"

    mock_extract_personal.return_value = PersonalInfoResponse(name="Refined New")
    mock_build_sections.return_value = reconstructed_content

    new_resume = DatabaseResume(
        user_id=test_user.id,
        name="New Name",
        content=reconstructed_content,
        is_base=False,
        parent_id=test_resume.id,
    )
    new_resume.id = 2
    mock_create_db.return_value = new_resume
    mock_get_resumes.return_value = [test_resume, new_resume]
    mock_gen_detail_html.return_value = "<html>New Detail</html>"
    mock_gen_list_html.return_value = "<html>Sidebar</html>"

    # Act
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/save_as_new",
        data={
            "refined_content": refined_content,
            "target_section": RefineTargetSection.PERSONAL.value,
            "new_resume_name": "New Name",
            # No job_description
        },
    )

    # Assert
    assert response.status_code == 200
    mock_extract_personal.assert_called_once_with(refined_content)
    mock_extract_education.assert_called_once_with(test_resume.content)
    mock_build_sections.assert_called_once()
    mock_pre_save.assert_called_once_with(reconstructed_content, test_resume.content)
    mock_create_db.assert_called_once_with(
        db=ANY,
        user_id=test_user.id,
        name="New Name",
        content=reconstructed_content,
        is_base=False,
        parent_id=test_resume.id,
        job_description=None,  # Expect None
        introduction=None,
    )
    mock_gen_detail_html.assert_called_once_with(new_resume)
    mock_gen_list_html.assert_called_once_with(
        base_resumes=[test_resume],
        refined_resumes=[new_resume],
        selected_resume_id=new_resume.id,
    )

    assert '<div id="left-sidebar-content" hx-swap-oob="true">' in response.text
    assert "<html>Sidebar</html>" in response.text
    assert "<html>New Detail</html>" in response.text


@patch("resume_editor.app.api.routes.resume_ai.perform_pre_save_validation")
def test_save_refined_resume_as_new_reconstruction_error(
    mock_pre_save,
    client_with_auth_and_resume,
    test_resume,
):
    """Test that a reconstruction error is handled when saving a new refined resume."""
    from resume_editor.app.api.routes.route_models import RefineTargetSection

    # Arrange
    mock_pre_save.side_effect = HTTPException(status_code=422, detail="Invalid")
    refined_content = "# Personal\nname: Refined New"

    # Act
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/save_as_new",
        data={
            "refined_content": refined_content,
            "target_section": RefineTargetSection.FULL.value,
            "new_resume_name": "New Name",
            "job_description": "A job description",
        },
    )

    # Assert
    assert response.status_code == 422
    assert "Failed to reconstruct" in response.json()["detail"]


@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
def test_accept_refined_resume_reconstruction_error(
    mock_extract_personal,
    client_with_auth_and_resume,
    test_resume,
):
    """Test that an error during reconstruction is handled."""
    from resume_editor.app.api.routes.route_models import RefineTargetSection

    # Arrange
    mock_extract_personal.side_effect = ValueError("test error")
    refined_content = "# Personal\nname: Refined"

    # Act
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/accept",
        data={
            "refined_content": refined_content,
            "target_section": RefineTargetSection.PERSONAL.value,
        },
    )

    # Assert
    assert response.status_code == 422
    assert "Failed to reconstruct" in response.json()["detail"]


def test_save_refined_resume_as_new_no_name(
    client_with_auth_and_resume,
    test_resume,
):
    """Test that saving as new without a name fails."""
    from resume_editor.app.api.routes.route_models import RefineTargetSection

    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/save_as_new",
        data={
            "refined_content": "...",
            "target_section": RefineTargetSection.FULL.value,
            "new_resume_name": "",
        },
    )
    assert response.status_code == 400
    assert "New resume name is required" in response.json()["detail"]


def test_accept_refined_resume_invalid_section(
    client_with_auth_and_resume,
    test_resume,
):
    """Test that providing an invalid section to the accept endpoint fails."""
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/accept",
        data={
            "refined_content": "content",
            "target_section": "invalid_section",
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


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.resume_ai._create_refine_result_html")
@patch("resume_editor.app.api.routes.resume_ai.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume_ai.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_education_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
@patch("resume_editor.app.llm.orchestration.refine_role", new_callable=AsyncMock)
@patch(
    "resume_editor.app.llm.orchestration.analyze_job_description",
    new_callable=AsyncMock,
)
@patch("resume_editor.app.llm.orchestration.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
async def test_refine_resume_stream_integrated(
    mock_get_user_settings,
    mock_orch_extract_experience,
    mock_analyze_job,
    mock_refine_role,
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_create_html,
    client_with_auth_and_resume,
    test_resume,
):
    """
    Test the full SSE stream generation with mocked LLM calls, including reconstruction.
    """
    from resume_editor.app.api.routes.route_models import ExperienceResponse
    from resume_editor.app.llm.models import JobAnalysis, RefinedRole
    from resume_editor.app.models.resume.experience import (
        Project,
        ProjectDescription,
        ProjectOverview,
        ProjectSkills,
        Role,
        RoleBasics,
        RoleSummary,
    )

    # Arrange
    # Use resume with two roles to test ordering
    test_resume.content = VALID_RESUME_TWO_ROLES

    # 1. Mock orchestrator dependencies
    mock_role_a = Role(
        basics=RoleBasics(company="A Company", title="A Role", start_date="2024-01-01")
    )
    mock_role_b = Role(
        basics=RoleBasics(company="B Company", title="B Role", start_date="2023-01-01")
    )
    mock_orch_extract_experience.return_value = ExperienceResponse(
        roles=[mock_role_a, mock_role_b], projects=[]
    )

    mock_job_analysis = JobAnalysis(
        key_skills=["a", "b"], primary_duties=["c"], themes=["d"]
    )
    mock_analyze_job.return_value = (
        mock_job_analysis,
        "Generated intro from orchestration",
    )

    mock_refined_role1 = RefinedRole(
        basics=RoleBasics(
            company="A Company", title="Refined A Role", start_date="2024-01-01"
        ),
        summary=RoleSummary(text="Refined Summary for A"),
    )
    mock_refined_role2 = RefinedRole(
        basics=RoleBasics(
            company="B Company", title="Refined B Role", start_date="2023-01-01"
        ),
        summary=RoleSummary(text="Refined Summary for B"),
    )

    # Mock the refinement to complete out of order
    async def refine_role_side_effect(*args, **kwargs):
        role_title = kwargs["role"].basics.title
        if role_title == "A Role":
            await _real_asyncio_sleep(0.02)  # Slower task
            return mock_refined_role1
        # B Role
        await _real_asyncio_sleep(0.01)  # Faster task
        return mock_refined_role2

    mock_refine_role.side_effect = refine_role_side_effect

    # 2. Mock reconstruction dependencies
    mock_extract_personal.return_value = MagicMock()
    mock_extract_education.return_value = MagicMock()
    # For experience, return a mock with projects to ensure they are preserved
    mock_project = Project(
        overview=ProjectOverview(title="Test Project"),
        description=ProjectDescription(text="A project description."),
        skills=ProjectSkills(skills=["testing"]),
    )
    mock_original_experience = ExperienceResponse(roles=[], projects=[mock_project])
    mock_extract_experience.return_value = mock_original_experience
    mock_extract_certifications.return_value = MagicMock()
    mock_build_sections.return_value = "reconstructed content"
    mock_create_html.return_value = "<html>final refined html</html>"

    # Act
    with client_with_auth_and_resume.stream(
        "GET",
        "/api/resumes/1/refine/stream?job_description=a%20new%20job&generate_introduction=true",
    ) as response:
        assert response.status_code == 200
        text_content = response.read().decode("utf-8")

    # Assert
    events = text_content.strip().split("\n\n")

    # Expected events: progress, progress, intro, 2x progress (refining), done, close
    assert len(events) == 7, f"Expected 7 events, but got {len(events)}: {events}"

    assert "event: progress" in events[0] and "Parsing resume" in events[0]
    assert "event: progress" in events[1] and "Analyzing job" in events[1]

    intro_event = next(e for e in events if "event: introduction_generated" in e)
    assert 'id="introduction-container"' in intro_event

    refining_events = [e for e in events if "Refining role" in e]
    assert len(refining_events) == 2
    assert any("Refining role &#x27;A Role @ A Company&#x27;..." in e for e in refining_events)
    assert any("Refining role &#x27;B Role @ B Company&#x27;..." in e for e in refining_events)

    done_event = next(e for e in events if "event: done" in e)
    assert "data: <html>final refined html</html>" in done_event

    close_event = next(e for e in events if "event: close" in e)
    assert close_event is not None

    # Assert mocks
    mock_analyze_job.assert_called_once()
    assert mock_refine_role.call_count == 2  # We have two roles in the fixture

    mock_extract_personal.assert_called_once()
    mock_build_sections.assert_called_once()

    # Check that the refined roles were re-ordered correctly before reconstruction
    reconstruct_kwargs = mock_build_sections.call_args.kwargs
    reconstructed_roles = reconstruct_kwargs["experience"].roles
    assert len(reconstructed_roles) == 2
    assert reconstructed_roles[0].basics.title == "Refined A Role"
    assert reconstructed_roles[1].basics.title == "Refined B Role"

    # Ensure original projects were preserved
    assert (
        reconstruct_kwargs["experience"].projects
        == mock_original_experience.projects
    )

    mock_create_html.assert_called_once_with(
        1,
        "experience",
        "reconstructed content",
        job_description="a new job",
        introduction="Generated intro from orchestration",
    )


@patch("resume_editor.app.api.routes.resume_ai._generate_resume_detail_html")
def test_discard_refined_resume(
    mock_generate_html, client_with_auth_and_resume, test_resume
):
    """Test the discard endpoint returns the original resume detail HTML."""
    # Arrange
    mock_generate_html.return_value = "<div>Original Detail HTML</div>"

    # Act
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/discard"
    )

    # Assert
    assert response.status_code == 200
    assert response.text == "<div>Original Detail HTML</div>"
    mock_generate_html.assert_called_once_with(test_resume)
