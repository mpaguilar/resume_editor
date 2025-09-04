import logging
from unittest.mock import MagicMock, patch

import pytest

from resume_editor.app.llm.orchestration import (
    _get_section_content,
    refine_resume_section_with_llm,
)
from resume_editor.app.llm.models import RefinedSection

FULL_RESUME = """# Personal
name: Test Person

# Education
school: Test University

# Experience
company: Test Company

# Certifications
name: Test Cert
"""


@pytest.mark.parametrize(
    "section_name, extractor, serializer, expected_output",
    [
        (
            "personal",
            "extract_personal_info",
            "serialize_personal_info_to_markdown",
            "personal section",
        ),
        (
            "education",
            "extract_education_info",
            "serialize_education_to_markdown",
            "education section",
        ),
        (
            "experience",
            "extract_experience_info",
            "serialize_experience_to_markdown",
            "experience section",
        ),
        (
            "certifications",
            "extract_certifications_info",
            "serialize_certifications_to_markdown",
            "certifications section",
        ),
    ],
)
def test_get_section_content(section_name, extractor, serializer, expected_output):
    """Test that _get_section_content correctly calls extract and serialize for each section."""
    with (
        patch(
            f"resume_editor.app.llm.orchestration.{extractor}",
        ) as mock_extract,
        patch(
            f"resume_editor.app.llm.orchestration.{serializer}",
            return_value=expected_output,
        ) as mock_serialize,
    ):
        result = _get_section_content(FULL_RESUME, section_name)

        mock_extract.assert_called_once_with(FULL_RESUME)
        mock_serialize.assert_called_once_with(mock_extract.return_value)
        assert result == expected_output


def test_get_section_content_full():
    """Test that _get_section_content returns the full resume for 'full' section."""
    assert _get_section_content(FULL_RESUME, "full") == FULL_RESUME


def test_get_section_content_invalid():
    """Test that _get_section_content raises ValueError for an invalid section."""
    with pytest.raises(ValueError, match="Invalid section name: invalid"):
        _get_section_content(FULL_RESUME, "invalid")


@patch("resume_editor.app.llm.orchestration._get_section_content")
def test_refine_resume_section_with_llm_empty_section(mock_get_section):
    """Test that the LLM is not called for an empty resume section."""
    mock_get_section.return_value = "  "
    result = refine_resume_section_with_llm(
        "resume",
        "job desc",
        "personal",
        "http://fake.llm",
        "key",
        llm_model_name=None,
    )
    assert result == ""
    mock_get_section.assert_called_once_with("resume", "personal")


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

        yield {
            "chat_openai": mock_chat_openai_class,
            "final_chain": final_chain,
            "prompt_template": mock_prompt_template_class,
            "prompt_from_messages": mock_prompt_from_messages,
        }


@pytest.mark.parametrize(
    "llm_endpoint, api_key, llm_model_name, expected_call_args",
    [
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
    ],
)
def test_refine_resume_section_llm_initialization(
    mock_chain_invocations,
    mock_get_section_content,
    llm_endpoint,
    api_key,
    llm_model_name,
    expected_call_args,
):
    """
    Test that ChatOpenAI is initialized with the correct parameters under various conditions.
    """
    result = refine_resume_section_with_llm(
        resume_content="resume",
        job_description="job desc",
        target_section="experience",
        llm_endpoint=llm_endpoint,
        api_key=api_key,
        llm_model_name=llm_model_name,
    )
    mock_chat_openai = mock_chain_invocations["chat_openai"]
    mock_chat_openai.assert_called_once_with(**expected_call_args)
    assert result == "refined content"
    mock_get_section_content.assert_called_once_with("resume", "experience")


def test_refine_resume_section_llm_json_decode_error(
    mock_chain_invocations, mock_get_section_content
):
    """
    Test that a JSONDecodeError from the LLM call is handled gracefully.
    """
    import json

    # Arrange: Get the final chain mock from the fixture
    final_chain = mock_chain_invocations["final_chain"]
    final_chain.invoke.side_effect = json.JSONDecodeError(
        "Expecting value",
        "some invalid json",
        0,
    )

    # Act & Assert
    with pytest.raises(
        ValueError,
        match="The AI service returned an unexpected response. Please try again.",
    ):
        refine_resume_section_with_llm(
            resume_content="resume",
            job_description="job desc",
            target_section="experience",
            llm_endpoint=None,
            api_key=None,
            llm_model_name=None,
        )


def test_refine_resume_section_llm_validation_error(
    mock_chain_invocations, mock_get_section_content
):
    """
    Test that a Pydantic validation error from the LLM call is handled gracefully.
    """
    # Arrange: mock chain to return valid JSON but with wrong schema
    final_chain = mock_chain_invocations["final_chain"]
    final_chain.invoke.return_value = '```json\n{"wrong_field": "wrong_value"}\n```'

    # Act & Assert
    with pytest.raises(
        ValueError,
        match="The AI service returned an unexpected response. Please try again.",
    ):
        refine_resume_section_with_llm(
            resume_content="resume",
            job_description="job desc",
            target_section="experience",
            llm_endpoint=None,
            api_key=None,
            llm_model_name=None,
        )


def test_refine_resume_section_llm_authentication_error(
    mock_chain_invocations, mock_get_section_content
):
    """
    Test that an AuthenticationError from the LLM call is propagated.
    """
    from openai import AuthenticationError

    # Arrange
    final_chain = mock_chain_invocations["final_chain"]
    final_chain.invoke.side_effect = AuthenticationError(
        message="Invalid API key", response=MagicMock(), body=None
    )

    # Act & Assert
    with pytest.raises(AuthenticationError):
        refine_resume_section_with_llm(
            resume_content="resume",
            job_description="job desc",
            target_section="experience",
            llm_endpoint=None,
            api_key=None,
            llm_model_name=None,
        )


@pytest.mark.parametrize(
    "target_section, expect_guidelines",
    [
        ("experience", True),
        ("personal", False),
        ("education", False),
        ("certifications", False),
        ("full", False),
    ],
)
def test_refine_resume_prompt_content(
    target_section,
    expect_guidelines,
    mock_chain_invocations,
    mock_get_section_content,
):
    """
    Test that the prompt is constructed correctly based on the target section.
    """
    # Act
    refine_resume_section_with_llm(
        resume_content="resume",
        job_description="job desc",
        target_section=target_section,
        llm_endpoint=None,
        api_key=None,
        llm_model_name=None,
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
    assert "Stick to the Facts" in system_template

    # Check that placeholders are in the templates
    assert "{goal}" in system_template
    assert "{processing_guidelines}" in system_template
    assert "{job_description}" in human_template
    assert "{resume_section}" in human_template

    # Check the content passed to partial()
    mock_prompt_from_messages.partial.assert_called_once()
    partial_kwargs = mock_prompt_from_messages.partial.call_args.kwargs
    assert "Rephrase and restructure" in partial_kwargs["goal"]

    if expect_guidelines:
        assert "**Processing Guidelines:**" in partial_kwargs["processing_guidelines"]
        assert "For each `### Role`" in partial_kwargs["processing_guidelines"]
    else:
        assert partial_kwargs["processing_guidelines"] == ""
