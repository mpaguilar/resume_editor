"""Tests for checkpoint integration in resume_ai.py.

This module tests the checkpoint system integration with the resume AI routes,
including log creation, retrieval, matching, and cleanup.

"""

import logging
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Set up logging for tests
logging.basicConfig(level=logging.DEBUG)


class TestGetOrCreateRunningLog:
    """Tests for the _get_or_create_running_log helper function."""

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Set up mocks for each test."""
        self.mock_manager = Mock()
        self.mock_manager.get_log = Mock(return_value=None)
        self.mock_manager.create_log = Mock(return_value=Mock())
        self.mock_manager.job_description_matches = Mock(return_value=False)
        self.mock_manager.clear_log = Mock()

        # Patch the running_log_manager import
        with patch(
            "resume_editor.app.api.routes.resume_ai.running_log_manager",
            self.mock_manager,
        ):
            yield

    def test_creates_new_log_when_none_exists(self):
        """Test that a new log is created when no existing log is found."""
        from resume_editor.app.api.routes.resume_ai import _get_or_create_running_log
        from resume_editor.app.llm.models import RunningLog

        # Arrange
        self.mock_manager.get_log.return_value = None
        expected_log = Mock(spec=RunningLog)
        self.mock_manager.create_log.return_value = expected_log

        # Act
        result = _get_or_create_running_log(
            resume_id=1,
            user_id=2,
            job_description="Test job description",
        )

        # Assert
        self.mock_manager.get_log.assert_called_once_with(1, 2)
        self.mock_manager.create_log.assert_called_once_with(
            1, 2, "Test job description"
        )
        assert result == expected_log

    def test_returns_existing_log_when_job_matches(self):
        """Test that existing log is returned when job description matches."""
        from resume_editor.app.api.routes.resume_ai import _get_or_create_running_log
        from resume_editor.app.llm.models import RunningLog

        # Arrange
        existing_log = Mock(spec=RunningLog)
        existing_log.job_description = "Test job description"
        self.mock_manager.get_log.return_value = existing_log
        self.mock_manager.job_description_matches.return_value = True

        # Act
        result = _get_or_create_running_log(
            resume_id=1,
            user_id=2,
            job_description="Test job description",
        )

        # Assert
        self.mock_manager.get_log.assert_called_once_with(1, 2)
        self.mock_manager.job_description_matches.assert_called_once_with(
            1, 2, "Test job description"
        )
        self.mock_manager.create_log.assert_not_called()
        self.mock_manager.clear_log.assert_not_called()
        assert result == existing_log

    def test_clears_and_creates_new_log_when_job_does_not_match(self):
        """Test that old log is cleared and new one created when job changes."""
        from resume_editor.app.api.routes.resume_ai import _get_or_create_running_log
        from resume_editor.app.llm.models import RunningLog

        # Arrange
        existing_log = Mock(spec=RunningLog)
        existing_log.job_description = "Old job description"
        self.mock_manager.get_log.return_value = existing_log
        self.mock_manager.job_description_matches.return_value = False
        new_log = Mock(spec=RunningLog)
        self.mock_manager.create_log.return_value = new_log

        # Act
        result = _get_or_create_running_log(
            resume_id=1,
            user_id=2,
            job_description="New job description",
        )

        # Assert
        self.mock_manager.get_log.assert_called_once_with(1, 2)
        self.mock_manager.job_description_matches.assert_called_once_with(
            1, 2, "New job description"
        )
        self.mock_manager.clear_log.assert_called_once_with(1, 2)
        self.mock_manager.create_log.assert_called_once_with(
            1, 2, "New job description"
        )
        assert result == new_log


class TestExperienceRefinementStreamIntegration:
    """Tests for _experience_refinement_stream checkpoint integration."""

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Set up mocks for each test."""
        self.mock_manager = Mock()
        self.mock_manager.get_log = Mock(return_value=None)
        self.mock_manager.create_log = Mock(return_value=Mock())
        self.mock_manager.job_description_matches = Mock(return_value=False)
        self.mock_manager.clear_log = Mock()

        self.mock_params = Mock()
        self.mock_params.resume = Mock()
        self.mock_params.resume.id = 1
        self.mock_params.resume.content = "Test resume content"
        self.mock_params.current_user = Mock()
        self.mock_params.current_user.id = 2
        self.mock_params.job_description = "Test job description"
        self.mock_params.parsed_limit_years = None
        self.mock_params.db = Mock()
        self.mock_params.limit_refinement_years = None
        self.mock_params.company = None
        self.mock_params.notes = None

        with patch(
            "resume_editor.app.api.routes.resume_ai.running_log_manager",
            self.mock_manager,
        ):
            with patch(
                "resume_editor.app.api.routes.resume_ai.extract_experience_info",
            ) as mock_extract:
                mock_experience = Mock()
                mock_experience.roles = [Mock()]
                mock_extract.return_value = mock_experience
                yield

    @pytest.mark.asyncio
    async def test_creates_running_log_at_start(self):
        """Test that running log is created at the start of stream."""
        from resume_editor.app.api.routes.resume_ai import (
            _experience_refinement_stream,
        )

        # Arrange
        self.mock_manager.get_log.return_value = None
        mock_log = Mock()
        self.mock_manager.create_log.return_value = mock_log

        # Create a proper async generator mock
        async def mock_generator():
            yield "event1"
            yield "event2"

        with patch(
            "resume_editor.app.api.routes.resume_ai.experience_refinement_sse_generator",
            return_value=mock_generator(),
        ):
            # Act
            async for _ in _experience_refinement_stream(self.mock_params):
                pass

        # Assert
        self.mock_manager.get_log.assert_called_once_with(1, 2)
        self.mock_manager.create_log.assert_called_once_with(
            1, 2, "Test job description"
        )

    @pytest.mark.asyncio
    async def test_passes_running_log_to_generator(self):
        """Test that running_log is passed to experience_refinement_sse_generator."""
        from resume_editor.app.api.routes.resume_ai import (
            ExperienceRefinementParams,
            _experience_refinement_stream,
        )

        # Arrange
        mock_log = Mock()
        self.mock_manager.get_log.return_value = None
        self.mock_manager.create_log.return_value = mock_log

        captured_params = None

        async def mock_generator():
            yield "event1"

        def capture_params(*, params):
            nonlocal captured_params
            captured_params = params
            return mock_generator()

        with patch(
            "resume_editor.app.api.routes.resume_ai.experience_refinement_sse_generator",
            side_effect=capture_params,
        ):
            async for _ in _experience_refinement_stream(self.mock_params):
                pass

        # Assert
        assert captured_params is not None
        assert hasattr(captured_params, "running_log")
        assert captured_params.running_log == mock_log

    @pytest.mark.asyncio
    async def test_clears_log_on_successful_completion(self):
        """Test that running log is cleared after successful completion."""
        from resume_editor.app.api.routes.resume_ai import (
            _experience_refinement_stream,
        )

        # Arrange
        mock_log = Mock()
        self.mock_manager.get_log.return_value = None
        self.mock_manager.create_log.return_value = mock_log

        # Create a proper async generator mock
        async def mock_generator():
            yield "event1"
            yield "event2"

        with patch(
            "resume_editor.app.api.routes.resume_ai.experience_refinement_sse_generator",
            return_value=mock_generator(),
        ):
            # Act
            async for _ in _experience_refinement_stream(self.mock_params):
                pass

        # Assert
        self.mock_manager.clear_log.assert_called_once_with(1, 2)


