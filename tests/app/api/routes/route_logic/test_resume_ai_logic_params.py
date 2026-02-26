"""Tests for resume_ai_logic_params module."""

from resume_editor.app.api.routes.route_logic.resume_ai_logic_params import (
    ProcessExperienceResultParams,
)


def test_process_experience_result_params_creation():
    """Test ProcessExperienceResultParams can be created."""
    params = ProcessExperienceResultParams(
        resume_id=1,
        original_resume_content="# Resume",
        resume_content_to_refine="# Resume",
        refined_roles={},
        job_description="Job",
        limit_refinement_years=None,
    )
    assert params.resume_id == 1
    assert params.limit_refinement_years is None
