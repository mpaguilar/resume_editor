import asyncio
from unittest.mock import Mock, patch

import pytest
from cryptography.fernet import InvalidToken

import logging

from openai import AuthenticationError

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
    refined_role1_data = refined_role1.model_dump(mode="json")
    refined_role2 = Role(
        basics=RoleBasics(
            company="Refined Company 2",
            title="Refined Role 2",
            start_date="2023-01-01",
        ),
        summary=RoleSummary(text="Summary 2"),
    )
    refined_role2_data = refined_role2.model_dump(mode="json")

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
        limit_refinement_years=None,
    )
    results = [
        item async for item in experience_refinement_sse_generator(params=params)
    ]

    # 1 progress, 2 roles, 1 intro progress, 1 intro generated, 1 done, 1 close
    expected_events = 7
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
    assert "event: introduction_generated" in results_str
    assert 'id="refine_introduction_preview"' in results_str
    assert "mocked intro" in results_str
    assert "event: done" in results_str
    assert "data: <html>final html</html>" in results_str
    assert "event: close" in results_str





@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_banner_text")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic._reconstruct_refined_resume_content"
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
async def test_sse_generator_generates_introduction_at_end(
    mock_get_llm_config,
    mock_async_refine_experience,
    mock_process_result,
    mock_generate_intro,
    mock_reconstruct,
    mock_extract_banner,
    test_user,
    test_resume,
):
    """Test intro is generated at the end, using refined content."""
    mock_get_llm_config.return_value = (None, None, None)
    mock_generate_intro.return_value = "mocked intro"
    mock_reconstruct.return_value = "reconstructed content for intro gen"
    mock_extract_banner.return_value = "original banner"
    mock_process_result.return_value = "<html>final refined html</html>"
    # The generator provides one role, but no introduction event
    refined_role1 = Role(
        basics=RoleBasics(
            company="Refined Company 1",
            title="Refined Role 1",
            start_date="2024-01-01",
        )
    )
    refined_role1_data = refined_role1.model_dump(mode="json")

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
        limit_refinement_years=None,
    )
    results = [
        item async for item in experience_refinement_sse_generator(params=params)
    ]

    # Assertions
    # 1 progress, 1 role, 1 intro progress, 1 intro generated, 1 done, 1 close
    expected_events = 6
    assert (
        len(results) == expected_events
    ), f"Expected {expected_events} events, got {len(results)}: {results}"

    results_str = "".join(results)
    assert "event: introduction_generated" in results_str
    assert 'id="refine_introduction_preview"' in results_str
    assert "mocked intro" in results_str

    # Check that intro gen was called correctly at the end
    mock_reconstruct.assert_called_once()
    mock_extract_banner.assert_called_once_with(test_resume.content)
    mock_generate_intro.assert_called_once_with(
        resume_content="reconstructed content for intro gen",
        job_description="a new job",
        llm_config=LLMConfig(llm_endpoint=None, api_key=None, llm_model_name=None),
        original_banner="original banner",
    )

    # Check that final processing received the generated intro
    mock_process_result.assert_called_once()
    final_params = mock_process_result.call_args.kwargs["params"]
    assert final_params.introduction == "mocked intro"


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
        "data": role.model_dump(mode="json"),
        "original_index": 0,
    }

    message = _process_refined_role_event(event, refined_roles)

    assert refined_roles == {0: role.model_dump(mode="json")}
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
        limit_refinement_years=None,
    )
    results = [
        item async for item in experience_refinement_sse_generator(params=params)
    ]

    # The stream skips the malformed event, then proceeds to finalization,
    # which yields: intro_progress, intro_generated, error (no roles), done, close
    assert len(results) == 5
    assert "event: introduction_generated" in "".join(results)
    assert "event: error" in results[2]
    assert "Refinement finished, but no roles were found to refine." in results[2]


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

    # intro_progress, intro_generated, error (no roles), done, close
    assert len(results) == 5
    assert "event: error" in results[2]
    assert "Refinement finished, but no roles were found to refine." in results[2]
    assert "event: done" in results[3]
    assert "<html>final html</html>" in results[3]
    assert "event: close" in results[4]


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










