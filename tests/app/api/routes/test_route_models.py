import pytest

from resume_editor.app.api.routes.route_models import (
    RefineForm,
    RefineRequest,
    RefineTargetSection,
    RenderFormat,
    RenderSettingsName,
    ResumeDetailResponse,
    ResumeResponse,
    SaveAsNewForm,
    SaveAsNewMetadata,
)





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


def test_refine_form_instantiation():
    """
    Test RefineForm can be instantiated with all fields,
    including the new optional field.
    """
    # Test with the optional field provided
    form_with_limit = RefineForm(
        job_description="A job.",
        target_section=RefineTargetSection.EXPERIENCE,
        limit_refinement_years=5,
    )
    assert form_with_limit.job_description == "A job."
    assert form_with_limit.target_section == RefineTargetSection.EXPERIENCE
    assert form_with_limit.limit_refinement_years == 5

    # Test without the optional field (it's passed as None by Depends default)
    form_without_limit = RefineForm(
        job_description="Another job.",
        target_section=RefineTargetSection.PERSONAL,
        limit_refinement_years=None,
    )
    assert form_without_limit.job_description == "Another job."
    assert form_without_limit.target_section == RefineTargetSection.PERSONAL
    assert form_without_limit.limit_refinement_years is None


def test_save_as_new_metadata_instantiation():
    """Test SaveAsNewMetadata can be instantiated with all fields."""
    # Test with all fields provided
    metadata_full = SaveAsNewMetadata(
        new_resume_name="New Resume",
        job_description="A job.",
        introduction="An intro.",
        limit_refinement_years="5",
    )
    assert metadata_full.new_resume_name == "New Resume"
    assert metadata_full.job_description == "A job."
    assert metadata_full.introduction == "An intro."
    assert metadata_full.limit_refinement_years == 5

    # Test with no fields provided
    metadata_empty = SaveAsNewMetadata(
        new_resume_name=None,
        job_description=None,
        introduction=None,
        limit_refinement_years=None,
    )
    assert metadata_empty.new_resume_name is None
    assert metadata_empty.job_description is None
    assert metadata_empty.introduction is None
    assert metadata_empty.limit_refinement_years is None

    # Test with invalid year string
    metadata_invalid_year = SaveAsNewMetadata(
        limit_refinement_years="abc",
    )
    assert metadata_invalid_year.limit_refinement_years is None


def test_save_as_new_form_instantiation():
    """Test SaveAsNewForm can be instantiated with its dependencies."""
    metadata = SaveAsNewMetadata(
        new_resume_name="New Resume",
        job_description="A job.",
        introduction="An intro.",
        limit_refinement_years="5",
    )

    form = SaveAsNewForm(
        refined_content="some content",
        target_section=RefineTargetSection.EXPERIENCE,
        metadata=metadata,
    )

    assert form.refined_content == "some content"
    assert form.target_section == RefineTargetSection.EXPERIENCE
    assert form.new_resume_name == "New Resume"
    assert form.job_description == "A job."
    assert form.introduction == "An intro."
    assert form.limit_refinement_years == 5
