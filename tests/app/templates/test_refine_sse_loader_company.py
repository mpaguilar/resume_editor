"""Tests for _refine_sse_loader.html template with company and notes."""

from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader


class TestRefineSseLoaderTemplate:
    """Tests for _refine_sse_loader.html template."""

    @pytest.fixture
    def template_env(self):
        """Create Jinja2 template environment."""
        templates_dir = Path("resume_editor/app/templates")
        return Environment(loader=FileSystemLoader(str(templates_dir)))

    def test_includes_company_in_sse_url(self, template_env):
        """Test that company is included in SSE connection URL."""
        template = template_env.get_template("partials/resume/_refine_sse_loader.html")
        html = template.render(
            resume_id=1,
            job_description="Job desc",
            company="Acme Corp",
            notes="Notes",
        )

        assert "company=" in html

    def test_includes_notes_in_sse_url(self, template_env):
        """Test that notes is included in SSE connection URL."""
        template = template_env.get_template("partials/resume/_refine_sse_loader.html")
        html = template.render(
            resume_id=1,
            job_description="Job desc",
            company="Acme Corp",
            notes="Notes",
        )

        assert "notes=" in html

    def test_conditionally_includes_company_when_present(self, template_env):
        """Test that company is conditionally included only when present."""
        template = template_env.get_template("partials/resume/_refine_sse_loader.html")

        # With company
        html_with = template.render(
            resume_id=1,
            job_description="Job desc",
            company="Acme Corp",
        )
        assert "company=" in html_with

        # Without company
        html_without = template.render(
            resume_id=1,
            job_description="Job desc",
            company=None,
        )
        # Should still render but without company param
        assert "refine-sse-loader" in html_without
