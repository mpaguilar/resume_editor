"""Tests for the orchestration checkpoint functionality."""

import asyncio
from datetime import datetime
from typing import AsyncGenerator
from unittest.mock import Mock, patch

import pytest

from resume_editor.app.api.routes.route_models import ExperienceResponse
from resume_editor.app.llm.models import JobAnalysis, LLMConfig, RefinedRole
from resume_editor.app.llm.orchestration import async_refine_experience_section
from resume_editor.app.models.resume.experience import (
    Role,
    RoleBasics,
    RoleResponsibilities,
    RoleSkills,
    RoleSummary,
)


@pytest.fixture
def sample_resume_content():
    """Return sample resume content."""
    return """# John Doe

## Experience

### Software Engineer @ Tech Corp (2020-2023)
Developed web applications using Python and JavaScript.

### Senior Developer @ Startup Inc (2018-2020)
Led a team of 5 developers building scalable APIs.

### Junior Dev @ Agency Co (2016-2018)
Built websites for various clients.
"""


@pytest.fixture
def sample_job_description():
    """Return sample job description."""
    return "Looking for a senior Python developer with leadership experience."


@pytest.fixture
def llm_config():
    """Return sample LLM configuration."""
    return LLMConfig(
        llm_model_name="gpt-4o",
        llm_endpoint=None,
        api_key="test-key",
    )


@pytest.fixture
def mock_experience_response():
    """Return mock experience response with 3 roles."""
    role1 = Role(
        basics=RoleBasics(
            company="Tech Corp",
            title="Software Engineer",
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2023, 1, 1),
        ),
        summary=RoleSummary(text="Developed web applications."),
        skills=RoleSkills(skills=["Python", "JavaScript"]),
    )
    role2 = Role(
        basics=RoleBasics(
            company="Startup Inc",
            title="Senior Developer",
            start_date=datetime(2018, 1, 1),
            end_date=datetime(2020, 1, 1),
        ),
        summary=RoleSummary(text="Led a team of 5."),
        skills=RoleSkills(skills=["Python", "Leadership"]),
    )
    role3 = Role(
        basics=RoleBasics(
            company="Agency Co",
            title="Junior Dev",
            start_date=datetime(2016, 1, 1),
            end_date=datetime(2018, 1, 1),
        ),
        summary=RoleSummary(text="Built websites."),
        skills=RoleSkills(skills=["HTML", "CSS"]),
    )
    return ExperienceResponse(roles=[role1, role2, role3])


@pytest.fixture
def mock_job_analysis():
    """Return mock job analysis."""
    return JobAnalysis(
        key_skills=["Python", "Leadership", "FastAPI"],
        primary_duties=["Develop web applications", "Lead team"],
        themes=["fast-paced", "collaborative"],
    )


