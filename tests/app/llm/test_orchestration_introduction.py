import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import AIMessage

from resume_editor.app.llm.models import LLMConfig
from resume_editor.app.llm.orchestration import analyze_job_description

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio


@patch("resume_editor.app.llm.orchestration.ChatOpenAI")
async def test_analyze_job_description_prompt_updated(mock_chat_open_ai: MagicMock):
    """
    Tests that analyze_job_description uses the updated prompt which has hardcoded
    introduction instructions and no longer has the {introduction_instructions} placeholder.
    This test verifies the change made to prompts.py and orchestration.py to hardcode
    the introduction instructions.
    """
    # Arrange
    # The llm instance returns an AIMessage, which StrOutputParser handles by
    # extracting the .content attribute.
    mock_ai_message = AIMessage(
        content='```json\n{"key_skills": [], "primary_duties": [], "themes": []}\n```'
    )
    # Use AsyncMock for the instance itself, as the Runnable protocol awaits it.
    ainvoke_mock = AsyncMock(return_value=mock_ai_message)
    mock_chat_open_ai.return_value = ainvoke_mock

    llm_config = LLMConfig(
        llm_endpoint=None, llm_model_name="gpt-4o", api_key="dummy_key"
    )

    job_description = "A test job description"
    resume_content = "Some resume content for introduction generation."

    # Act
    await analyze_job_description(
        job_description=job_description,
        llm_config=llm_config,
        resume_content_for_intro=resume_content,
    )

    # Assert
    # The prompt is the first argument passed to the llm instance's ainvoke method.
    assert ainvoke_mock.call_count == 1
    call_args, _ = ainvoke_mock.call_args
    # The prompt is passed as the first positional argument to the mocked llm instance
    prompt_value = call_args[0]
    prompt_string = str(prompt_value)

    # Check that new, hardcoded instructions are in the prompt
    assert "Strictly Adhere to Resume Content" in prompt_string
    assert "The introduction must only reference skills" in prompt_string

    # Check that the old placeholder is GONE
    assert "{introduction_instructions}" not in prompt_string
