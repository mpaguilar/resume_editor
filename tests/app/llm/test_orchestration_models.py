"""Tests for orchestration_models module."""

import pytest

from resume_editor.app.llm.orchestration_models import (
    HandleRetryDelayParams,
    ProcessRefinementErrorParams,
)


def test_handle_retry_delay_params_creation():
    """Test HandleRetryDelayParams can be created with all fields."""
    params = HandleRetryDelayParams(
        attempt=0,
        role=None,
        response_str="test",
        error=Exception("test"),
        job_analysis=None,
    )
    assert params.attempt == 0
    assert params.response_str == "test"
    assert params.semaphore is None
    assert params.progress_callback is None


def test_process_refinement_error_params_creation():
    """Test ProcessRefinementErrorParams can be created with all fields."""
    params = ProcessRefinementErrorParams(
        attempt=1,
        error=ValueError("test"),
        role=None,
        response_str="response",
        job_analysis=None,
    )
    assert params.attempt == 1
    assert isinstance(params.error, ValueError)
