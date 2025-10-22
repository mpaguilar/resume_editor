import asyncio
from unittest.mock import Mock, patch

import pytest
from cryptography.fernet import InvalidToken

import logging

from openai import AuthenticationError
from starlette.middleware.base import ClientDisconnect

from resume_editor.app.api.routes.route_logic.resume_ai_logic import (
    ProcessExperienceResultParams,
    experience_refinement_sse_generator,
)
from resume_editor.app.api.routes.route_models import ExperienceRefinementParams
from resume_editor.app.llm.models import LLMConfig
from resume_editor.app.models.resume.experience import (
    Role,
    RoleBasics,
    RoleSummary,
)



@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.process_refined_experience_result"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_experience_refinement_sse_generator_happy_path(
    mock_get_llm_config,
    mock_async_refine_experience,
    mock_process_result,
    test_user,
    test_resume,
):
    """Test successful SSE refinement via the SSE generator."""
    expected_intro = "Generated Intro"
    intro_event_present = True

    mock_get_llm_config.return_value = (
        "http://llm.test",
        "test-model",
        "decrypted_key",
    )

    refined_role1 = Role(
        basics=RoleBasics(
            company="Refined Company 1",
            title="Refined Role 1",
            start_date="2024-01-01",
        ),
        summary=RoleSummary(text="Refined Summary 1"),
    )
    refined_role1_data = refined_role1.model_dump(mode="json")
    refined_role2 = Role(
        basics=RoleBasics(
            company="Refined Company 2",
            title="Refined Role 2",
            start_date="2023-01-01",
        ),
        summary=RoleSummary(text="Refined Summary 2"),
    )
    refined_role2_data = refined_role2.model_dump(mode="json")

    async def mock_async_generator():
        yield {"status": "in_progress", "message": "doing stuff"}
        yield {"status": "introduction_generated", "data": "Generated Intro"}
        yield {
            "status": "role_refined",
            "data": refined_role2_data,
            "original_index": 1,
        }
        yield {
            "status": "role_refined",
            "data": refined_role1_data,
            "original_index": 0,
        }

    mock_async_refine_experience.return_value = mock_async_generator()
    mock_process_result.return_value = "<html>final refined html</html>"

    mock_db = Mock()
    params = ExperienceRefinementParams(
        db=mock_db,
        user=test_user,
        resume=test_resume,
        resume_content_to_refine=test_resume.content,
        original_resume_content=test_resume.content,
        job_description="a new job",
    )
    results = [
        item async for item in experience_refinement_sse_generator(params=params)
    ]

    expected_events = 3 + (1 if intro_event_present else 0)
    assert (
        len(results) == expected_events
    ), f"Expected {expected_events} events, got {len(results)}: {results}"
    results_str = "".join(results)
    assert "event: progress" in results_str
    assert "data: <li>doing stuff</li>" in results_str
    assert "event: done" in results_str
    assert "data: <html>final refined html</html>" in results_str
    assert "event: close" in results_str

    if intro_event_present:
        assert "event: introduction_generated" in results_str
        assert 'id="introduction-container"' in results_str
    else:
        assert "event: introduction_generated" not in results_str

    mock_get_llm_config.assert_called_once_with(mock_db, test_user.id)
    expected_llm_config = LLMConfig(
        llm_endpoint="http://llm.test",
        api_key="decrypted_key",
        llm_model_name="test-model",
    )
    mock_async_refine_experience.assert_called_once_with(
        resume_content=test_resume.content,
        job_description="a new job",
        llm_config=expected_llm_config,
    )
    mock_process_result.assert_called_once()
    call_args = mock_process_result.call_args.args
    assert len(call_args) == 1
    params = call_args[0]

    assert isinstance(params, ProcessExperienceResultParams)
    assert params.resume_id == test_resume.id
    assert params.original_resume_content == test_resume.content
    assert params.resume_content_to_refine == test_resume.content
    assert params.refined_roles == {1: refined_role2_data, 0: refined_role1_data}
    assert params.job_description == "a new job"
    assert params.introduction == expected_intro
    assert params.limit_refinement_years is None



