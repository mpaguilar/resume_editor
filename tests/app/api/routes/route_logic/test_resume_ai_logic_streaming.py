"""Tests for resume AI logic streaming functions."""

import asyncio
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from cryptography.fernet import InvalidToken
from openai import AuthenticationError

from resume_editor.app.api.routes.route_logic.resume_ai_logic_params import (
    ProcessExperienceResultParams,
)
from resume_editor.app.api.routes.route_logic.resume_ai_logic_sse import (
    create_sse_close_message,
    create_sse_done_message,
    create_sse_error_message,
    create_sse_progress_message,
)
from resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming import (
    _build_skip_indices_from_log,
    _create_refined_role_record,
    _generate_introduction_with_fallback,
    _handle_job_analysis_event,
    _handle_role_refined_event,
    _handle_sse_exception,
    _prepare_refinement_params,
    _process_single_event,
    _stream_final_events,
    _stream_llm_events,
    experience_refinement_sse_generator,
)
from resume_editor.app.api.routes.route_models import ExperienceRefinementParams
from resume_editor.app.llm.models import LLMConfig, RefinedRoleRecord, RunningLog
from resume_editor.app.models.resume.experience import Role, RoleBasics, RoleSummary


def create_test_running_log(**kwargs):
    """Create a RunningLog with default required fields."""
    defaults = {
        "resume_id": 1,
        "user_id": 1,
        "job_description": "Test job description",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "refined_roles": [],
    }
    defaults.update(kwargs)
    return RunningLog(**defaults)


class TestProcessSingleEvent:
    """Tests for _process_single_event function."""

    def test_in_progress_event(self):
        """Test processing in_progress event."""
        refined_roles = {}
        event = {"status": "in_progress", "message": "Processing..."}

        result = _process_single_event(event, refined_roles)

        assert result is not None
        assert "event: progress" in result
        assert "Processing..." in result

    def test_job_analysis_complete_event(self):
        """Test processing job_analysis_complete event."""
        refined_roles = {}
        event = {"status": "job_analysis_complete", "message": "Analysis done"}

        result = _process_single_event(event, refined_roles)

        assert result is not None
        assert "event: progress" in result
        assert "Analysis done" in result

    def test_role_refined_event_valid(self):
        """Test processing valid role_refined event."""
        refined_roles = {}
        role = Role(
            basics=RoleBasics(
                company="Test Corp",
                title="Engineer",
                start_date=datetime.now(),
            )
        )
        event = {
            "status": "role_refined",
            "data": role.model_dump(mode="json"),
            "original_index": 0,
        }

        result = _process_single_event(event, refined_roles)

        assert result is not None
        assert "event: progress" in result
        assert "Engineer at Test Corp" in result
        assert refined_roles[0] == role.model_dump(mode="json")

    def test_unknown_event(self):
        """Test processing unknown event type."""
        refined_roles = {}
        event = {"status": "unknown_status", "message": "test"}

        result = _process_single_event(event, refined_roles)

        assert result is None


class TestHandleJobAnalysisEvent:
    """Tests for _handle_job_analysis_event function."""

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.running_log_manager"
    )
    def test_stores_job_analysis(self, mock_manager):
        """Test that job analysis is stored in running log."""
        job_analysis_data = {
            "key_skills": ["Python", "FastAPI"],
            "primary_duties": ["Develop APIs"],
            "themes": ["Backend"],
        }
        event = {"status": "job_analysis_complete", "job_analysis": job_analysis_data}
        running_log = create_test_running_log()

        _handle_job_analysis_event(event, running_log, resume_id=1, user_id=1)

        mock_manager.update_job_analysis.assert_called_once()

    def test_no_job_analysis_data(self):
        """Test handling when no job_analysis data present."""
        event = {"status": "job_analysis_complete"}
        running_log = create_test_running_log()

        # Should not raise any errors
        _handle_job_analysis_event(event, running_log, resume_id=1, user_id=1)

    def test_no_running_log(self):
        """Test handling when running_log is None."""
        job_analysis_data = {"key_skills": ["Python"]}
        event = {"status": "job_analysis_complete", "job_analysis": job_analysis_data}

        # Should not raise any errors
        _handle_job_analysis_event(event, None, resume_id=1, user_id=1)


