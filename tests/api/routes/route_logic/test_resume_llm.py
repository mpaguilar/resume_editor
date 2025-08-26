import logging
from unittest.mock import MagicMock, patch

import pytest

from resume_editor.app.api.routes.route_logic.resume_llm import (
    _get_section_content,
    refine_resume_section_with_llm,
)
from resume_editor.app.schemas.llm import RefinedSection

log = logging.getLogger(__name__)


def test_get_section_content_full():
    """Test that _get_section_content returns the full content for 'full' section."""
    content = "# Personal\n\nName: Test\n\n# Experience\n\n## Role\n\nTitle: Dev"
    result = _get_section_content(content, "full")
    assert result == content


@patch("resume_editor.app.api.routes.route_logic.resume_llm.extract_personal_info")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_llm.serialize_personal_info_to_markdown",
)
def test_get_section_content_specific(mock_serializer, mock_extractor):
    """Test that _get_section_content calls correct extractor and serializer."""
    mock_extractor.return_value = {"name": "Test"}
    mock_serializer.return_value = "# Personal\nName: Test"
    resume_content = "some markdown"
    section_name = "personal"

    result = _get_section_content(resume_content, section_name)

    mock_extractor.assert_called_once_with(resume_content)
    mock_serializer.assert_called_once_with({"name": "Test"})
    assert result == "# Personal\nName: Test"


def test_get_section_content_invalid():
    """Test that _get_section_content raises ValueError for invalid section."""
    with pytest.raises(ValueError):
        _get_section_content("some content", "invalid_section")


@patch("resume_editor.app.api.routes.route_logic.resume_llm.PydanticOutputParser")
@patch("resume_editor.app.api.routes.route_logic.resume_llm.ChatOpenAI")
@patch("resume_editor.app.api.routes.route_logic.resume_llm.PromptTemplate")
@patch("resume_editor.app.api.routes.route_logic.resume_llm._get_section_content")
def test_refine_resume_section_with_llm_success(
    mock_get_section_content,
    mock_prompt_template,
    mock_chat_openai,
    mock_pydantic_parser,
):
    """Test successful refinement of a resume section using LLM."""
    mock_get_section_content.return_value = "## Experience\n\nSome experience details."

    # Setup mocks for the chain components
    mock_prompt_instance = MagicMock()
    mock_llm_instance = MagicMock()
    mock_parser_instance = MagicMock()
    mock_prompt_template.return_value = mock_prompt_instance
    mock_chat_openai.return_value = mock_llm_instance
    mock_pydantic_parser.return_value = mock_parser_instance

    # Mock the chaining `|` behavior
    mock_chain_after_prompt = MagicMock()
    mock_prompt_instance.__or__.return_value = mock_chain_after_prompt
    mock_chain_after_llm = MagicMock()
    mock_chain_after_prompt.__or__.return_value = mock_chain_after_llm

    # Mock the final `invoke` call
    mock_refined_output = RefinedSection(
        refined_markdown="## Experience\n\nRefined experience details.",
    )
    mock_chain_after_llm.invoke.return_value = mock_refined_output

    # Call the function
    result = refine_resume_section_with_llm(
        resume_content="Original content.",
        job_description="A job.",
        target_section="experience",
        llm_endpoint="http://localhost:8080",
        api_key="test_key",
    )

    # Assertions
    mock_get_section_content.assert_called_once_with("Original content.", "experience")
    mock_chat_openai.assert_called_once_with(
        model="gpt-4o",
        temperature=0.7,
        openai_api_base="http://localhost:8080",
        api_key="test_key",
    )
    mock_chain_after_llm.invoke.assert_called_once_with(
        {
            "job_description": "A job.",
            "resume_section": "## Experience\n\nSome experience details.",
        },
    )
    assert result == "## Experience\n\nRefined experience details."


@patch("resume_editor.app.api.routes.route_logic.resume_llm._get_section_content")
def test_refine_resume_section_with_llm_empty_section(mock_get_section_content):
    """Test that refinement is skipped for an empty resume section."""
    mock_get_section_content.return_value = "   "

    with patch(
        "resume_editor.app.api.routes.route_logic.resume_llm.ChatOpenAI",
    ) as mock_chat_openai:
        result = refine_resume_section_with_llm(
            resume_content="Original content.",
            job_description="A job.",
            target_section="experience",
            llm_endpoint=None,
            api_key=None,
        )

        assert result == ""
        mock_chat_openai.assert_not_called()


@patch("resume_editor.app.api.routes.route_logic.resume_llm.PydanticOutputParser")
@patch("resume_editor.app.api.routes.route_logic.resume_llm.ChatOpenAI")
@patch("resume_editor.app.api.routes.route_logic.resume_llm.PromptTemplate")
@patch("resume_editor.app.api.routes.route_logic.resume_llm._get_section_content")
def test_refine_resume_section_with_llm_returns_string(
    mock_get_section_content,
    mock_prompt_template,
    mock_chat_openai,
    mock_pydantic_parser,
):
    """Test refinement when LLM returns a JSON string to be parsed."""
    mock_get_section_content.return_value = "## Experience\n\nSome experience details."

    # Setup mocks
    mock_prompt_instance = MagicMock()
    mock_llm_instance = MagicMock()
    mock_parser_instance = MagicMock()
    mock_prompt_template.return_value = mock_prompt_instance
    mock_chat_openai.return_value = mock_llm_instance
    mock_pydantic_parser.return_value = mock_parser_instance

    mock_chain_after_prompt = MagicMock()
    mock_prompt_instance.__or__.return_value = mock_chain_after_prompt
    mock_chain_after_llm = MagicMock()
    mock_chain_after_prompt.__or__.return_value = mock_chain_after_llm

    # Mock invoke to return a string instead of a pydantic object
    llm_output_str = '```json\n{"refined_markdown": "Refined from string"}\n```'
    mock_chain_after_llm.invoke.return_value = llm_output_str

    # Call the function
    result = refine_resume_section_with_llm(
        resume_content="Original content.",
        job_description="A job.",
        target_section="experience",
        llm_endpoint=None,
        api_key=None,
    )

    # Assertions
    assert result == "Refined from string"
    mock_chain_after_llm.invoke.assert_called_once()
