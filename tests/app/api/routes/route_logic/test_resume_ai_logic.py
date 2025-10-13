from unittest.mock import MagicMock, patch

import pytest
from cryptography.fernet import InvalidToken

import asyncio
import logging
from unittest.mock import AsyncMock, Mock

from cryptography.fernet import InvalidToken
from fastapi import HTTPException
from openai import AuthenticationError
from starlette.middleware.base import ClientDisconnect

from resume_editor.app.api.routes.route_logic.resume_ai_logic import (
    _handle_sse_exception,
    _process_sse_event,
    create_sse_close_message,
    create_sse_done_message,
    create_sse_error_message,
    create_sse_introduction_message,
    create_sse_message,
    create_sse_progress_message,
    experience_refinement_sse_generator,
    get_llm_config,
    handle_accept_refinement,
    handle_save_as_new_refinement,
    handle_sync_refinement,
    process_refined_experience_result,
    reconstruct_resume_from_refined_section,
)
from resume_editor.app.api.routes.route_models import (
    ExperienceResponse,
    RefineResponse,
    RefineTargetSection,
)
from resume_editor.app.models.resume.experience import (
    Project,
    ProjectOverview,
    Role,
    RoleBasics,
    RoleSummary,
)
from resume_editor.app.models.resume_model import Resume as DatabaseResume
from resume_editor.app.models.user import User
from resume_editor.app.models.user_settings import UserSettings


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

# Store the real asyncio.sleep
_real_asyncio_sleep = asyncio.sleep


@pytest.fixture
def test_user():
    """Fixture for a test user."""
    user = User(
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
        content=VALID_RESUME_TWO_ROLES,
    )
    resume.id = 1
    return resume


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.decrypt_data")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_user_settings")
def test_get_llm_config_with_key(mock_get_user_settings, mock_decrypt_data):
    """Test get_llm_config when user settings and API key exist."""
    # Arrange
    mock_db = MagicMock()
    user_id = 1
    mock_settings = UserSettings(
        user_id=user_id,
        llm_endpoint="http://example.com",
        llm_model_name="test-model",
        encrypted_api_key="encrypted_key",
    )
    mock_get_user_settings.return_value = mock_settings
    mock_decrypt_data.return_value = "decrypted_key"

    # Act
    llm_endpoint, llm_model_name, api_key = get_llm_config(mock_db, user_id)

    # Assert
    assert llm_endpoint == "http://example.com"
    assert llm_model_name == "test-model"
    assert api_key == "decrypted_key"
    mock_get_user_settings.assert_called_once_with(mock_db, user_id)
    mock_decrypt_data.assert_called_once_with("encrypted_key")


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.decrypt_data")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_user_settings")
def test_get_llm_config_no_key(mock_get_user_settings, mock_decrypt_data):
    """Test get_llm_config when user settings exist but no API key."""
    # Arrange
    mock_db = MagicMock()
    user_id = 1
    mock_settings = UserSettings(
        user_id=user_id,
        llm_endpoint="http://example.com",
        llm_model_name="test-model",
        encrypted_api_key=None,
    )
    mock_get_user_settings.return_value = mock_settings

    # Act
    llm_endpoint, llm_model_name, api_key = get_llm_config(mock_db, user_id)

    # Assert
    assert llm_endpoint == "http://example.com"
    assert llm_model_name == "test-model"
    assert api_key is None
    mock_get_user_settings.assert_called_once_with(mock_db, user_id)
    mock_decrypt_data.assert_not_called()


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_user_settings")
def test_get_llm_config_no_settings(mock_get_user_settings):
    """Test get_llm_config when user has no settings."""
    # Arrange
    mock_db = MagicMock()
    user_id = 1
    mock_get_user_settings.return_value = None

    # Act
    llm_endpoint, llm_model_name, api_key = get_llm_config(mock_db, user_id)

    # Assert
    assert llm_endpoint is None
    assert llm_model_name is None
    assert api_key is None
    mock_get_user_settings.assert_called_once_with(mock_db, user_id)


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.decrypt_data")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_user_settings")
def test_get_llm_config_decryption_error(mock_get_user_settings, mock_decrypt_data):
    """Test get_llm_config raises InvalidToken on decryption failure."""
    # Arrange
    mock_db = MagicMock()
    user_id = 1
    mock_settings = UserSettings(
        user_id=user_id, encrypted_api_key="bad_encrypted_key"
    )
    mock_get_user_settings.return_value = mock_settings
    mock_decrypt_data.side_effect = InvalidToken

    # Act & Assert
    with pytest.raises(InvalidToken):
        get_llm_config(mock_db, user_id)
    mock_decrypt_data.assert_called_once_with("bad_encrypted_key")


def test_create_sse_message_single_line():
    """Test create_sse_message with single-line data."""
    result = create_sse_message("test_event", "some data")
    assert result == "event: test_event\ndata: some data\n\n"


def test_create_sse_message_multi_line():
    """Test create_sse_message with multi-line data."""
    result = create_sse_message("test_event", "line1\nline2")
    assert result == "event: test_event\ndata: line1\ndata: line2\n\n"


def test_create_sse_progress_message():
    """Test create_sse_progress_message."""
    result = create_sse_progress_message("In progress...")
    assert result == "event: progress\ndata: <li>In progress...</li>\n\n"


