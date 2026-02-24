"""Tests to cover specific uncovered lines for 100% coverage.

This module contains targeted tests for edge cases and exception handling
that were previously uncovered.
"""

from datetime import datetime, timezone
from unittest.mock import ANY, AsyncMock, MagicMock, Mock, patch

import pytest

from resume_editor.app.api.routes.route_logic.refinement_checkpoint import (
    RunningLog,
)
from resume_editor.app.llm.models import (
    BannerBullet,
    GeneratedBanner,
    JobAnalysis,
)


class TestCalculateEducationRelevanceThemeMatching:
    """Tests for _calculate_education_relevance theme matching - covers lines 1213-1214."""

    def test_theme_matching_adds_score_and_breaks(self):
        """Test that theme matching adds score and breaks - covers lines 1213-1214."""
        from resume_editor.app.llm.orchestration import (
            _calculate_education_relevance,
        )

        # Line with theme keyword
        education_line = "Master's in Computer Science with focus on backend systems"
        job_skills = ["python"]
        job_themes = ["backend", "api", "microservices"]

        score = _calculate_education_relevance(education_line, job_skills, job_themes)

        # Score should include +1 for theme match
        assert score >= 6  # Base 5 + 1 for theme

    def test_theme_breaks_after_first_match(self):
        """Test that theme matching breaks after first match - line 1214."""
        from resume_editor.app.llm.orchestration import (
            _calculate_education_relevance,
        )

        # Line with multiple theme keywords
        education_line = "Master's in backend and api development"
        job_skills = []
        job_themes = ["backend", "api", "microservices", "cloud"]

        score = _calculate_education_relevance(education_line, job_skills, job_themes)

        # Theme match should only add 1 (breaks after first), not 2
        # Base 5 + 1 for first theme match = 6
        assert score == 6


class TestInvokeBannerGenerationChainSuccess:
    """Tests for _invoke_banner_generation_chain success path - covers lines 1418-1423."""

    @patch("resume_editor.app.llm.orchestration.GeneratedBanner")
    @patch("resume_editor.app.llm.orchestration.ChatPromptTemplate")
    @patch("resume_editor.app.llm.orchestration.StrOutputParser")
    @patch("resume_editor.app.llm.orchestration._parse_json_with_fix")
    def test_invoke_banner_chain_successful_parse_and_validate(
        self,
        mock_parse_json,
        mock_str_parser,
        mock_prompt_template,
        mock_banner_model,
    ):
        """Test successful banner generation covering lines 1418-1423."""
        from resume_editor.app.llm.orchestration import (
            _invoke_banner_generation_chain,
        )

        # Setup the mock chain using pipe operator
        mock_prompt = MagicMock()
        mock_prompt_partial = MagicMock()
        mock_prompt.partial.return_value = mock_prompt_partial
        mock_prompt_template.from_messages.return_value = mock_prompt

        # Mock the pipe operations: prompt | llm | parser
        mock_chain_after_prompt = MagicMock()
        mock_prompt_partial.__or__ = MagicMock(return_value=mock_chain_after_prompt)

        mock_chain_final = MagicMock()
        mock_chain_after_prompt.__or__ = MagicMock(return_value=mock_chain_final)

        mock_chain_final.invoke.return_value = '{"bullets": []}'

        mock_parse_json.return_value = {
            "bullets": [{"category": "Backend", "description": "Python expert"}],
            "education_bullet": None,
        }

        expected_banner = GeneratedBanner(
            bullets=[BannerBullet(category="Backend", description="Python expert")],
            education_bullet=None,
        )
        mock_banner_model.model_validate.return_value = expected_banner

        mock_llm = MagicMock()

        result = _invoke_banner_generation_chain(
            llm=mock_llm,
            job_analysis=JobAnalysis(
                key_skills=[],
                primary_duties=[],
                themes=[],
            ),
            refined_roles=[],
            cross_section_evidence=[],
            original_banner=None,
        )

        # Verify the chain was invoked and parsing/validation happened
        mock_chain_final.invoke.assert_called_once()
        mock_parse_json.assert_called_once()
        mock_banner_model.model_validate.assert_called_once()
        assert result == expected_banner


