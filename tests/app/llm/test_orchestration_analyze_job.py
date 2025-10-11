from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import AuthenticationError

import json
from resume_editor.app.llm.orchestration import (
    analyze_job_description,
)
from resume_editor.app.llm.models import JobAnalysis

LLM_INIT_PARAMS = [
    # Case 1: Endpoint, API key, and model name provided
    (
        "http://fake.llm",
        "key",
        "custom-model",
        {
            "model": "custom-model",
            "temperature": 0.7,
            "openai_api_base": "http://fake.llm",
            "api_key": "key",
        },
    ),
    # Case 2: Endpoint and model name, but no API key (should use dummy key)
    (
        "http://fake.llm",
        None,
        "custom-model",
        {
            "model": "custom-model",
            "temperature": 0.7,
            "openai_api_base": "http://fake.llm",
            "api_key": "not-needed",
        },
    ),
    # Case 3: API key and model name, but no endpoint
    (
        None,
        "key",
        "custom-model",
        {"model": "custom-model", "temperature": 0.7, "api_key": "key"},
    ),
    # Case 4: No endpoint, no API key (relies on env var)
    (
        None,
        None,
        "custom-model",
        {"model": "custom-model", "temperature": 0.7},
    ),
    # Case 5: Fallback to default model name when None is provided
    (
        "http://fake.llm",
        "key",
        None,
        {
            "model": "gpt-4o",
            "temperature": 0.7,
            "openai_api_base": "http://fake.llm",
            "api_key": "key",
        },
    ),
    # Case 6: Fallback to default model name when empty string is provided
    (
        "http://fake.llm",
        "key",
        "",
        {
            "model": "gpt-4o",
            "temperature": 0.7,
            "openai_api_base": "http://fake.llm",
            "api_key": "key",
        },
    ),
    # Case 7: OpenRouter endpoint with API key
    (
        "https://openrouter.ai/api/v1",
        "or-key",
        "openrouter/model",
        {
            "model": "openrouter/model",
            "temperature": 0.7,
            "openai_api_base": "https://openrouter.ai/api/v1",
            "api_key": "or-key",
            "default_headers": {
                "HTTP-Referer": "http://localhost:8000/",
                "X-Title": "Resume Editor",
            },
        },
    ),
]


@pytest.mark.asyncio
async def test_analyze_job_description_empty_input():
    """Test that analyze_job_description raises ValueError for empty input."""
    with pytest.raises(ValueError, match="Job description cannot be empty."):
        await analyze_job_description(
            job_description=" ",
            llm_endpoint=None,
            api_key=None,
            llm_model_name=None,
        )


@pytest.fixture
def mock_chain_invocations_for_analysis():
    """
    Fixture to mock the LangChain chain invocation for job analysis.
    """
    with patch(
        "resume_editor.app.llm.orchestration.ChatOpenAI"
    ) as mock_chat_openai_class, patch(
        "resume_editor.app.llm.orchestration.ChatPromptTemplate"
    ) as mock_prompt_template_class, patch(
        "resume_editor.app.llm.orchestration.PydanticOutputParser"
    ), patch(
        "resume_editor.app.llm.orchestration.StrOutputParser"
    ):
        mock_prompt_from_messages = MagicMock()
        mock_prompt_template_class.from_messages.return_value = (
            mock_prompt_from_messages
        )

        mock_prompt_partial = MagicMock()
        mock_prompt_from_messages.partial.return_value = mock_prompt_partial

        # Mock the `|` operator chaining
        prompt_llm_chain = MagicMock()
        mock_prompt_partial.__or__.return_value = prompt_llm_chain

        final_chain = MagicMock()
        prompt_llm_chain.__or__.return_value = final_chain

        # The final ainvoke should return a string, not a JobAnalysis object
        final_chain.ainvoke = AsyncMock(
            return_value='```json\n{"key_skills": ["python", "fastapi"], "primary_duties": ["develop things"], "themes": ["agile"]}\n```'
        )

        yield {
            "chat_openai": mock_chat_openai_class,
            "final_chain": final_chain,
            "prompt_template": mock_prompt_template_class,
            "prompt_from_messages": mock_prompt_from_messages,
        }


@pytest.mark.asyncio
async def test_analyze_job_description(mock_chain_invocations_for_analysis):
    """Test that analyze_job_description returns a JobAnalysis object and no introduction."""
    # Act
    job_analysis, introduction = await analyze_job_description(
        job_description="some job description",
        llm_endpoint=None,
        api_key=None,
        llm_model_name=None,
        resume_content_for_intro=None,  # Explicitly None
    )

    # Assert results
    assert isinstance(job_analysis, JobAnalysis)
    assert job_analysis.key_skills == ["python", "fastapi"]
    assert introduction is None

    # Assert prompt construction
    final_chain = mock_chain_invocations_for_analysis["final_chain"]
    final_chain.ainvoke.assert_called_once()
    invoke_args = final_chain.ainvoke.call_args.args[0]
    assert invoke_args["resume_content_block"] == ""

    partial_kwargs = mock_chain_invocations_for_analysis[
        "prompt_from_messages"
    ].partial.call_args.kwargs
    assert partial_kwargs["introduction_instructions"] == ""


