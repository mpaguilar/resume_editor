import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import json

# get a reference to the real function before any patches
_real_asyncio_create_task = asyncio.create_task

from resume_editor.app.api.routes.route_models import ExperienceResponse
from resume_editor.app.llm.orchestration import async_refine_experience_section
from resume_editor.app.llm.models import JobAnalysis, LLMConfig, RefinedRole
from resume_editor.app.models.resume.experience import (
    Role,
    RoleBasics,
    RoleResponsibilities,
    RoleSkills,
    RoleSummary,
)

_real_asyncio_sleep = asyncio.sleep


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


def create_mock_refined_role() -> RefinedRole:
    """Helper to create a mock RefinedRole object for testing."""
    return RefinedRole(
        basics=RoleBasics(
            company="Old Company",
            title="Old Title",
            start_date=datetime(2020, 1, 1),
        ),
        summary=RoleSummary(text="Refined summary."),
        responsibilities=RoleResponsibilities(text="* Do refined things."),
        skills=RoleSkills(skills=["Refined Skill"]),
    )


@pytest.mark.asyncio
@patch("resume_editor.app.llm.orchestration.refine_role", new_callable=AsyncMock)
@patch(
    "resume_editor.app.llm.orchestration.analyze_job_description",
    new_callable=AsyncMock,
)
@patch("resume_editor.app.llm.orchestration.extract_experience_info")
async def test_async_refine_experience_section_execution(
    mock_extract_experience,
    mock_analyze_job,
    mock_refine_role,
):
    """
    Test the full execution flow of async_refine_experience_section with new queuing logic.
    """
    # Arrange
    resume_content = "some resume"
    job_description = "some job"
    llm_endpoint = "http://fake.llm"
    api_key = "key"
    llm_model_name = "model"
    max_concurrency = 3

    # Mocks for parsing
    mock_role1 = create_mock_role()
    mock_role1.basics.title = "Engineer I"
    mock_role1.basics.company = "Company A"
    mock_role2 = create_mock_role()
    mock_role2.basics.title = "Engineer II"
    mock_role2.basics.company = "Company B"
    mock_roles = [mock_role1, mock_role2]
    mock_experience_info = ExperienceResponse(roles=mock_roles, projects=[])
    mock_extract_experience.return_value = mock_experience_info
    mock_job_analysis = create_mock_job_analysis()
    mock_analyze_job.return_value = (mock_job_analysis, None)

    # Mock for refinement results
    mock_refined_role1 = create_mock_refined_role()
    mock_refined_role1.basics.title = "Refined Engineer I"
    mock_refined_role2 = create_mock_refined_role()
    mock_refined_role2.basics.title = "Refined Engineer II"

    async def refine_role_side_effect(role, **kwargs):
        if role.basics.title == "Engineer I":
            return mock_refined_role1
        return mock_refined_role2

    mock_refine_role.side_effect = refine_role_side_effect

    # Act
    events = []
    llm_config = LLMConfig(
        llm_endpoint=llm_endpoint, api_key=api_key, llm_model_name=llm_model_name
    )
    async for event in async_refine_experience_section(
        resume_content=resume_content,
        job_description=job_description,
        llm_config=llm_config,
        max_concurrency=max_concurrency,
    ):
        events.append(event)

    # Assert
    # 1. Initial setup calls
    mock_extract_experience.assert_called_once_with(resume_content)
    mock_analyze_job.assert_awaited_once_with(
        job_description=job_description,
        llm_config=llm_config,
        resume_content_for_context=resume_content,
    )
    assert mock_refine_role.call_count == len(mock_roles)

    # 4. Yielded events
    # We expect 2 initial progress, 2 refining progress, and 2 result events
    assert len(events) == 6

    initial_events = [
        e for e in events if e.get("message") in ("Parsing resume...", "Analyzing job description...")
    ]
    refining_events = [e for e in events if "Refining role" in e.get("message", "")]
    result_events = [e for e in events if e.get("status") == "role_refined"]

    assert initial_events == [
        {"status": "in_progress", "message": "Parsing resume..."},
        {"status": "in_progress", "message": "Analyzing job description..."},
    ]
    
    # Check for presence of refining messages, order is not guaranteed.
    assert len(refining_events) == 2
    refining_messages = {e["message"] for e in refining_events}
    assert "Refining role 'Engineer I @ Company A'..." in refining_messages
    assert "Refining role 'Engineer II @ Company B'..." in refining_messages

    # Order of results is not guaranteed. Extract index and data, then sort by index.
    received_results = sorted(
        [(e["original_index"], json.dumps(e["data"], sort_keys=True)) for e in result_events]
    )
    expected_refined_data = [
        mock_refined_role1.model_dump(mode="json"),
        mock_refined_role2.model_dump(mode="json"),
    ]
    expected_results = [
        (i, json.dumps(data, sort_keys=True)) for i, data in enumerate(expected_refined_data)
    ]
    assert received_results == expected_results