class TestRefineRoleAndPutOnQueueProgressCallback:
    """Tests for progress callback in _refine_role_and_put_on_queue - covers line 293."""

    @pytest.mark.asyncio
    @patch("resume_editor.app.llm.orchestration.refine_role")
    async def test_progress_callback_called_during_role_refinement(
        self, mock_refine_role
    ):
        """Test that progress callback is called - covers line 293."""
        import asyncio

        from resume_editor.app.llm.models import LLMConfig, RoleRefinementJob
        from resume_editor.app.llm.orchestration import _refine_role_and_put_on_queue
        from resume_editor.app.models.resume.experience import (
            Role,
            RoleBasics,
        )

        # Create an event queue to capture events
        event_queue = asyncio.Queue()

        # Create a mock role with proper attributes
        mock_role = MagicMock(spec=Role)
        mock_role.basics = MagicMock(spec=RoleBasics)
        mock_role.basics.title = "Software Engineer"
        mock_role.basics.company = "Tech Corp"

        # Create a job
        job = RoleRefinementJob(
            original_index=0,
            role=mock_role,
            job_analysis=JobAnalysis(
                key_skills=["Python"],
                primary_duties=["Development"],
                themes=["backend"],
            ),
            llm_config=LLMConfig(),
        )

        # Mock refine_role to capture and call the progress callback
        async def mock_refine_with_callback(*args, **kwargs):
            progress_callback = kwargs.get("progress_callback")
            if progress_callback:
                await progress_callback("Test progress message")
            return MagicMock(model_dump=lambda mode: {"test": "data"})

        mock_refine_role.side_effect = mock_refine_with_callback

        # Create a real semaphore
        semaphore = asyncio.Semaphore(1)

        await _refine_role_and_put_on_queue(job, semaphore, event_queue)

        # Verify refine_role was called with progress_callback
        mock_refine_role.assert_called_once()
        call_kwargs = mock_refine_role.call_args.kwargs
        assert "progress_callback" in call_kwargs
        assert call_kwargs["progress_callback"] is not None

        # Verify progress message was queued (line 293 coverage)
        # Check that in_progress event was queued
        events = []
        while not event_queue.empty():
            events.append(event_queue.get_nowait())

        progress_events = [e for e in events if e.get("status") == "in_progress"]
        assert len(progress_events) >= 1


class TestExperienceRefinementStreamException:
    """Tests for exception handling in _experience_refinement_stream - covers lines 389-392."""

    @pytest.mark.asyncio
    @patch("resume_editor.app.api.routes.resume_ai.running_log_manager")
    @patch("resume_editor.app.api.routes.resume_ai.experience_refinement_sse_generator")
    @patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
    @patch("resume_editor.app.api.routes.resume_ai._build_filtered_content_if_needed")
    async def test_exception_keeps_running_log(
        self,
        mock_build_filtered,
        mock_extract_exp,
        mock_generator,
        mock_running_log_manager,
    ):
        """Test that exception keeps running log for resumption - lines 389-392."""
        from resume_editor.app.api.routes.resume_ai import (
            _ExperienceStreamParams,
            _experience_refinement_stream,
        )

        # Setup running log
        mock_running_log = MagicMock()
        mock_running_log_manager.get_log.return_value = mock_running_log
        mock_running_log_manager.job_description_matches.return_value = True

        # Setup mocks
        mock_resume = MagicMock()
        mock_resume.id = 1
        mock_resume.content = "test content"

        mock_user = MagicMock()
        mock_user.id = 1

        mock_db = MagicMock()

        mock_build_filtered.return_value = "filtered content"
        mock_extract_exp.return_value = MagicMock(roles=[MagicMock()])

        # Create generator that raises exception after yielding
        async def failing_generator(*args, **kwargs):
            yield "some progress"
            raise ValueError("Test exception")

        mock_generator.return_value = failing_generator()

        params = _ExperienceStreamParams(
            db=mock_db,
            current_user=mock_user,
            resume=mock_resume,
            job_description="test job",
            limit_refinement_years=None,
            parsed_limit_years=None,
        )

        # Collect yielded items
        items = []
        try:
            async for item in _experience_refinement_stream(params):
                items.append(item)
        except ValueError:
            pass  # Expected

        # Verify running log was NOT cleared (kept for resumption)
        mock_running_log_manager.clear_log.assert_not_called()

    @pytest.mark.asyncio
    @patch("resume_editor.app.api.routes.resume_ai.running_log_manager")
    @patch("resume_editor.app.api.routes.resume_ai.experience_refinement_sse_generator")
    @patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
    @patch("resume_editor.app.api.routes.resume_ai._build_filtered_content_if_needed")
    async def test_success_clears_running_log(
        self,
        mock_build_filtered,
        mock_extract_exp,
        mock_generator,
        mock_running_log_manager,
    ):
        """Test that success clears running log."""
        from resume_editor.app.api.routes.resume_ai import (
            _ExperienceStreamParams,
            _experience_refinement_stream,
        )

        # Setup running log
        mock_running_log = MagicMock()
        mock_running_log_manager.get_log.return_value = mock_running_log
        mock_running_log_manager.job_description_matches.return_value = True

        # Setup mocks
        mock_resume = MagicMock()
        mock_resume.id = 1
        mock_resume.content = "test content"

        mock_user = MagicMock()
        mock_user.id = 1

        mock_db = MagicMock()

        mock_build_filtered.return_value = "filtered content"
        mock_extract_exp.return_value = MagicMock(roles=[MagicMock()])

        # Create successful generator
        async def success_generator(*args, **kwargs):
            yield "success result"

        mock_generator.return_value = success_generator()

        params = _ExperienceStreamParams(
            db=mock_db,
            current_user=mock_user,
            resume=mock_resume,
            job_description="test job",
            limit_refinement_years=None,
            parsed_limit_years=None,
        )

        # Collect yielded items
        items = []
        async for item in _experience_refinement_stream(params):
            items.append(item)

        # Verify running log WAS cleared
        mock_running_log_manager.clear_log.assert_called_once_with(1, 1)