class TestHandleRoleRefinedEvent:
    """Tests for _handle_role_refined_event function."""

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.running_log_manager"
    )
    def test_adds_role_to_log(self, mock_manager):
        """Test that refined role is added to running log."""
        role_data = {
            "basics": {
                "company": "Test Corp",
                "title": "Engineer",
                "start_date": "2023-01-01",
            },
            "summary": {"text": "Test summary"},
            "skills": {"items": ["Python", "FastAPI"]},
        }
        event = {"status": "role_refined", "data": role_data, "original_index": 0}
        running_log = create_test_running_log()

        _handle_role_refined_event(event, running_log, resume_id=1, user_id=1)

        mock_manager.add_refined_role.assert_called_once()

    def test_no_running_log(self):
        """Test handling when running_log is None."""
        role_data = {"basics": {"company": "Test"}}
        event = {"status": "role_refined", "data": role_data, "original_index": 0}

        # Should not raise any errors
        _handle_role_refined_event(event, None, resume_id=1, user_id=1)

    def test_no_original_index(self):
        """Test handling when original_index is missing."""
        role_data = {"basics": {"company": "Test"}}
        event = {"status": "role_refined", "data": role_data}
        running_log = create_test_running_log()

        # Should not raise any errors
        _handle_role_refined_event(event, running_log, resume_id=1, user_id=1)

    def test_no_data(self):
        """Test handling when data is missing."""
        event = {"status": "role_refined", "original_index": 0}
        running_log = create_test_running_log()

        # Should not raise any errors
        _handle_role_refined_event(event, running_log, resume_id=1, user_id=1)


class TestGenerateIntroductionWithFallback:
    """Tests for _generate_introduction_with_fallback function."""

    @pytest.mark.asyncio
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.generate_banner_from_running_log"
    )
    async def test_uses_running_log_banner(self, mock_generate_banner):
        """Test using banner from running log."""
        mock_generate_banner.return_value = "Generated banner"
        resume_content = "test content"
        job_description = "test job"
        llm_config = LLMConfig()
        original_banner = "original"
        now = datetime.now()
        refined_role = RefinedRoleRecord(
            original_index=0,
            company="Test Corp",
            title="Engineer",
            refined_description="",
            relevant_skills=[],
            start_date=now,
            end_date=None,
            timestamp=now,
        )
        running_log = create_test_running_log(refined_roles=[refined_role])

        result = await _generate_introduction_with_fallback(
            resume_content, job_description, llm_config, original_banner, running_log
        )

        assert result == "Generated banner"
        mock_generate_banner.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.generate_introduction_from_resume"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.generate_banner_from_running_log"
    )
    async def test_falls_back_to_legacy(
        self, mock_generate_banner, mock_generate_intro
    ):
        """Test falling back to legacy introduction generation."""
        mock_generate_banner.return_value = None
        mock_generate_intro.return_value = "Legacy intro"
        resume_content = "test content"
        job_description = "test job"
        llm_config = LLMConfig()
        original_banner = "original"

        result = await _generate_introduction_with_fallback(
            resume_content, job_description, llm_config, original_banner, None
        )

        assert result == "Legacy intro"
        mock_generate_intro.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.generate_introduction_from_resume"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.generate_banner_from_running_log"
    )
    async def test_retries_on_failure(self, mock_generate_banner, mock_generate_intro):
        """Test retry mechanism on generation failure."""
        mock_generate_banner.return_value = None
        mock_generate_intro.side_effect = [Exception("Fail"), "Success"]
        resume_content = "test content"
        job_description = "test job"
        llm_config = LLMConfig()
        original_banner = "original"

        result = await _generate_introduction_with_fallback(
            resume_content, job_description, llm_config, original_banner, None
        )

        assert result == "Success"
        assert mock_generate_intro.call_count == 2

    @pytest.mark.asyncio
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.generate_introduction_from_resume"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.generate_banner_from_running_log"
    )
    async def test_retries_on_empty_string(
        self, mock_generate_banner, mock_generate_intro
    ):
        """Test retry mechanism on empty string result."""
        mock_generate_banner.return_value = None
        mock_generate_intro.side_effect = ["   ", "Success"]
        resume_content = "test content"
        job_description = "test job"
        llm_config = LLMConfig()
        original_banner = "original"

        result = await _generate_introduction_with_fallback(
            resume_content, job_description, llm_config, original_banner, None
        )

        assert result == "Success"
        assert mock_generate_intro.call_count == 2

    @pytest.mark.asyncio
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.generate_introduction_from_resume"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.generate_banner_from_running_log"
    )
    async def test_default_on_total_failure(
        self, mock_generate_banner, mock_generate_intro
    ):
        """Test default intro when all retries fail."""
        mock_generate_banner.return_value = None
        mock_generate_intro.side_effect = [
            Exception("Fail 1"),
            Exception("Fail 2"),
            Exception("Fail 3"),
        ]
        resume_content = "test content"
        job_description = "test job"
        llm_config = LLMConfig()
        original_banner = "original"

        result = await _generate_introduction_with_fallback(
            resume_content, job_description, llm_config, original_banner, None
        )

        assert "Professional summary tailored" in result
        assert mock_generate_intro.call_count == 3


