import pytest

from resume_editor.app.api.routes.route_models import (
    RefineAcceptRequest,
    RefineAction,
    RefineTargetSection,
    RenderFormat,
    RenderSettingsName,
)


def test_refine_accept_request_with_job_description():
    """Test RefineAcceptRequest can be instantiated with job_description."""
    data = {
        "refined_content": "some content",
        "target_section": RefineTargetSection.EXPERIENCE,
        "action": RefineAction.SAVE_AS_NEW,
        "new_resume_name": "New Resume",
        "job_description": "A job description",
    }
    req = RefineAcceptRequest(**data)
    assert req.job_description == "A job description"
    assert req.new_resume_name == "New Resume"


def test_refine_accept_request_without_job_description():
    """Test RefineAcceptRequest can be instantiated without job_description."""
    data = {
        "refined_content": "some content",
        "target_section": RefineTargetSection.PERSONAL,
        "action": RefineAction.OVERWRITE,
    }
    req = RefineAcceptRequest(**data)
    assert req.job_description is None
    assert req.new_resume_name is None


def test_render_format_enum():
    """Test RenderFormat enum values."""
    assert RenderFormat.PLAIN.value == "plain"
    assert RenderFormat.ATS.value == "ats"
    assert len(RenderFormat) == 2


def test_render_settings_name_enum():
    """Test RenderSettingsName enum values."""
    assert RenderSettingsName.GENERAL.value == "general"
    assert RenderSettingsName.EXECUTIVE_SUMMARY.value == "executive_summary"
    assert len(RenderSettingsName) == 2
