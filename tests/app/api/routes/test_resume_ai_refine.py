from unittest.mock import ANY, Mock, patch

import pytest
from cryptography.fernet import InvalidToken
from fastapi.testclient import TestClient
from openai import AuthenticationError

from resume_editor.app.core.auth import get_current_user_from_cookie
from resume_editor.app.core.config import get_settings
from resume_editor.app.database.database import get_db
from resume_editor.app.main import create_app
from resume_editor.app.models.resume_model import Resume as DatabaseResume
from resume_editor.app.models.user import User as DBUser
from resume_editor.app.models.user_settings import UserSettings

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
