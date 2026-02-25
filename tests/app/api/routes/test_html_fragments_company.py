"""Tests for html_fragments with company and notes fields."""

import pytest

from resume_editor.app.api.routes.html_fragments import RefineResultParams


class TestRefineResultParams:
    """Tests for RefineResultParams with company and notes."""

    def test_refine_result_params_with_company_and_notes(self):
        """Test RefineResultParams with all fields."""
        params = RefineResultParams(
            resume_id=1,
            refined_content="Refined content",
            introduction="Intro",
            job_description="Job desc",
            limit_refinement_years=5,
            company="Acme Corp",
            notes="Notes here",
        )
        assert params.company == "Acme Corp"
        assert params.notes == "Notes here"

    def test_refine_result_params_company_optional(self):
        """Test that company is optional."""
        params = RefineResultParams(
            resume_id=1,
            refined_content="Refined content",
        )
        assert params.company is None
        assert params.notes is None

    def test_refine_result_params_model_dump_includes_new_fields(self):
        """Test that model_dump includes new fields."""
        params = RefineResultParams(
            resume_id=1,
            refined_content="Refined content",
            company="Acme Corp",
            notes="Notes",
        )
        dumped = params.model_dump()
        assert dumped["company"] == "Acme Corp"
        assert dumped["notes"] == "Notes"
