from unittest.mock import MagicMock, patch

import pytest
from openai import AuthenticationError

from resume_editor.app.llm.models import LLMConfig
from resume_editor.app.llm.orchestration import (
    DEFAULT_LLM_TEMPERATURE,
    _refine_generic_section,
    refine_resume_section_with_llm,
)

LLM_INIT_PARAMS = [
    # Case 1: Endpoint, API key, and model name provided
    (
        "http://fake.llm",
        "key",
        "custom-model",
        {
            "model": "custom-model",
            "temperature": DEFAULT_LLM_TEMPERATURE,
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
            "temperature": DEFAULT_LLM_TEMPERATURE,
            "openai_api_base": "http://fake.llm",
            "api_key": "not-needed",
        },
    ),
    # Case 3: API key and model name, but no endpoint
    (
        None,
        "key",
        "custom-model",
        {"model": "custom-model", "temperature": DEFAULT_LLM_TEMPERATURE, "api_key": "key"},
    ),
    # Case 4: No endpoint, no API key (relies on env var)
    (
        None,
        None,
        "custom-model",
        {"model": "custom-model", "temperature": DEFAULT_LLM_TEMPERATURE},
    ),
    # Case 5: Fallback to default model name when None is provided
    (
        "http://fake.llm",
        "key",
        None,
        {
            "model": "gpt-4o",
            "temperature": DEFAULT_LLM_TEMPERATURE,
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
            "temperature": DEFAULT_LLM_TEMPERATURE,
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
            "temperature": DEFAULT_LLM_TEMPERATURE,
            "openai_api_base": "https://openrouter.ai/api/v1",
            "api_key": "or-key",
            "default_headers": {
                "HTTP-Referer": "http://localhost:8000/",
                "X-Title": "Resume Editor",
            },
        },
    ),
]


@pytest.fixture
def mock_get_section_content():
    """Fixture to mock _get_section_content."""
    with patch(
        "resume_editor.app.llm.orchestration._get_section_content"
    ) as mock:
        mock.return_value = "some resume section"
        yield mock


