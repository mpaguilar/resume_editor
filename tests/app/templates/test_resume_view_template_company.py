"""Tests for resume_view.html template with company field."""

from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader


class TestResumeViewTemplate:
    """Tests for resume_view.html template."""

    @pytest.fixture
    def template_env(self):
        """Create Jinja2 template environment."""
        templates_dir = Path("resume_editor/app/templates")
        return Environment(loader=FileSystemLoader(str(templates_dir)))

    def test_template_includes_company_field(self, template_env):
        """Test that template includes company input field."""
        template = template_env.get_template("pages/resume_view.html")
        html = template.render(
            resume={
                "id": 1,
                "name": "Test Resume",
                "company": "Acme Corp",
                "notes": "Notes",
                "introduction": "Intro",
                "is_base": False,
                "parent_id": 5,
            }
        )

        assert 'id="company"' in html
        assert 'name="company"' in html
        assert 'maxlength="255"' in html

    def test_template_prefills_company_value(self, template_env):
        """Test that company field is prefilled with resume value."""
        template = template_env.get_template("pages/resume_view.html")
        html = template.render(
            resume={
                "id": 1,
                "name": "Test Resume",
                "company": "Acme Corp",
                "notes": "Notes",
                "introduction": "Intro",
                "is_base": False,
                "parent_id": 5,
            }
        )

        assert 'value="Acme Corp"' in html


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
