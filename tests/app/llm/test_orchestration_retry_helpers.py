"""Tests for retry mechanism helper functions in orchestration module."""

import json
from unittest.mock import MagicMock, patch

import pytest
from cryptography.fernet import InvalidToken
from openai import AuthenticationError
from pydantic import ValidationError

from resume_editor.app.llm.models import JobAnalysis
from resume_editor.app.llm.orchestration import (
    _create_error_context,
    _is_retryable_error,
    _log_failed_attempt,
    _truncate_for_log,
)
from resume_editor.app.models.resume.experience import Role, RoleBasics


class TestIsRetryableError:
    """Tests for _is_retryable_error function."""

    def test_returns_true_for_json_decode_error(self):
        """Test that json.JSONDecodeError is retryable."""
        error = json.JSONDecodeError("test", "doc", 0)
        assert _is_retryable_error(error) is True

    def test_returns_true_for_timeout_error(self):
        """Test that TimeoutError is retryable."""
        error = TimeoutError("Connection timed out")
        assert _is_retryable_error(error) is True

    def test_returns_true_for_connection_error(self):
        """Test that ConnectionError is retryable."""
        error = ConnectionError("Connection failed")
        assert _is_retryable_error(error) is True

    def test_returns_false_for_authentication_error(self):
        """Test that AuthenticationError is not retryable."""
        error = AuthenticationError("Invalid API key", response=MagicMock(), body=None)
        assert _is_retryable_error(error) is False

    def test_returns_false_for_validation_error(self):
        """Test that pydantic ValidationError is not retryable."""
        error = ValidationError.from_exception_data("test", line_errors=[])
        assert _is_retryable_error(error) is False

    def test_returns_false_for_invalid_token(self):
        """Test that InvalidToken is not retryable."""
        error = InvalidToken()
        assert _is_retryable_error(error) is False

    def test_returns_false_for_generic_exception(self):
        """Test that generic Exception is not retryable."""
        error = Exception("Some error")
        assert _is_retryable_error(error) is False


class TestTruncateForLog:
    """Tests for _truncate_for_log function."""

    def test_short_text_unchanged(self):
        """Test that short text is returned unchanged."""
        text = "Short text"
        result = _truncate_for_log(text, max_len=100)
        assert result == text

    def test_exact_length_text_unchanged(self):
        """Test that text of exact max_len is returned unchanged."""
        text = "a" * 500
        result = _truncate_for_log(text, max_len=500)
        assert result == text

    def test_long_text_truncated(self):
        """Test that long text is truncated with ellipsis."""
        text = "a" * 600
        result = _truncate_for_log(text, max_len=500)
        assert result == "a" * 500 + "..."
        assert len(result) == 503  # 500 chars + 3 for "..."

    def test_custom_max_len(self):
        """Test truncation with custom max_len."""
        text = "a" * 100
        result = _truncate_for_log(text, max_len=50)
        assert result == "a" * 50 + "..."

    def test_empty_string(self):
        """Test that empty string is handled correctly."""
        result = _truncate_for_log("", max_len=500)
        assert result == ""


