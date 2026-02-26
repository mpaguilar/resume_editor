"""Tests for orchestration_analysis module."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from resume_editor.app.llm.models import JobAnalysis
from resume_editor.app.llm.orchestration_analysis import (
    _parse_job_analysis_response,
    analyze_job_description,
)


def test_parse_job_analysis_response_valid():
    """Test parsing valid job analysis response."""
    mock_job_analysis = Mock()
    mock_job_analysis.model_validate.return_value = Mock(spec=JobAnalysis)

    with patch(
        "resume_editor.app.llm.orchestration_analysis.parse_json_markdown"
    ) as mock_parse:
        with patch(
            "resume_editor.app.llm.orchestration_analysis.JobAnalysis"
        ) as mock_model:
            mock_parse.return_value = {"key": "value"}
            mock_model.model_validate.return_value = Mock(spec=JobAnalysis)
            result = _parse_job_analysis_response('{"key": "value"}')
            assert result is not None


def test_parse_job_analysis_response_invalid_json():
    """Test parsing invalid JSON raises ValueError."""
    with pytest.raises(ValueError, match="unexpected response"):
        _parse_job_analysis_response("invalid json")


@pytest.mark.asyncio
async def test_analyze_job_description_empty():
    """Test analyze_job_description raises ValueError for empty input."""
    with pytest.raises(ValueError, match="cannot be empty"):
        await analyze_job_description("", Mock(), "resume content")


@pytest.mark.asyncio
async def test_analyze_job_description_success():
    """Test successful job analysis."""
    mock_config = Mock()
    mock_llm = Mock()
    mock_response = '{"key_skills": ["python"], "themes": ["backend"]}'

    with patch(
        "resume_editor.app.llm.orchestration_analysis.initialize_llm_client"
    ) as mock_init:
        with patch(
            "resume_editor.app.llm.orchestration_analysis._parse_job_analysis_response"
        ) as mock_parse:
            mock_init.return_value = mock_llm
            mock_parse.return_value = Mock(spec=JobAnalysis)

            # Patch the chain construction
            with patch("langchain_core.output_parsers.StrOutputParser") as mock_parser:
                mock_parser_instance = Mock()
                mock_parser.return_value = mock_parser_instance
                # Configure the final chain to return the mock response
                mock_final_chain = AsyncMock()
                mock_final_chain.ainvoke.return_value = mock_response
                mock_parser_instance.ainvoke = mock_final_chain.ainvoke

                result = await analyze_job_description(
                    "Job description",
                    mock_config,
                    "resume content",
                )
                assert result is not None
