import logging
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from resume_editor.app.llm.models import (
    JobAnalysis,
    LLMConfig,
    RefinedRoleRecord,
    RunningLog,
)
from resume_editor.app.api.routes.route_logic.resume_ai_logic import (
    _stream_final_events,
)

log = logging.getLogger(__name__)


@pytest.fixture
def llm_config_fixture():
    """Fixture for a sample LLMConfig."""
    return LLMConfig(
        llm_endpoint="http://localhost:8000/v1",
        api_key="test_api_key",
        llm_model_name="test_model",
    )


@pytest.fixture
def job_analysis_fixture():
    """Fixture for a sample JobAnalysis."""
    return JobAnalysis(
        key_skills=["Python", "AWS", "Leadership"],
        primary_duties=["Backend development", "Team management"],
        themes=["fast-paced", "data-driven"],
        inferred_themes=["leadership potential", "collaborative culture"],
    )


@pytest.fixture
def refined_role_records_fixture():
    """Fixture for sample RefinedRoleRecord list."""
    return [
        RefinedRoleRecord(
            original_index=0,
            company="Tech Corp",
            title="Senior Engineer",
            refined_description="Led backend development using Python and AWS.",
            relevant_skills=["Python", "AWS", "Docker"],
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2023, 1, 1),
            timestamp=datetime.now(),
        ),
    ]


