from unittest.mock import Mock, patch

import pytest
from cryptography.fernet import InvalidToken
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse
from openai import AuthenticationError

from resume_editor.app.api.routes.html_fragments import RefineResultParams
from resume_editor.app.api.routes.route_logic.resume_ai_logic import (
    handle_sync_refinement,
)
from resume_editor.app.llm.models import LLMConfig
from resume_editor.app.api.routes.route_models import (
    RefineResponse,
    RefineTargetSection,
    SyncRefinementParams,
)


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.refine_resume_section_with_llm"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_handle_sync_refinement_success_with_key(
    mock_get_llm_config, mock_refine_llm, test_user, test_resume
):
    """Test successful synchronous refinement returns RefineResponse."""
    # Arrange
    mock_request = Request(scope={"type": "http", "headers": []})
    mock_db = Mock()
    params = SyncRefinementParams(
        request=mock_request,
        db=mock_db,
        user=test_user,
        resume=test_resume,
        job_description="job",
        target_section=RefineTargetSection.PERSONAL,
    )
    mock_get_llm_config.return_value = (
        "http://llm.test",
        "test-model",
        "decrypted_key",
    )
    mock_refine_llm.return_value = ("refined content", "this is an intro")

    # Act
    response = await handle_sync_refinement(params)

    # Assert
    assert isinstance(response, RefineResponse)
    assert response.refined_content == "refined content"
    assert response.introduction == "this is an intro"
    mock_get_llm_config.assert_called_once_with(params.db, params.user.id)
    expected_llm_config = LLMConfig(
        llm_endpoint="http://llm.test",
        api_key="decrypted_key",
        llm_model_name="test-model",
    )
    mock_refine_llm.assert_called_once_with(
        resume_content=params.resume.content,
        job_description=params.job_description,
        target_section=params.target_section.value,
        llm_config=expected_llm_config,
    )


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic._create_refine_result_html"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.refine_resume_section_with_llm"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_handle_sync_refinement_htmx_response(
    mock_get_llm_config, mock_refine_llm, mock_create_html, test_user, test_resume
):
    """Test that handle_sync_refinement returns HTML for an HTMX request."""
    # Arrange
    mock_request = Request(
        scope={"type": "http", "headers": [(b"hx-request", b"true")]}
    )
    mock_db = Mock()
    params = SyncRefinementParams(
        request=mock_request,
        db=mock_db,
        user=test_user,
        resume=test_resume,
        job_description="job",
        target_section=RefineTargetSection.PERSONAL,
    )
    mock_get_llm_config.return_value = ("http://llm.test", "test-model", "key")
    mock_refine_llm.return_value = ("refined content", "this is an intro")
    mock_create_html.return_value = "<html>refine result</html>"

    # Act
    response = await handle_sync_refinement(params)

    # Assert
    assert isinstance(response, HTMLResponse)
    assert response.body.decode("utf-8") == "<html>refine result</html>"
    mock_create_html.assert_called_once()
    call_args = mock_create_html.call_args.kwargs
    assert "params" in call_args
    call_params = call_args["params"]
    assert isinstance(call_params, RefineResultParams)
    assert call_params.resume_id == params.resume.id
    assert call_params.target_section_val == params.target_section.value
    assert call_params.refined_content == "refined content"
    assert call_params.job_description == params.job_description
    assert call_params.introduction == "this is an intro"
    assert call_params.limit_refinement_years is None


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_handle_sync_refinement_decryption_failure_htmx(
    mock_get_llm_config, test_user, test_resume
):
    """Test handle_sync_refinement returns HTML error on decryption failure for HTMX."""
    # Arrange
    mock_request = Request(
        scope={"type": "http", "headers": [(b"hx-request", b"true")]}
    )
    mock_db = Mock()
    params = SyncRefinementParams(
        request=mock_request,
        db=mock_db,
        user=test_user,
        resume=test_resume,
        job_description="job",
        target_section=RefineTargetSection.PERSONAL,
    )
    mock_get_llm_config.side_effect = InvalidToken

    # Act
    response = await handle_sync_refinement(params)

    # Assert
    assert isinstance(response, HTMLResponse)
    assert response.status_code == 200
    assert "Invalid API key" in response.body.decode("utf-8")


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_handle_sync_refinement_decryption_failure_non_htmx(
    mock_get_llm_config, test_user, test_resume
):
    """Test handle_sync_refinement raises HTTPException on decryption failure for non-HTMX."""
    # Arrange
    mock_request = Request(scope={"type": "http", "headers": []})
    mock_db = Mock()
    params = SyncRefinementParams(
        request=mock_request,
        db=mock_db,
        user=test_user,
        resume=test_resume,
        job_description="job",
        target_section=RefineTargetSection.PERSONAL,
    )
    mock_get_llm_config.side_effect = InvalidToken

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await handle_sync_refinement(params)
    assert exc_info.value.status_code == 400
    assert "Invalid API key" in exc_info.value.detail


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.refine_resume_section_with_llm"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_handle_sync_refinement_auth_failure_htmx(
    mock_get_llm_config, mock_refine_llm, test_user, test_resume
):
    """Test handle_sync_refinement returns HTML error on auth failure for HTMX."""
    # Arrange
    mock_request = Request(
        scope={"type": "http", "headers": [(b"hx-request", b"true")]}
    )
    mock_db = Mock()
    params = SyncRefinementParams(
        request=mock_request,
        db=mock_db,
        user=test_user,
        resume=test_resume,
        job_description="job",
        target_section=RefineTargetSection.PERSONAL,
    )
    mock_get_llm_config.return_value = (None, None, None)
    mock_refine_llm.side_effect = AuthenticationError(
        message="auth failed", response=Mock(), body=None
    )

    # Act
    response = await handle_sync_refinement(params)

    # Assert
    assert isinstance(response, HTMLResponse)
    assert "LLM authentication failed" in response.body.decode("utf-8")


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.refine_resume_section_with_llm"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_handle_sync_refinement_auth_failure_non_htmx(
    mock_get_llm_config, mock_refine_llm, test_user, test_resume
):
    """Test handle_sync_refinement raises HTTPException on auth failure for non-HTMX."""
    # Arrange
    mock_request = Request(scope={"type": "http", "headers": []})
    mock_db = Mock()
    params = SyncRefinementParams(
        request=mock_request,
        db=mock_db,
        user=test_user,
        resume=test_resume,
        job_description="job",
        target_section=RefineTargetSection.PERSONAL,
    )
    mock_get_llm_config.return_value = (None, None, None)
    mock_refine_llm.side_effect = AuthenticationError(
        message="auth failed", response=Mock(), body=None
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await handle_sync_refinement(params)
    assert exc_info.value.status_code == 401
    assert "LLM authentication failed" in exc_info.value.detail


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.refine_resume_section_with_llm"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_handle_sync_refinement_value_error_htmx(
    mock_get_llm_config, mock_refine_llm, test_user, test_resume
):
    """Test handle_sync_refinement returns HTML error on ValueError for HTMX."""
    # Arrange
    mock_request = Request(
        scope={"type": "http", "headers": [(b"hx-request", b"true")]}
    )
    mock_db = Mock()
    params = SyncRefinementParams(
        request=mock_request,
        db=mock_db,
        user=test_user,
        resume=test_resume,
        job_description="job",
        target_section=RefineTargetSection.PERSONAL,
    )
    mock_get_llm_config.return_value = (None, None, None)
    error_message = "The AI service returned an unexpected response."
    mock_refine_llm.side_effect = ValueError(error_message)

    # Act
    response = await handle_sync_refinement(params)

    # Assert
    assert isinstance(response, HTMLResponse)
    assert "Refinement failed: " in response.body.decode("utf-8")
    assert error_message in response.body.decode("utf-8")


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.refine_resume_section_with_llm"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_handle_sync_refinement_value_error_non_htmx(
    mock_get_llm_config, mock_refine_llm, test_user, test_resume
):
    """Test handle_sync_refinement raises HTTPException on ValueError for non-HTMX."""
    # Arrange
    mock_request = Request(scope={"type": "http", "headers": []})
    mock_db = Mock()
    params = SyncRefinementParams(
        request=mock_request,
        db=mock_db,
        user=test_user,
        resume=test_resume,
        job_description="job",
        target_section=RefineTargetSection.PERSONAL,
    )
    mock_get_llm_config.return_value = (None, None, None)
    error_message = "The AI service returned an unexpected response."
    mock_refine_llm.side_effect = ValueError(error_message)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await handle_sync_refinement(params)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == error_message


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.refine_resume_section_with_llm"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_handle_sync_refinement_generic_exception_htmx(
    mock_get_llm_config, mock_refine_llm, test_user, test_resume
):
    """Test handle_sync_refinement returns HTML on generic Exception for HTMX."""
    # Arrange
    mock_request = Request(
        scope={"type": "http", "headers": [(b"hx-request", b"true")]}
    )
    mock_db = Mock()
    params = SyncRefinementParams(
        request=mock_request,
        db=mock_db,
        user=test_user,
        resume=test_resume,
        job_description="job",
        target_section=RefineTargetSection.PERSONAL,
    )
    mock_get_llm_config.return_value = (None, None, None)
    mock_refine_llm.side_effect = Exception("LLM call failed")

    # Act
    response = await handle_sync_refinement(params)

    # Assert
    assert isinstance(response, HTMLResponse)
    assert "An unexpected error occurred during refinement" in response.body.decode(
        "utf-8"
    )
    assert "LLM call failed" in response.body.decode("utf-8")


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.route_logic.resume_ai_logic.refine_resume_section_with_llm"
)
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_llm_config")
async def test_handle_sync_refinement_generic_exception_non_htmx(
    mock_get_llm_config, mock_refine_llm, test_user, test_resume
):
    """Test handle_sync_refinement raises HTTPException on generic Exception for non-HTMX."""
    # Arrange
    mock_request = Request(scope={"type": "http", "headers": []})
    mock_db = Mock()
    params = SyncRefinementParams(
        request=mock_request,
        db=mock_db,
        user=test_user,
        resume=test_resume,
        job_description="job",
        target_section=RefineTargetSection.PERSONAL,
    )
    mock_get_llm_config.return_value = (None, None, None)
    mock_refine_llm.side_effect = Exception("LLM call failed")

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await handle_sync_refinement(params)
    assert exc_info.value.status_code == 500
    assert "LLM refinement failed: LLM call failed" in exc_info.value.detail