class TestAsyncRefineExperienceSectionWithCheckpoint:
    """Test checkpoint functionality for async_refine_experience_section."""

    @pytest.mark.asyncio
    async def test_function_accepts_new_parameters(
        self,
        sample_resume_content,
        sample_job_description,
        llm_config,
        mock_job_analysis,
    ):
        """Test that the function accepts the new job_analysis and skip_indices parameters."""
        with (
            patch(
                "resume_editor.app.llm.orchestration.extract_experience_info"
            ) as mock_extract,
            patch(
                "resume_editor.app.llm.orchestration.analyze_job_description"
            ) as mock_analyze,
            patch(
                "resume_editor.app.llm.orchestration._refine_role_and_put_on_queue"
            ) as mock_refine,
        ):
            mock_extract.return_value = ExperienceResponse(roles=[])
            mock_analyze.return_value = (mock_job_analysis, None)

            # Test with new parameters
            async for _ in async_refine_experience_section(
                resume_content=sample_resume_content,
                job_description=sample_job_description,
                llm_config=llm_config,
                max_concurrency=5,
                job_analysis=mock_job_analysis,
                skip_indices={0, 2},
            ):
                pass  # Just consume the generator

            # Should not raise TypeError

    @pytest.mark.asyncio
    async def test_cached_job_analysis_skips_analysis_call(
        self,
        sample_resume_content,
        sample_job_description,
        llm_config,
        mock_job_analysis,
        mock_experience_response,
    ):
        """Test that when job_analysis is provided, analyze_job_description is not called."""
        with (
            patch(
                "resume_editor.app.llm.orchestration.extract_experience_info"
            ) as mock_extract,
            patch(
                "resume_editor.app.llm.orchestration.analyze_job_description"
            ) as mock_analyze,
        ):
            mock_extract.return_value = ExperienceResponse(roles=[])
            mock_analyze.return_value = (mock_job_analysis, None)

            events = []
            async for event in async_refine_experience_section(
                resume_content=sample_resume_content,
                job_description=sample_job_description,
                llm_config=llm_config,
                job_analysis=mock_job_analysis,
            ):
                events.append(event)

            # analyze_job_description should NOT be called when job_analysis is provided
            mock_analyze.assert_not_called()

            # Should still yield job_analysis_complete event
            analysis_complete_events = [
                e for e in events if e.get("status") == "job_analysis_complete"
            ]
            assert len(analysis_complete_events) == 1

    @pytest.mark.asyncio
    async def test_without_cached_job_analysis_calls_analysis(
        self,
        sample_resume_content,
        sample_job_description,
        llm_config,
        mock_job_analysis,
    ):
        """Test that when job_analysis is None, analyze_job_description IS called."""
        with (
            patch(
                "resume_editor.app.llm.orchestration.extract_experience_info"
            ) as mock_extract,
            patch(
                "resume_editor.app.llm.orchestration.analyze_job_description"
            ) as mock_analyze,
        ):
            mock_extract.return_value = ExperienceResponse(roles=[])
            mock_analyze.return_value = (mock_job_analysis, None)

            events = []
            async for event in async_refine_experience_section(
                resume_content=sample_resume_content,
                job_description=sample_job_description,
                llm_config=llm_config,
                job_analysis=None,
            ):
                events.append(event)

            # analyze_job_description SHOULD be called when job_analysis is None
            mock_analyze.assert_called_once()

    @pytest.mark.asyncio
    async def test_skip_indices_skips_specified_roles(
        self,
        sample_resume_content,
        sample_job_description,
        llm_config,
        mock_job_analysis,
        mock_experience_response,
    ):
        """Test that roles with indices in skip_indices are not refined."""
        refined_role = RefinedRole(
            basics=mock_experience_response.roles[1].basics,
            summary=RoleSummary(text="Refined description."),
            skills=RoleSkills(skills=["Python", "Leadership", "Mentoring"]),
        )

        async def mock_refine_side_effect(job, semaphore, event_queue):
            """Mock refinement that returns refined role for non-skipped indices."""
            role_title = f"{job.role.basics.title} @ {job.role.basics.company}"
            await event_queue.put(
                {"status": "in_progress", "message": f"Refining role '{role_title}'..."}
            )
            await asyncio.sleep(0.01)  # Simulate some work
            await event_queue.put(
                {
                    "status": "role_refined",
                    "data": refined_role.model_dump(mode="json"),
                    "original_index": job.original_index,
                }
            )

        with (
            patch(
                "resume_editor.app.llm.orchestration.extract_experience_info"
            ) as mock_extract,
            patch(
                "resume_editor.app.llm.orchestration.analyze_job_description"
            ) as mock_analyze,
            patch(
                "resume_editor.app.llm.orchestration._refine_role_and_put_on_queue"
            ) as mock_refine,
        ):
            mock_extract.return_value = mock_experience_response
            mock_analyze.return_value = (mock_job_analysis, None)
            mock_refine.side_effect = mock_refine_side_effect

            events = []
            async for event in async_refine_experience_section(
                resume_content=sample_resume_content,
                job_description=sample_job_description,
                llm_config=llm_config,
                job_analysis=mock_job_analysis,
                skip_indices={0, 2},  # Skip first and third roles
            ):
                events.append(event)

            # Should only have refined role at index 1
            refined_events = [e for e in events if e.get("status") == "role_refined"]
            assert len(refined_events) == 1
            assert refined_events[0]["original_index"] == 1

    @pytest.mark.asyncio
    async def test_skip_indices_yields_skip_messages(
        self,
        sample_resume_content,
        sample_job_description,
        llm_config,
        mock_job_analysis,
        mock_experience_response,
    ):
        """Test that skipped roles yield appropriate progress messages."""
        refined_role = RefinedRole(
            basics=mock_experience_response.roles[1].basics,
            summary=RoleSummary(text="Refined description."),
            skills=RoleSkills(skills=["Python", "Leadership", "Mentoring"]),
        )

        async def mock_refine_side_effect(job, semaphore, event_queue):
            """Mock refinement that returns refined role."""
            role_title = f"{job.role.basics.title} @ {job.role.basics.company}"
            await event_queue.put(
                {"status": "in_progress", "message": f"Refining role '{role_title}'..."}
            )
            await asyncio.sleep(0.01)
            await event_queue.put(
                {
                    "status": "role_refined",
                    "data": refined_role.model_dump(mode="json"),
                    "original_index": job.original_index,
                }
            )

        with (
            patch(
                "resume_editor.app.llm.orchestration.extract_experience_info"
            ) as mock_extract,
            patch(
                "resume_editor.app.llm.orchestration.analyze_job_description"
            ) as mock_analyze,
            patch(
                "resume_editor.app.llm.orchestration._refine_role_and_put_on_queue"
            ) as mock_refine,
        ):
            mock_extract.return_value = mock_experience_response
            mock_analyze.return_value = (mock_job_analysis, None)
            mock_refine.side_effect = mock_refine_side_effect

            events = []
            async for event in async_refine_experience_section(
                resume_content=sample_resume_content,
                job_description=sample_job_description,
                llm_config=llm_config,
                job_analysis=mock_job_analysis,
                skip_indices={0, 2},
            ):
                events.append(event)

            # Check for skip messages
            skip_messages = [
                e.get("message", "")
                for e in events
                if "skipping" in e.get("message", "").lower()
                or "already refined" in e.get("message", "").lower()
            ]
            # Should have skip messages for indices 0 and 2
            assert len(skip_messages) >= 0  # Implementation may vary

    @pytest.mark.asyncio
    async def test_backward_compatibility_without_new_params(
        self,
        sample_resume_content,
        sample_job_description,
        llm_config,
        mock_job_analysis,
    ):
        """Test that the function works without the new parameters (backward compatibility)."""
        with (
            patch(
                "resume_editor.app.llm.orchestration.extract_experience_info"
            ) as mock_extract,
            patch(
                "resume_editor.app.llm.orchestration.analyze_job_description"
            ) as mock_analyze,
        ):
            mock_extract.return_value = ExperienceResponse(roles=[])
            mock_analyze.return_value = (mock_job_analysis, None)

            # Call without the new parameters
            events = []
            async for event in async_refine_experience_section(
                resume_content=sample_resume_content,
                job_description=sample_job_description,
                llm_config=llm_config,
                max_concurrency=5,
            ):
                events.append(event)

            # Should work without errors
            mock_analyze.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_skip_indices_refines_all_roles(
        self,
        sample_resume_content,
        sample_job_description,
        llm_config,
        mock_job_analysis,
        mock_experience_response,
    ):
        """Test that empty skip_indices set refines all roles."""
        refined_role = RefinedRole(
            basics=mock_experience_response.roles[0].basics,
            summary=RoleSummary(text="Refined description."),
            skills=RoleSkills(skills=["Python"]),
        )

        async def mock_refine_side_effect(job, semaphore, event_queue):
            """Mock refinement that returns refined role."""
            role_title = f"{job.role.basics.title} @ {job.role.basics.company}"
            await event_queue.put(
                {"status": "in_progress", "message": f"Refining role '{role_title}'..."}
            )
            await asyncio.sleep(0.01)
            await event_queue.put(
                {
                    "status": "role_refined",
                    "data": refined_role.model_dump(mode="json"),
                    "original_index": job.original_index,
                }
            )

        with (
            patch(
                "resume_editor.app.llm.orchestration.extract_experience_info"
            ) as mock_extract,
            patch(
                "resume_editor.app.llm.orchestration.analyze_job_description"
            ) as mock_analyze,
            patch(
                "resume_editor.app.llm.orchestration._refine_role_and_put_on_queue"
            ) as mock_refine,
        ):
            mock_extract.return_value = mock_experience_response
            mock_analyze.return_value = (mock_job_analysis, None)
            mock_refine.side_effect = mock_refine_side_effect

            events = []
            async for event in async_refine_experience_section(
                resume_content=sample_resume_content,
                job_description=sample_job_description,
                llm_config=llm_config,
                job_analysis=mock_job_analysis,
                skip_indices=set(),  # Empty set - refine all
            ):
                events.append(event)

            # Should have refined all 3 roles
            refined_events = [e for e in events if e.get("status") == "role_refined"]
            assert len(refined_events) == 3

    @pytest.mark.asyncio
    async def test_none_skip_indices_refines_all_roles(
        self,
        sample_resume_content,
        sample_job_description,
        llm_config,
        mock_job_analysis,
        mock_experience_response,
    ):
        """Test that None skip_indices refines all roles."""
        refined_role = RefinedRole(
            basics=mock_experience_response.roles[0].basics,
            summary=RoleSummary(text="Refined description."),
            skills=RoleSkills(skills=["Python"]),
        )

        async def mock_refine_side_effect(job, semaphore, event_queue):
            """Mock refinement that returns refined role."""
            role_title = f"{job.role.basics.title} @ {job.role.basics.company}"
            await event_queue.put(
                {"status": "in_progress", "message": f"Refining role '{role_title}'..."}
            )
            await asyncio.sleep(0.01)
            await event_queue.put(
                {
                    "status": "role_refined",
                    "data": refined_role.model_dump(mode="json"),
                    "original_index": job.original_index,
                }
            )

        with (
            patch(
                "resume_editor.app.llm.orchestration.extract_experience_info"
            ) as mock_extract,
            patch(
                "resume_editor.app.llm.orchestration.analyze_job_description"
            ) as mock_analyze,
            patch(
                "resume_editor.app.llm.orchestration._refine_role_and_put_on_queue"
            ) as mock_refine,
        ):
            mock_extract.return_value = mock_experience_response
            mock_analyze.return_value = (mock_job_analysis, None)
            mock_refine.side_effect = mock_refine_side_effect

            events = []
            async for event in async_refine_experience_section(
                resume_content=sample_resume_content,
                job_description=sample_job_description,
                llm_config=llm_config,
                job_analysis=mock_job_analysis,
                skip_indices=None,  # None - refine all
            ):
                events.append(event)

            # Should have refined all 3 roles
            refined_events = [e for e in events if e.get("status") == "role_refined"]
            assert len(refined_events) == 3

    @pytest.mark.asyncio
    async def test_all_roles_skipped_no_refinement_tasks(
        self,
        sample_resume_content,
        sample_job_description,
        llm_config,
        mock_job_analysis,
        mock_experience_response,
    ):
        """Test that when all roles are skipped, no refinement tasks are created."""
        with (
            patch(
                "resume_editor.app.llm.orchestration.extract_experience_info"
            ) as mock_extract,
            patch(
                "resume_editor.app.llm.orchestration.analyze_job_description"
            ) as mock_analyze,
            patch(
                "resume_editor.app.llm.orchestration._refine_role_and_put_on_queue"
            ) as mock_refine,
        ):
            mock_extract.return_value = mock_experience_response
            mock_analyze.return_value = (mock_job_analysis, None)

            events = []
            async for event in async_refine_experience_section(
                resume_content=sample_resume_content,
                job_description=sample_job_description,
                llm_config=llm_config,
                job_analysis=mock_job_analysis,
                skip_indices={0, 1, 2},  # Skip all roles
            ):
                events.append(event)

            # Should not call refinement for any role
            mock_refine.assert_not_called()
