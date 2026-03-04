"""Tests for _refine_result.html template with company and notes."""

from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader


class TestRefineResultTemplate:
    """Tests for _refine_result.html template."""

    @pytest.fixture
    def template_env(self):
        """Create Jinja2 template environment."""
        templates_dir = Path("resume_editor/app/templates")
        return Environment(loader=FileSystemLoader(str(templates_dir)))

    def test_template_includes_company_hidden_field(self, template_env):
        """Test that template includes company as hidden field."""
        template = template_env.get_template("partials/resume/_refine_result.html")
        html = template.render(
            resume_id=1,
            refined_content="Content",
            company="Acme Corp",
            notes="Notes here",
        )

        # Company is now a hidden field, not a visible input
        assert 'name="company"' in html
        assert 'type="hidden"' in html
        assert 'value="Acme Corp"' in html

    def test_template_includes_notes_hidden_field(self, template_env):
        """Test that template includes notes as hidden field."""
        template = template_env.get_template("partials/resume/_refine_result.html")
        html = template.render(
            resume_id=1,
            refined_content="Content",
            company="Acme Corp",
            notes="Notes here",
        )

        # Notes is now a hidden field, not a visible textarea
        assert 'name="notes"' in html
        assert 'type="hidden"' in html
        assert 'value="Notes here"' in html

    def test_template_handles_null_values(self, template_env):
        """Test that template handles null company/notes gracefully."""
        template = template_env.get_template("partials/resume/_refine_result.html")
        html = template.render(
            resume_id=1,
            refined_content="Content",
            company=None,
            notes=None,
        )

        # Hidden fields should still exist with empty string values
        assert 'name="company"' in html
        assert 'name="notes"' in html
        assert 'value=""' in html
