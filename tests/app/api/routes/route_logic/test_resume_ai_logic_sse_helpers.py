import logging
from unittest.mock import Mock, patch

import pytest
from cryptography.fernet import InvalidToken
from openai import AuthenticationError

from resume_editor.app.api.routes.route_logic.resume_ai_logic import (
    _handle_sse_exception,
    _process_sse_event,
    create_sse_close_message,
    create_sse_done_message,
    create_sse_error_message,
    create_sse_message,
    create_sse_progress_message,
)


@pytest.mark.parametrize(
    "test_input, expected_output",
    [
        ("some data", "event: test_event\ndata: some data\n\n"),
        (
            "line1\nline2",
            "event: test_event\ndata: line1\ndata: line2\n\n",
        ),
        ("", "event: test_event\ndata: \n\n"),
        # Per SSE spec, a single newline in data should be sent as one data field.
        ("\n", "event: test_event\ndata: \n\n"),
    ],
)
def test_create_sse_message_variations(test_input, expected_output):
    """Test create_sse_message with various inputs."""
    result = create_sse_message("test_event", test_input)
    assert result == expected_output


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


def test_create_sse_error_message_with_html():
    """Test create_sse_error_message handles HTML escaping."""
    result = create_sse_error_message("<b>Error</b>")
    assert (
        result
        == "event: error\ndata: <div role='alert' class='text-red-500 p-2'>&lt;b&gt;Error&lt;/b&gt;</div>\n\n"
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


def test_process_sse_event_in_progress():
    """Test _process_sse_event for 'in_progress' status."""
    event = {"status": "in_progress", "message": "Doing it"}
    refined_roles = {}
    sse_message = _process_sse_event(event, refined_roles)

    assert sse_message == create_sse_progress_message("Doing it")
    assert not refined_roles




def test_process_sse_event_role_refined_validation_fails(caplog):
    """
    Test _process_sse_event for 'role_refined' where model validation fails.
    """
    event = {"status": "role_refined", "data": {"some": "data"}, "original_index": 0}
    refined_roles = {}

    with caplog.at_level(logging.WARNING):
        sse_message = _process_sse_event(event, refined_roles)

    # A message is not generated, and the role is not stored.
    assert sse_message is None
    assert not refined_roles
    assert "Failed to validate refined role data" in caplog.text


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
        sse_message = _process_sse_event(malformed_event, refined_roles)

    assert sse_message is None
    assert not refined_roles
    assert "Malformed role_refined event received" in caplog.text


def test_process_sse_event_unknown_event(caplog):
    """Test _process_sse_event for an unknown event status."""
    event = {"status": "unknown_status", "message": "hello"}
    refined_roles = {}
    with caplog.at_level(logging.WARNING):
        sse_message = _process_sse_event(event, refined_roles)

    assert sse_message is None
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