def test_process_sse_event_handles_job_analysis_complete():
    """Test that _process_sse_event handles a job_analysis_complete event."""
    refined_roles = {}
    message_text = "Job analysis has completed."
    event = {"status": "job_analysis_complete", "message": message_text}

    sse_message = _process_sse_event(event, refined_roles)

    assert sse_message is not None
    assert "event: progress" in sse_message
    assert f"data: <li>{message_text}</li>" in sse_message
    assert not refined_roles


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
async def test_generator_with_progress_but_no_refined_roles(
    mock_get_llm_config,
    mock_async_refine_experience,
    mock_process_result,
    mock_generate_intro,
    mock_create_close,
    test_user,
    test_resume,
    caplog,
):
    """Test generator handles a stream that yields progress but no refined roles."""
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
        limit_refinement_years=None,
    )

    with caplog.at_level(logging.DEBUG):
        results = [
            item async for item in experience_refinement_sse_generator(params=params)
        ]

    assert len(results) == 6
    results_str = "".join(results)
    assert "event: progress" in results[0]
    assert "done" in results[0]
    assert "event: progress" in results[1]
    assert "Generating AI introduction" in results[1]
    assert "event: introduction_generated" in results[2]
    assert "event: error" in results[3]
    assert "Refinement finished, but no roles were found to refine." in results[3]
    assert "event: done" in results[4]
    assert "<html>final html</html>" in results[4]
    assert "not a close message" in results[5]


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_generator_handles_client_disconnect_gracefully(
    mock_get_llm_config,
    mock_async_refine_experience,
    test_user,
    test_resume,
    caplog,
):
    """Test that the generator handles client disconnects gracefully."""
    mock_get_llm_config.return_value = (None, None, None)

    generator_was_closed = asyncio.Event()

    async def slow_generator():
        """A mock generator that runs slowly and signals when closed."""
        try:
            yield {"status": "in_progress", "message": "starting"}
            await asyncio.sleep(10)  # Simulate a long-running process
        finally:
            generator_was_closed.set()

    mock_async_refine_experience.return_value = slow_generator()

    params = ExperienceRefinementParams(
        db=Mock(),
        user=test_user,
        resume=test_resume,
        resume_content_to_refine=test_resume.content,
        original_resume_content=test_resume.content,
        job_description="job",
        limit_refinement_years=None,
    )

    sse_generator = experience_refinement_sse_generator(params=params)

    with caplog.at_level(logging.WARNING):
        # Start iterating the generator to kick off the background task
        first_item = await sse_generator.__anext__()
        assert "event: progress" in first_item
        assert "starting" in first_item

        # Simulate the client disconnecting by throwing an exception into the generator.
        with pytest.raises(StopAsyncIteration):
            await sse_generator.athrow(GeneratorExit)

    assert f"SSE stream closed for resume {test_resume.id}." in caplog.text

    # Check that the underlying generator was closed.
    try:
        await asyncio.wait_for(generator_was_closed.wait(), timeout=1.0)
    except asyncio.TimeoutError:
        pytest.fail("The underlying generator was not closed.")





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
async def test_generator_with_slow_llm_stream(
    mock_get_llm_config,
    mock_async_refine_experience,
    mock_process_result,
    mock_generate_intro,
    test_user,
    test_resume,
    caplog,
):
    """Test that the generator handles a slow/laggy LLM stream."""
    mock_get_llm_config.return_value = (None, None, None)
    mock_generate_intro.return_value = "mock intro"
    mock_process_result.return_value = "<html>final html</html>"

    async def slow_generator():
        """A generator that waits before yielding a message."""
        await asyncio.sleep(0.1)
        yield {"status": "in_progress", "message": "I was slow"}

    mock_async_refine_experience.return_value = slow_generator()

    params = ExperienceRefinementParams(
        db=Mock(),
        user=test_user,
        resume=test_resume,
        resume_content_to_refine=test_resume.content,
        original_resume_content=test_resume.content,
        job_description="job",
        limit_refinement_years=None,
    )

    with caplog.at_level(logging.DEBUG):
        results = [
            item async for item in experience_refinement_sse_generator(params=params)
        ]

    # The final stream should contain all events, even with a slow stream.
    # progress, intro_progress, intro_generated, error, done, close
    assert len(results) == 6
    results_str = "".join(results)
    assert "event: progress" in results_str
    assert "I was slow" in results_str
    assert "event: introduction_generated" in results_str
    assert "event: error" in results_str
    assert "Refinement finished, but no roles were found to refine" in results_str
    assert "event: done" in results_str
    assert "<html>final html</html>" in results_str
    assert "event: close" in results_str


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_banner_text")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic._reconstruct_refined_resume_content"
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
async def test_sse_generator_intro_generation_retries_on_failure(
    mock_get_llm_config,
    mock_async_refine_experience,
    mock_process_result,
    mock_generate_intro,
    mock_reconstruct,
    mock_extract_banner,
    test_user,
    test_resume,
    caplog,
):
    """Test that introduction generation is retried on failure."""
    mock_get_llm_config.return_value = (None, None, None)
    mock_generate_intro.side_effect = [Exception("Fail 1"), "Success on 2nd try"]
    mock_reconstruct.return_value = "content"
    mock_extract_banner.return_value = "banner"
    mock_process_result.return_value = "<html>final</html>"

    async def mock_async_generator():
        yield {"status": "in_progress", "message": "doing stuff"}

    mock_async_refine_experience.return_value = mock_async_generator()

    params = ExperienceRefinementParams(
        db=Mock(),
        user=test_user,
        resume=test_resume,
        resume_content_to_refine=test_resume.content,
        original_resume_content=test_resume.content,
        job_description="a job",
        limit_refinement_years=None,
    )

    with caplog.at_level(logging.WARNING):
        _ = [item async for item in experience_refinement_sse_generator(params=params)]

    assert "Attempt 1 to generate introduction failed: Fail 1" in caplog.text
    assert mock_generate_intro.call_count == 2

    mock_process_result.assert_called_once()
    final_params = mock_process_result.call_args.kwargs["params"]
    assert final_params.introduction == "Success on 2nd try"


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_banner_text")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic._reconstruct_refined_resume_content"
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
async def test_sse_generator_intro_generation_retries_on_empty_string(
    mock_get_llm_config,
    mock_async_refine_experience,
    mock_process_result,
    mock_generate_intro,
    mock_reconstruct,
    mock_extract_banner,
    test_user,
    test_resume,
    caplog,
):
    """Test intro generation is retried if the LLM returns an empty string."""
    mock_get_llm_config.return_value = (None, None, None)
    # First call returns empty string, second call succeeds
    mock_generate_intro.side_effect = ["   ", "Success on 2nd try"]
    mock_reconstruct.return_value = "content"
    mock_extract_banner.return_value = "banner"
    mock_process_result.return_value = "<html>final</html>"

    async def mock_async_generator():
        yield {"status": "in_progress", "message": "doing stuff"}

    mock_async_refine_experience.return_value = mock_async_generator()

    params = ExperienceRefinementParams(
        db=Mock(),
        user=test_user,
        resume=test_resume,
        resume_content_to_refine=test_resume.content,
        original_resume_content=test_resume.content,
        job_description="a job",
        limit_refinement_years=None,
    )

    with caplog.at_level(logging.DEBUG):
        _ = [item async for item in experience_refinement_sse_generator(params=params)]

    assert mock_generate_intro.call_count == 2
    mock_process_result.assert_called_once()
    final_params = mock_process_result.call_args.kwargs["params"]
    assert final_params.introduction == "Success on 2nd try"


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_banner_text")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic._reconstruct_refined_resume_content"
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
async def test_sse_generator_intro_generation_fallback_on_total_failure(
    mock_get_llm_config,
    mock_async_refine_experience,
    mock_process_result,
    mock_generate_intro,
    mock_reconstruct,
    mock_extract_banner,
    test_user,
    test_resume,
    caplog,
):
    """Test intro generation falls back to default if all retries fail."""
    mock_get_llm_config.return_value = (None, None, None)
    # All three calls fail
    mock_generate_intro.side_effect = [
        Exception("Fail 1"),
        Exception("Fail 2"),
        Exception("Fail 3"),
    ]
    mock_reconstruct.return_value = "content"
    mock_extract_banner.return_value = "banner"
    mock_process_result.return_value = "<html>final</html>"

    async def mock_async_generator():
        yield {"status": "in_progress", "message": "doing stuff"}

    mock_async_refine_experience.return_value = mock_async_generator()

    params = ExperienceRefinementParams(
        db=Mock(),
        user=test_user,
        resume=test_resume,
        resume_content_to_refine=test_resume.content,
        original_resume_content=test_resume.content,
        job_description="a job",
        limit_refinement_years=None,
    )

    with caplog.at_level(logging.ERROR):
        _ = [item async for item in experience_refinement_sse_generator(params=params)]

    assert (
        "Failed to generate introduction after all retries. Using default."
        in caplog.text
    )
    assert mock_generate_intro.call_count == 3

    mock_process_result.assert_called_once()
    final_params = mock_process_result.call_args.kwargs["params"]
    assert "Professional summary tailored" in final_params.introduction




