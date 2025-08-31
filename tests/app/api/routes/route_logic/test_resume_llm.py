from unittest.mock import Mock, patch

import pytest

from resume_editor.app.api.routes.route_logic.resume_llm import (
    _get_section_content,
    refine_resume_section_with_llm,
)
from resume_editor.app.schemas.llm import RefinedSection

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
            f"resume_editor.app.api.routes.route_logic.resume_llm.{extractor}",
        ) as mock_extract,
        patch(
            f"resume_editor.app.api.routes.route_logic.resume_llm.{serializer}",
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


@patch("resume_editor.app.api.routes.route_logic.resume_llm._get_section_content")
def test_refine_resume_section_with_llm_empty_section(mock_get_section):
    """Test that the LLM is not called for an empty resume section."""
    mock_get_section.return_value = "  "
    result = refine_resume_section_with_llm(
        "resume",
        "job desc",
        "personal",
        "http://fake.llm",
        "key",
    )
    assert result == ""
    mock_get_section.assert_called_once_with("resume", "personal")


@patch("resume_editor.app.api.routes.route_logic.resume_llm.ChatOpenAI")
@patch("resume_editor.app.api.routes.route_logic.resume_llm.PromptTemplate")
@patch("resume_editor.app.api.routes.route_logic.resume_llm.PydanticOutputParser")
@patch("resume_editor.app.api.routes.route_logic.resume_llm._get_section_content")
def test_refine_resume_section_pydantic_object(
    mock_get_section,
    mock_parser_class,
    mock_prompt_class,
    mock_llm_class,
):
    """Test LLM refinement when the chain returns a Pydantic object."""
    mock_get_section.return_value = "Some content"
    mock_parser_instance = mock_parser_class.return_value
    mock_llm_instance = mock_llm_class.return_value
    mock_prompt_instance = mock_prompt_class.return_value

    # Mock the chain of |.
    chain_mock = Mock()
    mock_prompt_instance.__or__.return_value.__or__.return_value = chain_mock

    refined_section_obj = RefinedSection(refined_markdown="refined content")
    chain_mock.invoke.return_value = refined_section_obj

    result = refine_resume_section_with_llm(
        "resume",
        "job desc",
        "personal",
        "http://fake.llm",
        "key",
    )

    assert result == "refined content"
    mock_llm_class.assert_called_with(
        model="gpt-4o",
        temperature=0.7,
        openai_api_base="http://fake.llm",
        api_key="key",
    )
    chain_mock.invoke.assert_called_once_with(
        {"job_description": "job desc", "resume_section": "Some content"},
    )


@patch("resume_editor.app.api.routes.route_logic.resume_llm.parse_json_markdown")
@patch("resume_editor.app.api.routes.route_logic.resume_llm.ChatOpenAI")
@patch("resume_editor.app.api.routes.route_logic.resume_llm.PromptTemplate")
@patch("resume_editor.app.api.routes.route_logic.resume_llm.PydanticOutputParser")
@patch("resume_editor.app.api.routes.route_logic.resume_llm._get_section_content")
def test_refine_resume_section_string_return(
    mock_get_section,
    mock_parser_class,
    mock_prompt_class,
    mock_llm_class,
    mock_parse_json,
):
    """Test LLM refinement when the chain returns a string to be parsed."""
    mock_get_section.return_value = "Some content"
    mock_parser_instance = mock_parser_class.return_value
    mock_llm_instance = mock_llm_class.return_value
    mock_prompt_instance = mock_prompt_class.return_value

    chain_mock = Mock()
    mock_prompt_instance.__or__.return_value.__or__.return_value = chain_mock

    chain_mock.invoke.return_value = (
        '```json\n{"refined_markdown": "refined content from string"}\n```'
    )
    mock_parse_json.return_value = {"refined_markdown": "refined content from string"}

    result = refine_resume_section_with_llm(
        "resume",
        "job desc",
        "personal",
        "http://fake.llm",
        "key",
    )

    assert result == "refined content from string"
    mock_parse_json.assert_called_once_with(
        '```json\n{"refined_markdown": "refined content from string"}\n```',
    )
    chain_mock.invoke.assert_called_once()
