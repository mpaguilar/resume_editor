"""Tests for refine template with company and notes fields."""

from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader


class TestRefineTemplate:
    """Tests for refine.html template."""

    @pytest.fixture
    def template_env(self):
        """Create Jinja2 template environment."""
        templates_dir = Path("resume_editor/app/templates")
        return Environment(loader=FileSystemLoader(str(templates_dir)))

    def test_template_includes_company_field(self, template_env):
        """Test that template includes company input field."""
        template = template_env.get_template("refine.html")
        html = template.render(resume={"id": 1, "name": "Test"})

        assert 'id="company"' in html
        assert 'name="company"' in html
        assert 'maxlength="255"' in html

    def test_template_includes_notes_field(self, template_env):
        """Test that template includes notes textarea."""
        template = template_env.get_template("refine.html")
        html = template.render(resume={"id": 1, "name": "Test"})

        assert 'id="notes"' in html
        assert 'name="notes"' in html
        assert 'maxlength="5000"' in html

    def test_company_field_has_label(self, template_env):
        """Test that company field has proper label."""
        template = template_env.get_template("refine.html")
        html = template.render(resume={"id": 1, "name": "Test"})

        assert '<label for="company"' in html
        assert "Company" in html

    def test_notes_field_has_label(self, template_env):
        """Test that notes field has proper label."""
        template = template_env.get_template("refine.html")
        html = template.render(resume={"id": 1, "name": "Test"})

        assert '<label for="notes"' in html
        assert "Notes" in html
