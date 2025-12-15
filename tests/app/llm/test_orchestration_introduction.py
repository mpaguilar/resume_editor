import json
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage
from openai import OpenAIError
from pydantic import BaseModel, ValidationError

from resume_editor.app.llm.models import (
    CandidateAnalysis,
    GeneratedIntroduction,
    JobKeyRequirements,
    LLMConfig,
)
from resume_editor.app.llm.orchestration import (
    _generate_introduction_from_resume,
    _invoke_chain_and_parse,
    generate_introduction_from_resume,
)


@patch("resume_editor.app.llm.orchestration._invoke_chain_and_parse")
def test_generate_introduction_from_resume_success(mock_invoke_and_parse: MagicMock):
    """
    Tests the successful execution of the three-step introduction generation chain.
    """
    # Arrange
    mock_invoke_and_parse.side_effect = [
        JobKeyRequirements(
            key_skills=["python", "fastapi"],
            candidate_priorities=["backend dev"],
        ),
        CandidateAnalysis(
            skill_summary={
                "python": {"assessment": "strong experience", "source": ["Work"]},
                "fastapi": {"assessment": "familiarity with", "source": ["Project"]},
            }
        ),
        GeneratedIntroduction(introduction="Final introduction text."),
    ]

    mock_llm = MagicMock()
    resume_content = "some resume content"
    job_description = "some job description"

    # Act
    result = _generate_introduction_from_resume(
        resume_content=resume_content,
        job_description=job_description,
        llm=mock_llm,
    )

    # Assert
    assert result == "Final introduction text."
    assert mock_invoke_and_parse.call_count == 3

    # Assert call arguments
    # Call 1 (Job Analysis)
    call_1_kwargs = mock_invoke_and_parse.call_args_list[0].kwargs
    assert call_1_kwargs["job_description"] == job_description

    # Call 2 (Resume Analysis)
    call_2_kwargs = mock_invoke_and_parse.call_args_list[1].kwargs
    assert call_2_kwargs["resume_content"] == resume_content
    job_reqs_json = json.loads(call_2_kwargs["job_requirements"])
    assert job_reqs_json["key_skills"] == ["python", "fastapi"]

    # Call 3 (Synthesis)
    call_3_kwargs = mock_invoke_and_parse.call_args_list[2].kwargs
    candidate_analysis_json = json.loads(call_3_kwargs["candidate_analysis"])
    assert (
        candidate_analysis_json["skill_summary"]["python"]["assessment"]
        == "strong experience"
    )


@patch("resume_editor.app.llm.orchestration._invoke_chain_and_parse")
def test_generate_introduction_from_resume_error(mock_invoke_and_parse: MagicMock):
    """
    Tests that the function handles errors during chain execution gracefully
    and returns an empty string.
    """
    # Arrange
    mock_invoke_and_parse.side_effect = ValueError("bad value")

    mock_llm = MagicMock()
    resume_content = "some resume content"
    job_description = "some job description"

    # Act
    result = _generate_introduction_from_resume(
        resume_content=resume_content,
        job_description=job_description,
        llm=mock_llm,
    )

    # Assert
    assert result == ""
    mock_invoke_and_parse.assert_called_once()


def test_invoke_chain_and_parse_success():
    """
    Tests that _invoke_chain_and_parse correctly invokes a chain, parses the
    JSON content, and validates it with a Pydantic model.
    """
    # Arrange
    mock_chain = MagicMock()
    mock_result = MagicMock()
    mock_result.content = '```json\n{"key": "value"}\n```'
    mock_chain.invoke.return_value = mock_result

    class SimpleModel(BaseModel):
        key: str

    kwargs = {"input": "some data"}

    # Act
    result = _invoke_chain_and_parse(mock_chain, SimpleModel, **kwargs)

    # Assert
    mock_chain.invoke.assert_called_once_with(kwargs)
    assert isinstance(result, SimpleModel)
    assert result.key == "value"


