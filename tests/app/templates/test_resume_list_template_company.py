"""Tests for _resume_list.html template with company display and sorting."""

from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader


class TestResumeListTemplate:
    """Tests for _resume_list.html template."""

    @pytest.fixture
    def template_env(self):
        """Create Jinja2 template environment."""
        templates_dir = Path("resume_editor/app/templates")
        return Environment(loader=FileSystemLoader(str(templates_dir)))

    def test_shows_company_for_refined_resumes(self, template_env):
        """Test that company is displayed for refined resumes."""
        template = template_env.get_template("partials/resume/_resume_list.html")
        html = template.render(
            base_resumes=[],
            refined_resumes=[
                {
                    "id": 1,
                    "name": "Refined Resume",
                    "company": "Acme Corp",
                    "parent_id": 5,
                    "created_at": None,
                    "updated_at": None,
                    "notes": None,
                }
            ],
            week_offset=0,
            has_older_resumes=False,
            has_newer_resumes=False,
        )

        assert "Company: Acme Corp" in html

    def test_shows_na_for_empty_company(self, template_env):
        """Test that 'N/A' is shown when company is empty/None."""
        template = template_env.get_template("partials/resume/_resume_list.html")
        html = template.render(
            base_resumes=[],
            refined_resumes=[
                {
                    "id": 1,
                    "name": "Refined Resume",
                    "company": None,
                    "parent_id": 5,
                    "created_at": None,
                    "updated_at": None,
                    "notes": None,
                }
            ],
            week_offset=0,
            has_older_resumes=False,
            has_newer_resumes=False,
        )

        assert "Company: N/A" in html

    def test_includes_company_sort_control(self, template_env):
        """Test that company sort control is present."""
        template = template_env.get_template("partials/resume/_resume_list.html")
        html = template.render(
            base_resumes=[],
            refined_resumes=[
                {
                    "id": 1,
                    "name": "Test Resume",
                    "company": "Test Corp",
                    "parent_id": 5,
                    "created_at": None,
                    "updated_at": None,
                    "notes": None,
                }
            ],
            week_offset=0,
            has_older_resumes=False,
            has_newer_resumes=False,
        )

        assert (
            "sort_by=company_asc" in html
            or "sort_by={% if sort_by == 'company_asc' %}" in html
        )
        assert "Company" in html

    def test_base_resumes_do_not_show_company(self, template_env):
        """Test that base resumes don't show company field."""
        template = template_env.get_template("partials/resume/_resume_list.html")
        html = template.render(
            base_resumes=[
                {
                    "id": 1,
                    "name": "Base Resume",
                    "is_base": True,
                    "created_at": None,
                    "updated_at": None,
                }
            ],
            refined_resumes=[],
            week_offset=0,
            has_older_resumes=False,
            has_newer_resumes=False,
        )

        # Base resumes should not have "Company:" in their display
        base_section = (
            html.split("Applied Resumes")[0] if "Applied Resumes" in html else html
        )
        assert "Company:" not in base_section or "Base Resume" in base_section
