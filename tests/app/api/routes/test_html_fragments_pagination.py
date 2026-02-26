import logging
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from resume_editor.app.api.routes.html_fragments import (
    GenerateResumeListHtmlParams,
    _generate_resume_list_html,
)
from resume_editor.app.models.resume_model import Resume as DatabaseResume, ResumeData
from resume_editor.app.models.user import User as DBUser, UserData

log = logging.getLogger(__name__)


@pytest.fixture
def test_user():
    """Fixture for a test user."""
    user = DBUser(
        data=UserData(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            id_=1,
        )
    )
    return user


@pytest.fixture
def test_resume(test_user):
    """Fixture for a test resume."""
    resume_data = ResumeData(
        user_id=test_user.id,
        name="Test Resume",
        content="some content",
    )
    resume = DatabaseResume(data=resume_data)
    resume.id = 1
    resume.created_at = datetime(2023, 1, 15)
    resume.updated_at = datetime(2023, 1, 16)
    return resume


@pytest.fixture
def test_refined_resume(test_user):
    """Fixture for a test refined resume."""
    resume_data = ResumeData(
        user_id=test_user.id,
        name="Refined Resume",
        content="some refined content",
        is_base=False,
        parent_id=1,
    )
    resume = DatabaseResume(data=resume_data)
    resume.id = 2
    resume.created_at = datetime(2023, 2, 20)
    resume.updated_at = datetime(2023, 2, 21)
    return resume


class TestGenerateResumeListHtmlPagination:
    """Tests for _generate_resume_list_html pagination features."""

    def test_generate_resume_list_html_includes_pagination_params(self, test_resume):
        """Test that _generate_resume_list_html passes pagination params to template."""
        with patch("resume_editor.app.api.routes.html_fragments.env") as mock_env:
            mock_template = MagicMock()
            mock_env.get_template.return_value = mock_template

            _generate_resume_list_html(
                GenerateResumeListHtmlParams(
                    base_resumes=[test_resume],
                    refined_resumes=[],
                    selected_resume_id=None,
                    sort_by="name_asc",
                    week_offset=-1,
                    has_older_resumes=True,
                    has_newer_resumes=True,
                    current_filter="engineer",
                    week_start=datetime(2026, 2, 18),
                    week_end=datetime(2026, 2, 25),
                    wrap_in_div=False,
                )
            )

            call_kwargs = mock_template.render.call_args[1]
            assert call_kwargs["week_offset"] == -1
            assert call_kwargs["has_older_resumes"] is True
            assert call_kwargs["has_newer_resumes"] is True
            assert call_kwargs["current_filter"] == "engineer"
            assert call_kwargs["week_start"] == datetime(2026, 2, 18)
            assert call_kwargs["week_end"] == datetime(2026, 2, 25)

    def test_generate_resume_list_html_default_pagination_values(self, test_resume):
        """Test that _generate_resume_list_html uses correct defaults for pagination."""
        with patch("resume_editor.app.api.routes.html_fragments.env") as mock_env:
            mock_template = MagicMock()
            mock_env.get_template.return_value = mock_template

            _generate_resume_list_html(
                GenerateResumeListHtmlParams(
                    base_resumes=[test_resume],
                    refined_resumes=[],
                )
            )

            call_kwargs = mock_template.render.call_args[1]
            assert call_kwargs["week_offset"] == 0
            assert call_kwargs["has_older_resumes"] is False
            assert call_kwargs["has_newer_resumes"] is False
            assert call_kwargs["current_filter"] is None
            assert call_kwargs["week_start"] is None
            assert call_kwargs["week_end"] is None

    def test_generate_resume_list_html_wrap_in_div_with_pagination(self, test_resume):
        """Test wrap_in_div with pagination params."""
        with patch("resume_editor.app.api.routes.html_fragments.env") as mock_env:
            mock_template = MagicMock()
            mock_template.render.return_value = "<div>content</div>"
            mock_env.get_template.return_value = mock_template

            result = _generate_resume_list_html(
                GenerateResumeListHtmlParams(
                    base_resumes=[test_resume],
                    refined_resumes=[],
                    week_offset=-2,
                    wrap_in_div=True,
                )
            )

            assert result == '<div id="resume-list"><div>content</div></div>'

    def test_generate_resume_list_html_preserves_sort_by(self, test_resume):
        """Test that sort_by is passed through correctly."""
        with patch("resume_editor.app.api.routes.html_fragments.env") as mock_env:
            mock_template = MagicMock()
            mock_env.get_template.return_value = mock_template

            _generate_resume_list_html(
                GenerateResumeListHtmlParams(
                    base_resumes=[test_resume],
                    refined_resumes=[],
                    sort_by="created_at_desc",
                    week_offset=0,
                )
            )

            call_kwargs = mock_template.render.call_args[1]
            assert call_kwargs["sort_by"] == "created_at_desc"