@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_experience_refinement_sse_generator_introduction_is_none(
    mock_get_llm_config, mock_async_refine_experience, test_user, test_resume
):
    """Test that an introduction_generated event with None data is handled."""
    mock_get_llm_config.return_value = (None, None, None)

    async def mock_generator():
        yield {"status": "introduction_generated", "data": None}
        yield {"status": "in_progress", "message": "doing stuff"}

    mock_async_refine_experience.return_value = mock_generator()

    params = ExperienceRefinementParams(
        db=Mock(),
        user=test_user,
        resume=test_resume,
        resume_content_to_refine=test_resume.content,
        original_resume_content=test_resume.content,
        job_description="job",
    )
    results = [
        item async for item in experience_refinement_sse_generator(params=params)
    ]

    assert len(results) == 3
    assert "event: progress" in results[0]
    assert "event: error" in results[1]
    assert "Refinement finished, but no roles were found to refine." in results[1]
    assert "event: close" in results[2]


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic._handle_sse_exception")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_experience_refinement_sse_generator_orchestration_error(
    mock_get_llm_config,
    mock_async_refine_experience,
    mock_handle_exception,
    test_user,
    test_resume,
):
    """Test that an error raised by the orchestrator is handled in the SSE stream."""
    mock_get_llm_config.return_value = (None, None, None)
    error = ValueError("Orchestration failed")
    mock_async_refine_experience.side_effect = error
    mock_handle_exception.return_value = "formatted error"

    params = ExperienceRefinementParams(
        db=Mock(),
        user=test_user,
        resume=test_resume,
        resume_content_to_refine=test_resume.content,
        original_resume_content=test_resume.content,
        job_description="job",
        limit_refinement_years=None,
    )
    results = [
        item async for item in experience_refinement_sse_generator(params=params)
    ]

    assert len(results) == 2
    assert results[0] == "formatted error"
    assert "event: close" in results[1]
    mock_handle_exception.assert_called_once_with(error, test_resume.id)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "malformed_event",
    [
        {"status": "processing", "message": "unhandled status"},
        {"status": "role_refined", "data": {"some": "data"}},
        {"status": "role_refined", "original_index": 0},
        {"status": "role_refined", "data": None, "original_index": 0},
        {"status": "role_refined", "data": {"some": "data"}, "original_index": None},
    ],
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_experience_refinement_sse_generator_malformed_events(
    mock_get_llm_config, mock_async_refine_experience, malformed_event, test_user, test_resume
):
    """Test SSE generator handles unknown or malformed events gracefully."""
    mock_get_llm_config.return_value = (None, None, None)

    async def mock_async_generator():
        yield malformed_event

    mock_async_refine_experience.return_value = mock_async_generator()

    params = ExperienceRefinementParams(
        db=Mock(),
        user=test_user,
        resume=test_resume,
        resume_content_to_refine=test_resume.content,
        original_resume_content=test_resume.content,
        job_description="a new job",
    )
    results = [
        item async for item in experience_refinement_sse_generator(params=params)
    ]

    assert len(results) == 2
    assert "event: error" in results[0]
    assert "Refinement finished, but no roles were found to refine." in results[0]
    assert "event: close" in results[1]


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_experience_refinement_sse_generator_empty_generator(
    mock_get_llm_config, mock_async_refine_experience, test_user, test_resume
):
    """Test SSE stream with an empty generator from the LLM service."""
    mock_get_llm_config.return_value = (None, None, None)

    async def mock_empty_async_generator():
        return
        yield

    mock_async_refine_experience.return_value = mock_empty_async_generator()

    params = ExperienceRefinementParams(
        db=Mock(),
        user=test_user,
        resume=test_resume,
        resume_content_to_refine=test_resume.content,
        original_resume_content=test_resume.content,
        job_description="a job",
        limit_refinement_years=None,
    )
    results = [
        item async for item in experience_refinement_sse_generator(params=params)
    ]

    assert len(results) == 2
    assert "event: error" in results[0]
    assert "Refinement finished, but no roles were found to refine." in results[0]
    assert "event: close" in results[1]


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic._handle_sse_exception")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_experience_refinement_sse_generator_invalid_token(
    mock_get_llm_config, mock_handle_exception, test_user, test_resume
):
    """Test SSE generator reports error on API key decryption failure."""
    error = InvalidToken()
    mock_get_llm_config.side_effect = error
    mock_handle_exception.return_value = "formatted error"

    params = ExperienceRefinementParams(
        db=Mock(),
        user=test_user,
        resume=test_resume,
        resume_content_to_refine=test_resume.content,
        original_resume_content=test_resume.content,
        job_description="job",
        limit_refinement_years=None,
    )
    results = [
        item async for item in experience_refinement_sse_generator(params=params)
    ]

    assert len(results) == 2
    assert results[0] == "formatted error"
    assert "event: close" in results[1]
    mock_handle_exception.assert_called_once_with(error, test_resume.id)


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic._handle_sse_exception")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_experience_refinement_sse_generator_auth_error(
    mock_get_llm_config,
    mock_async_refine_experience,
    mock_handle_exception,
    test_user,
    test_resume,
):
    """Test SSE generator reports error on LLM authentication failure."""
    mock_get_llm_config.return_value = (None, None, None)
    error = AuthenticationError(message="auth error", response=Mock(), body=None)
    mock_async_refine_experience.side_effect = error
    mock_handle_exception.return_value = "formatted error"

    params = ExperienceRefinementParams(
        db=Mock(),
        user=test_user,
        resume=test_resume,
        resume_content_to_refine=test_resume.content,
        original_resume_content=test_resume.content,
        job_description="job",
        limit_refinement_years=None,
    )
    results = [
        item async for item in experience_refinement_sse_generator(params=params)
    ]

    assert len(results) == 2
    assert results[0] == "formatted error"
    assert "event: close" in results[1]
    mock_handle_exception.assert_called_once_with(error, test_resume.id)


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic._handle_sse_exception")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_experience_refinement_sse_generator_generic_exception(
    mock_get_llm_config,
    mock_async_refine_experience,
    mock_handle_exception,
    test_user,
    test_resume,
):
    """Test SSE generator reports error on a generic exception."""
    mock_get_llm_config.return_value = (None, None, None)
    error = Exception("Generic test error")
    mock_async_refine_experience.side_effect = error
    mock_handle_exception.return_value = "formatted error"

    params = ExperienceRefinementParams(
        db=Mock(),
        user=test_user,
        resume=test_resume,
        resume_content_to_refine=test_resume.content,
        original_resume_content=test_resume.content,
        job_description="job",
        limit_refinement_years=None,
    )
    results = [
        item async for item in experience_refinement_sse_generator(params=params)
    ]

    assert len(results) == 2
    assert results[0] == "formatted error"
    assert "event: close" in results[1]
    mock_handle_exception.assert_called_once_with(error, test_resume.id)


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.create_sse_close_message",
    return_value="not a close message",
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_generator_breaks_on_timeout_if_task_done(
    mock_get_llm_config,
    mock_async_refine_experience,
    mock_create_close,
    test_user,
    test_resume,
    caplog,
):
    """Test generator breaks on TimeoutError if the background task is done and the queue is empty."""
    mock_get_llm_config.return_value = (None, None, None)

    async def mock_generator():
        yield {"status": "in_progress", "message": "done"}

    mock_async_refine_experience.return_value = mock_generator()

    params = ExperienceRefinementParams(
        db=Mock(),
        user=test_user,
        resume=test_resume,
        resume_content_to_refine=test_resume.content,
        original_resume_content=test_resume.content,
        job_description="job",
    )

    with caplog.at_level(logging.DEBUG):
        results = [
            item async for item in experience_refinement_sse_generator(params=params)
        ]

    assert len(results) == 3
    assert "event: progress" in results[0]
    assert "event: error" in results[1]
    assert "Refinement finished, but no roles were found to refine." in results[1]
    assert "not a close message" in results[2]
    assert "LLM task finished and queue is empty. Closing stream." in caplog.text


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_generator_cancels_task_on_client_disconnect(
    mock_get_llm_config,
    mock_async_refine_experience,
    test_user,
    test_resume,
    caplog,
):
    """Test that the background LLM task is cancelled when the client disconnects from the generator."""
    mock_get_llm_config.return_value = (None, None, None)

    task_was_cancelled = asyncio.Event()

    async def slow_generator():
        """A mock generator that runs slowly and signals when cancelled."""
        try:
            yield {"status": "in_progress", "message": "starting"}
            await asyncio.sleep(10)  # Simulate a long-running process
        except asyncio.CancelledError:
            task_was_cancelled.set()
            raise

    mock_async_refine_experience.return_value = slow_generator()

    params = ExperienceRefinementParams(
        db=Mock(),
        user=test_user,
        resume=test_resume,
        resume_content_to_refine=test_resume.content,
        original_resume_content=test_resume.content,
        job_description="job",
    )

    sse_generator = experience_refinement_sse_generator(params=params)

    with caplog.at_level(logging.WARNING):
        # Start iterating the generator to kick off the background task
        first_item = await sse_generator.__anext__()
        assert "event: progress" in first_item
        assert "starting" in first_item

        # Simulate the client disconnecting by throwing an exception into the generator.
        # The generator will catch GeneratorExit, log a warning, and then finish,
        # which causes athrow to raise StopAsyncIteration.
        with pytest.raises(StopAsyncIteration):
            await sse_generator.athrow(GeneratorExit)

    assert f"SSE stream closed for resume {test_resume.id}." in caplog.text

    # Check that the underlying llm_task was cancelled
    try:
        await asyncio.wait_for(task_was_cancelled.wait(), timeout=1.0)
    except asyncio.TimeoutError:
        pytest.fail("The llm_task was not cancelled.")


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_generator_continues_on_timeout_if_task_not_done(
    mock_get_llm_config,
    mock_async_refine_experience,
    test_user,
    test_resume,
    caplog,
):
    """Test that the generator continues on TimeoutError if the background task is not yet done."""
    mock_get_llm_config.return_value = (None, None, None)

    async def slow_generator():
        """A generator that waits before yielding a message."""
        await asyncio.sleep(1.2)  # longer than the timeout
        yield {"status": "in_progress", "message": "I was slow"}

    mock_async_refine_experience.return_value = slow_generator()

    params = ExperienceRefinementParams(
        db=Mock(),
        user=test_user,
        resume=test_resume,
        resume_content_to_refine=test_resume.content,
        original_resume_content=test_resume.content,
        job_description="job",
    )

    with caplog.at_level(logging.DEBUG):
        # This will iterate through the generator. It should experience at least one timeout
        # while waiting for the slow generator.
        results = [
            item async for item in experience_refinement_sse_generator(params=params)
        ]

    # The loop should have timed out at least once, but continued because main_task wasn't done.
    # We should have one progress message, one error (no roles refined), and one close event.
    assert len(results) == 3
    results_str = "".join(results)
    assert "event: progress" in results_str
    assert "I was slow" in results_str
    assert "event: error" in results_str
    assert "Refinement finished, but no roles were found to refine" in results_str
    assert "event: close" in results_str
    # Check that we did not prematurely log the "task finished" message
    assert "LLM task finished and queue is empty" not in caplog.text