class TestRunningLogHelperFunctionSignature:
    """Tests for _get_or_create_running_log function signature and docstring."""

    def test_function_has_proper_docstring(self):
        """Test that the helper function has proper docstring."""
        from resume_editor.app.api.routes.resume_ai import _get_or_create_running_log

        assert _get_or_create_running_log.__doc__ is not None
        assert "Args:" in _get_or_create_running_log.__doc__
        assert "Returns:" in _get_or_create_running_log.__doc__
        assert "Notes:" in _get_or_create_running_log.__doc__

    def test_function_has_type_hints(self):
        """Test that the helper function has proper type hints."""
        import inspect

        from resume_editor.app.api.routes.resume_ai import _get_or_create_running_log

        sig = inspect.signature(_get_or_create_running_log)
        assert "resume_id" in sig.parameters
        assert "user_id" in sig.parameters
        assert "job_description" in sig.parameters

        # Check return annotation
        assert sig.return_annotation is not inspect.Signature.empty


class TestCheckpointEdgeCases:
    """Tests for edge cases in checkpoint handling."""

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Set up mocks for each test."""
        self.mock_manager = Mock()

        with patch(
            "resume_editor.app.api.routes.resume_ai.running_log_manager",
            self.mock_manager,
        ):
            yield

    def test_handles_empty_job_description(self):
        """Test that empty job description is handled correctly."""
        from resume_editor.app.api.routes.resume_ai import _get_or_create_running_log

        # Arrange
        self.mock_manager.get_log.return_value = None
        mock_log = Mock()
        self.mock_manager.create_log.return_value = mock_log

        # Act
        result = _get_or_create_running_log(
            resume_id=1,
            user_id=2,
            job_description="",
        )

        # Assert
        self.mock_manager.create_log.assert_called_once_with(1, 2, "")
        assert result == mock_log

    def test_handles_special_characters_in_job_description(self):
        """Test that special characters in job description are handled."""
        from resume_editor.app.api.routes.resume_ai import _get_or_create_running_log

        # Arrange
        special_job = "Job with special chars: äöü ñ 日本語 🚀 <script>"
        self.mock_manager.get_log.return_value = None
        mock_log = Mock()
        self.mock_manager.create_log.return_value = mock_log

        # Act
        result = _get_or_create_running_log(
            resume_id=1,
            user_id=2,
            job_description=special_job,
        )

        # Assert
        self.mock_manager.create_log.assert_called_once_with(1, 2, special_job)
        assert result == mock_log
