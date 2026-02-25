"""Tests for Resume model with company field."""

import pytest

from resume_editor.app.models.resume_model import Resume, ResumeData


class TestResumeModelWithCompany:
    """Tests for Resume model with company field."""

    def test_resume_data_accepts_company(self):
        """Test that ResumeData accepts company parameter."""
        data = ResumeData(
            user_id=1,
            name="Test Resume",
            content="Test content",
            company="Acme Corp",
        )
        assert data.company == "Acme Corp"

    def test_resume_data_company_defaults_to_none(self):
        """Test that ResumeData company defaults to None."""
        data = ResumeData(
            user_id=1,
            name="Test Resume",
            content="Test content",
        )
        assert data.company is None

    def test_resume_initialization_with_company(self):
        """Test Resume initialization with company."""
        data = ResumeData(
            user_id=1,
            name="Test Resume",
            content="Test content",
            company="Acme Corp",
        )
        resume = Resume(data=data)
        assert resume.company == "Acme Corp"

    def test_resume_initialization_without_company(self):
        """Test Resume initialization without company (defaults to None)."""
        data = ResumeData(
            user_id=1,
            name="Test Resume",
            content="Test content",
        )
        resume = Resume(data=data)
        assert resume.company is None

    def test_resume_company_can_be_empty_string(self):
        """Test that company can be empty string."""
        data = ResumeData(
            user_id=1,
            name="Test Resume",
            content="Test content",
            company="",
        )
        resume = Resume(data=data)
        assert resume.company == ""

    def test_resume_company_max_length_validation(self):
        """Test that company field enforces max length at model level."""
        data = ResumeData(
            user_id=1,
            name="Test Resume",
            content="Test content",
            company="A" * 255,
        )
        resume = Resume(data=data)
        assert len(resume.company) == 255

    def test_resume_with_all_fields(self):
        """Test Resume initialization with all fields including company."""
        data = ResumeData(
            user_id=1,
            name="Complete Resume",
            content="# Resume Content",
            is_base=False,
            parent_id=5,
            job_description="Job description here",
            notes="Some notes",
            introduction="AI-generated intro",
            company="Tech Corp Inc.",
            export_settings_include_projects=False,
            export_settings_render_projects_first=True,
            export_settings_include_education=False,
        )
        resume = Resume(data=data)
        assert resume.user_id == 1
        assert resume.name == "Complete Resume"
        assert resume.content == "# Resume Content"
        assert resume.is_base is False
        assert resume.parent_id == 5
        assert resume.job_description == "Job description here"
        assert resume.notes == "Some notes"
        assert resume.introduction == "AI-generated intro"
        assert resume.company == "Tech Corp Inc."
        assert resume.export_settings_include_projects is False
        assert resume.export_settings_render_projects_first is True
        assert resume.export_settings_include_education is False