def test_create_sse_progress_message_with_html():
    """Test create_sse_progress_message handles HTML escaping."""
    result = create_sse_progress_message("<p>In progress...</p>")
    assert (
        result == "event: progress\ndata: <li>&lt;p&gt;In progress...&lt;/p&gt;</li>\n\n"
    )


def test_create_sse_introduction_message():
    """Test create_sse_introduction_message."""
    intro = "This is an introduction."
    result = create_sse_introduction_message(intro)
    expected = (
        "event: introduction_generated\n"
        'data: <div id="introduction-container" hx-swap-oob="true">\n'
        'data: <h4 class="text-lg font-semibold text-gray-700">Suggested Introduction:</h4>\n'
        'data: <p class="mt-1 text-sm text-gray-600 bg-gray-50 p-3 rounded-md border">This is an introduction.</p>\n'
        "data: </div>\n\n"
    )
    assert result == expected


def test_create_sse_error_message_error():
    """Test create_sse_error_message for an error."""
    result = create_sse_error_message("An error occurred.")
    assert (
        result
        == "event: error\ndata: <div role='alert' class='text-red-500 p-2'>An error occurred.</div>\n\n"
    )


def test_create_sse_error_message_warning():
    """Test create_sse_error_message for a warning."""
    result = create_sse_error_message("A warning.", is_warning=True)
    assert (
        result
        == "event: error\ndata: <div role='alert' class='text-yellow-500 p-2'>A warning.</div>\n\n"
    )


def test_create_sse_done_message():
    """Test create_sse_done_message."""
    html_content = "<div>Done</div>"
    result = create_sse_done_message(html_content)
    assert result == "event: done\ndata: <div>Done</div>\n\n"


def test_create_sse_close_message():
    """Test create_sse_close_message."""
    result = create_sse_close_message()
    assert result == "event: close\ndata: stream complete\n\n"


@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic._create_refine_result_html"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.build_complete_resume_from_sections"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_certifications_info"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_experience_info"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_education_info"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_personal_info"
)
def test_process_refined_experience_result(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_create_html,
):
    """Test process_refined_experience_result successfully reconstructs and generates HTML."""
    # Arrange
    resume = DatabaseResume(user_id=1, name="Test", content="Original content")
    resume.id = 1

    refined_role1 = Role(
        basics=RoleBasics(
            company="Refined Co", title="Refined Role", start_date="2023-01-01"
        ),
        summary=RoleSummary(text="Refined Summary"),
    )
    refined_roles = {0: refined_role1.model_dump(mode="json")}

    job_description = "A job"
    introduction = "An intro"

    mock_project = Project(overview=ProjectOverview(title="My Project"))
    mock_original_experience = ExperienceResponse(roles=[], projects=[mock_project])

    mock_extract_personal.return_value = "personal"
    mock_extract_education.return_value = "education"
    mock_extract_experience.return_value = mock_original_experience
    mock_extract_certifications.return_value = "certifications"
    mock_build_sections.return_value = "updated content"
    mock_create_html.return_value = "final html"

    # Act
    result = process_refined_experience_result(
        resume, refined_roles, job_description, introduction
    )

    # Assert
    assert result == "final html"

    mock_extract_personal.assert_called_once_with(resume.content)
    mock_extract_education.assert_called_once_with(resume.content)
    mock_extract_experience.assert_called_once_with(resume.content)
    mock_extract_certifications.assert_called_once_with(resume.content)

    mock_build_sections.assert_called_once()
    call_args = mock_build_sections.call_args.kwargs
    assert call_args["personal_info"] == "personal"
    assert call_args["education"] == "education"
    assert call_args["certifications"] == "certifications"

    reconstructed_experience = call_args["experience"]
    assert len(reconstructed_experience.roles) == 1
    assert reconstructed_experience.roles[0].summary.text == "Refined Summary"
    assert reconstructed_experience.projects == mock_original_experience.projects

    mock_create_html.assert_called_once_with(
        resume.id,
        "experience",
        "updated content",
        job_description=job_description,
        introduction=introduction,
    )


@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.build_complete_resume_from_sections"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_certifications_info"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_experience_info"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_education_info"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_personal_info"
)
@pytest.mark.parametrize(
    "target_section",
    [
        RefineTargetSection.PERSONAL,
        RefineTargetSection.EDUCATION,
        RefineTargetSection.EXPERIENCE,
        RefineTargetSection.CERTIFICATIONS,
    ],
)
def test_reconstruct_resume_from_refined_section_partial(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    target_section,
):
    """Test partial reconstruction for each section."""
    original_content = "original"
    refined_content = "refined"
    mock_build_sections.return_value = "reconstructed"

    result = reconstruct_resume_from_refined_section(
        original_content, refined_content, target_section
    )

    assert result == "reconstructed"

    if target_section == RefineTargetSection.PERSONAL:
        mock_extract_personal.assert_called_once_with(refined_content)
        mock_extract_education.assert_called_once_with(original_content)
        mock_extract_experience.assert_called_once_with(original_content)
        mock_extract_certifications.assert_called_once_with(original_content)
    elif target_section == RefineTargetSection.EDUCATION:
        mock_extract_personal.assert_called_once_with(original_content)
        mock_extract_education.assert_called_once_with(refined_content)
        mock_extract_experience.assert_called_once_with(original_content)
        mock_extract_certifications.assert_called_once_with(original_content)
    elif target_section == RefineTargetSection.EXPERIENCE:
        mock_extract_personal.assert_called_once_with(original_content)
        mock_extract_education.assert_called_once_with(original_content)
        mock_extract_experience.assert_called_once_with(refined_content)
        mock_extract_certifications.assert_called_once_with(original_content)
    elif target_section == RefineTargetSection.CERTIFICATIONS:
        mock_extract_personal.assert_called_once_with(original_content)
        mock_extract_education.assert_called_once_with(original_content)
        mock_extract_experience.assert_called_once_with(original_content)
        mock_extract_certifications.assert_called_once_with(refined_content)

    mock_build_sections.assert_called_once()


