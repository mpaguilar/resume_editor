import datetime
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel, ValidationError

from resume_editor.app.llm.models import JobAnalysis, LLMConfig, RefinedRole
from resume_editor.app.llm.orchestration import (
    _invoke_chain_and_parse,
    _parse_json_with_fix,
    refine_role,
)
from resume_editor.app.models.resume.experience import InclusionStatus, Role


def test_parse_json_with_fix_valid_json():
    """Test _parse_json_with_fix with a valid JSON string."""
    json_string = '{"key": "value", "number": 123}'
    expected = {"key": "value", "number": 123}
    assert _parse_json_with_fix(json_string) == expected


def test_parse_json_with_fix_valid_escapes():
    """Test _parse_json_with_fix with valid JSON escape sequences."""
    json_string = '{"line": "first\\nsecond", "quote": "\\"quoted\\""}'
    expected = {"line": "first\nsecond", "quote": '"quoted"'}
    assert _parse_json_with_fix(json_string) == expected


def test_parse_json_with_fix_invalid_escape_corrects_and_parses():
    """Test _parse_json_with_fix corrects an invalid backslash and parses."""
    # This raw string has an invalid JSON escape sequence `\U` but a valid one `\t`.
    # `json.loads` would fail on `\U`. The fix should escape `\U` but preserve `\t`.
    bad_json_string = r'{"path": "C:\Users\test"}'
    expected = {"path": "C:\\Users\test"}  # The \t becomes a tab
    assert _parse_json_with_fix(bad_json_string) == expected


def test_parse_json_with_fix_unfixable_json_raises_error():
    """Test _parse_json_with_fix raises an error for unfixable JSON."""
    # This JSON has a trailing comma, which is not an "Invalid \\escape" error.
    unfixable_json_string = '{"key": "value",}'
    with pytest.raises(json.JSONDecodeError):
        _parse_json_with_fix(unfixable_json_string)


def test_parse_json_with_fix_still_fails_after_fix():
    """
    Test that _parse_json_with_fix raises an error if the corrected JSON is still invalid.
    This covers the case where the inner try-except block fails.
    """
    # This string has an invalid escape `\U` and a trailing comma.
    # The fix will correct the backslash, but the trailing comma will still cause a parse error.
    bad_json_string = r'{"path": "C:\Users\test",}'
    with pytest.raises(json.JSONDecodeError) as excinfo:
        _parse_json_with_fix(bad_json_string)
    # Check that the original exception (about the escape) is re-raised.
    assert "Invalid \\escape" in str(excinfo.value)


class _TestModel(BaseModel):
    key: str
    number: int


@patch("resume_editor.app.llm.orchestration_banner._parse_json_with_fix")
def test_invoke_chain_and_parse_success(mock_parse_json_with_fix):
    """Test _invoke_chain_and_parse successfully parses and validates."""
    mock_chain = MagicMock()
    mock_chain.invoke.return_value.content = '{"key": "value", "number": 123}'
    mock_parse_json_with_fix.return_value = {"key": "value", "number": 123}

    result = _invoke_chain_and_parse(mock_chain, _TestModel, arg="test")

    mock_chain.invoke.assert_called_once_with({"arg": "test"})
    mock_parse_json_with_fix.assert_called_once_with('{"key": "value", "number": 123}')
    assert isinstance(result, _TestModel)
    assert result.key == "value"
    assert result.number == 123


@patch("resume_editor.app.llm.orchestration_banner._parse_json_with_fix")
def test_invoke_chain_and_parse_parse_failure(mock_parse_json_with_fix):
    """Test _invoke_chain_and_parse raises ValueError on JSONDecodeError."""
    mock_chain = MagicMock()
    mock_chain.invoke.return_value.content = "invalid json"
    mock_parse_json_with_fix.side_effect = json.JSONDecodeError("msg", "doc", 0)

    with pytest.raises(
        ValueError,
        match="The AI service returned an unexpected response. Please try again.",
    ):
        _invoke_chain_and_parse(mock_chain, _TestModel)
    mock_parse_json_with_fix.assert_called_once_with("invalid json")