class TestPrepareRefinementParams:
    """Tests for _prepare_refinement_params function."""

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.get_llm_config"
    )
    def test_prepares_params_correctly(self, mock_get_llm_config):
        """Test that refinement params are prepared correctly."""
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_get_llm_config.return_value = ("http://endpoint", "gpt-4", "api_key")

        params = ExperienceRefinementParams(
            db=mock_db,
            user=mock_user,
            resume=Mock(),
            resume_content_to_refine="content",
            original_resume_content="original",
            job_description="job",
            limit_refinement_years="5",
            company="Test Corp",
            notes="Notes",
        )

        llm_config = _prepare_refinement_params(params)

        assert llm_config.llm_endpoint == "http://endpoint"
        assert llm_config.llm_model_name == "gpt-4"
        assert llm_config.api_key == "api_key"
        mock_get_llm_config.assert_called_once_with(mock_db, 1)

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.get_llm_config"
    )
    def test_handles_none_values(self, mock_get_llm_config):
        """Test handling of None config values."""
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_get_llm_config.return_value = (None, None, None)

        params = ExperienceRefinementParams(
            db=mock_db,
            user=mock_user,
            resume=Mock(),
            resume_content_to_refine="content",
            original_resume_content="original",
            job_description="job",
            limit_refinement_years=None,
        )

        llm_config = _prepare_refinement_params(params)

        assert llm_config.llm_endpoint is None
        assert llm_config.llm_model_name is None
        assert llm_config.api_key is None


class TestBuildSkipIndicesFromLog:
    """Tests for _build_skip_indices_from_log function."""

    def test_extracts_indices_from_log(self):
        """Test extracting indices from running log."""
        now = datetime.now()
        log = create_test_running_log(
            refined_roles=[
                RefinedRoleRecord(
                    original_index=0,
                    company="Corp1",
                    title="Title1",
                    refined_description="",
                    relevant_skills=[],
                    start_date=now,
                    end_date=None,
                    timestamp=now,
                ),
                RefinedRoleRecord(
                    original_index=2,
                    company="Corp2",
                    title="Title2",
                    refined_description="",
                    relevant_skills=[],
                    start_date=now,
                    end_date=None,
                    timestamp=now,
                ),
            ],
        )

        result = _build_skip_indices_from_log(log)

        assert result == {0, 2}

    def test_empty_log(self):
        """Test with empty log."""
        log = create_test_running_log()

        result = _build_skip_indices_from_log(log)

        assert result == set()

    def test_none_log(self):
        """Test with None log."""
        result = _build_skip_indices_from_log(None)

        assert result == set()


