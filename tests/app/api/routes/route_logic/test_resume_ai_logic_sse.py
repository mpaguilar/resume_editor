"""Tests for resume_ai_logic_sse module."""

from resume_editor.app.api.routes.route_logic.resume_ai_logic_sse import (
    create_sse_close_message,
    create_sse_done_message,
    create_sse_error_message,
    create_sse_message,
    create_sse_progress_message,
)


def test_create_sse_message():
    """Test basic SSE message creation."""
    result = create_sse_message("test_event", "test data")
    assert "event: test_event" in result
    assert "data: test data" in result


def test_create_sse_message_multiline():
    """Test SSE message with multiline data."""
    result = create_sse_message("test_event", "line1\nline2")
    assert "event: test_event" in result
    assert "data: line1" in result
    assert "data: line2" in result


def test_create_sse_progress_message():
    """Test progress message creation."""
    result = create_sse_progress_message("Test progress")
    assert "event: progress" in result
    assert "<li>" in result
    assert "Test progress" in result


def test_create_sse_error_message():
    """Test error message creation."""
    result = create_sse_error_message("Error occurred")
    assert "event: error" in result
    assert "text-red-500" in result
    assert "Error occurred" in result


def test_create_sse_error_message_warning():
    """Test warning message creation."""
    result = create_sse_error_message("Warning message", is_warning=True)
    assert "event: error" in result
    assert "text-yellow-500" in result
    assert "Warning message" in result


def test_create_sse_done_message():
    """Test done message creation."""
    result = create_sse_done_message("<div>Result</div>")
    assert "event: done" in result
    assert "<div>Result</div>" in result


def test_create_sse_close_message():
    """Test close message creation."""
    result = create_sse_close_message()
    assert "event: close" in result
    assert "stream complete" in result