@patch("resume_editor.app.llm.orchestration_banner._parse_json_with_fix")
def test_invoke_chain_and_parse_validation_failure(mock_parse_json_with_fix):
    """Test _invoke_chain_and_parse raises ValueError on ValidationError."""
    mock_chain = MagicMock()
    mock_chain.invoke.return_value.content = '{"key": "value"}'  # missing 'number'
    mock_parse_json_with_fix.return_value = {"key": "value"}  # missing 'number'

    with pytest.raises(
        ValueError,
        match="The AI service returned an unexpected response. Please try again.",
    ):
        _invoke_chain_and_parse(mock_chain, _TestModel)

    mock_parse_json_with_fix.assert_called_once_with('{"key": "value"}')


@pytest.fixture
def sample_role():
    """Fixture for a sample Role object."""
    return Role.model_validate(
        {
            "basics": {
                "company": "Test Co",
                "title": "Engineer",
                "start_date": datetime.datetime(2022, 1, 1),
                "inclusion_status": InclusionStatus.INCLUDE,
            }
        }
    )


@pytest.fixture
def sample_job_analysis():
    """Fixture for a sample JobAnalysis object."""
    return JobAnalysis.model_validate(
        {
            "primary_duties": ["coding"],
            "key_skills": ["python"],
            "candidate_priorities": ["backend"],
            "themes": ["fast-paced"],
        }
    )


@pytest.fixture
def sample_llm_config():
    """Fixture for a sample LLMConfig object."""
    return LLMConfig()


@pytest.mark.asyncio
@patch("resume_editor.app.llm.orchestration_refinement.parse_json_markdown")
@patch("resume_editor.app.llm.orchestration_refinement.initialize_llm_client")
@patch("resume_editor.app.llm.orchestration_refinement.ChatPromptTemplate")
async def test_refine_role_success(
    mock_prompt_template,
    mock_init_llm,
    mock_parse_json,
    sample_role,
    sample_job_analysis,
    sample_llm_config,
):
    """Test refine_role successfully on a valid response."""
    # Mocking the chain and its invocation
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(return_value="llm response string")

    # `prompt | llm | StrOutputParser()`
    # The result of `ChatPromptTemplate.from_messages().partial()` is the prompt.
    # The `|` operator is `__or__`.
    mock_prompt_template.from_messages.return_value.partial.return_value.__or__.return_value.__or__.return_value = mock_chain

    refined_role_dict = {
        "basics": {
            "company": "Test Co",
            "title": "Python Engineer",
            "start_date": "2022-01-01T00:00:00",
            "inclusion_status": "Include",
        },
        "summary": {"text": "Refined summary"},
    }
    mock_parse_json.return_value = refined_role_dict

    # Call the function
    result = await refine_role(sample_role, sample_job_analysis, sample_llm_config)

    # Assertions
    mock_init_llm.assert_called_once_with(sample_llm_config)
    mock_chain.ainvoke.assert_awaited_once()  # Assert chain was invoked
    mock_parse_json.assert_called_once_with("llm response string")
    assert isinstance(result, RefinedRole)
    assert result.basics.title == "Python Engineer"
    assert result.summary.text == "Refined summary"
    assert result.basics.inclusion_status == InclusionStatus.INCLUDE


@pytest.mark.asyncio
@patch("resume_editor.app.llm.orchestration_refinement.parse_json_markdown")
@patch("resume_editor.app.llm.orchestration_refinement.initialize_llm_client")
@patch("resume_editor.app.llm.orchestration_refinement.ChatPromptTemplate")
async def test_refine_role_parse_failure(
    mock_prompt_template,
    mock_init_llm,
    mock_parse_json,
    sample_role,
    sample_job_analysis,
    sample_llm_config,
):
    """Test refine_role handles JSON parsing failure with retry logic."""
    # Mocking the chain and its invocation
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(return_value="invalid json")

    mock_prompt_template.from_messages.return_value.partial.return_value.__or__.return_value.__or__.return_value = mock_chain

    mock_parse_json.side_effect = json.JSONDecodeError("msg", "doc", 0)

    # Call and assert - JSONDecodeError is retryable, so it will retry 3 times
    with pytest.raises(ValueError, match="Unable to refine"):
        await refine_role(sample_role, sample_job_analysis, sample_llm_config)

    # Should be called 3 times due to retry logic
    assert mock_chain.ainvoke.await_count == 3
    assert mock_parse_json.call_count == 3
