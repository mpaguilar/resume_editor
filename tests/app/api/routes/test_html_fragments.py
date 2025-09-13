from unittest.mock import MagicMock, patch

import pytest

from resume_editor.app.api.routes.html_fragments import (
    _create_refine_result_html,
    _generate_resume_detail_html,
    _generate_resume_list_html,
)
from resume_editor.app.models.resume_model import Resume as DatabaseResume
from resume_editor.app.models.user import User as DBUser


@pytest.fixture
def test_user():
    """Fixture for a test user."""
    user = DBUser(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
    )
    user.id = 1
    return user


@pytest.fixture
def test_resume(test_user):
    """Fixture for a test resume."""
    resume = DatabaseResume(
        user_id=test_user.id,
        name="Test Resume",
        content="some content",
    )
    resume.id = 1
    return resume


def test_generate_resume_list_html_empty():
    """Test that _generate_resume_list_html returns the correct message for an empty list."""
    with patch("resume_editor.app.api.routes.html_fragments.env") as mock_env:
        mock_template = MagicMock()
        mock_env.get_template.return_value = mock_template
        _generate_resume_list_html([])
        mock_env.get_template.assert_called_once_with(
            "partials/resume/_resume_list.html"
        )
        mock_template.render.assert_called_once_with(
            resumes=[], selected_resume_id=None
        )


def test_generate_resume_list_html(test_resume):
    """Test that _generate_resume_list_html correctly handles no selection."""
    with patch("resume_editor.app.api.routes.html_fragments.env") as mock_env:
        mock_template = MagicMock()
        mock_env.get_template.return_value = mock_template
        resumes = [test_resume]
        _generate_resume_list_html(resumes)
        mock_env.get_template.assert_called_once_with(
            "partials/resume/_resume_list.html"
        )
        mock_template.render.assert_called_once_with(
            resumes=resumes, selected_resume_id=None
        )


def test_generate_resume_list_html_template(test_resume):
    """Test that _generate_resume_list_html renders the correct template."""
    with patch("resume_editor.app.api.routes.html_fragments.env") as mock_env:
        mock_template = MagicMock()
        mock_env.get_template.return_value = mock_template
        resumes = [test_resume]
        selected_id = 1
        _generate_resume_list_html(resumes, selected_id)
        mock_env.get_template.assert_called_once_with(
            "partials/resume/_resume_list.html"
        )
        mock_template.render.assert_called_once_with(
            resumes=resumes, selected_resume_id=selected_id
        )


def test_generate_resume_detail_html_template_usage(test_resume):
    """Test that _generate_resume_detail_html renders via template."""
    with patch("resume_editor.app.api.routes.html_fragments.env") as mock_env:
        mock_template = MagicMock()
        mock_env.get_template.return_value = mock_template
        _generate_resume_detail_html(test_resume)
        mock_env.get_template.assert_called_once_with(
            "partials/resume/_resume_detail.html"
        )
        mock_template.render.assert_called_once_with(resume=test_resume)


def test_create_refine_result_html_template():
    """Test that _create_refine_result_html renders the correct template."""
    resume_id = 123
    target_section_val = "experience"
    refined_content = "some <refined> content"

    with patch("resume_editor.app.api.routes.html_fragments.env") as mock_env:
        mock_template = MagicMock()
        mock_env.get_template.return_value = mock_template
        _create_refine_result_html(resume_id, target_section_val, refined_content)
        mock_env.get_template.assert_called_once_with(
            "partials/resume/_refine_result.html"
        )
        mock_template.render.assert_called_once_with(
            resume_id=resume_id,
            target_section_val=target_section_val,
            refined_content=refined_content,
        )


def test_create_refine_result_html_output():
    """Test that the rendered HTML from _create_refine_result_html is correct."""
    resume_id = 42
    target_section_val = "experience"
    refined_content = "This is *refined* markdown."

    html_output = _create_refine_result_html(
        resume_id, target_section_val, refined_content
    )

    assert 'id="refine-result"' in html_output
    assert 'hx-post="/api/resumes/42/refine/accept"' in html_output
    assert 'name="target_section" value="experience"' in html_output
    assert '<textarea name="refined_content"' in html_output
    assert ">This is *refined* markdown.</textarea>" in html_output
    assert 'hx-post="/api/resumes/42/refine/save_as_new"' in html_output
    assert "Accept & Overwrite" in html_output
    assert 'href="/resumes/42/edit"' in html_output
    assert "Discard" in html_output
    assert "Save as New" in html_output
    assert "Reject" not in html_output