@pytest.fixture
def mock_chain_invocations():
    """
    Fixture to mock the entire LangChain chain invocation process.
    It patches the key components and mocks the `|` operator to
    ensure the final `chain.invoke` call returns a valid object.
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

        # The final invoke should return a string, not a RefinedSection object
        final_chain.invoke.return_value = (
            '```json\n{"refined_markdown": "refined content"}\n```'
        )
        # Stream should return an iterator yielding string chunks
        final_chain.stream.return_value = iter(
            ['```json\n{"refined_markdown": "refined content"}\n```']
        )

        yield {
            "chat_openai": mock_chat_openai_class,
            "final_chain": final_chain,
            "prompt_template": mock_prompt_template_class,
            "prompt_from_messages": mock_prompt_from_messages,
        }


@patch("resume_editor.app.llm.orchestration._get_section_content")
def test_refine_generic_section_empty_section(mock_get_section):
    """Test that the LLM is not called for an empty resume section."""
    mock_get_section.return_value = "  "
    # We pass a mock LLM because the function being tested doesn't create one.
    mock_llm = MagicMock()
    result_content = _refine_generic_section(
        "resume", "job desc", "personal", llm=mock_llm
    )
    assert result_content == ""
    mock_get_section.assert_called_once_with("resume", "personal")
    # The LLM's chain should not be invoked.
    mock_llm.stream.assert_not_called()


def test_refine_resume_section_with_llm_dispatcher():
    """Test that the refine_resume_section_with_llm dispatcher calls the correct helper."""
    with patch(
        "resume_editor.app.llm.orchestration._refine_generic_section"
    ) as mock_refine_generic, patch(
        "resume_editor.app.llm.orchestration.ChatOpenAI"
    ) as mock_chat_openai_class:
        mock_refine_generic.return_value = "refined content from helper"
        result_content = refine_resume_section_with_llm(
            resume_content="resume",
            job_description="job desc",
            target_section="personal",
            llm_config=LLMConfig(),
        )
        assert result_content == "refined content from helper"
        mock_chat_openai_class.assert_called_once()
        mock_refine_generic.assert_called_once()
        assert "generate_introduction" not in mock_refine_generic.call_args.kwargs


@pytest.mark.parametrize("llm_endpoint, api_key, llm_model_name, expected_call_args", LLM_INIT_PARAMS)
def test_refine_resume_section_with_llm_initialization(
    llm_endpoint,
    api_key,
    llm_model_name,
    expected_call_args,
):
    """
    Test that ChatOpenAI is initialized with the correct parameters under various conditions
    and that the helper function is called.
    """
    with patch(
        "resume_editor.app.llm.orchestration._refine_generic_section"
    ) as mock_refine_helper, patch(
        "resume_editor.app.llm.orchestration.ChatOpenAI"
    ) as mock_chat_openai_class:
        # Mock the LLM object that will be created
        mock_llm_instance = MagicMock()
        mock_chat_openai_class.return_value = mock_llm_instance
        mock_refine_helper.return_value = "refined"

        refine_resume_section_with_llm(
            resume_content="resume",
            job_description="job desc",
            target_section="personal",
            llm_config=LLMConfig(
                llm_endpoint=llm_endpoint,
                api_key=api_key,
                llm_model_name=llm_model_name,
            ),
        )

        # Assert ChatOpenAI was initialized correctly
        mock_chat_openai_class.assert_called_once_with(**expected_call_args)

        # Assert helper was called with the created LLM instance
        mock_refine_helper.assert_called_once_with(
            resume_content="resume",
            job_description="job desc",
            target_section="personal",
            llm=mock_llm_instance,
        )


def test_refine_resume_section_with_llm_experience_raises_error():
    """
    Test that refine_resume_section_with_llm raises an error for 'experience' section.
    """
    with pytest.raises(
        ValueError,
        match="Experience section refinement must be called via the async 'refine_experience_section' method.",
    ):
        refine_resume_section_with_llm(
            resume_content="resume",
            job_description="job desc",
            target_section="experience",
            llm_config=LLMConfig(),
        )


def test_refine_generic_section_json_decode_error(
    mock_chain_invocations, mock_get_section_content
):
    """
    Test that _refine_generic_section handles a JSONDecodeError from manual parsing.
    """
    # Arrange
    final_chain = mock_chain_invocations["final_chain"]
    # The stream will return invalid JSON, causing parse_json_markdown to fail.
    final_chain.stream.return_value = iter(["not valid json"])
    mock_llm = mock_chain_invocations["chat_openai"].return_value

    # Act & Assert
    with pytest.raises(
        ValueError,
        match="The AI service returned an unexpected response. Please try again.",
    ):
        _refine_generic_section(
            resume_content="resume",
            job_description="job desc",
            target_section="personal",
            llm=mock_llm,
        )


@pytest.mark.parametrize(
    "target_section, expect_guidelines",
    [
        ("personal", False),
        ("education", False),
        ("certifications", False),
        ("full", False),
    ],
)
def test_refine_generic_section_prompt_content(
    target_section,
    expect_guidelines,
    mock_chain_invocations,
    mock_get_section_content,
):
    """
    Test that the prompt for _refine_generic_section is constructed correctly.
    """
    # Arrange
    mock_llm = mock_chain_invocations["chat_openai"].return_value

    # Act
    _refine_generic_section(
        resume_content="resume",
        job_description="job desc",
        target_section=target_section,
        llm=mock_llm,
    )

    # Assert
    mock_prompt_template = mock_chain_invocations["prompt_template"]
    mock_prompt_from_messages = mock_chain_invocations["prompt_from_messages"]

    # Check that from_messages was called with system and human templates
    mock_prompt_template.from_messages.assert_called_once()
    messages = mock_prompt_template.from_messages.call_args.args[0]
    assert messages[0][0] == "system"
    assert messages[1][0] == "human"

    system_template = messages[0][1]
    human_template = messages[1][1]

    # Check that crucial rules and spec are always in the system template
    assert "MARKDOWN RESUME SPECIFICATION EXAMPLE" in system_template
    assert "Rephrase and Re-contextualize, Do Not Invent" in system_template

    # Check that placeholders are in the templates
    assert "{goal}" in system_template
    assert "{processing_guidelines}" in system_template
    assert "{job_description}" in human_template
    assert "{resume_section}" in human_template

    # Check the content passed to partial()
    mock_prompt_from_messages.partial.assert_called_once()
    partial_kwargs = mock_prompt_from_messages.partial.call_args.kwargs
    assert "Rephrase and restructure" in partial_kwargs["goal"]
    assert "Additionally, write a brief" not in partial_kwargs["goal"]

    if expect_guidelines:
        assert "**Processing Guidelines:**" in partial_kwargs["processing_guidelines"]
        assert "For each `### Role`" in partial_kwargs["processing_guidelines"]
    else:
        assert partial_kwargs["processing_guidelines"] == ""


def test_refine_generic_section_authentication_error(
    mock_chain_invocations, mock_get_section_content
):
    """
    Test that _refine_generic_section propagates an AuthenticationError from the LLM call.
    """
    # Arrange
    final_chain = mock_chain_invocations["final_chain"]
    final_chain.stream.side_effect = AuthenticationError(
        message="Invalid API key", response=MagicMock(), body=None
    )
    mock_llm = mock_chain_invocations["chat_openai"].return_value

    # Act & Assert
    with pytest.raises(AuthenticationError):
        _refine_generic_section(
            resume_content="resume",
            job_description="job desc",
            target_section="personal",
            llm=mock_llm,
        )


def test_refine_generic_section_validation_error(
    mock_chain_invocations, mock_get_section_content
):
    """
    Test that _refine_generic_section handles a Pydantic validation error gracefully.
    """
    # Arrange
    final_chain = mock_chain_invocations["final_chain"]
    final_chain.stream.return_value = iter(
        ['```json\n{"wrong_field": "wrong_value"}\n```']
    )
    mock_llm = mock_chain_invocations["chat_openai"].return_value

    # Act & Assert
    with pytest.raises(
        ValueError,
        match="The AI service returned an unexpected response. Please try again.",
    ):
        _refine_generic_section(
            resume_content="resume",
            job_description="job desc",
            target_section="personal",
            llm=mock_llm,
        )
