from unittest.mock import MagicMock, patch

import pytest
from cryptography.fernet import InvalidToken

from resume_editor.app.api.routes.route_logic.resume_ai_logic import get_llm_config
from resume_editor.app.models.user_settings import UserSettings


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.decrypt_data")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_user_settings")
def test_get_llm_config_with_key(mock_get_user_settings, mock_decrypt_data):
    """Test get_llm_config when user settings and API key exist."""
    # Arrange
    mock_db = MagicMock()
    user_id = 1
    mock_settings = UserSettings(
        user_id=user_id,
        llm_endpoint="http://example.com",
        llm_model_name="test-model",
        encrypted_api_key="encrypted_key",
    )
    mock_get_user_settings.return_value = mock_settings
    mock_decrypt_data.return_value = "decrypted_key"

    # Act
    llm_endpoint, llm_model_name, api_key = get_llm_config(mock_db, user_id)

    # Assert
    assert llm_endpoint == "http://example.com"
    assert llm_model_name == "test-model"
    assert api_key == "decrypted_key"
    mock_get_user_settings.assert_called_once_with(mock_db, user_id)
    mock_decrypt_data.assert_called_once_with("encrypted_key")


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.decrypt_data")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_user_settings")
def test_get_llm_config_no_key(mock_get_user_settings, mock_decrypt_data):
    """Test get_llm_config when user settings exist but no API key."""
    # Arrange
    mock_db = MagicMock()
    user_id = 1
    mock_settings = UserSettings(
        user_id=user_id,
        llm_endpoint="http://example.com",
        llm_model_name="test-model",
        encrypted_api_key=None,
    )
    mock_get_user_settings.return_value = mock_settings

    # Act
    llm_endpoint, llm_model_name, api_key = get_llm_config(mock_db, user_id)

    # Assert
    assert llm_endpoint == "http://example.com"
    assert llm_model_name == "test-model"
    assert api_key is None
    mock_get_user_settings.assert_called_once_with(mock_db, user_id)
    mock_decrypt_data.assert_not_called()


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_user_settings")
def test_get_llm_config_no_settings(mock_get_user_settings):
    """Test get_llm_config when user has no settings."""
    # Arrange
    mock_db = MagicMock()
    user_id = 1
    mock_get_user_settings.return_value = None

    # Act
    llm_endpoint, llm_model_name, api_key = get_llm_config(mock_db, user_id)

    # Assert
    assert llm_endpoint is None
    assert llm_model_name is None
    assert api_key is None
    mock_get_user_settings.assert_called_once_with(mock_db, user_id)


@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.decrypt_data")
@patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.get_user_settings")
def test_get_llm_config_decryption_error(mock_get_user_settings, mock_decrypt_data):
    """Test get_llm_config raises InvalidToken on decryption failure."""
    # Arrange
    mock_db = MagicMock()
    user_id = 1
    mock_settings = UserSettings(
        user_id=user_id, encrypted_api_key="bad_encrypted_key"
    )
    mock_get_user_settings.return_value = mock_settings
    mock_decrypt_data.side_effect = InvalidToken

    # Act & Assert
    with pytest.raises(InvalidToken):
        get_llm_config(mock_db, user_id)
    mock_decrypt_data.assert_called_once_with("bad_encrypted_key")