@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.build_complete_resume_from_sections"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_certifications_info"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_experience_info"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_education_info"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_personal_info"
)
def test_reconstruct_resume_from_refined_section_full(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
):
    """Test 'full' reconstruction directly returns refined content."""
    original_content = "original"
    refined_content = "refined"
    result = reconstruct_resume_from_refined_section(
        original_content, refined_content, RefineTargetSection.FULL
    )

    assert result == refined_content
    mock_extract_personal.assert_not_called()
    mock_extract_education.assert_not_called()
    mock_extract_experience.assert_not_called()
    mock_extract_certifications.assert_not_called()
    mock_build_sections.assert_not_called()


def test_process_sse_event_in_progress():
    """Test _process_sse_event for 'in_progress' status."""
    event = {"status": "in_progress", "message": "Doing it"}
    refined_roles = {}
    sse_message, new_intro = _process_sse_event(event, refined_roles)

    assert sse_message == create_sse_progress_message("Doing it")
    assert new_intro is None
    assert not refined_roles


def test_process_sse_event_introduction_generated():
    """Test _process_sse_event for 'introduction_generated' status."""
    event = {"status": "introduction_generated", "data": "A new intro"}
    refined_roles = {}
    sse_message, new_intro = _process_sse_event(event, refined_roles)

    assert sse_message == create_sse_introduction_message("A new intro")
    assert new_intro == "A new intro"
    assert not refined_roles


def test_process_sse_event_introduction_generated_with_none():
    """Test _process_sse_event for 'introduction_generated' with None data."""
    event = {"status": "introduction_generated", "data": None}
    refined_roles = {}
    sse_message, new_intro = _process_sse_event(event, refined_roles)

    assert sse_message is None
    assert new_intro is None
    assert not refined_roles


def test_process_sse_event_role_refined_success():
    """Test _process_sse_event for a successful 'role_refined' status."""
    event = {"status": "role_refined", "data": {"some": "data"}, "original_index": 0}
    refined_roles = {}
    sse_message, new_intro = _process_sse_event(event, refined_roles)

    assert sse_message is None
    assert new_intro is None
    assert refined_roles == {0: {"some": "data"}}


@pytest.mark.parametrize(
    "malformed_event",
    [
        {"status": "role_refined", "data": {"some": "data"}},  # Missing index
        {"status": "role_refined", "original_index": 0},  # Missing data
        {"status": "role_refined", "data": None, "original_index": 0},
        {"status": "role_refined", "data": {"some": "data"}, "original_index": None},
    ],
)
def test_process_sse_event_role_refined_malformed(malformed_event, caplog):
    """Test _process_sse_event handles malformed 'role_refined' events."""
    refined_roles = {}
    with caplog.at_level(logging.WARNING):
        sse_message, new_intro = _process_sse_event(malformed_event, refined_roles)

    assert sse_message is None
    assert new_intro is None
    assert not refined_roles
    assert "Malformed role_refined event received" in caplog.text


