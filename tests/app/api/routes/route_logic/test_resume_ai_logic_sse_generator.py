import asyncio
from unittest.mock import Mock, patch

import pytest
from cryptography.fernet import InvalidToken

import logging

from openai import AuthenticationError
from starlette.middleware.base import ClientDisconnect

from resume_editor.app.api.routes.route_logic.resume_ai_logic import (
    ProcessExperienceResultParams,
    _process_sse_event,
    _process_refined_role_event,
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
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.generate_introduction_from_resume"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.process_refined_experience_result"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_sse_generator_processes_multiple_roles(
    mock_get_llm_config,
    mock_async_refine_experience,
    mock_process_result,
    mock_generate_intro,
    test_user,
    test_resume,
):
    """Test the SSE generator correctly processes multiple 'role_refined' events."""
    mock_get_llm_config.return_value = (None, None, None)
    mock_generate_intro.return_value = "mocked intro"
    mock_process_result.return_value = "<html>final html</html>"

    refined_role1 = Role(
        basics=RoleBasics(
            company="Refined Company 1",
            title="Refined Role 1",
            start_date="2024-01-01",
        ),
        summary=RoleSummary(text="Summary 1"),
    )
    refined_role1_data = refined_role1.model_dump()
    refined_role2 = Role(
        basics=RoleBasics(
            company="Refined Company 2",
            title="Refined Role 2",
            start_date="2023-01-01",
        ),
        summary=RoleSummary(text="Summary 2"),
    )
    refined_role2_data = refined_role2.model_dump()

    async def mock_async_generator():
        yield {"status": "in_progress", "message": "doing stuff"}
        yield {
            "status": "role_refined",
            "data": refined_role1_data,
            "original_index": 0,
        }
        yield {
            "status": "role_refined",
            "data": refined_role2_data,
            "original_index": 1,
        }

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

    expected_events = 5  # 1 progress, 2 roles, 1 done, 1 close
    assert (
        len(results) == expected_events
    ), f"Expected {expected_events} events, got {len(results)}: {results}"
    results_str = "".join(results)
    assert "event: progress" in results_str
    assert "data: <li>doing stuff</li>" in results_str
    assert (
        "data: <li>Refined Role: Refined Role 1 at Refined Company 1</li>"
        in results_str
    )
    assert (
        "data: <li>Refined Role: Refined Role 2 at Refined Company 2</li>"
        in results_str
    )
    assert "event: done" in results_str
    assert "data: <html>final html</html>" in results_str
    assert "event: close" in results_str





@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.generate_introduction_from_resume"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.process_refined_experience_result"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_sse_generator_with_fallback_introduction_success(
    mock_get_llm_config,
    mock_async_refine_experience,
    mock_process_result,
    mock_generate_intro,
    test_user,
    test_resume,
):
    """Test that introduction fallback is triggered when no intro is streamed."""
    mock_get_llm_config.return_value = (
        "http://llm.test",
        "test-model",
        "decrypted_key",
    )
    mock_generate_intro.return_value = "mocked intro"
    mock_process_result.return_value = "<html>final refined html</html>"
    # The generator provides one role, but no introduction event
    refined_role1 = Role(
        basics=RoleBasics(
            company="Refined Company 1",
            title="Refined Role 1",
            start_date="2024-01-01",
        )
    )
    refined_role1_data = refined_role1.model_dump()

    async def mock_async_generator():
        yield {"status": "in_progress", "message": "doing stuff"}
        yield {
            "status": "role_refined",
            "data": refined_role1_data,
            "original_index": 0,
        }

    mock_async_refine_experience.return_value = mock_async_generator()

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

    # Assertions
    expected_events = 4  # 1 progress, 1 role, 1 done, 1 close
    assert (
        len(results) == expected_events
    ), f"Expected {expected_events} events, got {len(results)}: {results}"
    results_str = "".join(results)
    assert "event: introduction_generated" not in results_str
    assert "event: done" in results_str

    mock_generate_intro.assert_called_once()
    mock_process_result.assert_called_once()
    call_args = mock_process_result.call_args.args[0]
    assert call_args.introduction == "mocked intro"


def test_process_refined_role_event_success():
    """Test that _process_refined_role_event correctly processes a valid event."""
    refined_roles = {}
    role = Role(
        basics=RoleBasics(
            company="Test Corp",
            title="Engineer",
            start_date="2023-01-01",
        )
    )
    event = {
        "status": "role_refined",
        "data": role.model_dump(),
        "original_index": 0,
    }

    message = _process_refined_role_event(event, refined_roles)

    assert refined_roles == {0: role.model_dump()}
    assert message is not None
    assert "event: progress" in message
    assert "data: <li>Refined Role: Engineer at Test Corp</li>" in message


@pytest.mark.parametrize(
    "bad_event",
    [
        {"status": "role_refined", "data": {}, "original_index": None},
        {"status": "role_refined", "data": None, "original_index": 0},
        {
            "status": "role_refined",
            "data": {"basics": {"company": "Test"}},
            "original_index": 0,
        },
    ],
)
def test_process_refined_role_event_malformed(bad_event):
    """Test that _process_refined_role_event handles malformed events."""
    refined_roles = {}
    message = _process_refined_role_event(bad_event, refined_roles)
    assert message is None
    # No roles should be added if the event is malformed.
    assert not refined_roles


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
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.generate_introduction_from_resume"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.process_refined_experience_result"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_experience_refinement_sse_generator_malformed_events(
    mock_get_llm_config,
    mock_async_refine_experience,
    mock_process_result,
    mock_generate_intro,
    malformed_event,
    test_user,
    test_resume,
):
    """Test SSE generator handles unknown or malformed events gracefully."""
    mock_get_llm_config.return_value = (None, None, None)
    mock_generate_intro.return_value = "mock intro"
    mock_process_result.return_value = "<html>final html</html>"

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

    assert len(results) == 3
    assert "event: error" in results[0]
    assert "Refinement finished, but no roles were found to refine." in results[0]
    assert "event: done" in results[1]
    assert "<html>final html</html>" in results[1]
    assert "event: close" in results[2]


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.generate_introduction_from_resume"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.process_refined_experience_result"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_experience_refinement_sse_generator_empty_generator(
    mock_get_llm_config,
    mock_async_refine_experience,
    mock_process_result,
    mock_generate_intro,
    test_user,
    test_resume,
):
    """Test SSE stream with an empty generator from the LLM service."""
    mock_get_llm_config.return_value = (None, None, None)
    mock_generate_intro.return_value = "mock intro"
    mock_process_result.return_value = "<html>final html</html>"

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

    assert len(results) == 3
    assert "event: error" in results[0]
    assert "Refinement finished, but no roles were found to refine." in results[0]
    assert "event: done" in results[1]
    assert "<html>final html</html>" in results[1]
    assert "event: close" in results[2]


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
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.generate_introduction_from_resume"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.process_refined_experience_result"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_generator_breaks_on_timeout_if_task_done(
    mock_get_llm_config,
    mock_async_refine_experience,
    mock_process_result,
    mock_generate_intro,
    mock_create_close,
    test_user,
    test_resume,
    caplog,
):
    """Test generator breaks on TimeoutError if the background task is done and the queue is empty."""
    mock_get_llm_config.return_value = (None, None, None)
    mock_generate_intro.return_value = "mock intro"
    mock_process_result.return_value = "<html>final html</html>"

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

    assert len(results) == 4
    assert "event: progress" in results[0]
    assert "event: error" in results[1]
    assert "Refinement finished, but no roles were found to refine." in results[1]
    assert "event: done" in results[2]
    assert "<html>final html</html>" in results[2]
    assert "not a close message" in results[3]
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
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.generate_introduction_from_resume"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.process_refined_experience_result"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_generator_continues_on_timeout_if_task_not_done(
    mock_get_llm_config,
    mock_async_refine_experience,
    mock_process_result,
    mock_generate_intro,
    test_user,
    test_resume,
    caplog,
):
    """Test that the generator continues on TimeoutError if the background task is not yet done."""
    mock_get_llm_config.return_value = (None, None, None)
    mock_generate_intro.return_value = "mock intro"
    mock_process_result.return_value = "<html>final html</html>"

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
    # The final stream should contain: progress, error, done, close.
    assert len(results) == 4
    results_str = "".join(results)
    assert "event: progress" in results_str
    assert "I was slow" in results_str
    assert "event: error" in results_str
    assert "Refinement finished, but no roles were found to refine" in results_str
    assert "event: done" in results_str
    assert "<html>final html</html>" in results_str
    assert "event: close" in results_str
    # Check that we did not prematurely log the "task finished" message
    assert "LLM task finished and queue is empty" not in caplog.text


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.generate_introduction_from_resume"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.process_refined_experience_result"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_experience_refinement_sse_generator_with_introduction(
    mock_get_llm_config,
    mock_async_refine_experience,
    mock_process_result,
    mock_generate_intro,
    test_user,
    test_resume,
):
    """Test SSE refinement where introduction is provided by the stream."""
    mock_get_llm_config.return_value = (
        "http://llm.test",
        "test-model",
        "decrypted_key",
    )
    stream_intro = "Generated Test Intro"

    async def mock_async_generator():
        yield {"status": "introduction_generated", "data": stream_intro}
        yield {"status": "in_progress", "message": "doing stuff"}

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

    expected_events = 5
    assert (
        len(results) == expected_events
    ), f"Expected {expected_events} events, got {len(results)}: {results}"
    results_str = "".join(results)
    assert "event: introduction_generated" in results_str
    assert "event: progress" in results_str
    assert "event: done" in results_str
    assert "event: error" in results_str
    assert "Refinement finished, but no roles were found to refine" in results_str
    assert "event: close" in results_str

    # Assert that the OOB swap for introduction is present
    assert 'hx-swap-oob="true"' in results_str
    assert stream_intro in results_str

    mock_get_llm_config.assert_called_once()
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

    mock_generate_intro.assert_not_called()
    mock_process_result.assert_called_once()
    call_args = mock_process_result.call_args.args[0]
    assert call_args.introduction == stream_intro
    assert not call_args.refined_roles


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.generate_introduction_from_resume"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.process_refined_experience_result"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_experience_refinement_sse_generator_fallback_introduction_fails(
    mock_get_llm_config,
    mock_async_refine_experience,
    mock_process_result,
    mock_generate_intro,
    test_user,
    test_resume,
    caplog,
):
    """Test SSE refinement with FAILED fallback introduction generation."""
    mock_get_llm_config.return_value = (
        "http://llm.test",
        "test-model",
        "decrypted_key",
    )
    fallback_error = Exception("Fallback failed")
    mock_generate_intro.side_effect = fallback_error

    # No introduction event from the stream, but one role refined
    refined_role1 = Role(
        basics=RoleBasics(
            company="Refined Company 1",
            title="Refined Role 1",
            start_date="2024-01-01",
        ),
        summary=RoleSummary(text="Refined Summary 1"),
    )
    refined_role1_data = refined_role1.model_dump()

    async def mock_async_generator():
        yield {"status": "in_progress", "message": "doing stuff"}
        yield {
            "status": "role_refined",
            "data": refined_role1_data,
            "original_index": 0,
        }

    mock_async_refine_experience.return_value = mock_async_generator()
    mock_process_result.return_value = "<html>final html</html>"

    mock_db = Mock()
    params = ExperienceRefinementParams(
        db=mock_db,
        user=test_user,
        resume=test_resume,
        resume_content_to_refine=test_resume.content,
        original_resume_content=test_resume.content,
        job_description="a new job",
    )

    with caplog.at_level(logging.DEBUG):
        results = [
            item async for item in experience_refinement_sse_generator(params=params)
        ]

    # Still progresses to 'done' and 'close'
    assert len(results) == 4
    results_str = "".join(results)
    assert "event: progress" in results_str
    assert "event: done" in results_str
    assert "event: close" in results_str

    mock_generate_intro.assert_called_once()
    mock_process_result.assert_called_once()

    # Check that introduction is the default string in the final processing step
    call_args = mock_process_result.call_args.args[0]
    expected_default_intro = "Professional summary tailored to the provided job description. Customize this section to emphasize your most relevant experience, accomplishments, and skills."
    assert call_args.introduction == expected_default_intro

    # Check that the exception was logged
    assert "Failed to generate introduction fallback: Fallback failed" in caplog.text


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.env.get_template")
def test_process_sse_event_handles_introduction(mock_get_template):
    """Test that _process_sse_event handles an introduction_generated event."""
    refined_roles = {}
    intro_text = "This is a generated introduction."
    event = {
        "status": "introduction_generated",
        "data": intro_text,
    }

    mock_template = Mock()
    mock_template.render.return_value = (
        f'<div hx-swap-oob="true">{intro_text}</div>'
    )
    mock_get_template.return_value = mock_template

    sse_message, introduction = _process_sse_event(event, refined_roles)

    assert introduction == intro_text
    assert sse_message is not None
    assert "event: introduction_generated" in sse_message
    assert 'hx-swap-oob="true"' in sse_message
    assert intro_text in sse_message
    assert not refined_roles

    mock_get_template.assert_called_once_with(
        "partials/resume/_refine_result_intro.html"
    )
    mock_template.render.assert_called_once_with(introduction=intro_text)
