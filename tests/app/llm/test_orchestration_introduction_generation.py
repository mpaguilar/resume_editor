import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage
from pydantic import ValidationError

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

log = logging.getLogger(__name__)


@pytest.fixture
def mock_llm():
    """Fixture for a mock ChatOpenAI instance."""
    mock = MagicMock(spec=AIMessage)
    mock.ainvoke = AsyncMock()
    return mock


@pytest.fixture
def mock_llm_sync():
    """Fixture for a synchronous mock ChatOpenAI instance."""
    mock = MagicMock()
    mock.invoke = MagicMock()
    return mock


@pytest.fixture
def llm_config_fixture():
    """Fixture for a sample LLMConfig."""
    return LLMConfig(
        llm_endpoint="http://localhost:8000/v1",
        api_key="test_api_key",
        llm_model_name="test_model",
    )


@pytest.fixture
def resume_content_fixture():
    """Fixture for sample resume content."""
    return "## Experience\n- Job 1\n## Education\n- Degree 1"


@pytest.fixture
def job_description_fixture():
    """Fixture for sample job description."""
    return "Software Engineer with Python experience."


@pytest.mark.parametrize(
    "mock_result_content, pydantic_model, expected_result",
    [
        (
            '{"key_skills": ["Python", "FastAPI"], "candidate_priorities": ["Backend"]}',
            JobKeyRequirements,
            JobKeyRequirements(key_skills=["Python", "FastAPI"], candidate_priorities=["Backend"]),
        ),
        (
            '{"skill_summary": {"python": {"assessment": "strong experience", "source": ["Work"]}}}',
            CandidateAnalysis,
            CandidateAnalysis(
                skill_summary={
                    "python": {"assessment": "strong experience", "source": ["Work"]}
                }
            ),
        ),
        (
            '{"introduction": "Hello world"}',
            GeneratedIntroduction,
            GeneratedIntroduction(introduction="Hello world"),
        ),
    ],
)
def test_invoke_chain_and_parse_success(
    mock_llm_sync,
    mock_result_content,
    pydantic_model,
    expected_result,
):
    """Test _invoke_chain_and_parse successfully parses and validates."""
    _msg = "test_invoke_chain_and_parse_success starting"
    log.debug(_msg)

    mock_llm_sync.invoke.return_value = MagicMock(content=mock_result_content)
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = mock_llm_sync.invoke.return_value

    result = _invoke_chain_and_parse(mock_chain, pydantic_model)

    assert result == expected_result
    mock_chain.invoke.assert_called_once()

    _msg = "test_invoke_chain_and_parse_success returning"
    log.debug(_msg)


@pytest.mark.parametrize(
    "mock_result_content, pydantic_model, expected_exception",
    [
        (
            '{"invalid_field": "value"}',
            JobKeyRequirements,
            ValidationError,
        ),  # Invalid JSON structure
        (
            "not valid json",
            JobKeyRequirements,
            json.JSONDecodeError,
        ),  # Malformed JSON
    ],
)
def test_invoke_chain_and_parse_failure(
    mock_llm_sync,
    mock_result_content,
    pydantic_model,
    expected_exception,
):
    """Test _invoke_chain_and_parse handles parsing and validation errors."""
    _msg = "test_invoke_chain_and_parse_failure starting"
    log.debug(_msg)

    mock_llm_sync.invoke.return_value = MagicMock(content=mock_result_content)
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = mock_llm_sync.invoke.return_value

    with pytest.raises(expected_exception):
        _invoke_chain_and_parse(mock_chain, pydantic_model)

    _msg = "test_invoke_chain_and_parse_failure returning"
    log.debug(_msg)


@patch(
    "resume_editor.app.llm.orchestration._invoke_chain_and_parse",
    new_callable=MagicMock,
)
def test_generate_introduction_from_resume_success(
    mock_invoke_chain_and_parse,
    mock_llm_sync,
    resume_content_fixture,
    job_description_fixture,
):
    """Test _generate_introduction_from_resume successfully generates an introduction."""
    _msg = "test_generate_introduction_from_resume_success starting"
    log.debug(_msg)

    mock_invoke_chain_and_parse.side_effect = [
        JobKeyRequirements(key_skills=["Python"], candidate_priorities=["Backend"]),
        CandidateAnalysis(
            skill_summary={
                "python": {"assessment": "strong experience", "source": ["Work"]}
            }
        ),
        GeneratedIntroduction(introduction="A great introduction."),
    ]

    introduction = _generate_introduction_from_resume(
        resume_content=resume_content_fixture,
        job_description=job_description_fixture,
        llm=mock_llm_sync,
    )

    assert introduction == "A great introduction."
    assert mock_invoke_chain_and_parse.call_count == 3

    _msg = "test_generate_introduction_from_resume_success returning"
    log.debug(_msg)