@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.extract_banner_text")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic._reconstruct_refined_resume_content"
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
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.env.get_template")
async def test_sse_generator_e2e_refine_then_introduce_workflow(
    mock_get_template,
    mock_get_llm_config,
    mock_async_refine_experience,
    mock_process_result,
    mock_generate_intro,
    mock_reconstruct,
    mock_extract_banner,
    test_user,
    test_resume,
):
    """
    Tests the complete end-to-end 'refine-then-introduce' workflow in the SSE generator.
    It verifies:
    1. Role refinement events are processed from the LLM stream.
    2. Introduction generation is triggered *after* role refinement.
    3. The correct events are yielded in the correct order (progress, role, intro, done, close).
    """
    # Arrange
    # Mock template rendering to isolate from actual template content
    mock_template = Mock()
    mock_template.render.return_value = "new mocked intro"
    mock_get_template.return_value = mock_template

    mock_get_llm_config.return_value = (None, None, None)
    mock_generate_intro.return_value = "new mocked intro"
    mock_reconstruct.return_value = "reconstructed content for intro gen"
    mock_extract_banner.return_value = "original banner"
    mock_process_result.return_value = "<html>final refined html</html>"

    refined_role = Role(
        basics=RoleBasics(
            company="Refined Company", title="Refined Role", start_date="2024-01-01"
        )
    )
    refined_role_data = refined_role.model_dump(mode="json")

    # The async_refine_experience_section stream now ONLY yields refinement events
    async def mock_refinement_stream():
        yield {"status": "in_progress", "message": "refining role..."}
        yield {
            "status": "role_refined",
            "data": refined_role_data,
            "original_index": 0,
        }

    mock_async_refine_experience.return_value = mock_refinement_stream()

    params = ExperienceRefinementParams(
        db=Mock(),
        user=test_user,
        resume=test_resume,
        resume_content_to_refine=test_resume.content,
        original_resume_content=test_resume.content,
        job_description="a new job",
        limit_refinement_years=None,
    )

    # Act
    results = [
        item async for item in experience_refinement_sse_generator(params=params)
    ]
    result_str = "".join(results)

    # Assert
    # Total events:
    # From refinement stream: 1 progress, 1 role_refined = 2
    # From main generator: 1 intro progress, 1 intro generated, 1 done, 1 close = 4
    # Total = 6
    assert len(results) == 6, f"Expected 6 events, but got {len(results)}: {results}"

    # 1. Check for refinement events
    assert "data: <li>refining role...</li>" in result_str
    assert "data: <li>Refined Role: Refined Role at Refined Company</li>" in result_str

    # 2. Check for introduction events
    assert "data: <li>Generating AI introduction...</li>" in result_str
    assert "event: introduction_generated" in result_str
    assert "data: new mocked intro" in result_str

    # 3. Check for final events
    assert "event: done" in result_str
    assert "data: <html>final refined html</html>" in result_str
    assert "event: close" in result_str

    # 4. Verify mocks to confirm flow
    mock_reconstruct.assert_called_once()
    mock_generate_intro.assert_called_once_with(
        resume_content="reconstructed content for intro gen",
        job_description="a new job",
        llm_config=LLMConfig(llm_endpoint=None, api_key=None, llm_model_name=None),
        original_banner="original banner",
    )
    mock_process_result.assert_called_once()
    final_params = mock_process_result.call_args.kwargs["params"]
    assert final_params.introduction == "new mocked intro"
