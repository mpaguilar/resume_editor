"""Unit tests for the rendering_settings module."""
import pytest

from resume_editor.app.core.rendering_settings import (
    EXEC_SUMMARY_SETTINGS,
    GENERAL_SETTINGS,
    get_render_settings,
)


def test_get_render_settings_general():
    """Test get_render_settings for 'general' settings."""
    settings = get_render_settings(name="general")
    assert settings == GENERAL_SETTINGS


def test_get_render_settings_exec_summary():
    """Test get_render_settings for 'executive_summary' settings."""
    settings = get_render_settings(name="executive_summary")
    assert settings == EXEC_SUMMARY_SETTINGS


def test_get_render_settings_invalid_name():
    """Test that get_render_settings raises ValueError for an invalid name."""
    with pytest.raises(ValueError):
        get_render_settings(name="invalid_name")