@pytest.mark.asyncio
@patch("resume_editor.app.llm.orchestration.refine_role", new_callable=AsyncMock)
@patch(
    "resume_editor.app.llm.orchestration.analyze_job_description",
    new_callable=AsyncMock,
)
@patch("resume_editor.app.llm.orchestration.extract_experience_info")
async def test_async_refine_experience_section_with_introduction(
    mock_extract_experience,
    mock_analyze_job,
    mock_refine_role,
):
    """
    Test async_refine_experience_section with introduction generation.
    """
    # Arrange
    resume_content = "some resume"
    job_description = "some job"

    mock_role = create_mock_role()
    mock_extract_experience.return_value = ExperienceResponse(
        roles=[mock_role], projects=[]
    )

    mock_job_analysis = create_mock_job_analysis()
    # Mock analyze_job_description to return an introduction
    mock_analyze_job.return_value = (mock_job_analysis, "This is the intro.")

    mock_refine_role.return_value = create_mock_refined_role()

    # Act
    events = []
    async for event in async_refine_experience_section(
        resume_content=resume_content,
        job_description=job_description,
        llm_config=LLMConfig(),
    ):
        events.append(event)

    # Assert
    # Check that analyze_job_description was called correctly
    mock_analyze_job.assert_awaited_once()
    call_kwargs = mock_analyze_job.call_args.kwargs
    assert call_kwargs["resume_content_for_context"] == resume_content

    # Check yielded events
    assert len(events) == 5
    assert events[0] == {"status": "in_progress", "message": "Parsing resume..."}
    assert events[1] == {
        "status": "in_progress",
        "message": "Analyzing job description...",
    }
    assert events[2] == {"status": "introduction_generated", "data": "This is the intro."}
    # Then progress for role, then result for role
    assert "Refining role" in events[3]["message"]
    assert events[4]["status"] == "role_refined"


@pytest.mark.asyncio
@patch("resume_editor.app.llm.orchestration.analyze_job_description", new_callable=AsyncMock)
@patch("resume_editor.app.llm.orchestration.extract_experience_info")
async def test_async_refine_experience_section_no_roles(
    mock_extract_experience: MagicMock,
    mock_analyze_job: AsyncMock,
):
    """
    Test that async_refine_experience_section handles cases with no roles gracefully.
    """
    # Arrange
    resume_content = "resume with no roles"
    job_description = "some job"
    llm_config = LLMConfig()

    mock_extract_experience.return_value = ExperienceResponse(roles=[], projects=[])
    # Ensure no introduction is returned to match the step's assertion criteria
    mock_analyze_job.return_value = (create_mock_job_analysis(), None)

    # Act
    events = []
    async for event in async_refine_experience_section(
        resume_content=resume_content,
        job_description=job_description,
        llm_config=llm_config,
    ):
        events.append(event)

    # Assert
    mock_extract_experience.assert_called_once_with(resume_content)
    mock_analyze_job.assert_awaited_once_with(
        job_description=job_description,
        llm_config=llm_config,
        resume_content_for_context=resume_content,
    )

    assert len(events) == 2
    assert events == [
        {"status": "in_progress", "message": "Parsing resume..."},
        {"status": "in_progress", "message": "Analyzing job description..."},
    ]


@pytest.mark.asyncio
@patch("resume_editor.app.llm.orchestration.asyncio.create_task")
@patch(
    "resume_editor.app.llm.orchestration._refine_role_and_put_on_queue",
    new_callable=AsyncMock,
)
@patch(
    "resume_editor.app.llm.orchestration.analyze_job_description",
    new_callable=AsyncMock,
)
@patch("resume_editor.app.llm.orchestration.extract_experience_info")
async def test_async_refine_experience_schedules_tasks_only_once(
    mock_extract_experience: MagicMock,
    mock_analyze_job: AsyncMock,
    mock_refine_and_put: AsyncMock,
    mock_create_task: MagicMock,
):
    """
    Test that async_refine_experience_section schedules tasks only once per role.
    This test is designed to fail if the task rescheduling bug is present.
    """
    # Arrange
    # Because we are mocking create_task to check its call count, we need to
    # provide a side effect that actually runs the coroutine to avoid
    # deadlocking the test. We use the real create_task for this.
    def create_task_side_effect(coro, *, name=None):
        return _real_asyncio_create_task(coro)

    mock_create_task.side_effect = create_task_side_effect

    # Mock extract_experience to return two roles
    mock_role1 = create_mock_role()
    mock_role2 = create_mock_role()
    mock_experience_info = ExperienceResponse(roles=[mock_role1, mock_role2], projects=[])
    mock_extract_experience.return_value = mock_experience_info

    # Mock analyze_job_description to return analysis and no intro
    mock_job_analysis = create_mock_job_analysis()
    mock_analyze_job.return_value = (mock_job_analysis, None)

    # Mock _refine_role_and_put_on_queue to simulate work by putting two
    # events on the queue for the main loop to consume.
    async def refine_and_put_side_effect(*args, **kwargs):
        event_queue = kwargs["event_queue"]
        await event_queue.put({"status": "in_progress", "message": "Refining..."})
        await event_queue.put({"status": "role_refined", "data": {}})

    mock_refine_and_put.side_effect = refine_and_put_side_effect

    # Act: Consume the async generator to trigger the logic
    events = []
    async for event in async_refine_experience_section(
        resume_content="resume",
        job_description="job",
        llm_config=LLMConfig(),
    ):
        events.append(event)

    # Assert
    # The main assertion: ensure create_task was called exactly once per role.
    # It should be called 2 times. With the bug, it is called more.
    assert mock_create_task.call_count == 2


