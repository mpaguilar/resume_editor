"""Tests for orchestration_refinement module."""

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from openai import AuthenticationError
from pydantic import ValidationError

from resume_editor.app.llm.models import (
    JobAnalysis,
    LLMConfig,
    RefinedRole,
    RoleRefinementJob,
)
from resume_editor.app.llm.orchestration_models import (
    HandleRetryDelayParams,
    ProcessRefinementErrorParams,
)
from resume_editor.app.llm.orchestration_refinement import (
    _attempt_refine_role,
    _create_error_context,
    _handle_retry_delay,
    _is_retryable_error,
    _log_failed_attempt,
    _process_refinement_error,
    _refine_role_and_put_on_queue,
    _truncate_for_log,
    _unwrap_exception_group,
    async_refine_experience_section,
    refine_role,
)
from resume_editor.app.models.resume.experience import (
    Role,
    RoleBasics,
    RoleResponsibilities,
    RoleSkills,
    RoleSummary,
)


def create_mock_role() -> Role:
    """Helper to create a mock Role object for testing."""
    return Role(
        basics=RoleBasics(
            company="Old Company",
            title="Old Title",
            start_date=datetime(2020, 1, 1),
        ),
        summary=RoleSummary(text="Old summary."),
        responsibilities=RoleResponsibilities(text="* Do old things."),
        skills=RoleSkills(skills=["Old Skill"]),
    )


def create_mock_job_analysis() -> JobAnalysis:
    """Helper to create a mock JobAnalysis object for testing."""
    return JobAnalysis(
        key_skills=["python", "fastapi"],
        primary_duties=["develop things"],
        themes=["agile"],
    )


class TestIsRetryableError:
    """Tests for _is_retryable_error function."""

    def test_json_decode_error_is_retryable(self):
        """Test that JSONDecodeError is retryable."""
        error = json.JSONDecodeError("test", "doc", 0)
        assert _is_retryable_error(error) is True

    def test_timeout_error_is_retryable(self):
        """Test that TimeoutError is retryable."""
        error = TimeoutError()
        assert _is_retryable_error(error) is True

    def test_connection_error_is_retryable(self):
        """Test that ConnectionError is retryable."""
        error = ConnectionError()
        assert _is_retryable_error(error) is True

    def test_authentication_error_is_not_retryable(self):
        """Test that AuthenticationError is not retryable."""
        error = AuthenticationError(
            message="Invalid API key",
            response=MagicMock(),
            body=None,
        )
        assert _is_retryable_error(error) is False

    def test_validation_error_is_not_retryable(self):
        """Test that ValidationError is not retryable."""
        # Create a proper ValidationError
        from pydantic import BaseModel

        class TestModel(BaseModel):
            name: str

        try:
            TestModel.model_validate({})
        except ValidationError as e:
            assert _is_retryable_error(e) is False

    def test_invalid_token_is_not_retryable(self):
        """Test that InvalidToken is not retryable."""
        from cryptography.fernet import InvalidToken

        error = InvalidToken()
        assert _is_retryable_error(error) is False

    def test_general_exception_is_not_retryable(self):
        """Test that general Exception is not retryable."""
        error = Exception("Something went wrong")
        assert _is_retryable_error(error) is False


class TestTruncateForLog:
    """Tests for _truncate_for_log function."""

    def test_short_text_not_truncated(self):
        """Test that short text is not truncated."""
        text = "Short text"
        result = _truncate_for_log(text, max_len=500)
        assert result == text

    def test_long_text_truncated(self):
        """Test that long text is truncated."""
        text = "a" * 600
        result = _truncate_for_log(text, max_len=500)
        assert result == "a" * 500 + "..."
        assert len(result) == 503

    def test_exact_length_not_truncated(self):
        """Test that text exactly at max_len is not truncated."""
        text = "a" * 500
        result = _truncate_for_log(text, max_len=500)
        assert result == text

    def test_custom_max_len(self):
        """Test truncation with custom max length."""
        text = "a" * 200
        result = _truncate_for_log(text, max_len=100)
        assert result == "a" * 100 + "..."