@patch(
    "resume_editor.app.llm.orchestration._invoke_chain_and_parse",
    new_callable=MagicMock,
)
def test_generate_introduction_from_resume_json_decode_error(
    mock_invoke_chain_and_parse,
    mock_llm_sync,
    resume_content_fixture,
    job_description_fixture,
):
    """Test _generate_introduction_from_resume handles JSONDecodeError."""
    _msg = "test_generate_introduction_from_resume_json_decode_error starting"
    log.debug(_msg)

    mock_invoke_chain_and_parse.side_effect = json.JSONDecodeError("test error", "{}", 0)

    introduction = _generate_introduction_from_resume(
        resume_content=resume_content_fixture,
        job_description=job_description_fixture,
        llm=mock_llm_sync,
    )

    assert introduction == ""
    assert mock_invoke_chain_and_parse.call_count == 1

    _msg = "test_generate_introduction_from_resume_json_decode_error returning"
    log.debug(_msg)


@patch(
    "resume_editor.app.llm.orchestration._invoke_chain_and_parse",
    new_callable=MagicMock,
)
def test_generate_introduction_from_resume_validation_error(
    mock_invoke_chain_and_parse,
    mock_llm_sync,
    resume_content_fixture,
    job_description_fixture,
):
    """Test _generate_introduction_from_resume handles ValidationError."""
    _msg = "test_generate_introduction_from_resume_validation_error starting"
    log.debug(_msg)

    # Simulate a ValidationError being raised during the second step (Resume Analysis)
    mock_invoke_chain_and_parse.side_effect = [
        JobKeyRequirements(key_skills=["Python"], candidate_priorities=["Backend"]),
        ValidationError.from_exception_data(
            "CandidateAnalysis",
            [{"loc": ("skill_summary", "python", "source"), "msg": "Input should be a valid list", "type": "list_type"}],
        ),
    ]

    introduction = _generate_introduction_from_resume(
        resume_content=resume_content_fixture,
        job_description=job_description_fixture,
        llm=mock_llm_sync,
    )

    assert introduction == ""
    assert mock_invoke_chain_and_parse.call_count == 2

    _msg = "test_generate_introduction_from_resume_validation_error returning"
    log.debug(_msg)


@patch(
    "resume_editor.app.llm.orchestration._invoke_chain_and_parse",
    new_callable=MagicMock,
)
def test_generate_introduction_from_resume_value_error(
    mock_invoke_chain_and_parse,
    mock_llm_sync,
    resume_content_fixture,
    job_description_fixture,
):
    """Test _generate_introduction_from_resume handles generic ValueError."""
    _msg = "test_generate_introduction_from_resume_value_error starting"
    log.debug(_msg)

    mock_invoke_chain_and_parse.side_effect = ValueError("Something went wrong")

    introduction = _generate_introduction_from_resume(
        resume_content=resume_content_fixture,
        job_description=job_description_fixture,
        llm=mock_llm_sync,
    )

    assert introduction == ""
    assert mock_invoke_chain_and_parse.call_count == 1

    _msg = "test_generate_introduction_from_resume_value_error returning"
    log.debug(_msg)


@patch("resume_editor.app.llm.orchestration.ChatOpenAI", autospec=True)
@patch("resume_editor.app.llm.orchestration._generate_introduction_from_resume")
def test_generate_introduction_from_resume_llm_init(
    mock_internal_generate,
    mock_chat_openai,
    llm_config_fixture,
    resume_content_fixture,
    job_description_fixture,
):
    """Test generate_introduction_from_resume initializes LLM correctly."""
    _msg = "test_generate_introduction_from_resume_llm_init starting"
    log.debug(_msg)

    mock_internal_generate.return_value = "Generated intro"

    generate_introduction_from_resume(
        resume_content=resume_content_fixture,
        job_description=job_description_fixture,
        llm_config=llm_config_fixture,
    )

    mock_chat_openai.assert_called_once_with(
        model="test_model",
        temperature=0.2,
        openai_api_base="http://localhost:8000/v1",
        api_key="test_api_key",
    )
    mock_internal_generate.assert_called_once()

    _msg = "test_generate_introduction_from_resume_llm_init returning"
    log.debug(_msg)