@pytest.mark.asyncio
@patch("resume_editor.app.llm.orchestration.refine_role", new_callable=AsyncMock)
@patch(
    "resume_editor.app.llm.orchestration.analyze_job_description",
    new_callable=AsyncMock,
)
@patch("resume_editor.app.llm.orchestration.extract_experience_info")
async def test_async_refine_experience_section_concurrency(
    mock_extract_experience,
    mock_analyze_job,
    mock_refine_role,
):
    """
    Test that async_refine_experience_section respects concurrency limits.
    This test does NOT mock asyncio.Semaphore to allow for real concurrency checks.
    """
    # Arrange
    resume_content = "some resume"
    job_description = "some job"
    max_concurrency = 2
    num_roles = 5

    # Mocks for parsing
    mock_roles = [create_mock_role() for i in range(num_roles)]
    mock_experience_info = ExperienceResponse(roles=mock_roles, projects=[])
    mock_extract_experience.return_value = mock_experience_info
    mock_analyze_job.return_value = (create_mock_job_analysis(), None)

    # Concurrency tracking setup
    active_tasks = 0
    max_observed_concurrency = 0
    lock = asyncio.Lock()

    async def mock_refinement_side_effect(*args, **kwargs):
        nonlocal active_tasks, max_observed_concurrency
        async with lock:
            active_tasks += 1
            max_observed_concurrency = max(max_observed_concurrency, active_tasks)

        await _real_asyncio_sleep(0.02)  # Use a small real sleep to yield control

        async with lock:
            active_tasks -= 1

        return create_mock_refined_role()

    mock_refine_role.side_effect = mock_refinement_side_effect

    # Act
    events = []
    async for event in async_refine_experience_section(
        resume_content=resume_content,
        job_description=job_description,
        llm_config=LLMConfig(),
        max_concurrency=max_concurrency,
    ):
        events.append(event)

    # Assert
    # 1. Concurrency limit was respected
    assert (
        max_observed_concurrency <= max_concurrency
    ), f"Expected concurrency <= {max_concurrency}, but observed {max_observed_concurrency}"

    # 2. All roles were processed
    assert mock_refine_role.call_count == num_roles
    result_events = [e for e in events if e.get("status") == "role_refined"]
    assert len(result_events) == num_roles


@pytest.mark.asyncio
@patch("resume_editor.app.llm.orchestration.refine_role", new_callable=AsyncMock)
@patch(
    "resume_editor.app.llm.orchestration.analyze_job_description",
    new_callable=AsyncMock,
)
@patch("resume_editor.app.llm.orchestration.extract_experience_info")
async def test_async_refine_experience_section_role_refinement_fails(
    mock_extract_experience,
    mock_analyze_job,
    mock_refine_role,
):
    """Test that the concurrent orchestrator raises an error if a role refinement task fails."""
    # Arrange
    mock_extract_experience.return_value = ExperienceResponse(
        roles=[create_mock_role()], projects=[]
    )
    mock_analyze_job.return_value = (create_mock_job_analysis(), None)

    async def mock_refine_side_effect(*args, **kwargs):
        raise ValueError("Role task failed")

    mock_refine_role.side_effect = mock_refine_side_effect

    # Act & Assert
    events = []
    with pytest.raises(ValueError, match="Role task failed"):
        async for event in async_refine_experience_section(
            resume_content="resume",
            job_description="job",
            llm_config=LLMConfig(),
        ):
            events.append(event)

    # Assert
    assert mock_refine_role.call_count == 1
    # Check that in_progress message was yielded before the exception
    assert events == [
        {"status": "in_progress", "message": "Parsing resume..."},
        {"status": "in_progress", "message": "Analyzing job description..."},
        {
            "status": "in_progress",
            "message": "Refining role 'Old Title @ Old Company'...",
        },
    ]


@pytest.mark.asyncio
@patch(
    "resume_editor.app.llm.orchestration.analyze_job_description",
    new_callable=AsyncMock,
)
@patch("resume_editor.app.llm.orchestration.extract_experience_info")
async def test_async_refine_experience_section_job_analysis_fails(
    mock_extract_experience, mock_analyze_job
):
    """Test that the concurrent orchestrator raises an error if job analysis fails."""
    # Arrange
    mock_extract_experience.return_value = ExperienceResponse(
        roles=[create_mock_role()], projects=[]
    )
    mock_analyze_job.side_effect = ValueError("Job analysis failed")

    # Act & Assert
    events = []
    with pytest.raises(ValueError, match="Job analysis failed"):
        async for event in async_refine_experience_section(
            resume_content="resume",
            job_description="job",
            llm_config=LLMConfig(),
        ):
            events.append(event)

    assert events == [
        {"status": "in_progress", "message": "Parsing resume..."},
        {"status": "in_progress", "message": "Analyzing job description..."},
    ]
