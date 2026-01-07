
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from resume_editor.app.api.routes.resume_ai import (
    _extract_original_limit_str_from_post,
    _parse_limit_years_for_stream,
    _validate_and_parse_limit_for_post,
    get_refine_stream_query,
)
from resume_editor.app.api.routes.route_models import RefineForm


def test_get_refine_stream_query_with_limit_years():
    """Test get_refine_stream_query with a valid limit_refinement_years."""
    job_description = "Software Engineer"
    limit_years = "5"
    query_params = get_refine_stream_query(job_description, limit_years)
    assert query_params.job_description == job_description
    assert query_params.limit_refinement_years == limit_years


def test_get_refine_stream_query_without_limit_years():
    """Test get_refine_stream_query without limit_refinement_years."""
    job_description = "Software Engineer"
    query_params = get_refine_stream_query(job_description)
    assert query_params.job_description == job_description
    assert query_params.limit_refinement_years is None


def test_parse_limit_years_for_stream_none():
    """Test _parse_limit_years_for_stream with None input."""
    years, response = _parse_limit_years_for_stream(None)
    assert years is None
    assert response is None


def test_parse_limit_years_for_stream_valid_int():
    """Test _parse_limit_years_for_stream with a valid integer string."""
    years, response = _parse_limit_years_for_stream("5")
    assert years == 5
    assert response is None


def test_parse_limit_years_for_stream_invalid_string():
    """Test _parse_limit_years_for_stream with an invalid string."""
    years, response = _parse_limit_years_for_stream("abc")
    assert years is None
    assert response is not None
    # Further checks on response content can be added if needed


def test_parse_limit_years_for_stream_zero():
    """Test _parse_limit_years_for_stream with zero."""
    years, response = _parse_limit_years_for_stream("0")
    assert years is None
    assert response is not None


def test_parse_limit_years_for_stream_negative():
    """Test _parse_limit_years_for_stream with a negative number."""
    years, response = _parse_limit_years_for_stream("-5")
    assert years is None
    assert response is not None


@patch("resume_editor.app.api.routes.resume_ai.Request")
async def test_extract_original_limit_str_from_post_form_data_present(
    mock_request: MagicMock,
):
    """Test _extract_original_limit_str_from_post when form_data already has the value."""
    form_data = RefineForm(job_description="test", limit_refinement_years="10")
    result = await _extract_original_limit_str_from_post(mock_request, form_data)
    assert result == "10"
    mock_request.form.assert_not_called()


@patch("resume_editor.app.api.routes.resume_ai.Request")
async def test_extract_original_limit_str_from_post_form_data_none_raw_present(
    mock_request: MagicMock,
):
    """Test _extract_original_limit_str_from_post when form_data is None but raw form has value."""
    form_data = RefineForm(job_description="test", limit_refinement_years=None)
    mock_form_data = {"limit_refinement_years": "7"}
    mock_request.form = AsyncMock(return_value=mock_form_data)

    result = await _extract_original_limit_str_from_post(mock_request, form_data)
    assert result == "7"
    mock_request.form.assert_awaited_once()


@patch("resume_editor.app.api.routes.resume_ai.Request")
async def test_extract_original_limit_str_from_post_form_data_none_raw_empty(
    mock_request: MagicMock,
):
    """Test _extract_original_limit_str_from_post when form_data is None and raw form has empty string."""
    form_data = RefineForm(job_description="test", limit_refinement_years=None)
    mock_form_data = {"limit_refinement_years": ""}
    mock_request.form = AsyncMock(return_value=mock_form_data)

    result = await _extract_original_limit_str_from_post(mock_request, form_data)
    assert result is None
    mock_request.form.assert_awaited_once()


@patch("resume_editor.app.api.routes.resume_ai.Request")
async def test_extract_original_limit_str_from_post_form_data_none_raw_not_present(
    mock_request: MagicMock,
):
    """Test _extract_original_limit_str_from_post when form_data is None and raw form lacks the field."""
    form_data = RefineForm(job_description="test", limit_refinement_years=None)
    mock_form_data = {"other_field": "value"}
    mock_request.form = AsyncMock(return_value=mock_form_data)

    result = await _extract_original_limit_str_from_post(mock_request, form_data)
    assert result is None
    mock_request.form.assert_awaited_once()


@patch("resume_editor.app.api.routes.resume_ai.Request")
async def test_extract_original_limit_str_from_post_form_read_exception(
    mock_request: MagicMock,
):
    """Test _extract_original_limit_str_from_post when reading raw form raises an exception."""
    form_data = RefineForm(job_description="test", limit_refinement_years=None)
    mock_request.form = AsyncMock(side_effect=Exception("Form read error"))

    result = await _extract_original_limit_str_from_post(mock_request, form_data)
    assert result is None
    mock_request.form.assert_awaited_once()


def test_validate_and_parse_limit_for_post_none():
    """Test _validate_and_parse_limit_for_post with None input."""
    years, response = _validate_and_parse_limit_for_post(None)
    assert years is None
    assert response is None


def test_validate_and_parse_limit_for_post_non_numeric():
    """Test _validate_and_parse_limit_for_post with a non-numeric string."""
    years, response = _validate_and_parse_limit_for_post("abc")
    assert years is None
    assert response is None


def test_validate_and_parse_limit_for_post_valid_numeric():
    """Test _validate_and_parse_limit_for_post with a valid numeric string."""
    years, response = _validate_and_parse_limit_for_post("5")
    assert years == 5
    assert response is None


def test_validate_and_parse_limit_for_post_zero():
    """Test _validate_and_parse_limit_for_post with zero."""
    years, response = _validate_and_parse_limit_for_post("0")
    assert years is None
    assert response is not None


def test_validate_and_parse_limit_for_post_negative():
    """Test _validate_and_parse_limit_for_post with a negative number."""
    years, response = _validate_and_parse_limit_for_post("-5")
    assert years is None
    assert response is not None


app = FastAPI()
client = TestClient(app)