@pytest.fixture
def running_log_fixture(job_analysis_fixture, refined_role_records_fixture):
    """Fixture for a sample RunningLog."""
    return RunningLog(
        resume_id=1,
        user_id=1,
        job_description="Senior Python engineer with AWS experience",
        job_analysis=job_analysis_fixture,
        refined_roles=refined_role_records_fixture,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


class TestStreamFinalEventsWithRunningLog:
    """Tests for _stream_final_events with running_log parameter."""

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.generate_banner_from_running_log"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic._reconstruct_refined_resume_content"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_banner_text"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.reconstruct_resume_with_new_introduction"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.process_refined_experience_result"
    )
    async def test_uses_banner_from_running_log_when_available(
        self,
        mock_process_result,
        mock_reconstruct_intro,
        mock_extract_banner,
        mock_reconstruct_resume,
        mock_generate_banner,
        running_log_fixture,
        llm_config_fixture,
    ):
        """Test that new banner generation is used when running_log is provided."""
        # Setup mocks
        mock_reconstruct_resume.return_value = "# Refined Resume"
        mock_extract_banner.return_value = "Original banner"
        mock_generate_banner.return_value = "- **Backend:** Python expert (Tech Corp)"
        mock_reconstruct_intro.return_value = "# Final Resume with Banner"
        mock_process_result.return_value = "<html>result</html>"

        # Create mock params
        mock_params = MagicMock()
        mock_params.resume.id = 1
        mock_params.original_resume_content = "# Original"
        mock_params.resume_content_to_refine = "# To Refine"
        mock_params.job_description = "Job description"
        mock_params.limit_refinement_years = None

        refined_roles = {0: {"basics": {"company": "Tech Corp", "title": "Engineer"}}}

        # Collect all messages
        messages = []
        async for message in _stream_final_events(
            refined_roles=refined_roles,
            params=mock_params,
            llm_config=llm_config_fixture,
            running_log=running_log_fixture,
        ):
            messages.append(message)

        # Verify generate_banner_from_running_log was called
        mock_generate_banner.assert_called_once()
        call_kwargs = mock_generate_banner.call_args.kwargs
        assert call_kwargs["running_log"] == running_log_fixture
        assert (
            call_kwargs["original_resume_content"]
            == mock_params.original_resume_content
        )
        assert call_kwargs["llm_config"] == llm_config_fixture

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.generate_introduction_from_resume"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.generate_banner_from_running_log"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic._reconstruct_refined_resume_content"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_banner_text"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.reconstruct_resume_with_new_introduction"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.process_refined_experience_result"
    )
    async def test_falls_back_to_legacy_when_banner_generation_fails(
        self,
        mock_process_result,
        mock_reconstruct_intro,
        mock_extract_banner,
        mock_reconstruct_resume,
        mock_generate_banner,
        mock_generate_intro,
        running_log_fixture,
        llm_config_fixture,
    ):
        """Test that legacy introduction generation is used when banner generation fails."""
        # Setup mocks
        mock_reconstruct_resume.return_value = "# Refined Resume"
        mock_extract_banner.return_value = "Original banner"
        mock_generate_banner.return_value = ""  # Empty - simulates failure
        mock_generate_intro.return_value = "- Legacy introduction bullet"
        mock_reconstruct_intro.return_value = "# Final Resume"
        mock_process_result.return_value = "<html>result</html>"

        # Create mock params
        mock_params = MagicMock()
        mock_params.resume.id = 1
        mock_params.original_resume_content = "# Original"
        mock_params.resume_content_to_refine = "# To Refine"
        mock_params.job_description = "Job description"
        mock_params.limit_refinement_years = None

        refined_roles = {0: {"basics": {"company": "Tech Corp", "title": "Engineer"}}}

        # Collect all messages
        messages = []
        async for message in _stream_final_events(
            refined_roles=refined_roles,
            params=mock_params,
            llm_config=llm_config_fixture,
            running_log=running_log_fixture,
        ):
            messages.append(message)

        # Verify both generation methods were attempted
        mock_generate_banner.assert_called_once()
        mock_generate_intro.assert_called_once()

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.generate_introduction_from_resume"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic._reconstruct_refined_resume_content"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_banner_text"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.reconstruct_resume_with_new_introduction"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.process_refined_experience_result"
    )
    async def test_uses_legacy_when_no_running_log(
        self,
        mock_process_result,
        mock_reconstruct_intro,
        mock_extract_banner,
        mock_reconstruct_resume,
        mock_generate_intro,
        llm_config_fixture,
    ):
        """Test that legacy method is used when no running_log is provided."""
        # Setup mocks
        mock_reconstruct_resume.return_value = "# Refined Resume"
        mock_extract_banner.return_value = "Original banner"
        mock_generate_intro.return_value = "- Legacy introduction"
        mock_reconstruct_intro.return_value = "# Final Resume"
        mock_process_result.return_value = "<html>result</html>"

        # Create mock params
        mock_params = MagicMock()
        mock_params.resume.id = 1
        mock_params.original_resume_content = "# Original"
        mock_params.resume_content_to_refine = "# To Refine"
        mock_params.job_description = "Job description"
        mock_params.limit_refinement_years = None

        refined_roles = {0: {"basics": {"company": "Tech Corp", "title": "Engineer"}}}

        # Collect all messages (running_log=None)
        messages = []
        async for message in _stream_final_events(
            refined_roles=refined_roles,
            params=mock_params,
            llm_config=llm_config_fixture,
            running_log=None,
        ):
            messages.append(message)

        # Verify legacy method was used
        mock_generate_intro.assert_called_once()
        # Banner generation from running log should not be called

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.generate_introduction_from_resume"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.generate_banner_from_running_log"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic._reconstruct_refined_resume_content"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_banner_text"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.reconstruct_resume_with_new_introduction"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.process_refined_experience_result"
    )
    async def test_running_log_without_refined_roles_uses_legacy(
        self,
        mock_process_result,
        mock_reconstruct_intro,
        mock_extract_banner,
        mock_reconstruct_resume,
        mock_generate_banner,
        mock_generate_intro,
        running_log_fixture,
        llm_config_fixture,
    ):
        """Test that empty refined_roles in running_log skips banner generation and uses legacy."""
        # Setup mocks
        mock_reconstruct_resume.return_value = "# Refined Resume"
        mock_extract_banner.return_value = "Original banner"
        mock_generate_banner.return_value = ""  # Empty because no roles
        mock_generate_intro.return_value = "- Legacy introduction"
        mock_reconstruct_intro.return_value = "# Final Resume"
        mock_process_result.return_value = "<html>result</html>"

        # Create running log without refined roles (empty list is falsy)
        running_log_fixture.refined_roles = []

        # Create mock params
        mock_params = MagicMock()
        mock_params.resume.id = 1
        mock_params.original_resume_content = "# Original"
        mock_params.resume_content_to_refine = "# To Refine"
        mock_params.job_description = "Job description"
        mock_params.limit_refinement_years = None

        refined_roles = {}

        # Collect all messages
        messages = []
        async for message in _stream_final_events(
            refined_roles=refined_roles,
            params=mock_params,
            llm_config=llm_config_fixture,
            running_log=running_log_fixture,
        ):
            messages.append(message)

        # Banner generation is NOT called when refined_roles is empty (falsy)
        # because the function checks `if running_log is not None and running_log.refined_roles:`
        mock_generate_banner.assert_not_called()
        # Legacy method is used instead
        mock_generate_intro.assert_called_once()

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.generate_introduction_from_resume"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.generate_banner_from_running_log"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic._reconstruct_refined_resume_content"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_banner_text"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.reconstruct_resume_with_new_introduction"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.process_refined_experience_result"
    )
    async def test_falls_back_to_legacy_when_banner_generation_raises_exception(
        self,
        mock_process_result,
        mock_reconstruct_intro,
        mock_extract_banner,
        mock_reconstruct_resume,
        mock_generate_banner,
        mock_generate_intro,
        running_log_fixture,
        llm_config_fixture,
    ):
        """Test that legacy introduction generation is used when banner generation raises an exception."""
        # Setup mocks
        mock_reconstruct_resume.return_value = "# Refined Resume"
        mock_extract_banner.return_value = "Original banner"
        mock_generate_banner.side_effect = Exception("Banner generation failed")
        mock_generate_intro.return_value = "- Legacy introduction bullet"
        mock_reconstruct_intro.return_value = "# Final Resume"
        mock_process_result.return_value = "<html>result</html>"

        # Create mock params
        mock_params = MagicMock()
        mock_params.resume.id = 1
        mock_params.original_resume_content = "# Original"
        mock_params.resume_content_to_refine = "# To Refine"
        mock_params.job_description = "Job description"
        mock_params.limit_refinement_years = None

        refined_roles = {0: {"basics": {"company": "Tech Corp", "title": "Engineer"}}}

        # Collect all messages
        messages = []
        async for message in _stream_final_events(
            refined_roles=refined_roles,
            params=mock_params,
            llm_config=llm_config_fixture,
            running_log=running_log_fixture,
        ):
            messages.append(message)

        # Verify banner generation was attempted and raised exception
        mock_generate_banner.assert_called_once()
        # Verify fallback to legacy method
        mock_generate_intro.assert_called_once()


