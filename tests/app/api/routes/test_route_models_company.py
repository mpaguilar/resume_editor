"""Tests for route models with company and notes fields."""

import pytest
from fastapi import Form

from resume_editor.app.api.routes.route_models import (
    RefineForm,
    RefinementContext,
    ResumeDetailResponse,
    ResumeResponse,
    ResumeSortBy,
    SaveAsNewForm,
)


class TestResumeSortBy:
    """Tests for ResumeSortBy enum with company options."""

    def test_company_asc_exists(self):
        assert ResumeSortBy.COMPANY_ASC == "company_asc"

    def test_company_desc_exists(self):
        assert ResumeSortBy.COMPANY_DESC == "company_desc"

    def test_all_sort_options(self):
        expected = {
            "name_asc",
            "name_desc",
            "company_asc",
            "company_desc",
            "created_at_asc",
            "created_at_desc",
            "updated_at_asc",
            "updated_at_desc",
        }
        actual = {sort.value for sort in ResumeSortBy}
        assert actual == expected


class TestResumeResponse:
    def test_resume_response_with_company(self):
        response = ResumeResponse(id=1, name="Test Resume", company="Acme Corp")
        assert response.company == "Acme Corp"

    def test_resume_response_company_optional(self):
        response = ResumeResponse(id=1, name="Test Resume")
        assert response.company is None

    def test_resume_response_company_none_explicit(self):
        response = ResumeResponse(id=1, name="Test Resume", company=None)
        assert response.company is None


class TestResumeDetailResponse:
    def test_resume_detail_response_with_company(self):
        response = ResumeDetailResponse(
            id=1, name="Test Resume", content="Content", company="Acme Corp"
        )
        assert response.company == "Acme Corp"

    def test_resume_detail_response_company_optional(self):
        response = ResumeDetailResponse(id=1, name="Test Resume", content="Content")
        assert response.company is None


class TestRefineForm:
    def test_refine_form_with_company_and_notes(self):
        form = RefineForm(
            job_description="Software Engineer job",
            limit_refinement_years="5",
            company="Acme Corp",
            notes="Important notes here",
        )
        assert form.job_description == "Software Engineer job"
        assert form.limit_refinement_years == "5"
        assert form.company == "Acme Corp"
        assert form.notes == "Important notes here"

    def test_refine_form_company_optional(self):
        """Test that RefineForm accepts optional company and notes fields.

        When instantiated directly (not through FastAPI DI), Form(None) remains
        as a Form object. We verify the attributes exist with the default value.
        """
        form = RefineForm(job_description="Software Engineer job")
        assert hasattr(form, "company")
        assert hasattr(form, "notes")
        # When called directly, Form(None) stays as Form object
        assert isinstance(form.company, type(Form(None))) or form.company is None
        assert isinstance(form.notes, type(Form(None))) or form.notes is None

    def test_refine_form_empty_strings(self):
        form = RefineForm(job_description="Job desc", company="", notes="")
        assert form.company == ""
        assert form.notes == ""


class TestRefinementContext:
    def test_refinement_context_with_company_and_notes(self):
        context = RefinementContext(
            job_description="Job desc",
            introduction="Intro",
            limit_refinement_years=5,
            company="Acme Corp",
            notes="Notes here",
        )
        assert context.company == "Acme Corp"
        assert context.notes == "Notes here"

    def test_refinement_context_optional_fields(self):
        """Test that RefinementContext accepts optional fields.

        When instantiated directly (not through FastAPI DI), Form(None) remains
        as a Form object. We verify the attributes exist.
        """
        context = RefinementContext()
        assert hasattr(context, "job_description")
        assert hasattr(context, "introduction")
        assert hasattr(context, "limit_refinement_years")
        assert hasattr(context, "company")
        assert hasattr(context, "notes")


class TestSaveAsNewForm:
    def test_save_as_new_form_has_company_and_notes_params(self):
        """Test that SaveAsNewForm accepts company and notes parameters.

        Note: This test verifies the form class accepts the parameters.
        Full testing requires FastAPI dependency injection which is tested
        via integration tests with the actual endpoints.
        """
        import inspect

        sig = inspect.signature(SaveAsNewForm.__init__)
        params = list(sig.parameters.keys())
        assert "company" in params
        assert "notes" in params
        assert "context" in params