class TestLogFailedAttempt:
    """Tests for _log_failed_attempt function."""

    def test_log_failed_attempt(self, caplog):
        """Test that _log_failed_attempt logs correctly."""
        import logging

        with caplog.at_level(logging.DEBUG):
            role = create_mock_role()
            job_analysis = create_mock_job_analysis()
            error = json.JSONDecodeError("test", "doc", 0)

            _log_failed_attempt(
                role=role,
                attempt=1,
                response="some response",
                error=error,
                job_analysis=job_analysis,
            )

        assert "Failed attempt 1" in caplog.text
        assert "Old Title @ Old Company" in caplog.text
        assert "JSONDecodeError" in caplog.text


class TestCreateErrorContext:
    """Tests for _create_error_context function."""

    def test_error_context_format(self):
        """Test that error context is formatted correctly."""
        role = create_mock_role()
        result = _create_error_context(role, 3)

        assert "Unable to refine" in result
        assert "Old Title @ Old Company" in result
        assert "after 3 attempts" in result
        assert "AI service may be experiencing issues" in result
        assert "Click Start Refinement to resume" in result


@pytest.mark.asyncio
class TestAttemptRefineRole:
    """Tests for _attempt_refine_role function."""

    async def test_attempt_refine_role_success(self):
        """Test successful role refinement attempt."""
        mock_chain = AsyncMock()
        refined_role_dict = {
            "basics": {
                "company": "Test Company",
                "title": "Test Title",
                "start_date": "2020-01-01T00:00:00",
                "inclusion_status": "Include",
            },
            "summary": {"text": "Test summary"},
            "responsibilities": {"text": "* Test responsibilities"},
            "skills": {"skills": ["Python"]},
        }
        mock_chain.ainvoke.return_value = (
            f"```json\n{json.dumps(refined_role_dict)}\n```"
        )

        success, result, error = await _attempt_refine_role(
            chain=mock_chain,
            job_analysis_json="{}",
            role_json="{}",
        )

        assert success is True
        assert isinstance(result, RefinedRole)
        assert error is None
        assert result.basics.company == "Test Company"

    async def test_attempt_refine_role_authentication_error(self):
        """Test that AuthenticationError is re-raised."""
        mock_chain = AsyncMock()
        mock_chain.ainvoke.side_effect = AuthenticationError(
            message="Invalid API key",
            response=MagicMock(),
            body=None,
        )

        with pytest.raises(AuthenticationError):
            await _attempt_refine_role(
                chain=mock_chain,
                job_analysis_json="{}",
                role_json="{}",
            )

    async def test_attempt_refine_role_json_error(self):
        """Test that JSON errors return failure."""
        mock_chain = AsyncMock()
        mock_chain.ainvoke.return_value = "not valid json"

        success, result, error = await _attempt_refine_role(
            chain=mock_chain,
            job_analysis_json="{}",
            role_json="{}",
        )

        assert success is False
        assert result is None
        assert error is not None
        assert isinstance(error, json.JSONDecodeError)


