from unittest.mock import ANY, MagicMock, Mock, patch

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
    mock_refine_llm.return_value = "refined"

    # Act
    response = client_with_auth_and_resume.post(
        "/api/resumes/1/refine",
        data={"job_description": "job", "target_section": "personal"},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"refined_content": "refined"}
    mock_get_user_settings.assert_called_once_with(mock_db_session, test_user.id)
    mock_decrypt_data.assert_called_once_with("key")
    mock_refine_llm.assert_called_once_with(
        resume_content=VALID_MINIMAL_RESUME_CONTENT,
        job_description="job",
        target_section="personal",
        llm_endpoint="http://llm.test",
        api_key="decrypted_key",
        llm_model_name="test-model",
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
    mock_refine_llm.return_value = "refined"

    # Act
    response = client_with_auth_and_resume.post(
        "/api/resumes/1/refine",
        data={"job_description": "job", "target_section": "personal"},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"refined_content": "refined"}
    mock_get_user_settings.assert_called_once_with(mock_db_session, test_user.id)
    mock_refine_llm.assert_called_once_with(
        resume_content=VALID_MINIMAL_RESUME_CONTENT,
        job_description="job",
        target_section="personal",
        llm_endpoint=None,
        api_key=None,
        llm_model_name=None,
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
    mock_refine_llm.return_value = "refined"

    # Act
    response = client_with_auth_and_resume.post(
        "/api/resumes/1/refine",
        data={"job_description": "job", "target_section": "personal"},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"refined_content": "refined"}
    mock_refine_llm.assert_called_once_with(
        resume_content=VALID_MINIMAL_RESUME_CONTENT,
        job_description="job",
        target_section="personal",
        llm_endpoint="http://llm.test",
        api_key=None,
        llm_model_name="test-model",
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
        data={"job_description": "job", "target_section": "personal"},
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
        data={"job_description": "job", "target_section": "personal"},
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
        data={"job_description": "job", "target_section": "personal"},
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
        data={"job_description": "job", "target_section": "personal"},
        headers={"HX-Request": "true"},
    )

    # Assert
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert (
        "LLM authentication failed. Please check your API key in settings."
        in response.text
    )


@pytest.mark.parametrize("target_section", ["personal", "experience"])
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
        data={"job_description": "job", "target_section": target_section},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Invalid API key. Please update your settings.",
    }
    mock_get_user_settings.assert_called_once()
    mock_decrypt_data.assert_called_once_with("key")


@patch("resume_editor.app.api.routes.resume_ai.refine_resume_section_with_llm")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
def test_refine_resume_post_for_experience_fails(
    mock_get_user_settings,
    mock_refine_llm,
    client_with_auth_and_resume,
):
    """Test that POST /refine for 'experience' section now fails correctly."""
    # Arrange
    error_message = (
        "Experience section refinement must be called via the async 'refine_experience_section' method."
    )
    mock_refine_llm.side_effect = ValueError(error_message)

    # Act
    response = client_with_auth_and_resume.post(
        "/api/resumes/1/refine",
        data={"job_description": "job", "target_section": "experience"},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == error_message


@pytest.mark.parametrize("target_section", ["personal", "experience"])
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
        data={"job_description": "job", "target_section": target_section},
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


@patch("resume_editor.app.api.routes.resume_ai.refine_resume_section_with_llm")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
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
        data={"job_description": "job", "target_section": "personal"},
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


@patch("resume_editor.app.api.routes.resume_ai.refine_resume_section_with_llm")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
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
        data={"job_description": "job", "target_section": "personal"},
    )

    # Assert
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {"refined_content": "## Refined Experience"}


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.resume_ai._create_refine_result_html")
@patch("resume_editor.app.api.routes.resume_ai.refine_experience_section")
@patch("resume_editor.app.api.routes.resume_ai.decrypt_data", return_value="decrypted_key")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings")
async def test_refine_resume_stream_happy_path(
    mock_get_user_settings,
    mock_decrypt_data,
    mock_refine_experience,
    mock_create_refine_result_html,
    client_with_auth_and_resume,
    test_user,
):
    """Test successful SSE refinement via the new GET stream endpoint."""
    import json

    mock_settings = UserSettings(
        user_id=test_user.id,
        llm_endpoint="http://llm.test",
        encrypted_api_key="key",
        llm_model_name="test-model",
    )
    mock_get_user_settings.return_value = mock_settings

    # Mock the async generator
    async def mock_async_generator():
        yield {"status": "in_progress", "message": "doing stuff"}
        yield {"status": "done", "content": "original refined content"}

    mock_refine_experience.return_value = mock_async_generator()
    mock_create_refine_result_html.return_value = "<html>final refined html</html>"

    # Act
    with client_with_auth_and_resume.stream(
        "GET",
        "/api/resumes/1/refine/stream?job_description=a%20new%20job",
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        parsed_events = []
        current_event_name = "message"
        for line in response.iter_lines():
            if not line:  # End of an event
                current_event_name = "message"
                continue
            if line.startswith("event:"):
                current_event_name = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data = line.split(":", 1)[1].strip()
                parsed_events.append({"event": current_event_name, "data": data})

    # Assert
    assert len(parsed_events) == 2

    # Check progress event
    assert parsed_events[0]["event"] == "progress"
    assert parsed_events[0]["data"] == "<li>doing stuff</li>"

    # Check message event for 'done'
    assert parsed_events[1]["event"] == "message"
    done_data = json.loads(parsed_events[1]["data"])
    assert done_data["status"] == "done"
    assert done_data["content"] == "<html>final refined html</html>"

    mock_refine_experience.assert_called_once_with(
        request=ANY,
        resume_content=VALID_MINIMAL_RESUME_CONTENT,
        job_description="a new job",
        llm_endpoint="http://llm.test",
        api_key="decrypted_key",
        llm_model_name="test-model",
    )
    mock_create_refine_result_html.assert_called_once_with(
        1, "experience", "original refined content"
    )


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.resume_ai.refine_experience_section")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
async def test_refine_resume_stream_unknown_status(
    mock_get_user_settings, mock_refine_experience, client_with_auth_and_resume
):
    """Test SSE stream handles unknown event statuses gracefully."""

    # Mock the async generator to yield an event with an unknown status
    async def mock_async_generator():
        yield {"status": "processing", "message": "unhandled status"}

    mock_refine_experience.return_value = mock_async_generator()

    # Act
    with client_with_auth_and_resume.stream(
        "GET",
        "/api/resumes/1/refine/stream?job_description=a%20new%20job",
    ) as response:
        # Assert
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        content = response.read()
        # The generator should not yield anything for an unknown status
        assert content == b""

    mock_refine_experience.assert_called_once()


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.resume_ai.refine_experience_section")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
async def test_refine_resume_stream_empty_generator(
    mock_get_user_settings, mock_refine_experience, client_with_auth_and_resume
):
    """Test SSE stream with an empty generator from the LLM service."""

    # Mock the async generator to be empty
    async def mock_empty_async_generator():
        return
        yield  # pylint: disable=unreachable

    mock_refine_experience.return_value = mock_empty_async_generator()

    # Act
    with client_with_auth_and_resume.stream(
        "GET",
        "/api/resumes/1/refine/stream?job_description=a%20new%20job",
    ) as response:
        # Assert
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        content = response.read()
        assert content == b""

    mock_refine_experience.assert_called_once()


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.resume_ai.refine_experience_section")
@patch("resume_editor.app.api.routes.resume_ai.decrypt_data", side_effect=InvalidToken)
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings")
async def test_refine_resume_stream_invalid_token(
    mock_get_user_settings,
    mock_decrypt_data,
    mock_refine_experience,
    client_with_auth_and_resume,
    test_user,
):
    """Test SSE stream reports error on API key decryption failure."""
    import json

    mock_settings = UserSettings(user_id=test_user.id, encrypted_api_key="key")
    mock_get_user_settings.return_value = mock_settings

    with client_with_auth_and_resume.stream(
        "GET", "/api/resumes/1/refine/stream?job_description=job"
    ) as response:
        assert response.status_code == 200
        events = []
        for line in response.iter_lines():
            if line.startswith("data:"):
                events.append(json.loads(line[len("data:") :]))

    assert len(events) == 1
    assert events[0]["status"] == "error"
    assert "Invalid API key" in events[0]["message"]
    mock_refine_experience.assert_not_called()


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.resume_ai.refine_experience_section",
    side_effect=AuthenticationError(message="auth error", response=Mock(), body=None),
)
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
async def test_refine_resume_stream_auth_error(
    mock_get_user_settings, mock_refine_experience, client_with_auth_and_resume
):
    """Test SSE stream reports error on LLM authentication failure."""
    import json

    with client_with_auth_and_resume.stream(
        "GET", "/api/resumes/1/refine/stream?job_description=job"
    ) as response:
        assert response.status_code == 200
        events = []
        for line in response.iter_lines():
            if line.startswith("data:"):
                events.append(json.loads(line[len("data:") :]))

    assert len(events) == 1
    assert events[0]["status"] == "error"
    assert "LLM authentication failed" in events[0]["message"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "exception,expected_message",
    [
        (ValueError("value error"), "Refinement failed: value error"),
        (
            Exception("generic error"),
            "An unexpected error occurred during refinement: generic error",
        ),
    ],
)
@patch("resume_editor.app.api.routes.resume_ai.refine_experience_section")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
async def test_refine_resume_stream_other_errors(
    mock_get_user_settings,
    mock_refine_experience,
    exception,
    expected_message,
    client_with_auth_and_resume,
):
    """Test SSE stream reports error on other failures."""
    import json

    mock_refine_experience.side_effect = exception

    with client_with_auth_and_resume.stream(
        "GET", "/api/resumes/1/refine/stream?job_description=job"
    ) as response:
        assert response.status_code == 200
        events = []
        for line in response.iter_lines():
            if line.startswith("data:"):
                events.append(json.loads(line[len("data:") :]))

    assert len(events) == 1
    assert events[0]["status"] == "error"
    assert events[0]["message"] == expected_message


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
        data={"job_description": "job", "target_section": "personal"},
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
        data={"job_description": "job", "target_section": "personal"},
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
    client_with_auth_and_resume,
    test_user,
    test_resume,
):
    """Test accepting a 'full' refinement and saving it as a new resume."""
    from resume_editor.app.api.routes.route_models import RefineTargetSection

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
    mock_gen_detail_html.return_value = "<html>New Detail</html>"

    # Act
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/save_as_new",
        data={
            "refined_content": refined_content,
            "target_section": RefineTargetSection.FULL.value,
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
    mock_create_db.assert_called_once_with(
        db=ANY,
        user_id=test_user.id,
        name="New Name",
        content=refined_content,
    )
    mock_get_resumes.assert_called_once()
    mock_gen_detail_html.assert_called_once_with(new_resume)

    assert '<div id="left-sidebar-content" hx-swap-oob="true">' in response.text
    assert "<html>New Detail</html>" in response.text

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(response.text, "html.parser")
    sidebar_content = soup.find(id="left-sidebar-content")
    assert sidebar_content is not None

    all_items = sidebar_content.find_all(class_="resume-item")
    assert len(all_items) == 2

    selected_item = sidebar_content.find(class_="selected")
    assert selected_item is not None
    assert "New Name" in selected_item.text

    edit_link = selected_item.find("a", href="/resumes/2/edit")
    assert edit_link is not None


@patch("resume_editor.app.api.routes.resume_ai._generate_resume_detail_html")
@patch("resume_editor.app.api.routes.resume_ai.get_user_resumes")
@patch("resume_editor.app.api.routes.resume_ai.create_resume_db")
@patch("resume_editor.app.api.routes.resume_ai.perform_pre_save_validation")
@patch("resume_editor.app.api.routes.resume_ai.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume_ai.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_education_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
def test_save_refined_resume_as_new_partial(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_pre_save,
    mock_create_db,
    mock_get_resumes,
    mock_gen_detail_html,
    client_with_auth_and_resume,
    test_user,
    test_resume,
):
    """Test accepting a partial refinement and saving it as a new resume."""
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
    )
    new_resume.id = 2
    mock_create_db.return_value = new_resume
    mock_get_resumes.return_value = [test_resume, new_resume]
    mock_gen_detail_html.return_value = "<html>New Detail</html>"

    # Act
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/save_as_new",
        data={
            "refined_content": refined_content,
            "target_section": RefineTargetSection.PERSONAL.value,
            "new_resume_name": "New Name",
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
    )
    mock_gen_detail_html.assert_called_once_with(new_resume)

    assert '<div id="left-sidebar-content" hx-swap-oob="true">' in response.text
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