@patch("resume_editor.app.llm.orchestration.ChatOpenAI", autospec=True)
@patch("resume_editor.app.llm.orchestration._generate_introduction_from_resume")
def test_generate_introduction_from_resume_llm_init_no_api_key_custom_endpoint(
    mock_internal_generate,
    mock_chat_openai,
    llm_config_fixture,
    resume_content_fixture,
    job_description_fixture,
):
    """Test LLM init when custom endpoint but no API key (should use 'not-needed')."""
    _msg = "test_generate_introduction_from_resume_llm_init_no_api_key_custom_endpoint starting"
    log.debug(_msg)

    llm_config_fixture.api_key = None
    mock_internal_generate.return_value = "Generated intro"

    generate_introduction_from_resume(
        resume_content=resume_content_fixture,
        job_description=job_description_fixture,
        llm_config=llm_config_fixture,
    )

    mock_chat_openai.assert_called_once_with(
        model="test_model",
        temperature=0.2,
        openai_api_base="http://localhost:8000/v1",
        api_key="not-needed",
    )
    mock_internal_generate.assert_called_once()

    _msg = "test_generate_introduction_from_resume_llm_init_no_api_key_custom_endpoint returning"
    log.debug(_msg)


@patch("resume_editor.app.llm.orchestration.ChatOpenAI", autospec=True)
@patch("resume_editor.app.llm.orchestration._generate_introduction_from_resume")
def test_generate_introduction_from_resume_llm_init_openrouter_endpoint(
    mock_internal_generate,
    mock_chat_openai,
    llm_config_fixture,
    resume_content_fixture,
    job_description_fixture,
):
    """Test LLM init when OpenRouter endpoint is used (should add default_headers)."""
    _msg = "test_generate_introduction_from_resume_llm_init_openrouter_endpoint starting"
    log.debug(_msg)

    llm_config_fixture.llm_endpoint = "https://openrouter.ai/api/v1"
    llm_config_fixture.api_key = "or_test_key"
    mock_internal_generate.return_value = "Generated intro"

    generate_introduction_from_resume(
        resume_content=resume_content_fixture,
        job_description=job_description_fixture,
        llm_config=llm_config_fixture,
    )

    mock_chat_openai.assert_called_once_with(
        model="test_model",
        temperature=0.2,
        openai_api_base="https://openrouter.ai/api/v1",
        api_key="or_test_key",
        default_headers={
            "HTTP-Referer": "http://localhost:8000/",
            "X-Title": "Resume Editor",
        },
    )
    mock_internal_generate.assert_called_once()

    _msg = "test_generate_introduction_from_resume_llm_init_openrouter_endpoint returning"
    log.debug(_msg)


@patch("resume_editor.app.llm.orchestration.ChatOpenAI", autospec=True)
@patch("resume_editor.app.llm.orchestration._generate_introduction_from_resume")
def test_generate_introduction_from_resume_llm_init_no_endpoint_no_api_key(
    mock_internal_generate,
    mock_chat_openai,
    llm_config_fixture,
    resume_content_fixture,
    job_description_fixture,
):
    """Test LLM init when no custom endpoint and no API key (should use default OpenAI)."""
    _msg = "test_generate_introduction_from_resume_llm_init_no_endpoint_no_api_key starting"
    log.debug(_msg)

    llm_config_fixture.llm_endpoint = None
    llm_config_fixture.api_key = None
    llm_config_fixture.llm_model_name = None  # Use default model name
    mock_internal_generate.return_value = "Generated intro"

    generate_introduction_from_resume(
        resume_content=resume_content_fixture,
        job_description=job_description_fixture,
        llm_config=llm_config_fixture,
    )

    mock_chat_openai.assert_called_once_with(
        model="gpt-4o",  # Default model
        temperature=0.2,
    )
    mock_internal_generate.assert_called_once()

    _msg = "test_generate_introduction_from_resume_llm_init_no_endpoint_no_api_key returning"
    log.debug(_msg)