class TestCreateRefinedRoleRecord:
    """Tests for _create_refined_role_record function."""

    def test_creates_record_correctly(self):
        """Test creating record from valid role data."""
        role_data = {
            "basics": {
                "company": "Test Corp",
                "title": "Engineer",
                "start_date": "2023-01-15",
                "end_date": "2024-01-15",
            },
            "summary": {"text": "Test summary"},
            "skills": {"items": ["Python", "FastAPI"]},
        }

        record = _create_refined_role_record(0, role_data)

        assert record.original_index == 0
        assert record.company == "Test Corp"
        assert record.title == "Engineer"
        assert record.refined_description == "Test summary"
        assert record.relevant_skills == ["Python", "FastAPI"]

    def test_handles_missing_dates(self):
        """Test handling missing dates."""
        role_data = {
            "basics": {"company": "Test", "title": "Engineer"},
            "summary": {},
            "skills": {},
        }

        record = _create_refined_role_record(1, role_data)

        assert record.original_index == 1
        assert record.company == "Test"
        assert record.title == "Engineer"
        assert record.end_date is None

    def test_handles_invalid_dates(self):
        """Test handling invalid date formats."""
        role_data = {
            "basics": {
                "company": "Test",
                "title": "Engineer",
                "start_date": "invalid-date",
                "end_date": "also-invalid",
            }
        }

        record = _create_refined_role_record(2, role_data)

        assert record.company == "Test"
        # Should not raise error, uses default


class TestHandleSseException:
    """Tests for _handle_sse_exception function."""

    def test_invalid_token(self):
        """Test handling InvalidToken exception."""
        e = InvalidToken()
        result = _handle_sse_exception(e, resume_id=1)

        assert "event: error" in result
        assert "Invalid API key" in result

    def test_authentication_error(self):
        """Test handling AuthenticationError."""
        e = AuthenticationError(message="auth failed", response=Mock(), body=None)
        result = _handle_sse_exception(e, resume_id=1)

        assert "event: error" in result
        assert "LLM authentication failed" in result

    def test_value_error(self):
        """Test handling ValueError."""
        e = ValueError("custom error")
        result = _handle_sse_exception(e, resume_id=1)

        assert "event: error" in result
        assert "Refinement failed: custom error" in result

    def test_generic_exception(self):
        """Test handling generic exception."""
        e = Exception("something went wrong")
        result = _handle_sse_exception(e, resume_id=1)

        assert "event: error" in result
        assert "An unexpected error occurred" in result


class TestStreamLlmEvents:
    """Tests for _stream_llm_events function."""

    @pytest.mark.asyncio
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.async_refine_experience_section"
    )
    async def test_yields_progress_events(self, mock_refine):
        """Test that progress events are yielded."""

        async def mock_generator():
            yield {"status": "in_progress", "message": "Processing..."}

        mock_refine.return_value = mock_generator()

        params = Mock()
        params.resume.id = 1
        params.resume_content_to_refine = "content"
        params.job_description = "job"
        llm_config = LLMConfig()
        refined_roles = {}

        results = []
        async for msg in _stream_llm_events(params, llm_config, refined_roles, None):
            results.append(msg)

        assert len(results) == 1
        assert "event: progress" in results[0]
        assert "Processing..." in results[0]

    @pytest.mark.asyncio
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.async_refine_experience_section"
    )
    async def test_yields_role_refined_events(self, mock_refine):
        """Test that role_refined events are yielded."""
        role = Role(
            basics=RoleBasics(
                company="Test Corp", title="Engineer", start_date=datetime.now()
            )
        )

        async def mock_generator():
            yield {
                "status": "role_refined",
                "data": role.model_dump(mode="json"),
                "original_index": 0,
            }

        mock_refine.return_value = mock_generator()

        params = Mock()
        params.resume.id = 1
        params.user.id = 1
        params.resume_content_to_refine = "content"
        params.job_description = "job"
        llm_config = LLMConfig()
        refined_roles = {}

        results = []
        async for msg in _stream_llm_events(params, llm_config, refined_roles, None):
            results.append(msg)

        assert len(results) == 1
        assert "event: progress" in results[0]
        assert "Engineer at Test Corp" in results[0]

    @pytest.mark.asyncio
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.async_refine_experience_section"
    )
    async def test_skips_indices(self, mock_refine):
        """Test that skip_indices are passed correctly."""

        async def mock_generator():
            yield {"status": "in_progress", "message": "Done"}

        mock_refine.return_value = mock_generator()

        params = Mock()
        params.resume.id = 1
        params.resume_content_to_refine = "content"
        params.job_description = "job"
        llm_config = LLMConfig()
        refined_roles = {}
        now = datetime.now()
        running_log = create_test_running_log(
            refined_roles=[
                RefinedRoleRecord(
                    original_index=0,
                    company="Corp",
                    title="Title",
                    refined_description="",
                    relevant_skills=[],
                    start_date=now,
                    end_date=None,
                    timestamp=now,
                )
            ]
        )

        results = []
        async for msg in _stream_llm_events(
            params, llm_config, refined_roles, running_log
        ):
            results.append(msg)

        # Verify skip_indices was passed in state
        call_kwargs = mock_refine.call_args.kwargs
        state = call_kwargs.get("state")
        assert state is not None
        assert state.skip_indices == {0}