@pytest.mark.parametrize(
    "llm_config_data, expected_llm_params",
    [
        # Case 1: Full config with custom endpoint and API key
        (
            {
                "llm_model_name": "test-model",
                "llm_endpoint": "https://example.com/api",
                "api_key": "test-key",
            },
            {
                "model": "test-model",
                "openai_api_base": "https://example.com/api",
                "api_key": "test-key",
            },
        ),
        # Case 2: OpenRouter endpoint
        (
            {"llm_endpoint": "https://openrouter.ai/api/v1", "api_key": "or-key"},
            {
                "model": "gpt-4o",
                "openai_api_base": "https://openrouter.ai/api/v1",
                "api_key": "or-key",
                "default_headers": {
                    "HTTP-Referer": "http://localhost:8000/",
                    "X-Title": "Resume Editor",
                },
            },
        ),
        # Case 3: Local LLM endpoint with no API key
        (
            {"llm_endpoint": "http://localhost:1234/v1"},
            {
                "model": "gpt-4o",
                "openai_api_base": "http://localhost:1234/v1",
                "api_key": "not-needed",
            },
        ),
        # Case 4: No model name (uses default) and no endpoint
        (
            {"api_key": "openai-key"},
            {"model": "gpt-4o", "api_key": "openai-key"},
        ),
    ],
)
@patch("resume_editor.app.llm.orchestration.ChatOpenAI")
@patch("resume_editor.app.llm.orchestration._generate_introduction_from_resume")
def test_generate_introduction_from_resume_wrapper(
    mock_private_generate: MagicMock,
    mock_chat_openai: MagicMock,
    llm_config_data: dict,
    expected_llm_params: dict,
):
    """
    Tests that the public wrapper function `generate_introduction_from_resume`
    correctly initializes the LLM client under various configurations.
    """
    # Arrange
    mock_private_generate.return_value = "Generated Intro"
    llm_config = LLMConfig(**llm_config_data)
    resume_content = "some resume"
    job_description = "some job"

    # Act
    result = generate_introduction_from_resume(
        resume_content=resume_content,
        job_description=job_description,
        llm_config=llm_config,
    )

    # Assert
    assert result == "Generated Intro"

    mock_chat_openai.assert_called_once()
    init_kwargs = mock_chat_openai.call_args.kwargs

    # Check model and temperature
    assert init_kwargs["model"] == expected_llm_params["model"]
    assert "temperature" in init_kwargs

    # Check other expected params
    for key, value in expected_llm_params.items():
        if key != "model":
            assert init_kwargs[key] == value

    mock_private_generate.assert_called_once()


@patch("resume_editor.app.llm.orchestration.ChatOpenAI")
def test_generate_introduction_wrapper_raises_openai_error(mock_chat_openai: MagicMock):
    """
    Tests that `generate_introduction_from_resume` raises an OpenAIError if an
    API key is missing for a service that requires it, covering the uncovered branch.
    """
    # Arrange
    # This simulates the error that happens inside ChatOpenAI.__init__ when no key is provided.
    mock_chat_openai.side_effect = OpenAIError("API key is missing.")

    # This config will cause both the `if` and `elif` for `api_key` to be false,
    # as there is no api_key, and the endpoint is for openrouter.ai. This covers
    # the missed branch.
    llm_config = LLMConfig(llm_endpoint="https://openrouter.ai/api/v1")

    # Act & Assert
    with pytest.raises(OpenAIError, match="API key is missing."):
        generate_introduction_from_resume(
            resume_content="some resume",
            job_description="some job",
            llm_config=llm_config,
        )

    # Check that we attempted to initialize ChatOpenAI
    mock_chat_openai.assert_called_once()
    init_kwargs = mock_chat_openai.call_args.kwargs
    # And we did so without providing an api_key, which is what triggers the error.
    assert "api_key" not in init_kwargs
