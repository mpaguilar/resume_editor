import logging

import pytest

from resume_editor.app.models.user_settings import UserSettings

log = logging.getLogger(__name__)


def test_user_settings_initialization():
    """
    Test UserSettings initialization.

    Args:
        None

    Returns:
        None

    Notes:
        1. Create a UserSettings instance with all parameters.
        2. Assert that all attributes are set correctly.
    """
    _msg = "Testing UserSettings initialization"
    log.info(_msg)
    user_settings = UserSettings(
        user_id=1,
        llm_endpoint="http://localhost:11434",
        llm_model_name="test-model",
        encrypted_api_key="encrypted-key",
    )
    assert user_settings.user_id == 1
    assert user_settings.llm_endpoint == "http://localhost:11434"
    assert user_settings.llm_model_name == "test-model"
    assert user_settings.encrypted_api_key == "encrypted-key"


def test_user_settings_initialization_with_defaults():
    """
    Test UserSettings initialization with default values.

    Args:
        None

    Returns:
        None

    Notes:
        1. Create a UserSettings instance with only required parameters.
        2. Assert that attributes with defaults are None.
    """
    _msg = "Testing UserSettings initialization with defaults"
    log.info(_msg)
    user_settings = UserSettings(user_id=1)
    assert user_settings.user_id == 1
    assert user_settings.llm_endpoint is None
    assert user_settings.llm_model_name is None
    assert user_settings.encrypted_api_key is None