class TestStreamFinalEvents:
    """Tests for _stream_final_events function."""

    @pytest.mark.asyncio
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.reconstruct_resume_with_new_introduction"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming._generate_introduction_with_fallback"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming._reconstruct_refined_resume_content"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.extract_banner_text"
    )
    async def test_yields_intro_progress(
        self,
        mock_extract_banner,
        mock_reconstruct_content,
        mock_generate_intro,
        mock_reconstruct_final,
    ):
        """Test that intro generation progress is yielded."""
        mock_extract_banner.return_value = "original"
        mock_reconstruct_content.return_value = "content"
        mock_generate_intro.return_value = "intro"
        mock_reconstruct_final.return_value = "final"

        params = Mock()
        params.resume.id = 1
        params.original_resume_content = "original"
        params.resume_content_to_refine = "content"
        params.job_description = "job"
        params.limit_refinement_years = None
        params.company = None
        params.notes = None
        llm_config = LLMConfig()
        refined_roles = {}

        results = []
        async for msg in _stream_final_events(refined_roles, params, llm_config, None):
            results.append(msg)

        # First message should be intro progress
        assert any("Generating AI introduction" in msg for msg in results)

    @pytest.mark.asyncio
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.reconstruct_resume_with_new_introduction"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming._generate_introduction_with_fallback"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming._reconstruct_refined_resume_content"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.extract_banner_text"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.process_refined_experience_result"
    )
    async def test_yields_done_event(
        self,
        mock_process_result,
        mock_extract_banner,
        mock_reconstruct_content,
        mock_generate_intro,
        mock_reconstruct_final,
    ):
        """Test that done event is yielded."""
        mock_extract_banner.return_value = "original"
        mock_reconstruct_content.return_value = "content"
        mock_generate_intro.return_value = "intro"
        mock_reconstruct_final.return_value = "final"
        mock_process_result.return_value = "<html>result</html>"

        params = Mock()
        params.resume.id = 1
        params.original_resume_content = "original"
        params.resume_content_to_refine = "content"
        params.job_description = "job"
        params.limit_refinement_years = None
        llm_config = LLMConfig()
        refined_roles = {0: {"basics": {"company": "Test"}}}

        results = []
        async for msg in _stream_final_events(refined_roles, params, llm_config, None):
            results.append(msg)

        assert any("event: done" in msg for msg in results)
        assert any("<html>result</html>" in msg for msg in results)

    @pytest.mark.asyncio
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.reconstruct_resume_with_new_introduction"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming._generate_introduction_with_fallback"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming._reconstruct_refined_resume_content"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.extract_banner_text"
    )
    async def test_warning_on_no_roles(
        self,
        mock_extract_banner,
        mock_reconstruct_content,
        mock_generate_intro,
        mock_reconstruct_final,
    ):
        """Test warning when no roles refined."""
        mock_extract_banner.return_value = "original"
        mock_reconstruct_content.return_value = "content"
        mock_generate_intro.return_value = "intro"
        mock_reconstruct_final.return_value = "final"

        params = Mock()
        params.resume.id = 1
        params.original_resume_content = "original"
        params.resume_content_to_refine = "content"
        params.job_description = "job"
        params.limit_refinement_years = None
        params.company = None
        params.notes = None
        llm_config = LLMConfig()
        refined_roles = {}  # No roles

        results = []
        async for msg in _stream_final_events(refined_roles, params, llm_config, None):
            results.append(msg)

        # Should yield warning
        assert any("no roles were found to refine" in msg for msg in results)


