import asyncio
from unittest.mock import Mock, patch

import pytest

from resume_editor.app.api.routes.route_logic.resume_ai_logic import (
    _finalize_llm_refinement,
    create_sse_done_message,
)
from resume_editor.app.llm.models import LLMConfig


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.process_refined_experience_result"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.generate_introduction_from_resume"
)
async def test_finalize_llm_refinement_intro_fallback_on_exception(
    mock_generate_intro, mock_process_result, caplog
):
    """
    Test _finalize_llm_refinement falls back to default intro when
    analyze_job_description raises an exception.
    """
    # Arrange
    message_queue = asyncio.Queue()

    params = Mock()
    params.job_description = "a job"
    params.original_resume_content = "original content"
    params.limit_refinement_years = None
    params.resume = Mock()
    params.resume.id = 1
    params.resume_content_to_refine = "to refine"

    llm_config = LLMConfig(api_key="test-key")
    refined_roles = {0: {}}
    mock_process_result.return_value = "<html>final html</html>"
    mock_generate_intro.side_effect = Exception("LLM call failed")

    default_intro = "Professional summary tailored to the provided job description. Customize this section to emphasize your most relevant experience, accomplishments, and skills."

    # Act
    await _finalize_llm_refinement(
        refined_roles=refined_roles,
        introduction=None,  # No intro from stream
        params=params,
        message_queue=message_queue,
        llm_config=llm_config,
    )

    # Assert
    assert "Failed to generate introduction fallback: LLM call failed" in caplog.text
    mock_process_result.assert_called_once()
    call_params = mock_process_result.call_args[0][0]  # First positional arg
    assert call_params.introduction == default_intro

    final_message = await message_queue.get()
    assert create_sse_done_message("<html>final html</html>") in final_message


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.process_refined_experience_result"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.generate_introduction_from_resume"
)
async def test_finalize_llm_refinement_intro_fallback_on_no_intro(
    mock_generate_intro, mock_process_result
):
    """
    Test _finalize_llm_refinement falls back to default intro when
    analyze_job_description returns no introduction.
    """
    # Arrange
    message_queue = asyncio.Queue()

    params = Mock()
    params.job_description = "a job"
    params.original_resume_content = "original content"
    params.limit_refinement_years = None
    params.resume = Mock()
    params.resume.id = 1
    params.resume_content_to_refine = "to refine"

    llm_config = LLMConfig(api_key="test-key")
    refined_roles = {0: {}}
    mock_process_result.return_value = "<html>final html</html>"
    # Mock generate_introduction_from_resume to return an empty string
    mock_generate_intro.return_value = ""

    default_intro = "Professional summary tailored to the provided job description. Customize this section to emphasize your most relevant experience, accomplishments, and skills."

    # Act
    await _finalize_llm_refinement(
        refined_roles=refined_roles,
        introduction="",  # Test with empty string from stream
        params=params,
        message_queue=message_queue,
        llm_config=llm_config,
    )

    # Assert
    mock_generate_intro.assert_called_once()
    mock_process_result.assert_called_once()
    call_params = mock_process_result.call_args[0][0]  # First positional arg
    assert call_params.introduction == default_intro

    final_message = await message_queue.get()
    assert create_sse_done_message("<html>final html</html>") in final_message
