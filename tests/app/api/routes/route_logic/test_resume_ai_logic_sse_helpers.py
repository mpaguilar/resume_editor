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
    create_sse_introduction_message,
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


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.env.get_template")
def test_create_sse_introduction_message(mock_get_template):
    """Test create_sse_introduction_message."""
    mock_template = Mock()
    mock_template.render.return_value = (
        '<div id="refine_introduction_preview" hx-swap-oob="true">intro html</div>'
    )
    mock_get_template.return_value = mock_template
    intro = "This is an introduction."

    result = create_sse_introduction_message(intro)

    mock_get_template.assert_called_once_with(
        "partials/resume/_refine_result_intro.html"
    )
    mock_template.render.assert_called_once_with(introduction=intro)
    assert (
        result
        == 'event: introduction_generated\ndata: <div id="refine_introduction_preview" hx-swap-oob="true">intro html</div>\n\n'
    )


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.env.get_template")
def test_create_sse_introduction_message_with_html(mock_get_template):
    """Test create_sse_introduction_message handles HTML escaping from Jinja."""
    mock_template = Mock()
    mock_template.render.return_value = (
        '<div id="refine_introduction_preview" hx-swap-oob="true">&lt;p&gt;Intro&lt;/p&gt;</div>'
    )
    mock_get_template.return_value = mock_template
    intro = "<p>Intro</p>"

    result = create_sse_introduction_message(intro)

    mock_get_template.assert_called_once_with(
        "partials/resume/_refine_result_intro.html"
    )
    mock_template.render.assert_called_once_with(introduction=intro)
    assert (
        result
        == 'event: introduction_generated\ndata: <div id="refine_introduction_preview" hx-swap-oob="true">&lt;p&gt;Intro&lt;/p&gt;</div>\n\n'
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
    sse_message, new_intro = _process_sse_event(event, refined_roles)

    assert sse_message == create_sse_progress_message("Doing it")
    assert new_intro is None
    assert not refined_roles


@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.create_sse_introduction_message"
)
def test_process_sse_event_introduction_generated(mock_create_intro_message):
    """Test _process_sse_event for 'introduction_generated' status."""
    mock_create_intro_message.return_value = "mocked sse intro message"
    event = {"status": "introduction_generated", "data": "A new intro"}
    refined_roles = {}

    sse_message, new_intro = _process_sse_event(event, refined_roles)

    mock_create_intro_message.assert_called_once_with("A new intro")
    assert sse_message == "mocked sse intro message"
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