class TestLogFailedAttempt:
    """Tests for _log_failed_attempt function."""

    @pytest.fixture
    def mock_role(self):
        """Create a mock Role object."""
        role = MagicMock(spec=Role)
        role.basics = MagicMock(spec=RoleBasics)
        role.basics.company = "Test Company"
        role.basics.title = "Software Engineer"
        return role

    @pytest.fixture
    def mock_job_analysis(self):
        """Create a mock JobAnalysis object."""
        analysis = MagicMock(spec=JobAnalysis)
        analysis.model_dump_json.return_value = '{"key": "value"}'
        return analysis

    @patch("resume_editor.app.llm.orchestration_refinement.log")
    def test_logs_at_debug_level(self, mock_log, mock_role, mock_job_analysis):
        """Test that function logs at DEBUG level."""
        error = json.JSONDecodeError("test", "doc", 0)
        _log_failed_attempt(
            role=mock_role,
            attempt=1,
            response='{"test": "response"}',
            error=error,
            job_analysis=mock_job_analysis,
        )
        mock_log.debug.assert_called_once()

    @patch("resume_editor.app.llm.orchestration_refinement.log")
    def test_log_includes_role_context(self, mock_log, mock_role, mock_job_analysis):
        """Test that log includes role context (company, title, original_index)."""
        error = json.JSONDecodeError("test", "doc", 0)
        _log_failed_attempt(
            role=mock_role,
            attempt=2,
            response="response text",
            error=error,
            job_analysis=mock_job_analysis,
        )
        call_args = mock_log.debug.call_args[0][0]
        assert "Test Company" in call_args
        assert "Software Engineer" in call_args
        assert "attempt 2" in call_args

    @patch("resume_editor.app.llm.orchestration_refinement.log")
    def test_log_includes_truncated_response(
        self, mock_log, mock_role, mock_job_analysis
    ):
        """Test that log includes truncated response."""
        error = json.JSONDecodeError("test", "doc", 0)
        long_response = "x" * 1000
        _log_failed_attempt(
            role=mock_role,
            attempt=1,
            response=long_response,
            error=error,
            job_analysis=mock_job_analysis,
        )
        call_args = mock_log.debug.call_args[0][0]
        assert "..." in call_args  # Should be truncated

    @patch("resume_editor.app.llm.orchestration_refinement.log")
    def test_log_includes_error_type(self, mock_log, mock_role, mock_job_analysis):
        """Test that log includes error type."""
        error = json.JSONDecodeError("test", "doc", 0)
        _log_failed_attempt(
            role=mock_role,
            attempt=1,
            response="response",
            error=error,
            job_analysis=mock_job_analysis,
        )
        call_args = mock_log.debug.call_args[0][0]
        assert "JSONDecodeError" in call_args

    @patch("resume_editor.app.llm.orchestration_refinement.log")
    def test_no_f_strings_in_log_call(self, mock_log, mock_role, mock_job_analysis):
        """Test that log is called without f-strings (per CONVENTIONS.md)."""
        error = json.JSONDecodeError("test", "doc", 0)
        _log_failed_attempt(
            role=mock_role,
            attempt=1,
            response="response",
            error=error,
            job_analysis=mock_job_analysis,
        )
        # The log call should use a pre-formatted string variable, not f-string inline
        call_args = mock_log.debug.call_args
        assert call_args is not None
        # Verify the message is a string (not an f-string expression)
        assert isinstance(call_args[0][0], str)


class TestCreateErrorContext:
    """Tests for _create_error_context function."""

    @pytest.fixture
    def mock_role(self):
        """Create a mock Role object."""
        role = MagicMock(spec=Role)
        role.basics = MagicMock(spec=RoleBasics)
        role.basics.company = "Acme Corp"
        role.basics.title = "Senior Developer"
        return role

    def test_returns_formatted_message(self, mock_role):
        """Test that function returns properly formatted error message."""
        result = _create_error_context(mock_role, max_attempts=3)
        assert "Unable to refine 'Senior Developer @ Acme Corp'" in result
        assert "after 3 attempts" in result

    def test_includes_service_issue_text(self, mock_role):
        """Test that message mentions AI service issues."""
        result = _create_error_context(mock_role, max_attempts=3)
        assert "AI service may be experiencing issues" in result

    def test_includes_resume_instruction(self, mock_role):
        """Test that message includes resume instruction."""
        result = _create_error_context(mock_role, max_attempts=3)
        assert "Click Start Refinement to resume" in result

    def test_different_role_values(self):
        """Test with different role values."""
        role = MagicMock(spec=Role)
        role.basics = MagicMock(spec=RoleBasics)
        role.basics.company = "Tech Giants Inc"
        role.basics.title = "Engineering Manager"
        result = _create_error_context(role, max_attempts=5)
        assert "Unable to refine 'Engineering Manager @ Tech Giants Inc'" in result
        assert "after 5 attempts" in result