@pytest.mark.asyncio
class TestHandleRetryDelay:
    """Tests for _handle_retry_delay function."""

    async def test_handle_retry_delay_with_semaphore(self):
        """Test retry delay with semaphore."""
        mock_semaphore = MagicMock()
        mock_semaphore.release = MagicMock()
        mock_semaphore.acquire = AsyncMock()

        role = create_mock_role()
        job_analysis = create_mock_job_analysis()
        error = json.JSONDecodeError("test", "doc", 0)

        params = HandleRetryDelayParams(
            attempt=0,
            role=role,
            response_str="test response",
            error=error,
            job_analysis=job_analysis,
            semaphore=mock_semaphore,
            progress_callback=None,
        )

        with patch(
            "resume_editor.app.llm.orchestration_refinement.asyncio.sleep"
        ) as mock_sleep:
            mock_sleep.return_value = None
            await _handle_retry_delay(params)

        mock_semaphore.release.assert_called_once()
        mock_semaphore.acquire.assert_called_once()
        mock_sleep.assert_called_once_with(3)

    async def test_handle_retry_delay_with_callback(self):
        """Test retry delay with progress callback."""
        mock_callback = AsyncMock()
        role = create_mock_role()
        job_analysis = create_mock_job_analysis()
        error = json.JSONDecodeError("test", "doc", 0)

        params = HandleRetryDelayParams(
            attempt=0,
            role=role,
            response_str="test response",
            error=error,
            job_analysis=job_analysis,
            semaphore=None,
            progress_callback=mock_callback,
        )

        with patch(
            "resume_editor.app.llm.orchestration_refinement.asyncio.sleep"
        ) as mock_sleep:
            mock_sleep.return_value = None
            await _handle_retry_delay(params)

        mock_callback.assert_called_once()
        call_args = mock_callback.call_args[0][0]
        assert "Retrying role refinement" in call_args
        assert "attempt 2/3" in call_args
        assert "Old Title @ Old Company" in call_args


@pytest.mark.asyncio
class TestProcessRefinementError:
    """Tests for _process_refinement_error function."""

    async def test_non_retryable_error_raises(self):
        """Test that non-retryable errors are raised."""
        error = AuthenticationError(
            message="Invalid API key",
            response=MagicMock(),
            body=None,
        )
        role = create_mock_role()
        job_analysis = create_mock_job_analysis()

        params = ProcessRefinementErrorParams(
            attempt=0,
            error=error,
            role=role,
            response_str="",
            job_analysis=job_analysis,
            semaphore=None,
            progress_callback=None,
        )

        with pytest.raises(AuthenticationError):
            await _process_refinement_error(params)

    async def test_retryable_error_first_attempt(self):
        """Test that retryable error on first attempt allows retry."""
        error = json.JSONDecodeError("test", "doc", 0)
        role = create_mock_role()
        job_analysis = create_mock_job_analysis()

        params = ProcessRefinementErrorParams(
            attempt=0,
            error=error,
            role=role,
            response_str="",
            job_analysis=job_analysis,
            semaphore=None,
            progress_callback=None,
        )

        with patch(
            "resume_editor.app.llm.orchestration_refinement._handle_retry_delay"
        ) as mock_delay:
            mock_delay.return_value = None
            result = await _process_refinement_error(params)

        assert result is True
        mock_delay.assert_called_once()

    async def test_retryable_error_last_attempt(self):
        """Test that retryable error on last attempt does not allow retry."""
        error = json.JSONDecodeError("test", "doc", 0)
        role = create_mock_role()
        job_analysis = create_mock_job_analysis()

        params = ProcessRefinementErrorParams(
            attempt=2,  # Last attempt (0-indexed)
            error=error,
            role=role,
            response_str="",
            job_analysis=job_analysis,
            semaphore=None,
            progress_callback=None,
        )

        result = await _process_refinement_error(params)

        assert result is False