class TestExperienceRefinementSseGenerator:
    """Tests for experience_refinement_sse_generator function."""

    @pytest.mark.asyncio
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming._stream_final_events"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming._stream_llm_events"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.get_llm_config"
    )
    async def test_successful_refinement(
        self, mock_get_config, mock_stream_llm, mock_stream_final
    ):
        """Test successful refinement flow."""
        mock_get_config.return_value = (None, None, None)

        async def mock_llm_gen():
            yield create_sse_progress_message("Progress 1")

        async def mock_final_gen():
            yield create_sse_done_message("<html>result</html>")

        mock_stream_llm.return_value = mock_llm_gen()
        mock_stream_final.return_value = mock_final_gen()

        params = Mock()
        params.db = Mock()
        params.user = Mock()
        params.user.id = 1
        params.resume = Mock()
        params.resume.id = 1
        params.original_resume_content = "original"
        params.resume_content_to_refine = "content"
        params.job_description = "job"
        params.limit_refinement_years = None
        params.company = None
        params.notes = None

        results = []
        async for msg in experience_refinement_sse_generator(params):
            results.append(msg)

        assert len(results) >= 3  # progress, done, close
        assert any("event: done" in msg for msg in results)
        assert any("event: close" in msg for msg in results)

    @pytest.mark.asyncio
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.running_log_manager"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.get_llm_config"
    )
    async def test_resumes_from_checkpoint(self, mock_get_config, mock_log_manager):
        """Test resumption from checkpoint."""
        mock_get_config.return_value = (None, None, None)
        now = datetime.now()
        mock_log_manager.get_log.return_value = create_test_running_log(
            refined_roles=[
                RefinedRoleRecord(
                    original_index=0,
                    company="Corp",
                    title="Title",
                    refined_description="desc",
                    relevant_skills=["skill"],
                    start_date=now,
                    end_date=None,
                    timestamp=now,
                )
            ],
        )

        @patch(
            "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming._stream_llm_events"
        )
        @patch(
            "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming._stream_final_events"
        )
        async def run_test(mock_stream_final, mock_stream_llm):
            async def mock_llm_gen():
                yield create_sse_progress_message("Progress")

            async def mock_final_gen():
                yield create_sse_done_message("<html>result</html>")

            mock_stream_llm.return_value = mock_llm_gen()
            mock_stream_final.return_value = mock_final_gen()

            params = Mock()
            params.db = Mock()
            params.user = Mock()
            params.user.id = 1
            params.resume = Mock()
            params.resume.id = 1
            params.original_resume_content = "original"
            params.resume_content_to_refine = "content"
            params.job_description = "job"
            params.limit_refinement_years = None
            params.company = None
            params.notes = None

            results = []
            async for msg in experience_refinement_sse_generator(params):
                results.append(msg)

            # Should include resumption message
            assert any("Resuming from previous attempt" in msg for msg in results)

        await run_test()

    @pytest.mark.asyncio
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.get_llm_config"
    )
    async def test_handles_exception(self, mock_get_config):
        """Test handling of exceptions."""
        mock_get_config.side_effect = ValueError("Config error")

        params = Mock()
        params.db = Mock()
        params.user = Mock()
        params.user.id = 1
        params.resume = Mock()
        params.resume.id = 1

        results = []
        async for msg in experience_refinement_sse_generator(params):
            results.append(msg)

        assert any("event: error" in msg for msg in results)
        assert any("event: close" in msg for msg in results)

    @pytest.mark.asyncio
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.get_llm_config"
    )
    async def test_handles_client_disconnect(self, mock_get_config):
        """Test handling of client disconnect (GeneratorExit)."""
        mock_get_config.return_value = (None, None, None)

        @patch(
            "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming._stream_llm_events"
        )
        async def run_test(mock_stream_llm):
            async def mock_llm_gen():
                yield create_sse_progress_message("Progress")
                # Simulate slow operation
                await asyncio.sleep(10)

            mock_stream_llm.return_value = mock_llm_gen()

            params = Mock()
            params.db = Mock()
            params.user = Mock()
            params.user.id = 1
            params.resume = Mock()
            params.resume.id = 1
            params.original_resume_content = "original"
            params.resume_content_to_refine = "content"
            params.job_description = "job"
            params.limit_refinement_years = None
            params.company = None
            params.notes = None

            gen = experience_refinement_sse_generator(params)
            await gen.__anext__()  # Get first item

            # Simulate disconnect
            with pytest.raises(StopAsyncIteration):
                await gen.athrow(GeneratorExit)

        await run_test()

    @pytest.mark.asyncio
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming._stream_final_events"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming._stream_llm_events"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.get_llm_config"
    )
    async def test_prepopulates_roles_from_log(
        self, mock_get_config, mock_stream_llm, mock_stream_final
    ):
        """Test that refined roles are pre-populated from running log."""
        mock_get_config.return_value = (None, None, None)

        async def mock_llm_gen():
            yield create_sse_progress_message("Progress")

        async def mock_final_gen():
            yield create_sse_done_message("<html>result</html>")

        mock_stream_llm.return_value = mock_llm_gen()
        mock_stream_final.return_value = mock_final_gen()

        now = datetime.now()
        running_log = create_test_running_log(
            refined_roles=[
                RefinedRoleRecord(
                    original_index=0,
                    company="Test Corp",
                    title="Engineer",
                    refined_description="Test summary",
                    relevant_skills=["Python"],
                    start_date=now,
                    end_date=None,
                    timestamp=now,
                )
            ],
        )

        with patch(
            "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.running_log_manager"
        ) as mock_manager:
            mock_manager.get_log.return_value = running_log

            params = Mock()
            params.db = Mock()
            params.user = Mock()
            params.user.id = 1
            params.resume = Mock()
            params.resume.id = 1
            params.original_resume_content = "original"
            params.resume_content_to_refine = "content"
            params.job_description = "job"
            params.limit_refinement_years = None
            params.company = None
            params.notes = None

            results = []
            async for msg in experience_refinement_sse_generator(params):
                results.append(msg)

            # The generator should complete successfully with pre-populated roles
            assert any("event: done" in msg for msg in results)


