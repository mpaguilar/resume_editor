import pytest

from resume_editor.app.api.routes.route_models import (
    RefineAcceptRequest,
    RefineAction,
    RefineTargetSection,
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