@pytest.mark.asyncio
class TestRefineRole:
    """Tests for refine_role function."""

    @pytest.fixture
    def mock_chain_invocations(self):
        """Fixture to mock the LangChain chain invocation."""
        with (
            patch(
                "resume_editor.app.llm.orchestration_refinement.initialize_llm_client"
            ) as mock_init,
            patch(
                "resume_editor.app.llm.orchestration_refinement.ChatPromptTemplate"
            ) as mock_prompt,
            patch(
                "resume_editor.app.llm.orchestration_refinement.PydanticOutputParser"
            ),
        ):
            mock_llm = MagicMock()
            mock_init.return_value = mock_llm

            mock_prompt_instance = MagicMock()
            mock_prompt.from_messages.return_value = mock_prompt_instance
            mock_prompt_instance.partial.return_value = mock_prompt_instance

            mock_chain = MagicMock()
            mock_prompt_instance.__or__.return_value = mock_chain
            mock_chain.__or__.return_value = mock_chain

            refined_role_dict = {
                "basics": {
                    "company": "Old Company",
                    "title": "Old Title",
                    "start_date": "2020-01-01T00:00:00",
                    "inclusion_status": "Include",
                },
                "summary": {"text": "Refined summary."},
                "responsibilities": {"text": "* Refined responsibilities"},
                "skills": {"skills": ["Python", "FastAPI"]},
            }
            mock_chain.ainvoke = AsyncMock(
                return_value=f"```json\n{json.dumps(refined_role_dict)}\n```"
            )

            yield {
                "chain": mock_chain,
                "init": mock_init,
            }

    async def test_refine_role_success(self, mock_chain_invocations):
        """Test successful role refinement."""
        role = create_mock_role()
        job_analysis = create_mock_job_analysis()

        result = await refine_role(
            role=role,
            job_analysis=job_analysis,
            llm_config=LLMConfig(),
        )

        assert isinstance(result, RefinedRole)
        assert result.summary.text == "Refined summary."
        assert result.basics.inclusion_status == role.basics.inclusion_status

    async def test_refine_role_with_retries(self, mock_chain_invocations):
        """Test role refinement with retries."""
        mock_chain = mock_chain_invocations["chain"]

        # First two calls fail, third succeeds
        refined_role_dict = {
            "basics": {
                "company": "Old Company",
                "title": "Old Title",
                "start_date": "2020-01-01T00:00:00",
                "inclusion_status": "Include",
            },
            "summary": {"text": "Refined summary."},
            "responsibilities": {"text": "* Refined responsibilities"},
            "skills": {"skills": ["Python"]},
        }
        mock_chain.ainvoke.side_effect = [
            "```json\n{ invalid json }\n```",
            "```json\n{ still invalid }\n```",
            f"```json\n{json.dumps(refined_role_dict)}\n```",
        ]

        role = create_mock_role()
        job_analysis = create_mock_job_analysis()

        with patch(
            "resume_editor.app.llm.orchestration_refinement.asyncio.sleep"
        ) as mock_sleep:
            mock_sleep.return_value = None
            result = await refine_role(
                role=role,
                job_analysis=job_analysis,
                llm_config=LLMConfig(),
            )

        assert isinstance(result, RefinedRole)
        assert mock_chain.ainvoke.call_count == 3
        assert mock_sleep.call_count == 2

    async def test_refine_role_all_attempts_fail(self, mock_chain_invocations):
        """Test that all failed attempts raise ValueError."""
        mock_chain = mock_chain_invocations["chain"]
        mock_chain.ainvoke.return_value = "```json\n{ invalid json }\n```"

        role = create_mock_role()
        job_analysis = create_mock_job_analysis()

        with patch(
            "resume_editor.app.llm.orchestration_refinement.asyncio.sleep"
        ) as mock_sleep:
            mock_sleep.return_value = None
            with pytest.raises(ValueError, match="Unable to refine"):
                await refine_role(
                    role=role,
                    job_analysis=job_analysis,
                    llm_config=LLMConfig(),
                )

        assert mock_chain.ainvoke.call_count == 3

    async def test_refine_role_authentication_error(self, mock_chain_invocations):
        """Test that authentication error is raised immediately."""
        mock_chain = mock_chain_invocations["chain"]
        mock_chain.ainvoke.side_effect = AuthenticationError(
            message="Invalid API key",
            response=MagicMock(),
            body=None,
        )

        role = create_mock_role()
        job_analysis = create_mock_job_analysis()

        with pytest.raises(AuthenticationError):
            await refine_role(
                role=role,
                job_analysis=job_analysis,
                llm_config=LLMConfig(),
            )

        assert mock_chain.ainvoke.call_count == 1