class TestIntegration:
    """Integration tests for streaming functions."""

    @pytest.mark.asyncio
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.process_refined_experience_result"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.reconstruct_resume_with_new_introduction"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming._generate_introduction_with_fallback"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming._reconstruct_refined_resume_content"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.async_refine_experience_section"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming.get_llm_config"
    )
    async def test_end_to_end_refinement(
        self,
        mock_get_config,
        mock_refine,
        mock_reconstruct_content,
        mock_generate_intro,
        mock_reconstruct_final,
        mock_process_result,
    ):
        """Test end-to-end refinement flow."""
        mock_get_config.return_value = (None, None, None)

        role = Role(
            basics=RoleBasics(
                company="Test Corp", title="Engineer", start_date=datetime.now()
            ),
            summary=RoleSummary(text="Test summary"),
        )

        async def mock_refinement_gen():
            yield {"status": "in_progress", "message": "Parsing resume..."}
            yield {
                "status": "role_refined",
                "data": role.model_dump(mode="json"),
                "original_index": 0,
            }

        mock_refine.return_value = mock_refinement_gen()
        mock_reconstruct_content.return_value = "content with roles"
        mock_generate_intro.return_value = "Generated intro"
        mock_reconstruct_final.return_value = "final content"
        mock_process_result.return_value = "<html>final result</html>"

        params = Mock()
        params.db = Mock()
        params.user = Mock()
        params.user.id = 1
        params.resume = Mock()
        params.resume.id = 1
        params.original_resume_content = "# Personal\n\n# Experience\n\n## Role"
        params.resume_content_to_refine = "# Experience\n\n## Role"
        params.job_description = "Job description"
        params.limit_refinement_years = None
        params.company = None
        params.notes = None

        results = []
        async for msg in experience_refinement_sse_generator(params):
            results.append(msg)

        result_str = "".join(results)

        # Verify all expected events are present
        assert "Parsing resume..." in result_str
        assert "Engineer at Test Corp" in result_str
        assert "Generating AI introduction" in result_str
        assert "event: done" in result_str
        assert "<html>final result</html>" in result_str
        assert "event: close" in result_str
