import pytest

from resume_editor.app.api.routes.route_models import (
    RefineAcceptRequest,
    RefineAction,
    RefineTargetSection,
    RenderFormat,
    RenderSettingsName,
    ResumeDetailResponse,
    ResumeResponse,
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


def test_resume_response_with_new_fields():
    """
    Test ResumeResponse can be instantiated with the new fields
    `notes` and `introduction`.
    """
    data = {
        "id": 1,
        "name": "My Resume",
        "notes": "Some notes.",
        "introduction": "An introduction.",
    }
    resp = ResumeResponse(**data)
    assert resp.id == 1
    assert resp.name == "My Resume"
    assert resp.notes == "Some notes."
    assert resp.introduction == "An introduction."


def test_resume_response_without_new_fields():
    """
    Test ResumeResponse can be instantiated without the new fields,
    which should default to None.
    """
    data = {"id": 1, "name": "My Resume"}
    resp = ResumeResponse(**data)
    assert resp.id == 1
    assert resp.name == "My Resume"
    assert resp.notes is None
    assert resp.introduction is None


def test_resume_detail_response_with_new_fields():
    """
    Test ResumeDetailResponse can be instantiated with the new fields
    `notes` and `introduction`.
    """
    data = {
        "id": 1,
        "name": "My Resume",
        "content": "Resume content.",
        "notes": "Some notes.",
        "introduction": "An introduction.",
    }
    resp = ResumeDetailResponse(**data)
    assert resp.id == 1
    assert resp.name == "My Resume"
    assert resp.content == "Resume content."
    assert resp.notes == "Some notes."
    assert resp.introduction == "An introduction."


def test_resume_detail_response_without_new_fields():
    """
    Test ResumeDetailResponse can be instantiated without the new fields,
    which should default to None.
    """
    data = {"id": 1, "name": "My Resume", "content": "Resume content."}
    resp = ResumeDetailResponse(**data)
    assert resp.id == 1
    assert resp.name == "My Resume"
    assert resp.content == "Resume content."
    assert resp.notes is None
    assert resp.introduction is None
