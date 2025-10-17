import pytest

from resume_editor.app.core.rendering_settings import get_render_settings


def test_get_render_settings_general():
    """Test get_render_settings for 'general' settings."""
    settings = get_render_settings("general")
    assert settings["education"] is True
    assert settings["section"]["education"]["degrees"] is True
    assert settings["section"]["education"]["school"] is True
    assert settings["section"]["education"]["degree"] is True
    assert settings["section"]["education"]["start_date"] is True
    assert settings["section"]["education"]["end_date"] is True


def test_get_render_settings_exec_summary():
    """Test get_render_settings for 'executive_summary' settings."""
    settings = get_render_settings("executive_summary")
    assert settings["education"] is True
    assert settings["section"]["education"]["degrees"] is True
    assert settings["section"]["education"]["school"] is True
    assert settings["section"]["education"]["degree"] is True
    assert settings["section"]["education"]["start_date"] is True
    assert settings["section"]["education"]["end_date"] is True


def test_get_render_settings_invalid_name():
    """Test that get_render_settings raises ValueError for an invalid name."""
    with pytest.raises(ValueError, match="Unknown render setting name: invalid_name"):
        get_render_settings("invalid_name")
