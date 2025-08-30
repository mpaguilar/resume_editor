import logging
from unittest.mock import Mock, patch

from resume_editor.app.api.routes.route_logic.settings_crud import (
    get_user_settings,
    update_user_settings,
)
from resume_editor.app.models.user_settings import UserSettings
from resume_editor.app.schemas.user import UserSettingsUpdateRequest

log = logging.getLogger(__name__)


def test_get_user_settings_found():
    """Test get_user_settings when settings are found."""
    mock_db = Mock()
    mock_user_settings = UserSettings(user_id=1, llm_endpoint="http://test.com")
    mock_db.query.return_value.filter.return_value.first.return_value = (
        mock_user_settings
    )

    settings = get_user_settings(mock_db, 1)

    assert settings is not None
    assert settings.user_id == 1
    assert settings.llm_endpoint == "http://test.com"
    mock_db.query.assert_called_once_with(UserSettings)
    mock_db.query.return_value.filter.assert_called_once()
    mock_db.query.return_value.filter.return_value.first.assert_called_once()


def test_get_user_settings_not_found():
    """Test get_user_settings when settings are not found."""
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    settings = get_user_settings(mock_db, 1)

    assert settings is None
    mock_db.query.assert_called_once_with(UserSettings)


@patch("resume_editor.app.api.routes.route_logic.settings_crud.encrypt_data")
@patch("resume_editor.app.api.routes.route_logic.settings_crud.get_user_settings")
def test_update_user_settings_existing_settings(mock_get_settings, mock_encrypt_data):
    """Test updating existing user settings."""
    mock_db = Mock()
    existing_settings = UserSettings(user_id=1)
    mock_get_settings.return_value = existing_settings
    mock_encrypt_data.return_value = "encrypted_key"

    update_data = UserSettingsUpdateRequest(
        llm_endpoint="http://new.com", api_key="new_key"
    )

    result = update_user_settings(mock_db, 1, update_data)

    mock_get_settings.assert_called_once_with(db=mock_db, user_id=1)
    assert result.llm_endpoint == "http://new.com"
    mock_encrypt_data.assert_called_once_with(data="new_key")
    assert result.encrypted_api_key == "encrypted_key"
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(existing_settings)
    mock_db.add.assert_not_called()


@patch("resume_editor.app.api.routes.route_logic.settings_crud.encrypt_data")
@patch("resume_editor.app.api.routes.route_logic.settings_crud.get_user_settings")
def test_update_user_settings_new_settings(mock_get_settings, mock_encrypt_data):
    """Test creating new user settings if none exist."""
    mock_db = Mock()
    mock_get_settings.return_value = None
    mock_encrypt_data.return_value = "encrypted_key"

    update_data = UserSettingsUpdateRequest(
        llm_endpoint="http://new.com", api_key="new_key"
    )

    with patch(
        "resume_editor.app.api.routes.route_logic.settings_crud.UserSettings"
    ) as mock_user_settings_model:
        mock_settings_instance = Mock()
        mock_user_settings_model.return_value = mock_settings_instance

        result = update_user_settings(mock_db, 1, update_data)

        mock_get_settings.assert_called_once_with(db=mock_db, user_id=1)
        mock_user_settings_model.assert_called_once_with(user_id=1)
        mock_db.add.assert_called_once_with(mock_settings_instance)

        assert mock_settings_instance.llm_endpoint == "http://new.com"
        mock_encrypt_data.assert_called_once_with(data="new_key")
        assert mock_settings_instance.encrypted_api_key == "encrypted_key"

        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_settings_instance)
        assert result == mock_settings_instance


@patch("resume_editor.app.api.routes.route_logic.settings_crud.encrypt_data")
@patch("resume_editor.app.api.routes.route_logic.settings_crud.get_user_settings")
def test_update_user_settings_remove_api_key(mock_get_settings, mock_encrypt_data):
    """Test removing an API key by providing an empty string."""
    mock_db = Mock()
    existing_settings = UserSettings(user_id=1, encrypted_api_key="old_encrypted_key")
    mock_get_settings.return_value = existing_settings

    update_data = UserSettingsUpdateRequest(api_key="")

    result = update_user_settings(mock_db, 1, update_data)

    mock_get_settings.assert_called_once_with(db=mock_db, user_id=1)
    assert result.encrypted_api_key is None
    mock_encrypt_data.assert_not_called()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(existing_settings)


@patch("resume_editor.app.api.routes.route_logic.settings_crud.get_user_settings")
def test_update_user_settings_remove_endpoint(mock_get_settings):
    """Test removing an llm_endpoint by providing an empty string."""
    mock_db = Mock()
    existing_settings = UserSettings(user_id=1, llm_endpoint="http://old-url.com")
    mock_get_settings.return_value = existing_settings

    update_data = UserSettingsUpdateRequest(llm_endpoint="")

    result = update_user_settings(mock_db, 1, update_data)

    mock_get_settings.assert_called_once_with(db=mock_db, user_id=1)
    assert result.llm_endpoint is None
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(existing_settings)


@patch("resume_editor.app.api.routes.route_logic.settings_crud.encrypt_data")
@patch("resume_editor.app.api.routes.route_logic.settings_crud.get_user_settings")
def test_update_user_settings_no_api_key_change(mock_get_settings, mock_encrypt_data):
    """Test that API key is not changed when not provided."""
    mock_db = Mock()
    existing_settings = UserSettings(user_id=1, encrypted_api_key="old_encrypted_key")
    mock_get_settings.return_value = existing_settings

    # api_key is None by default in UserSettingsUpdateRequest
    update_data = UserSettingsUpdateRequest(llm_endpoint="http://some-url.com")

    result = update_user_settings(mock_db, 1, update_data)

    mock_get_settings.assert_called_once_with(db=mock_db, user_id=1)
    assert result.llm_endpoint == "http://some-url.com"
    assert result.encrypted_api_key == "old_encrypted_key"
    mock_encrypt_data.assert_not_called()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(existing_settings)


@patch("resume_editor.app.api.routes.route_logic.settings_crud.encrypt_data")
@patch("resume_editor.app.api.routes.route_logic.settings_crud.get_user_settings")
def test_update_user_settings_no_endpoint_change(mock_get_settings, mock_encrypt_data):
    """Test that endpoint is not changed when not provided."""
    mock_db = Mock()
    existing_settings = UserSettings(user_id=1, llm_endpoint="http://old-url.com")
    mock_get_settings.return_value = existing_settings
    mock_encrypt_data.return_value = "encrypted_key"

    # llm_endpoint is None by default
    update_data = UserSettingsUpdateRequest(api_key="new_key")

    result = update_user_settings(mock_db, 1, update_data)

    # The old value should be preserved
    assert result.llm_endpoint == "http://old-url.com"
    assert result.encrypted_api_key == "encrypted_key"
    mock_encrypt_data.assert_called_once_with(data="new_key")
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(existing_settings)
