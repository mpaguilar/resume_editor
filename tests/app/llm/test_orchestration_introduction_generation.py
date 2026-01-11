import json
import logging
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from pydantic import ValidationError

from resume_editor.app.llm.models import (
    CandidateAnalysis,
    GeneratedIntroduction,
    JobKeyRequirements,
    LLMConfig,
)
from resume_editor.app.llm.orchestration import (
    _generate_introduction_from_analysis,
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
            '{"strengths": ["Strength 1", "Strength 2"]}',
            GeneratedIntroduction,
            GeneratedIntroduction(strengths=["Strength 1", "Strength 2"]),
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
def test_generate_introduction_from_analysis_success(
    mock_invoke_chain_and_parse,
    mock_llm_sync,
    resume_content_fixture,
):
    """Test _generate_introduction_from_analysis successfully generates an introduction."""
    _msg = "test_generate_introduction_from_analysis_success starting"
    log.debug(_msg)

    job_analysis_json = '{"key_skills": ["Python"], "candidate_priorities": ["Backend"]}'
    mock_invoke_chain_and_parse.side_effect = [
        CandidateAnalysis(
            skill_summary={
                "python": {"assessment": "strong experience", "source": ["Work"]}
            }
        ),
        GeneratedIntroduction(strengths=["Expert in Python", "Loves backend work"]),
    ]

    introduction = _generate_introduction_from_analysis(
        job_analysis_json=job_analysis_json,
        resume_content=resume_content_fixture,
        llm=mock_llm_sync,
    )

    assert introduction == "- Expert in Python\n- Loves backend work"
    assert mock_invoke_chain_and_parse.call_count == 2

    # Check call arguments for resume analysis
    resume_analysis_call = mock_invoke_chain_and_parse.call_args_list[0]
    assert resume_analysis_call.args[1] == CandidateAnalysis
    assert resume_analysis_call.kwargs["resume_content"] == resume_content_fixture
    assert resume_analysis_call.kwargs["job_requirements"] == job_analysis_json

    # Check call arguments for synthesis
    synthesis_call = mock_invoke_chain_and_parse.call_args_list[1]
    assert synthesis_call.args[1] == GeneratedIntroduction
    assert "candidate_analysis" in synthesis_call.kwargs

    _msg = "test_generate_introduction_from_analysis_success returning"
    log.debug(_msg)


@patch(
    "resume_editor.app.llm.orchestration._invoke_chain_and_parse",
    new_callable=MagicMock,
)
def test_generate_introduction_from_analysis_failure(
    mock_invoke_chain_and_parse,
    mock_llm_sync,
    resume_content_fixture,
):
    """Test _generate_introduction_from_analysis handles exceptions."""
    _msg = "test_generate_introduction_from_analysis_failure starting"
    log.debug(_msg)

    job_analysis_json = '{"key_skills": ["Python"]}'
    mock_invoke_chain_and_parse.side_effect = ValueError("test error")

    introduction = _generate_introduction_from_analysis(
        job_analysis_json=job_analysis_json,
        resume_content=resume_content_fixture,
        llm=mock_llm_sync,
    )

    assert introduction == ""
    mock_invoke_chain_and_parse.assert_called_once()

    _msg = "test_generate_introduction_from_analysis_failure returning"
    log.debug(_msg)


@patch("resume_editor.app.llm.orchestration._initialize_llm_client")
def test_generate_introduction_from_resume_end_to_end_mocked(
    mock_init_llm,
    llm_config_fixture,
    resume_content_fixture,
    job_description_fixture,
):
    """Test generate_introduction_from_resume end-to-end with mocked LLM calls."""
    _msg = "test_generate_introduction_from_resume_end_to_end_mocked starting"
    log.debug(_msg)

    mock_llm_sync = MagicMock(spec=ChatOpenAI)
    mock_init_llm.return_value = mock_llm_sync

    # Setup side effects for the three LLM calls
    mock_llm_sync.invoke.side_effect = [
        # 1. Job Analysis call (for JobKeyRequirements)
        AIMessage(
            content='```json\n{"key_skills": ["Python", "FastAPI"], "candidate_priorities": ["Backend"]}\n```'
        ),
        # 2. Resume Analysis call (for CandidateAnalysis)
        AIMessage(
            content='```json\n{"skill_summary": {"python": {"assessment": "strong experience", "source": ["Work"]}}}\n```'
        ),
        # 3. Synthesis call (for GeneratedIntroduction)
        AIMessage(
            content='```json\n{"strengths": ["Expert in Python", "Great with FastAPI"]}\n```'
        ),
    ]

    result = generate_introduction_from_resume(
        resume_content=resume_content_fixture,
        job_description=job_description_fixture,
        llm_config=llm_config_fixture,
    )

    assert result == "- Expert in Python\n- Great with FastAPI"
    assert mock_init_llm.call_count == 1
    assert mock_llm_sync.invoke.call_count == 3

    _msg = "test_generate_introduction_from_resume_end_to_end_mocked returning"
    log.debug(_msg)


@patch("resume_editor.app.llm.orchestration._initialize_llm_client")
@patch("resume_editor.app.llm.orchestration._generate_introduction_from_analysis")
@patch("resume_editor.app.llm.orchestration._invoke_chain_and_parse")
def test_generate_introduction_from_resume_success(
    mock_invoke_chain,
    mock_internal_generate,
    mock_init_llm,
    llm_config_fixture,
    resume_content_fixture,
    job_description_fixture,
):
    """Test generate_introduction_from_resume orchestrates calls and returns result."""
    _msg = "test_generate_introduction_from_resume_success starting"
    log.debug(_msg)

    # Mock the return values of the dependencies
    mock_invoke_chain.return_value = JobKeyRequirements(
        key_skills=["Python"], candidate_priorities=["Backend"]
    )
    mock_internal_generate.return_value = "This is a generated introduction."

    # Call the function under test
    result = generate_introduction_from_resume(
        resume_content=resume_content_fixture,
        job_description=job_description_fixture,
        llm_config=llm_config_fixture,
    )

    # Assert the final result
    assert result == "This is a generated introduction."

    # Assert that dependencies were called correctly
    mock_init_llm.assert_called_once_with(llm_config_fixture)
    mock_invoke_chain.assert_called_once()
    # Can't easily check chain object, so use ANY
    assert mock_invoke_chain.call_args.args[1] == JobKeyRequirements
    assert (
        mock_invoke_chain.call_args.kwargs["job_description"]
        == job_description_fixture
    )

    mock_internal_generate.assert_called_once()
    assert (
        mock_internal_generate.call_args.kwargs["resume_content"]
        == resume_content_fixture
    )
    assert "job_analysis_json" in mock_internal_generate.call_args.kwargs

    _msg = "test_generate_introduction_from_resume_success returning"
    log.debug(_msg)


@patch("resume_editor.app.llm.orchestration._initialize_llm_client")
@patch("resume_editor.app.llm.orchestration._invoke_chain_and_parse")
@patch("resume_editor.app.llm.orchestration._generate_introduction_from_analysis")
def test_generate_introduction_from_resume_job_analysis_fails(
    mock_generate_from_analysis,
    mock_invoke_chain_and_parse,
    mock_init_llm,
    llm_config_fixture,
    resume_content_fixture,
    job_description_fixture,
):
    """Test generate_introduction_from_resume returns empty on job analysis failure."""
    _msg = "test_generate_introduction_from_resume_job_analysis_fails starting"
    log.debug(_msg)

    mock_invoke_chain_and_parse.side_effect = json.JSONDecodeError("err", "doc", 0)

    result = generate_introduction_from_resume(
        resume_content=resume_content_fixture,
        job_description=job_description_fixture,
        llm_config=llm_config_fixture,
    )

    assert result == ""
    mock_init_llm.assert_called_once_with(llm_config_fixture)
    mock_invoke_chain_and_parse.assert_called_once()
    mock_generate_from_analysis.assert_not_called()

    _msg = "test_generate_introduction_from_resume_job_analysis_fails returning"
    log.debug(_msg)