class TestUnwrapExceptionGroup:
    """Tests for _unwrap_exception_group function."""

    def test_unwrap_single_non_cancel_error(self):
        """Test unwrapping exception group with single non-cancellation error."""
        inner_error = ValueError("Something went wrong")
        eg = ExceptionGroup("multiple errors", [inner_error])

        with pytest.raises(ValueError, match="Something went wrong"):
            _unwrap_exception_group(eg)

    def test_unwrap_with_cancel_error(self):
        """Test that cancellation errors are filtered out.

        Note: CancelledError is a BaseException, not an Exception, so it cannot
        be directly in an ExceptionGroup. This test verifies the logic of the
        filtering by checking that exceptions are properly filtered.
        """
        inner_error = ValueError("Something went wrong")

        # Create an exception that simulates a CancelledError check
        # We test the logic by verifying the function filters properly
        class FakeCancelledError(Exception):
            """Fake class to test isinstance check."""

        # Monkey patch for test
        import resume_editor.app.llm.orchestration_refinement as orch_module

        original_cancelled_error = asyncio.CancelledError
        asyncio.CancelledError = FakeCancelledError

        try:
            cancel_like_error = FakeCancelledError()
            eg = ExceptionGroup("multiple errors", [inner_error, cancel_like_error])

            with pytest.raises(ValueError, match="Something went wrong"):
                _unwrap_exception_group(eg)
        finally:
            asyncio.CancelledError = original_cancelled_error

    def test_unwrap_multiple_errors(self):
        """Test that multiple non-cancellation errors re-raise the group."""
        error1 = ValueError("Error 1")
        error2 = ValueError("Error 2")
        eg = ExceptionGroup("multiple errors", [error1, error2])

        with pytest.raises(ExceptionGroup):
            _unwrap_exception_group(eg)

    def test_unwrap_non_exception_group(self):
        """Test that non-exception groups are re-raised as-is."""
        error = ValueError("Not a group")

        with pytest.raises(ValueError, match="Not a group"):
            _unwrap_exception_group(error)


@pytest.mark.asyncio
class TestRefineRoleAndPutOnQueue:
    """Tests for _refine_role_and_put_on_queue function."""

    async def test_refine_role_and_put_on_queue(self):
        """Test role refinement and queue event."""
        role = create_mock_role()
        job_analysis = create_mock_job_analysis()

        job = RoleRefinementJob(
            role=role,
            job_analysis=job_analysis,
            llm_config=LLMConfig(),
            original_index=0,
        )

        semaphore = asyncio.Semaphore(1)
        event_queue = asyncio.Queue()

        refined_role_dict = {
            "basics": {
                "company": "Old Company",
                "title": "Old Title",
                "start_date": "2020-01-01T00:00:00",
                "inclusion_status": "Include",
            },
            "summary": {"text": "Refined summary."},
            "responsibilities": {"text": "* Refined responsibilities"},
            "skills": {"skills": ["Python"]},
        }

        with patch(
            "resume_editor.app.llm.orchestration_refinement.refine_role"
        ) as mock_refine:
            mock_refine.return_value = RefinedRole.model_validate(refined_role_dict)
            await _refine_role_and_put_on_queue(job, semaphore, event_queue)

        # Check that events were put on the queue
        events = []
        while not event_queue.empty():
            events.append(await event_queue.get())

        assert len(events) == 2
        assert events[0]["status"] == "in_progress"
        assert "Refining role" in events[0]["message"]
        assert events[1]["status"] == "role_refined"
        assert events[1]["original_index"] == 0