class TestStreamFinalEventsBannerIntegration:
    """Integration-style tests for banner generation in _stream_final_events."""

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.generate_banner_from_running_log"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic._reconstruct_refined_resume_content"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_banner_text"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.reconstruct_resume_with_new_introduction"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.process_refined_experience_result"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.create_sse_done_message"
    )
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.create_sse_progress_message"
    )
    async def test_yields_progress_message(
        self,
        mock_progress_msg,
        mock_done_msg,
        mock_process_result,
        mock_reconstruct_intro,
        mock_extract_banner,
        mock_reconstruct_resume,
        mock_generate_banner,
        running_log_fixture,
        llm_config_fixture,
    ):
        """Test that progress message is yielded during banner generation."""
        # Setup mocks
        mock_reconstruct_resume.return_value = "# Refined Resume"
        mock_extract_banner.return_value = "Original banner"
        mock_generate_banner.return_value = "- **Backend:** Python expert"
        mock_reconstruct_intro.return_value = "# Final Resume"
        mock_process_result.return_value = "<html>result</html>"
        mock_progress_msg.return_value = "progress message"
        mock_done_msg.return_value = "done message"

        # Create mock params
        mock_params = MagicMock()
        mock_params.resume.id = 1
        mock_params.original_resume_content = "# Original"
        mock_params.resume_content_to_refine = "# To Refine"
        mock_params.job_description = "Job description"
        mock_params.limit_refinement_years = None

        refined_roles = {0: {"basics": {"company": "Tech Corp", "title": "Engineer"}}}

        # Collect all messages
        messages = []
        async for message in _stream_final_events(
            refined_roles=refined_roles,
            params=mock_params,
            llm_config=llm_config_fixture,
            running_log=running_log_fixture,
        ):
            messages.append(message)

        # Verify progress message was created
        mock_progress_msg.assert_any_call("Generating AI introduction...")
        # Verify done message was created
        mock_done_msg.assert_called_once()