def test_process_sse_event_unknown_event(caplog):
    """Test _process_sse_event for an unknown event status."""
    event = {"status": "unknown_status", "message": "hello"}
    refined_roles = {}
    with caplog.at_level(logging.WARNING):
        sse_message, new_intro = _process_sse_event(event, refined_roles)

    assert sse_message is None
    assert new_intro is None
    assert not refined_roles
    assert "Unhandled SSE event received" in caplog.text


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.create_sse_error_message")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.log")
def test_handle_sse_exception_invalid_token(mock_log, mock_create_sse_error):
    """Test _handle_sse_exception for InvalidToken."""
    # Arrange
    exception = InvalidToken()
    resume_id = 1
    expected_msg = "Invalid API key. Please update your settings."
    mock_create_sse_error.return_value = "formatted sse error"

    # Act
    result = _handle_sse_exception(exception, resume_id)

    # Assert
    assert result == "formatted sse error"
    log_msg = f"SSE stream error for resume {resume_id}: {expected_msg}"
    mock_log.exception.assert_called_once_with(log_msg)
    mock_create_sse_error.assert_called_once_with(expected_msg)


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.create_sse_error_message")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.log")
def test_handle_sse_exception_authentication_error(mock_log, mock_create_sse_error):
    """Test _handle_sse_exception for AuthenticationError."""
    # Arrange
    exception = AuthenticationError(response=Mock(), message="auth error", body=None)
    resume_id = 1
    expected_msg = "LLM authentication failed. Please check your API key."
    mock_create_sse_error.return_value = "formatted sse error"

    # Act
    result = _handle_sse_exception(exception, resume_id)

    # Assert
    assert result == "formatted sse error"
    log_msg = f"SSE stream error for resume {resume_id}: {expected_msg}"
    mock_log.exception.assert_called_once_with(log_msg)
    mock_create_sse_error.assert_called_once_with(expected_msg)


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.create_sse_error_message")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.log")
def test_handle_sse_exception_value_error(mock_log, mock_create_sse_error):
    """Test _handle_sse_exception for ValueError."""
    # Arrange
    exception = ValueError("some value error")
    resume_id = 1
    expected_msg = "Refinement failed: some value error"
    mock_create_sse_error.return_value = "formatted sse error"

    # Act
    result = _handle_sse_exception(exception, resume_id)

    # Assert
    assert result == "formatted sse error"
    log_msg = f"SSE stream error for resume {resume_id}: {expected_msg}"
    mock_log.exception.assert_called_once_with(log_msg)
    mock_create_sse_error.assert_called_once_with(expected_msg)


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.create_sse_error_message")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.log")
def test_handle_sse_exception_generic_exception(mock_log, mock_create_sse_error):
    """Test _handle_sse_exception for a generic Exception."""
    # Arrange
    exception = Exception("some generic error")
    resume_id = 1
    expected_msg = "An unexpected error occurred."
    mock_create_sse_error.return_value = "formatted sse error"

    # Act
    result = _handle_sse_exception(exception, resume_id)

    # Assert
    assert result == "formatted sse error"
    log_msg = f"SSE stream error for resume {resume_id}: {expected_msg}"
    mock_log.exception.assert_called_once_with(log_msg)
    mock_create_sse_error.assert_called_once_with(expected_msg)


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.refine_resume_section_with_llm"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_handle_sync_refinement_success_with_key(
    mock_get_llm_config, mock_refine_llm, test_user, test_resume
):
    """Test successful synchronous refinement returns RefineResponse."""
    from fastapi import Request

    # Arrange
    mock_request = Request(scope={"type": "http", "headers": []})
    mock_db = Mock()
    mock_get_llm_config.return_value = (
        "http://llm.test",
        "test-model",
        "decrypted_key",
    )
    mock_refine_llm.return_value = ("refined content", "this is an intro")

    # Act
    response = await handle_sync_refinement(
        request=mock_request,
        db=mock_db,
        user=test_user,
        resume=test_resume,
        job_description="job",
        target_section=RefineTargetSection.PERSONAL,
        generate_introduction=True,
    )

    # Assert
    assert isinstance(response, RefineResponse)
    assert response.refined_content == "refined content"
    assert response.introduction == "this is an intro"
    mock_get_llm_config.assert_called_once_with(mock_db, test_user.id)
    mock_refine_llm.assert_called_once_with(
        resume_content=VALID_RESUME_TWO_ROLES,
        job_description="job",
        target_section="personal",
        llm_endpoint="http://llm.test",
        api_key="decrypted_key",
        llm_model_name="test-model",
        generate_introduction=True,
    )


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic._create_refine_result_html"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.refine_resume_section_with_llm"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_handle_sync_refinement_htmx_response(
    mock_get_llm_config, mock_refine_llm, mock_create_html, test_user, test_resume
):
    """Test that handle_sync_refinement returns HTML for an HTMX request."""
    from fastapi import Request
    from fastapi.responses import HTMLResponse

    # Arrange
    mock_request = Request(
        scope={"type": "http", "headers": [(b"hx-request", b"true")]}
    )
    mock_db = Mock()
    mock_get_llm_config.return_value = ("http://llm.test", "test-model", "key")
    mock_refine_llm.return_value = ("refined content", "this is an intro")
    mock_create_html.return_value = "<html>refine result</html>"

    # Act
    response = await handle_sync_refinement(
        request=mock_request,
        db=mock_db,
        user=test_user,
        resume=test_resume,
        job_description="job",
        target_section=RefineTargetSection.PERSONAL,
        generate_introduction=True,
    )

    # Assert
    assert isinstance(response, HTMLResponse)
    assert response.body.decode("utf-8") == "<html>refine result</html>"
    mock_create_html.assert_called_once_with(
        resume_id=test_resume.id,
        target_section_val="personal",
        refined_content="refined content",
        job_description="job",
        introduction="this is an intro",
    )


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_handle_sync_refinement_decryption_failure_htmx(
    mock_get_llm_config, test_user, test_resume
):
    """Test handle_sync_refinement returns HTML error on decryption failure for HTMX."""
    from fastapi import Request
    from fastapi.responses import HTMLResponse

    # Arrange
    mock_request = Request(
        scope={"type": "http", "headers": [(b"hx-request", b"true")]}
    )
    mock_db = Mock()
    mock_get_llm_config.side_effect = InvalidToken

    # Act
    response = await handle_sync_refinement(
        request=mock_request,
        db=mock_db,
        user=test_user,
        resume=test_resume,
        job_description="job",
        target_section=RefineTargetSection.PERSONAL,
        generate_introduction=True,
    )

    # Assert
    assert isinstance(response, HTMLResponse)
    assert response.status_code == 200
    assert "Invalid API key" in response.body.decode("utf-8")


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_handle_sync_refinement_decryption_failure_non_htmx(
    mock_get_llm_config, test_user, test_resume
):
    """Test handle_sync_refinement raises HTTPException on decryption failure for non-HTMX."""
    from fastapi import Request, HTTPException

    # Arrange
    mock_request = Request(scope={"type": "http", "headers": []})
    mock_db = Mock()
    mock_get_llm_config.side_effect = InvalidToken

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await handle_sync_refinement(
            request=mock_request,
            db=mock_db,
            user=test_user,
            resume=test_resume,
            job_description="job",
            target_section=RefineTargetSection.PERSONAL,
            generate_introduction=True,
        )
    assert exc_info.value.status_code == 400
    assert "Invalid API key" in exc_info.value.detail


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.refine_resume_section_with_llm"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_handle_sync_refinement_auth_failure_htmx(
    mock_get_llm_config, mock_refine_llm, test_user, test_resume
):
    """Test handle_sync_refinement returns HTML error on auth failure for HTMX."""
    from fastapi import Request
    from fastapi.responses import HTMLResponse

    # Arrange
    mock_request = Request(
        scope={"type": "http", "headers": [(b"hx-request", b"true")]}
    )
    mock_db = Mock()
    mock_get_llm_config.return_value = (None, None, None)
    mock_refine_llm.side_effect = AuthenticationError(
        message="auth failed", response=Mock(), body=None
    )

    # Act
    response = await handle_sync_refinement(
        request=mock_request,
        db=mock_db,
        user=test_user,
        resume=test_resume,
        job_description="job",
        target_section=RefineTargetSection.PERSONAL,
        generate_introduction=True,
    )

    # Assert
    assert isinstance(response, HTMLResponse)
    assert "LLM authentication failed" in response.body.decode("utf-8")


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.refine_resume_section_with_llm"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_handle_sync_refinement_auth_failure_non_htmx(
    mock_get_llm_config, mock_refine_llm, test_user, test_resume
):
    """Test handle_sync_refinement raises HTTPException on auth failure for non-HTMX."""
    from fastapi import Request, HTTPException

    # Arrange
    mock_request = Request(scope={"type": "http", "headers": []})
    mock_db = Mock()
    mock_get_llm_config.return_value = (None, None, None)
    mock_refine_llm.side_effect = AuthenticationError(
        message="auth failed", response=Mock(), body=None
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await handle_sync_refinement(
            request=mock_request,
            db=mock_db,
            user=test_user,
            resume=test_resume,
            job_description="job",
            target_section=RefineTargetSection.PERSONAL,
            generate_introduction=True,
        )
    assert exc_info.value.status_code == 401
    assert "LLM authentication failed" in exc_info.value.detail


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.refine_resume_section_with_llm"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_handle_sync_refinement_value_error_htmx(
    mock_get_llm_config, mock_refine_llm, test_user, test_resume
):
    """Test handle_sync_refinement returns HTML error on ValueError for HTMX."""
    from fastapi import Request
    from fastapi.responses import HTMLResponse

    # Arrange
    mock_request = Request(
        scope={"type": "http", "headers": [(b"hx-request", b"true")]}
    )
    mock_db = Mock()
    mock_get_llm_config.return_value = (None, None, None)
    error_message = "The AI service returned an unexpected response."
    mock_refine_llm.side_effect = ValueError(error_message)

    # Act
    response = await handle_sync_refinement(
        request=mock_request,
        db=mock_db,
        user=test_user,
        resume=test_resume,
        job_description="job",
        target_section=RefineTargetSection.PERSONAL,
        generate_introduction=True,
    )

    # Assert
    assert isinstance(response, HTMLResponse)
    assert "Refinement failed: " in response.body.decode("utf-8")
    assert error_message in response.body.decode("utf-8")


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.refine_resume_section_with_llm"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_handle_sync_refinement_value_error_non_htmx(
    mock_get_llm_config, mock_refine_llm, test_user, test_resume
):
    """Test handle_sync_refinement raises HTTPException on ValueError for non-HTMX."""
    from fastapi import Request, HTTPException

    # Arrange
    mock_request = Request(scope={"type": "http", "headers": []})
    mock_db = Mock()
    mock_get_llm_config.return_value = (None, None, None)
    error_message = "The AI service returned an unexpected response."
    mock_refine_llm.side_effect = ValueError(error_message)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await handle_sync_refinement(
            request=mock_request,
            db=mock_db,
            user=test_user,
            resume=test_resume,
            job_description="job",
            target_section=RefineTargetSection.PERSONAL,
            generate_introduction=True,
        )
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == error_message


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.refine_resume_section_with_llm"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_handle_sync_refinement_generic_exception_htmx(
    mock_get_llm_config, mock_refine_llm, test_user, test_resume
):
    """Test handle_sync_refinement returns HTML on generic Exception for HTMX."""
    from fastapi import Request
    from fastapi.responses import HTMLResponse

    # Arrange
    mock_request = Request(
        scope={"type": "http", "headers": [(b"hx-request", b"true")]}
    )
    mock_db = Mock()
    mock_get_llm_config.return_value = (None, None, None)
    mock_refine_llm.side_effect = Exception("LLM call failed")

    # Act
    response = await handle_sync_refinement(
        request=mock_request,
        db=mock_db,
        user=test_user,
        resume=test_resume,
        job_description="job",
        target_section=RefineTargetSection.PERSONAL,
        generate_introduction=True,
    )

    # Assert
    assert isinstance(response, HTMLResponse)
    assert "An unexpected error occurred during refinement" in response.body.decode(
        "utf-8"
    )
    assert "LLM call failed" in response.body.decode("utf-8")


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.refine_resume_section_with_llm"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_handle_sync_refinement_generic_exception_non_htmx(
    mock_get_llm_config, mock_refine_llm, test_user, test_resume
):
    """Test handle_sync_refinement raises HTTPException on generic Exception for non-HTMX."""
    from fastapi import Request, HTTPException

    # Arrange
    mock_request = Request(scope={"type": "http", "headers": []})
    mock_db = Mock()
    mock_get_llm_config.return_value = (None, None, None)
    mock_refine_llm.side_effect = Exception("LLM call failed")

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await handle_sync_refinement(
            request=mock_request,
            db=mock_db,
            user=test_user,
            resume=test_resume,
            job_description="job",
            target_section=RefineTargetSection.PERSONAL,
            generate_introduction=True,
        )
    assert exc_info.value.status_code == 500
    assert "LLM refinement failed: LLM call failed" in exc_info.value.detail


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.process_refined_experience_result"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_experience_refinement_sse_generator_happy_path(
    mock_get_llm_config,
    mock_async_refine_experience,
    mock_process_result,
    test_user,
    test_resume,
):
    """Test successful SSE refinement via the SSE generator."""
    test_resume.content = VALID_RESUME_TWO_ROLES

    from resume_editor.app.models.resume.experience import Role, RoleBasics, RoleSummary

    mock_get_llm_config.return_value = (
        "http://llm.test",
        "test-model",
        "decrypted_key",
    )

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
    mock_process_result.return_value = "<html>final refined html</html>"

    mock_db = Mock()
    results = [
        item
        async for item in experience_refinement_sse_generator(
            db=mock_db,
            user=test_user,
            resume=test_resume,
            job_description="a new job",
            generate_introduction=True,
        )
    ]

    assert len(results) == 4, f"Expected 4 events, got {len(results)}: {results}"
    assert "event: progress" in results[0]
    assert "data: <li>doing stuff</li>" in results[0]
    assert "event: introduction_generated" in results[1]
    assert 'id="introduction-container"' in results[1]
    assert "event: done" in results[2]
    assert "data: <html>final refined html</html>" in results[2]
    assert "event: close" in results[3]

    mock_get_llm_config.assert_called_once_with(mock_db, test_user.id)
    mock_async_refine_experience.assert_called_once_with(
        resume_content=VALID_RESUME_TWO_ROLES,
        job_description="a new job",
        llm_endpoint="http://llm.test",
        api_key="decrypted_key",
        llm_model_name="test-model",
        generate_introduction=True,
    )
    mock_process_result.assert_called_once_with(
        test_resume,
        {1: refined_role2_data, 0: refined_role1_data},
        "a new job",
        "Generated Intro",
    )


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.process_refined_experience_result"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_experience_refinement_sse_generator_gen_intro_false(
    mock_get_llm_config,
    mock_async_refine_experience,
    mock_process_result,
    test_user,
    test_resume,
):
    """Test SSE generator when generate_introduction is false."""
    test_resume.content = VALID_RESUME_TWO_ROLES
    mock_get_llm_config.return_value = (None, None, None)
    refined_role1_data = {"test": "data"}

    async def mock_async_generator():
        yield {"status": "role_refined", "data": refined_role1_data, "original_index": 0}

    mock_async_refine_experience.return_value = mock_async_generator()
    mock_process_result.return_value = "final html"

    await NthAsyncItem.of(
        experience_refinement_sse_generator(
            db=Mock(),
            user=test_user,
            resume=test_resume,
            job_description="a job",
            generate_introduction=False,
        ),
        2,  # Wait for all events
    )

    mock_async_refine_experience.assert_called_once_with(
        resume_content=VALID_RESUME_TWO_ROLES,
        job_description="a job",
        llm_endpoint=None,
        api_key=None,
        llm_model_name=None,
        generate_introduction=False,
    )
    mock_process_result.assert_called_once_with(
        test_resume, {0: refined_role1_data}, "a job", None
    )


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_experience_refinement_sse_generator_introduction_is_none(
    mock_get_llm_config, mock_async_refine_experience, test_user, test_resume
):
    """Test that an introduction_generated event with None data is handled."""
    mock_get_llm_config.return_value = (None, None, None)

    async def mock_generator():
        yield {"status": "introduction_generated", "data": None}
        yield {"status": "in_progress", "message": "doing stuff"}

    mock_async_refine_experience.return_value = mock_generator()

    results = [
        item
        async for item in experience_refinement_sse_generator(
            db=Mock(),
            user=test_user,
            resume=test_resume,
            job_description="job",
            generate_introduction=True,
        )
    ]

    assert len(results) == 3
    assert "event: progress" in results[0]
    assert "event: error" in results[1]
    assert "Refinement finished, but no roles were found to refine." in results[1]
    assert "event: close" in results[2]


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic._handle_sse_exception")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_experience_refinement_sse_generator_orchestration_error(
    mock_get_llm_config,
    mock_async_refine_experience,
    mock_handle_exception,
    test_user,
    test_resume,
):
    """Test that an error raised by the orchestrator is handled in the SSE stream."""
    mock_get_llm_config.return_value = (None, None, None)
    error = ValueError("Orchestration failed")
    mock_async_refine_experience.side_effect = error
    mock_handle_exception.return_value = "formatted error"

    results = [
        item
        async for item in experience_refinement_sse_generator(
            db=Mock(),
            user=test_user,
            resume=test_resume,
            job_description="job",
            generate_introduction=True,
        )
    ]

    assert len(results) == 2
    assert results[0] == "formatted error"
    assert "event: close" in results[1]
    mock_handle_exception.assert_called_once_with(error, test_resume.id)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "malformed_event",
    [
        {"status": "processing", "message": "unhandled status"},
        {"status": "role_refined", "data": {"some": "data"}},
        {"status": "role_refined", "original_index": 0},
        {"status": "role_refined", "data": None, "original_index": 0},
        {"status": "role_refined", "data": {"some": "data"}, "original_index": None},
    ],
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_experience_refinement_sse_generator_malformed_events(
    mock_get_llm_config, mock_async_refine_experience, malformed_event, test_user, test_resume
):
    """Test SSE generator handles unknown or malformed events gracefully."""
    mock_get_llm_config.return_value = (None, None, None)

    async def mock_async_generator():
        yield malformed_event

    mock_async_refine_experience.return_value = mock_async_generator()

    results = [
        item
        async for item in experience_refinement_sse_generator(
            db=Mock(),
            user=test_user,
            resume=test_resume,
            job_description="a new job",
            generate_introduction=True,
        )
    ]

    assert len(results) == 2
    assert "event: error" in results[0]
    assert "Refinement finished, but no roles were found to refine." in results[0]
    assert "event: close" in results[1]


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_experience_refinement_sse_generator_empty_generator(
    mock_get_llm_config, mock_async_refine_experience, test_user, test_resume
):
    """Test SSE stream with an empty generator from the LLM service."""
    mock_get_llm_config.return_value = (None, None, None)

    async def mock_empty_async_generator():
        return
        yield

    mock_async_refine_experience.return_value = mock_empty_async_generator()

    results = [
        item
        async for item in experience_refinement_sse_generator(
            db=Mock(),
            user=test_user,
            resume=test_resume,
            job_description="a job",
            generate_introduction=True,
        )
    ]

    assert len(results) == 2
    assert "event: error" in results[0]
    assert "Refinement finished, but no roles were found to refine." in results[0]
    assert "event: close" in results[1]


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic._handle_sse_exception")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_experience_refinement_sse_generator_invalid_token(
    mock_get_llm_config, mock_handle_exception, test_user, test_resume
):
    """Test SSE generator reports error on API key decryption failure."""
    error = InvalidToken()
    mock_get_llm_config.side_effect = error
    mock_handle_exception.return_value = "formatted error"

    results = [
        item
        async for item in experience_refinement_sse_generator(
            db=Mock(),
            user=test_user,
            resume=test_resume,
            job_description="job",
            generate_introduction=True,
        )
    ]

    assert len(results) == 2
    assert results[0] == "formatted error"
    assert "event: close" in results[1]
    mock_handle_exception.assert_called_once_with(error, test_resume.id)


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic._handle_sse_exception")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_experience_refinement_sse_generator_auth_error(
    mock_get_llm_config,
    mock_async_refine_experience,
    mock_handle_exception,
    test_user,
    test_resume,
):
    """Test SSE generator reports error on LLM authentication failure."""
    mock_get_llm_config.return_value = (None, None, None)
    error = AuthenticationError(message="auth error", response=Mock(), body=None)
    mock_async_refine_experience.side_effect = error
    mock_handle_exception.return_value = "formatted error"

    results = [
        item
        async for item in experience_refinement_sse_generator(
            db=Mock(),
            user=test_user,
            resume=test_resume,
            job_description="job",
            generate_introduction=True,
        )
    ]

    assert len(results) == 2
    assert results[0] == "formatted error"
    assert "event: close" in results[1]
    mock_handle_exception.assert_called_once_with(error, test_resume.id)


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic._handle_sse_exception")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_experience_refinement_sse_generator_generic_exception(
    mock_get_llm_config,
    mock_async_refine_experience,
    mock_handle_exception,
    test_user,
    test_resume,
):
    """Test SSE generator reports error on a generic exception."""
    mock_get_llm_config.return_value = (None, None, None)
    error = Exception("Generic test error")
    mock_async_refine_experience.side_effect = error
    mock_handle_exception.return_value = "formatted error"

    results = [
        item
        async for item in experience_refinement_sse_generator(
            db=Mock(),
            user=test_user,
            resume=test_resume,
            job_description="job",
            generate_introduction=True,
        )
    ]

    assert len(results) == 2
    assert results[0] == "formatted error"
    assert "event: close" in results[1]
    mock_handle_exception.assert_called_once_with(error, test_resume.id)


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_experience_refinement_sse_generator_client_disconnect(
    mock_get_llm_config, mock_async_refine_experience, test_user, test_resume, caplog
):
    """Test that the SSE generator handles a ClientDisconnect gracefully."""
    mock_get_llm_config.return_value = (None, None, None)

    async def mock_generator_with_disconnect():
        raise ClientDisconnect()
        yield

    mock_async_refine_experience.return_value = mock_generator_with_disconnect()

    with caplog.at_level(logging.WARNING):
        results = [
            item
            async for item in experience_refinement_sse_generator(
                db=Mock(),
                user=test_user,
                resume=test_resume,
                job_description="job",
                generate_introduction=True,
            )
        ]

    assert len(results) == 1
    assert "event: close" in results[0]
    assert f"Client disconnected from SSE stream for resume {test_resume.id}." in caplog.text


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.update_resume_db")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.perform_pre_save_validation"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.reconstruct_resume_from_refined_section"
)
def test_handle_accept_refinement_success(
    mock_reconstruct, mock_validate, mock_update, test_resume
):
    """Test handle_accept_refinement successfully updates a resume."""
    # Arrange
    db = MagicMock()
    refined_content = "refined"
    target_section = RefineTargetSection.PERSONAL
    introduction = "intro"
    mock_reconstruct.return_value = "updated content"
    mock_update.return_value = test_resume

    # Act
    result = handle_accept_refinement(
        db, test_resume, refined_content, target_section, introduction
    )

    # Assert
    assert result == test_resume
    mock_reconstruct.assert_called_once_with(
        original_resume_content=test_resume.content,
        refined_content=refined_content,
        target_section=target_section,
    )
    mock_validate.assert_called_once_with("updated content", test_resume.content)
    mock_update.assert_called_once_with(
        db=db, resume=test_resume, content="updated content", introduction=introduction
    )


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.update_resume_db")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.perform_pre_save_validation"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.reconstruct_resume_from_refined_section"
)
def test_handle_accept_refinement_failure(
    mock_reconstruct, mock_validate, mock_update, test_resume
):
    """Test handle_accept_refinement raises HTTPException on failure."""
    # Arrange
    db = MagicMock()
    mock_reconstruct.side_effect = ValueError("reconstruction failed")

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        handle_accept_refinement(
            db, test_resume, "refined", RefineTargetSection.PERSONAL, None
        )
    assert exc_info.value.status_code == 422
    assert "Failed to reconstruct" in exc_info.value.detail
    mock_validate.assert_not_called()
    mock_update.assert_not_called()


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.create_resume_db")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.perform_pre_save_validation"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.reconstruct_resume_from_refined_section"
)
def test_handle_save_as_new_refinement_success(
    mock_reconstruct, mock_validate, mock_create, test_user, test_resume
):
    """Test handle_save_as_new_refinement successfully creates a new resume."""
    # Arrange
    db = MagicMock()
    refined_content = "refined"
    target_section = RefineTargetSection.PERSONAL
    new_name = "New Resume"
    job_desc = "job desc"
    introduction = "intro"

    mock_reconstruct.return_value = "updated content"
    new_resume = DatabaseResume(
        user_id=test_user.id, name=new_name, content="updated content"
    )
    mock_create.return_value = new_resume

    # Act
    result = handle_save_as_new_refinement(
        db,
        test_user,
        test_resume,
        refined_content,
        target_section,
        new_name,
        job_desc,
        introduction,
    )

    # Assert
    assert result == new_resume
    mock_reconstruct.assert_called_once_with(
        original_resume_content=test_resume.content,
        refined_content=refined_content,
        target_section=target_section,
    )
    mock_validate.assert_called_once_with("updated content", test_resume.content)
    mock_create.assert_called_once_with(
        db=db,
        user_id=test_user.id,
        name=new_name,
        content="updated content",
        is_base=False,
        parent_id=test_resume.id,
        job_description=job_desc,
        introduction=introduction,
    )


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.create_resume_db")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.perform_pre_save_validation"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.reconstruct_resume_from_refined_section"
)
def test_handle_save_as_new_refinement_failure(
    mock_reconstruct, mock_validate, mock_create, test_user, test_resume
):
    """Test handle_save_as_new_refinement raises HTTPException on failure."""
    # Arrange
    db = MagicMock()
    mock_validate.side_effect = ValueError("validation failed")

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        handle_save_as_new_refinement(
            db,
            test_user,
            test_resume,
            "refined",
            RefineTargetSection.PERSONAL,
            "New",
            None,
            None,
        )
    assert exc_info.value.status_code == 422
    assert "Failed to reconstruct" in exc_info.value.detail
    mock_reconstruct.assert_called_once()
    mock_create.assert_not_called()


class NthAsyncItem:
    """Helper to await until the nth item of an async iterator is produced."""

    def __init__(self, async_iterator, n):
        self.async_iterator = async_iterator
        self.n = n
        self.items = []

    def __await__(self):
        return self.get_items().__await__()

    async def get_items(self):
        async for item in self.async_iterator:
            self.items.append(item)
            if len(self.items) == self.n:
                break
        return self.items

    @classmethod
    def of(cls, async_iterator, n):
        return cls(async_iterator, n)