@pytest.mark.asyncio
async def test_analyze_job_description_with_introduction(
    mock_chain_invocations_for_analysis,
):
    """Test that analyze_job_description returns a JobAnalysis and an an introduction when requested."""
    # Arrange: modify the mock to return an introduction
    final_chain = mock_chain_invocations_for_analysis["final_chain"]
    final_chain.ainvoke.return_value = '```json\n{"key_skills": ["python", "fastapi"], "primary_duties": ["develop things"], "themes": ["agile"], "introduction": "This is an intro."}\n```'

    # Act
    job_analysis, introduction = await analyze_job_description(
        job_description="some job description",
        llm_endpoint=None,
        api_key=None,
        llm_model_name=None,
        resume_content_for_intro="some resume content",
    )

    # Assert
    assert isinstance(job_analysis, JobAnalysis)
    assert job_analysis.key_skills == ["python", "fastapi"]
    assert introduction == "This is an intro."
    assert job_analysis.introduction == "This is an intro."

    # Assert prompt construction
    final_chain.ainvoke.assert_called_once()
    invoke_args = final_chain.ainvoke.call_args.args[0]
    assert "some resume content" in invoke_args["resume_content_block"]

    partial_kwargs = mock_chain_invocations_for_analysis[
        "prompt_from_messages"
    ].partial.call_args.kwargs
    assert "Instructions for Introduction Generation" in partial_kwargs["introduction_instructions"]


@pytest.mark.parametrize("llm_endpoint, api_key, llm_model_name, expected_call_args", LLM_INIT_PARAMS)
@pytest.mark.asyncio
async def test_analyze_job_description_llm_initialization(
    mock_chain_invocations_for_analysis,
    llm_endpoint,
    api_key,
    llm_model_name,
    expected_call_args,
):
    """
    Test that ChatOpenAI is initialized with the correct parameters for analysis.
    """
    await analyze_job_description(
        job_description="some job description",
        llm_endpoint=llm_endpoint,
        api_key=api_key,
        llm_model_name=llm_model_name,
    )
    mock_chat_openai = mock_chain_invocations_for_analysis["chat_openai"]
    mock_chat_openai.assert_called_once_with(**expected_call_args)


@pytest.mark.asyncio
async def test_analyze_job_description_json_decode_error(
    mock_chain_invocations_for_analysis,
):
    """
    Test that a JSONDecodeError from the LLM call is handled gracefully in analysis.
    """
    import json

    final_chain = mock_chain_invocations_for_analysis["final_chain"]
    final_chain.ainvoke.side_effect = json.JSONDecodeError(
        "Expecting value", "invalid json", 0
    )

    with pytest.raises(
        ValueError,
        match="The AI service returned an unexpected response. Please try again.",
    ):
        await analyze_job_description(
            job_description="job desc",
            llm_endpoint=None,
            api_key=None,
            llm_model_name=None,
        )


@pytest.mark.asyncio
async def test_analyze_job_description_validation_error(
    mock_chain_invocations_for_analysis,
):
    """
    Test that a Pydantic validation error is handled gracefully in analysis.
    """
    final_chain = mock_chain_invocations_for_analysis["final_chain"]
    final_chain.ainvoke.return_value = '```json\n{"wrong_field": "wrong_value"}\n```'

    with pytest.raises(
        ValueError,
        match="The AI service returned an unexpected response. Please try again.",
    ):
        await analyze_job_description(
            job_description="job desc",
            llm_endpoint=None,
            api_key=None,
            llm_model_name=None,
        )


@pytest.mark.asyncio
async def test_analyze_job_description_authentication_error(
    mock_chain_invocations_for_analysis,
):
    """
    Test that an AuthenticationError from the LLM call is propagated during analysis.
    """
    from openai import AuthenticationError

    final_chain = mock_chain_invocations_for_analysis["final_chain"]
    final_chain.ainvoke.side_effect = AuthenticationError(
        message="Invalid API key", response=MagicMock(), body=None
    )

    with pytest.raises(AuthenticationError):
        await analyze_job_description(
            job_description="job desc",
            llm_endpoint=None,
            api_key=None,
            llm_model_name=None,
        )


@pytest.mark.asyncio
async def test_analyze_job_description_prompt_content(
    mock_chain_invocations_for_analysis,
):
    """Test that the prompt for analyze_job_description is constructed correctly."""
    # Act
    await analyze_job_description(
        job_description="A job description",
        llm_endpoint=None,
        api_key=None,
        llm_model_name=None,
    )

    # Assert
    mock_prompt_template = mock_chain_invocations_for_analysis["prompt_template"]
    mock_prompt_from_messages = mock_chain_invocations_for_analysis[
        "prompt_from_messages"
    ]

    # Check that from_messages was called with system and human templates
    mock_prompt_template.from_messages.assert_called_once()
    messages = mock_prompt_template.from_messages.call_args.args[0]
    assert messages[0][0] == "system"
    assert messages[1][0] == "human"

    system_template = messages[0][1]
    human_template = messages[1][1]

    # Check that crucial rules and spec are always in the system template
    assert "As a professional resume writer and career coach" in system_template
    assert "{format_instructions}" in system_template
    assert "{job_description}" in human_template

    # Check the content passed to partial()
    mock_prompt_from_messages.partial.assert_called_once()
    partial_kwargs = mock_prompt_from_messages.partial.call_args.kwargs
    assert "format_instructions" in partial_kwargs