@pytest.mark.asyncio
class TestAsyncRefineExperienceSection:
    """Tests for async_refine_experience_section function."""

    async def test_no_roles_to_refine(self):
        """Test when there are no roles to refine."""
        resume_content = "# Experience\n\nNo roles here"

        with patch(
            "resume_editor.app.llm.orchestration_refinement.extract_experience_info"
        ) as mock_extract:
            with patch(
                "resume_editor.app.llm.orchestration_analysis.analyze_job_description"
            ) as mock_analyze:
                mock_job_analysis = create_mock_job_analysis()
                mock_analyze.return_value = (mock_job_analysis, None)

                mock_experience_info = MagicMock()
                mock_experience_info.roles = []
                mock_extract.return_value = mock_experience_info

                events = []
                async for event in async_refine_experience_section(
                    resume_content=resume_content,
                    job_description="Test job",
                    llm_config=LLMConfig(),
                ):
                    events.append(event)

        assert len(events) >= 1
        assert any(
            e["status"] == "in_progress"
            and "Parsing resume" in str(e.get("message", ""))
            for e in events
        )

    async def test_with_job_analysis_cache(self):
        """Test using cached job analysis."""
        resume_content = "# Experience\n\nSome role"
        job_analysis = create_mock_job_analysis()

        with patch(
            "resume_editor.app.llm.orchestration_refinement.extract_experience_info"
        ) as mock_extract:
            with patch(
                "resume_editor.app.llm.orchestration_refinement.refine_role"
            ) as mock_refine:
                mock_refined_role = RefinedRole(
                    basics=create_mock_role().basics,
                    summary=RoleSummary(text="Refined summary"),
                    responsibilities=RoleResponsibilities(text="* Refined"),
                    skills=RoleSkills(skills=["Python"]),
                )
                mock_refine.return_value = mock_refined_role

                mock_experience_info = MagicMock()
                mock_role = create_mock_role()
                mock_experience_info.roles = [mock_role]
                mock_extract.return_value = mock_experience_info

                # Mock analyze_job_description to verify it's NOT called
                with patch(
                    "resume_editor.app.llm.orchestration_analysis.analyze_job_description"
                ) as mock_analyze:
                    from resume_editor.app.llm.orchestration_refinement import (
                        RefinementState,
                    )

                    events = []
                    refinement_state = RefinementState(job_analysis=job_analysis)
                    async for event in async_refine_experience_section(
                        resume_content=resume_content,
                        job_description="Test job",
                        llm_config=LLMConfig(),
                        state=refinement_state,
                    ):
                        events.append(event)
                        # Only collect first few events to avoid infinite loop
                        if len(events) > 5:
                            break

                    # analyze_job_description should not be called when job_analysis is provided
                    mock_analyze.assert_not_called()

    async def test_skip_indices(self):
        """Test that skip_indices are properly handled."""
        resume_content = "# Experience\n\nRole 1\n\nRole 2"

        with patch(
            "resume_editor.app.llm.orchestration_refinement.extract_experience_info"
        ) as mock_extract:
            with patch(
                "resume_editor.app.llm.orchestration_refinement.refine_role"
            ) as mock_refine:
                mock_refined_role = RefinedRole(
                    basics=create_mock_role().basics,
                    summary=RoleSummary(text="Refined summary"),
                    responsibilities=RoleResponsibilities(text="* Refined"),
                    skills=RoleSkills(skills=["Python"]),
                )
                mock_refine.return_value = mock_refined_role

                mock_experience_info = MagicMock()
                mock_role1 = create_mock_role()
                mock_role2 = create_mock_role()
                mock_role2.basics.title = "Second Title"
                mock_role2.basics.company = "Second Company"
                mock_experience_info.roles = [mock_role1, mock_role2]
                mock_extract.return_value = mock_experience_info

                events = []
                from resume_editor.app.llm.orchestration_refinement import (
                    RefinementState,
                )

                refinement_state = RefinementState(
                    job_analysis=create_mock_job_analysis(),
                    skip_indices={0},
                )
                async for event in async_refine_experience_section(
                    resume_content=resume_content,
                    job_description="Test job",
                    llm_config=LLMConfig(),
                    state=refinement_state,
                ):
                    events.append(event)
                    # Only collect first few events
                    if len(events) > 10:
                        break

        # Check that skip message is in events
        skip_messages = [e for e in events if "Skipping" in str(e.get("message", ""))]
        assert len(skip_messages) > 0
