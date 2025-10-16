from unittest.mock import Mock, patch

import pytest
from cryptography.fernet import InvalidToken

import logging

from openai import AuthenticationError
from starlette.middleware.base import ClientDisconnect

from resume_editor.app.api.routes.route_logic.resume_ai_logic import (
    experience_refinement_sse_generator,
)
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
    results = [
        item
        async for item in experience_refinement_sse_generator(
            db=mock_db,
            user=test_user,
            resume=test_resume,
            job_description="a new job",
            generate_introduction=True,
        )
    ]

    assert len(results) == 4, f"Expected 4 events, got {len(results)}: {results}"
    assert "event: progress" in results[0]
    assert "data: <li>doing stuff</li>" in results[0]
    assert "event: introduction_generated" in results[1]
    assert 'id="introduction-container"' in results[1]
    assert "event: done" in results[2]
    assert "data: <html>final refined html</html>" in results[2]
    assert "event: close" in results[3]

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
        generate_introduction=True,
    )
    mock_process_result.assert_called_once_with(
        test_resume,
        {1: refined_role2_data, 0: refined_role1_data},
        "a new job",
        "Generated Intro",
    )


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.process_refined_experience_result"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_experience_refinement_sse_generator_gen_intro_false(
    mock_get_llm_config,
    mock_async_refine_experience,
    mock_process_result,
    test_user,
    test_resume,
):
    """Test SSE generator when generate_introduction is false."""
    mock_get_llm_config.return_value = (None, None, None)
    refined_role1_data = {"test": "data"}

    async def mock_async_generator():
        yield {"status": "role_refined", "data": refined_role1_data, "original_index": 0}

    mock_async_refine_experience.return_value = mock_async_generator()
    mock_process_result.return_value = "final html"

    results = [
        item
        async for item in experience_refinement_sse_generator(
            db=Mock(),
            user=test_user,
            resume=test_resume,
            job_description="a job",
            generate_introduction=False,
        )
    ]

    assert len(results) == 2
    assert "event: done" in results[0]
    assert "data: final html" in results[0]
    assert "event: close" in results[1]

    expected_llm_config = LLMConfig(
        llm_endpoint=None,
        api_key=None,
        llm_model_name=None,
    )
    mock_async_refine_experience.assert_called_once_with(
        resume_content=test_resume.content,
        job_description="a job",
        llm_config=expected_llm_config,
        generate_introduction=False,
    )
    mock_process_result.assert_called_once_with(
        test_resume, {0: refined_role1_data}, "a job", None
    )


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

    results = [
        item
        async for item in experience_refinement_sse_generator(
            db=Mock(),
            user=test_user,
            resume=test_resume,
            job_description="job",
            generate_introduction=True,
        )
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

    results = [
        item
        async for item in experience_refinement_sse_generator(
            db=Mock(),
            user=test_user,
            resume=test_resume,
            job_description="job",
            generate_introduction=True,
        )
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

    results = [
        item
        async for item in experience_refinement_sse_generator(
            db=Mock(),
            user=test_user,
            resume=test_resume,
            job_description="a new job",
            generate_introduction=True,
        )
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

    results = [
        item
        async for item in experience_refinement_sse_generator(
            db=Mock(),
            user=test_user,
            resume=test_resume,
            job_description="a job",
            generate_introduction=True,
        )
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

    results = [
        item
        async for item in experience_refinement_sse_generator(
            db=Mock(),
            user=test_user,
            resume=test_resume,
            job_description="job",
            generate_introduction=True,
        )
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

    results = [
        item
        async for item in experience_refinement_sse_generator(
            db=Mock(),
            user=test_user,
            resume=test_resume,
            job_description="job",
            generate_introduction=True,
        )
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

    results = [
        item
        async for item in experience_refinement_sse_generator(
            db=Mock(),
            user=test_user,
            resume=test_resume,
            job_description="job",
            generate_introduction=True,
        )
    ]

    assert len(results) == 2
    assert results[0] == "formatted error"
    assert "event: close" in results[1]
    mock_handle_exception.assert_called_once_with(error, test_resume.id)


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.async_refine_experience_section"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_experience_refinement_sse_generator_client_disconnect(
    mock_get_llm_config, mock_async_refine_experience, test_user, test_resume, caplog
):
    """Test that the SSE generator handles a ClientDisconnect gracefully."""
    mock_get_llm_config.return_value = (None, None, None)

    async def mock_generator_with_disconnect():
        raise ClientDisconnect()
        yield

    mock_async_refine_experience.return_value = mock_generator_with_disconnect()

    with caplog.at_level(logging.WARNING):
        results = [
            item
            async for item in experience_refinement_sse_generator(
                db=Mock(),
                user=test_user,
                resume=test_resume,
                job_description="job",
                generate_introduction=True,
            )
        ]

    assert len(results) == 1
    assert "event: close" in results[0]
    assert f"Client disconnected from SSE stream for resume {test_resume.id}." in caplog.text
