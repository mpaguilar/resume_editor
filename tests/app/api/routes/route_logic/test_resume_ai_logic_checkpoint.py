"""Tests for resume_ai_logic checkpoint support."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from resume_editor.app.api.routes.route_logic.resume_ai_logic import (
    _build_skip_indices_from_log,
    _create_refined_role_record,
    _stream_llm_events,
    experience_refinement_sse_generator,
)
from resume_editor.app.api.routes.route_models import ExperienceRefinementParams
from resume_editor.app.llm.models import (
    JobAnalysis,
    RefinedRoleRecord,
    RunningLog,
)


class TestBuildSkipIndicesFromLog:
    """Tests for _build_skip_indices_from_log function."""

    def test_returns_empty_set_when_no_log(self):
        """Test that an empty set is returned when no log is provided."""
        result = _build_skip_indices_from_log(None)
        assert result == set()

    def test_returns_empty_set_when_no_refined_roles(self):
        """Test that an empty set is returned when log has no refined roles."""
        now = datetime.now()
        log = RunningLog(
            resume_id=1,
            user_id=1,
            job_description="test",
            created_at=now,
            updated_at=now,
            refined_roles=[],
        )
        result = _build_skip_indices_from_log(log)
        assert result == set()

    def test_extracts_indices_from_refined_roles(self):
        """Test that original indices are correctly extracted from refined roles."""
        now = datetime.now()
        log = RunningLog(
            resume_id=1,
            user_id=1,
            job_description="test",
            created_at=now,
            updated_at=now,
            refined_roles=[
                RefinedRoleRecord(
                    original_index=0,
                    company="Company A",
                    title="Role A",
                    refined_description="Desc A",
                    timestamp=now,
                    start_date=now,
                ),
                RefinedRoleRecord(
                    original_index=2,
                    company="Company B",
                    title="Role B",
                    refined_description="Desc B",
                    timestamp=now,
                    start_date=now,
                ),
            ],
        )
        result = _build_skip_indices_from_log(log)
        assert result == {0, 2}


class TestCreateRefinedRoleRecord:
    """Tests for _create_refined_role_record function."""

    def test_creates_record_from_complete_role_data(self):
        """Test creating a RefinedRoleRecord from complete role data."""
        now = datetime.now()
        role_data = {
            "basics": {
                "company": "Test Corp",
                "title": "Engineer",
                "start_date": now.isoformat(),
                "end_date": None,
            },
            "summary": {"text": "A great role"},
            "responsibilities": {"items": ["Task 1", "Task 2"]},
            "skills": {"items": ["Python", "FastAPI"]},
        }

        result = _create_refined_role_record(0, role_data)

        assert isinstance(result, RefinedRoleRecord)
        assert result.original_index == 0
        assert result.company == "Test Corp"
        assert result.title == "Engineer"
        assert result.refined_description == "A great role"
        assert result.relevant_skills == ["Python", "FastAPI"]
        assert result.start_date == now
        assert result.end_date is None

    def test_creates_record_with_minimal_role_data(self):
        """Test creating a record when role data has minimal fields."""
        now = datetime.now()
        role_data = {
            "basics": {
                "company": "Minimal Corp",
                "title": "Developer",
                "start_date": now.isoformat(),
            },
        }

        result = _create_refined_role_record(1, role_data)

        assert result.original_index == 1
        assert result.company == "Minimal Corp"
        assert result.title == "Developer"
        assert result.refined_description == ""
        assert result.relevant_skills == []

    def test_handles_invalid_start_date_format(self):
        """Test that invalid start_date format uses default datetime."""
        from datetime import datetime

        before_test = datetime.now()
        role_data = {
            "basics": {
                "company": "Test Corp",
                "title": "Engineer",
                "start_date": "invalid-date-format",
                "end_date": None,
            },
            "summary": {"text": "Test role"},
        }

        result = _create_refined_role_record(0, role_data)

        assert isinstance(result, RefinedRoleRecord)
        assert result.company == "Test Corp"
        # Invalid date should use default (current datetime)
        assert result.start_date is not None
        assert result.start_date >= before_test
        assert result.end_date is None

    def test_handles_invalid_end_date_format(self):
        """Test that invalid end_date format is handled gracefully."""
        now = datetime.now()
        role_data = {
            "basics": {
                "company": "Test Corp",
                "title": "Engineer",
                "start_date": now.isoformat(),
                "end_date": "not-a-valid-date",
            },
            "summary": {"text": "Test role"},
        }

        result = _create_refined_role_record(0, role_data)

        assert isinstance(result, RefinedRoleRecord)
        # Start date should be valid, end date should be None
        assert result.start_date == now
        assert result.end_date is None


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_stream_llm_events_with_running_log(
    mock_get_llm_config,
    mock_async_refine,
):
    """Test that _stream_llm_events uses running_log for job_analysis and skip_indices."""
    mock_get_llm_config.return_value = (None, None, None)

    job_analysis = JobAnalysis(
        key_skills=["Python"],
        primary_duties=["Development"],
        themes=["Fast-paced"],
    )

    async def mock_generator():
        yield {"status": "in_progress", "message": "Processing..."}

    mock_async_refine.return_value = mock_generator()

    mock_params = Mock()
    mock_params.resume_content_to_refine = "# Experience\n## Role"
    mock_params.job_description = "Job desc"
    mock_params.resume.id = 1
    mock_params.user.id = 1

    mock_running_log = Mock()
    mock_running_log.job_analysis = job_analysis
    mock_running_log.refined_roles = []

    llm_config = Mock()
    refined_roles = {}

    # Collect results
    results = []
    async for msg in _stream_llm_events(
        params=mock_params,
        llm_config=llm_config,
        refined_roles=refined_roles,
        running_log=mock_running_log,
    ):
        results.append(msg)

    # Verify that async_refine_experience_section was called with job_analysis and skip_indices
    mock_async_refine.assert_called_once()
    call_kwargs = mock_async_refine.call_args.kwargs
    assert call_kwargs.get("job_analysis") == job_analysis
    assert call_kwargs.get("skip_indices") == set()


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.running_log_manager")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_stream_llm_events_adds_to_running_log(
    mock_get_llm_config,
    mock_async_refine,
    mock_log_manager,
):
    """Test that refined roles are added to the running log."""
    mock_get_llm_config.return_value = (None, None, None)

    now = datetime.now()
    role_data = {
        "basics": {
            "company": "Test Corp",
            "title": "Engineer",
            "start_date": now.isoformat(),
            "end_date": None,
        },
        "summary": {"text": "Great work"},
        "skills": {"items": ["Python", "FastAPI"]},
    }

    async def mock_generator():
        yield {
            "status": "role_refined",
            "data": role_data,
            "original_index": 0,
        }

    mock_async_refine.return_value = mock_generator()

    mock_params = Mock()
    mock_params.resume_content_to_refine = "# Experience"
    mock_params.job_description = "Job"
    mock_params.resume.id = 1
    mock_params.user.id = 1

    mock_running_log = Mock()
    mock_running_log.job_analysis = None
    mock_running_log.refined_roles = []

    llm_config = Mock()
    refined_roles = {}

    async for _ in _stream_llm_events(
        params=mock_params,
        llm_config=llm_config,
        refined_roles=refined_roles,
        running_log=mock_running_log,
    ):
        pass

    # Verify add_refined_role was called
    mock_log_manager.add_refined_role.assert_called_once()
    call_args = mock_log_manager.add_refined_role.call_args
    # Check keyword arguments
    assert call_args.kwargs.get("resume_id") == 1
    assert call_args.kwargs.get("user_id") == 1
    assert isinstance(call_args.kwargs.get("role_record"), RefinedRoleRecord)


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic._stream_llm_events")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic._stream_final_events")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.running_log_manager")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_experience_refinement_sse_generator_yields_resuming_message(
    mock_get_llm_config,
    mock_log_manager,
    mock_stream_final,
    mock_stream_llm,
):
    """Test that SSE generator yields 'Resuming' message when running_log has refined_roles."""
    mock_get_llm_config.return_value = (None, None, None)

    # Create a running log with existing refined roles (indicating a resume)
    now = datetime.now()
    running_log = RunningLog(
        resume_id=1,
        user_id=1,
        job_description="test job",
        created_at=now,
        updated_at=now,
        refined_roles=[
            RefinedRoleRecord(
                original_index=0,
                company="Prev Corp",
                title="Previous Role",
                refined_description="Previous desc",
                timestamp=now,
                start_date=now,
            ),
        ],
    )

    mock_log_manager.get_log.return_value = running_log

    # Mock the stream functions
    async def mock_llm_stream():
        yield "progress: refining role..."

    async def mock_final_stream():
        yield "done: final html"

    mock_stream_llm.return_value = mock_llm_stream()
    mock_stream_final.return_value = mock_final_stream()

    params = ExperienceRefinementParams(
        db=Mock(),
        user=Mock(id=1),
        resume=Mock(id=1),
        resume_content_to_refine="# Experience",
        original_resume_content="# Experience",
        job_description="test job",
        limit_refinement_years=None,
    )

    results = []
    async for msg in experience_refinement_sse_generator(params=params):
        results.append(msg)

    results_str = "".join(results)
    assert "Resuming from previous attempt" in results_str


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic._stream_llm_events")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic._stream_final_events")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.running_log_manager")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_experience_refinement_sse_generator_no_resuming_for_fresh_start(
    mock_get_llm_config,
    mock_log_manager,
    mock_stream_final,
    mock_stream_llm,
):
    """Test that SSE generator does not yield 'Resuming' for fresh starts."""
    mock_get_llm_config.return_value = (None, None, None)

    # Create a running log with no refined roles (fresh start)
    now = datetime.now()
    running_log = RunningLog(
        resume_id=1,
        user_id=1,
        job_description="test job",
        created_at=now,
        updated_at=now,
        refined_roles=[],
    )

    mock_log_manager.get_log.return_value = running_log

    # Mock the stream functions
    async def mock_llm_stream():
        yield "progress: parsing..."

    async def mock_final_stream():
        yield "done: final html"

    mock_stream_llm.return_value = mock_llm_stream()
    mock_stream_final.return_value = mock_final_stream()

    params = ExperienceRefinementParams(
        db=Mock(),
        user=Mock(id=1),
        resume=Mock(id=1),
        resume_content_to_refine="# Experience",
        original_resume_content="# Experience",
        job_description="test job",
        limit_refinement_years=None,
    )

    results = []
    async for msg in experience_refinement_sse_generator(params=params):
        results.append(msg)

    results_str = "".join(results)
    assert "Resuming from previous attempt" not in results_str


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic._stream_llm_events")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic._stream_final_events")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.running_log_manager")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_experience_refinement_sse_generator_no_resuming_when_no_log(
    mock_get_llm_config,
    mock_log_manager,
    mock_stream_final,
    mock_stream_llm,
):
    """Test that SSE generator does not yield 'Resuming' when no running log exists."""
    mock_get_llm_config.return_value = (None, None, None)

    mock_log_manager.get_log.return_value = None

    # Mock the stream functions
    async def mock_llm_stream():
        yield "progress: parsing..."

    async def mock_final_stream():
        yield "done: final html"

    mock_stream_llm.return_value = mock_llm_stream()
    mock_stream_final.return_value = mock_final_stream()

    params = ExperienceRefinementParams(
        db=Mock(),
        user=Mock(id=1),
        resume=Mock(id=1),
        resume_content_to_refine="# Experience",
        original_resume_content="# Experience",
        job_description="test job",
        limit_refinement_years=None,
    )

    results = []
    async for msg in experience_refinement_sse_generator(params=params):
        results.append(msg)

    results_str = "".join(results)
    assert "Resuming from previous attempt" not in results_str


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.running_log_manager")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_experience_refinement_sse_generator_passes_running_log_to_stream(
    mock_get_llm_config,
    mock_log_manager,
):
    """Test that the running_log is passed to _stream_llm_events."""
    mock_get_llm_config.return_value = (None, None, None)

    now = datetime.now()
    running_log = RunningLog(
        resume_id=1,
        user_id=1,
        job_description="test job",
        created_at=now,
        updated_at=now,
        job_analysis=JobAnalysis(
            key_skills=["Python"],
            primary_duties=["Coding"],
            themes=["Agile"],
        ),
    )

    mock_log_manager.get_log.return_value = running_log

    with (
        patch(
            "resume_editor.app.api.routes.route_logic.resume_ai_logic._stream_llm_events"
        ) as mock_stream,
        patch(
            "resume_editor.app.api.routes.route_logic.resume_ai_logic._stream_final_events"
        ) as mock_final,
    ):

        async def mock_llm_stream(*args, **kwargs):
            yield "progress"

        async def mock_final_stream(*args, **kwargs):
            yield "done"

        mock_stream.return_value = mock_llm_stream()
        mock_final.return_value = mock_final_stream()

        params = ExperienceRefinementParams(
            db=Mock(),
            user=Mock(id=1),
            resume=Mock(id=1),
            resume_content_to_refine="# Experience",
            original_resume_content="# Experience",
            job_description="test job",
            limit_refinement_years=None,
        )

        async for _ in experience_refinement_sse_generator(params=params):
            pass

        # Verify _stream_llm_events was called with running_log
        mock_stream.assert_called_once()
        call_kwargs = mock_stream.call_args.kwargs
        assert call_kwargs.get("running_log") == running_log


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.running_log_manager")
async def test_stream_llm_events_logs_skip_indices(
    mock_log_manager,
    mock_async_refine,
):
    """Test that skip indices are logged when resuming from running log."""
    from datetime import datetime

    now = datetime.now()
    running_log = RunningLog(
        resume_id=1,
        user_id=1,
        job_description="test job",
        created_at=now,
        updated_at=now,
        refined_roles=[
            RefinedRoleRecord(
                original_index=0,
                company="Company A",
                title="Role A",
                refined_description="Desc A",
                timestamp=now,
                start_date=now,
            ),
            RefinedRoleRecord(
                original_index=2,
                company="Company B",
                title="Role B",
                refined_description="Desc B",
                timestamp=now,
                start_date=now,
            ),
        ],
    )

    async def mock_generator():
        yield {"status": "in_progress", "message": "Processing..."}

    mock_async_refine.return_value = mock_generator()

    mock_params = Mock()
    mock_params.resume_content_to_refine = "# Experience"
    mock_params.job_description = "Job"
    mock_params.resume.id = 1
    mock_params.user.id = 1

    llm_config = Mock()
    refined_roles = {}

    # Collect results
    results = []
    async for msg in _stream_llm_events(
        params=mock_params,
        llm_config=llm_config,
        refined_roles=refined_roles,
        running_log=running_log,
    ):
        results.append(msg)

    # Verify that async_refine_experience_section was called with skip_indices
    mock_async_refine.assert_called_once()
    call_kwargs = mock_async_refine.call_args.kwargs
    assert call_kwargs.get("skip_indices") == {0, 2}


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.running_log_manager")
async def test_stream_llm_events_stores_job_analysis(
    mock_log_manager,
    mock_async_refine,
):
    """Test that _stream_llm_events stores job_analysis from event in running log."""
    # Arrange
    job_analysis_data = {
        "key_skills": ["Python", "AWS"],
        "primary_duties": ["Develop backend services"],
        "themes": ["fast-paced"],
        "inferred_themes": ["Backend Development"],
    }

    async def mock_generator():
        yield {
            "status": "job_analysis_complete",
            "message": "Job analysis complete.",
            "job_analysis": job_analysis_data,
        }
        yield {
            "status": "role_refined",
            "data": {
                "basics": {"company": "TestCo", "title": "Dev"},
                "summary": {"text": "Summary"},
                "skills": {"items": ["Python"]},
            },
            "original_index": 0,
        }

    mock_async_refine.return_value = mock_generator()
    mock_log_manager.update_job_analysis = Mock()
    mock_log_manager.add_refined_role = Mock()

    mock_params = Mock()
    mock_params.resume_content_to_refine = "# Experience"
    mock_params.job_description = "Job"
    mock_params.resume.id = 1
    mock_params.user.id = 1

    mock_running_log = Mock()
    mock_running_log.job_analysis = None
    mock_running_log.refined_roles = []

    llm_config = Mock()
    refined_roles = {}

    # Act
    async for _ in _stream_llm_events(
        params=mock_params,
        llm_config=llm_config,
        refined_roles=refined_roles,
        running_log=mock_running_log,
    ):
        pass

    # Assert
    mock_log_manager.update_job_analysis.assert_called_once()
    call_args = mock_log_manager.update_job_analysis.call_args
    assert call_args.kwargs.get("resume_id") == 1
    assert call_args.kwargs.get("user_id") == 1
    # Verify a JobAnalysis object was passed
    from resume_editor.app.llm.models import JobAnalysis

    assert isinstance(call_args.kwargs.get("job_analysis"), JobAnalysis)


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.running_log_manager")
async def test_stream_llm_events_handles_job_analysis_storage_exception(
    mock_log_manager,
    mock_async_refine,
):
    """Test that exceptions when storing job_analysis are handled gracefully."""
    job_analysis_data = {
        "key_skills": ["Python"],
        "primary_duties": ["Coding"],
        "themes": ["agile"],
        "inferred_themes": [],
    }

    async def mock_generator():
        yield {
            "status": "job_analysis_complete",
            "message": "Job analysis complete.",
            "job_analysis": job_analysis_data,
        }

    mock_async_refine.return_value = mock_generator()
    # Simulate exception when storing job analysis
    mock_log_manager.update_job_analysis.side_effect = Exception("Storage failed")

    mock_params = Mock()
    mock_params.resume_content_to_refine = "# Experience"
    mock_params.job_description = "Job"
    mock_params.resume.id = 1
    mock_params.user.id = 1

    mock_running_log = Mock()
    mock_running_log.job_analysis = None
    mock_running_log.refined_roles = []

    llm_config = Mock()
    refined_roles = {}

    # Should not raise exception - handled gracefully
    messages = []
    async for msg in _stream_llm_events(
        params=mock_params,
        llm_config=llm_config,
        refined_roles=refined_roles,
        running_log=mock_running_log,
    ):
        messages.append(msg)

    # Verify update_job_analysis was called (even though it failed)
    mock_log_manager.update_job_analysis.assert_called_once()
    # Stream should continue despite the exception
    assert len(messages) > 0


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.running_log_manager")
async def test_stream_llm_events_handles_role_record_creation_exception(
    mock_log_manager,
    mock_async_refine,
):
    """Test that exceptions when creating refined role record are handled gracefully."""

    async def mock_generator():
        yield {
            "status": "role_refined",
            "data": {
                "basics": {"company": "TestCo", "title": "Dev"},
                "summary": {"text": "Summary"},
                "skills": {"items": ["Python"]},
            },
            "original_index": 0,
        }

    mock_async_refine.return_value = mock_generator()
    # Simulate exception when adding refined role
    mock_log_manager.add_refined_role.side_effect = Exception("Database error")

    mock_params = Mock()
    mock_params.resume_content_to_refine = "# Experience"
    mock_params.job_description = "Job"
    mock_params.resume.id = 1
    mock_params.user.id = 1

    mock_running_log = Mock()
    mock_running_log.job_analysis = None
    mock_running_log.refined_roles = []

    llm_config = Mock()
    refined_roles = {}

    # Should not raise exception - handled gracefully
    messages = []
    async for msg in _stream_llm_events(
        params=mock_params,
        llm_config=llm_config,
        refined_roles=refined_roles,
        running_log=mock_running_log,
    ):
        messages.append(msg)

    # Verify add_refined_role was called (even though it failed)
    mock_log_manager.add_refined_role.assert_called_once()
    # Stream continues despite the exception - role_refined event processing
    # may fail validation but exception is caught and logged
