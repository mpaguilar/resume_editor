"""Comprehensive template tests for company and notes fields."""

from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader


class TestAllTemplates:
    """Tests for all templates with company and notes."""

    @pytest.fixture
    def template_env(self):
        templates_dir = Path("resume_editor/app/templates")
        return Environment(loader=FileSystemLoader(str(templates_dir)))

    def test_refine_template_has_company_field(self, template_env):
        template = template_env.get_template("refine.html")
        html = template.render(resume={"id": 1, "name": "Test"})
        assert 'name="company"' in html
        assert 'maxlength="255"' in html

    def test_refine_template_has_notes_field(self, template_env):
        template = template_env.get_template("refine.html")
        html = template.render(resume={"id": 1, "name": "Test"})
        assert 'name="notes"' in html
        assert 'maxlength="5000"' in html

    def test_refine_result_template_has_company(self, template_env):
        template = template_env.get_template("partials/resume/_refine_result.html")
        html = template.render(
            resume_id=1, refined_content="Content", company="Acme Corp", notes="Notes"
        )
        assert 'name="company"' in html
        assert "Acme Corp" in html

    def test_refine_result_template_has_notes(self, template_env):
        template = template_env.get_template("partials/resume/_refine_result.html")
        html = template.render(
            resume_id=1, refined_content="Content", company="Acme Corp", notes="Notes"
        )
        assert 'name="notes"' in html
        assert "Notes" in html

    def test_resume_view_template_has_company(self, template_env):
        template = template_env.get_template("pages/resume_view.html")
        html = template.render(
            resume={
                "id": 1,
                "name": "Test",
                "company": "Acme Corp",
                "notes": "Notes",
                "introduction": "Intro",
                "is_base": False,
                "parent_id": 5,
            }
        )
        assert 'name="company"' in html
        assert 'value="Acme Corp"' in html

    def test_resume_list_template_shows_company(self, template_env):
        template = template_env.get_template("partials/resume/_resume_list.html")
        html = template.render(
            base_resumes=[],
            refined_resumes=[
                {"id": 1, "name": "Resume", "company": "Acme Corp", "parent_id": 5}
            ],
            week_offset=0,
            has_older_resumes=False,
            has_newer_resumes=False,
        )
        assert "Company: Acme Corp" in html

    def test_resume_list_template_has_company_sort(self, template_env):
        template = template_env.get_template("partials/resume/_resume_list.html")
        # Provide a resume so sorting controls are rendered (empty lists show empty state)
        html = template.render(
            base_resumes=[{"id": 1, "name": "Base Resume"}],
            refined_resumes=[],
            week_offset=0,
            has_older_resumes=False,
            has_newer_resumes=False,
        )
        assert "company_asc" in html or "company_desc" in html

    def test_refine_sse_loader_has_company_in_url(self, template_env):
        template = template_env.get_template("partials/resume/_refine_sse_loader.html")
        html = template.render(
            resume_id=1, job_description="Job desc", company="Acme Corp", notes="Notes"
        )
        assert "company=" in html
        assert "notes=" in html
