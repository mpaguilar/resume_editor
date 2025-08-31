import logging
from unittest.mock import Mock, patch

from sqlalchemy.orm import Session

from resume_editor.app.api.routes.route_logic.settings_crud import (
    get_user_settings,
    update_user_settings,
)
from resume_editor.app.models.user_settings import UserSettings
from resume_editor.app.schemas.user import UserSettingsUpdateRequest

log = logging.getLogger(__name__)


def test_get_user_settings():
    """Test retrieving user settings when they exist."""
    mock_db = Mock(spec=Session)
    user_id = 1
    mock_settings = UserSettings(user_id=user_id, llm_endpoint="http://example.com")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_settings

    result = get_user_settings(db=mock_db, user_id=user_id)

    mock_db.query.assert_called_once_with(UserSettings)
    mock_db.query.return_value.filter.assert_called_once()
    assert result == mock_settings


def test_get_user_settings_not_found():
    """Test retrieving user settings when they do not exist."""
    mock_db = Mock(spec=Session)
    user_id = 1
    mock_db.query.return_value.filter.return_value.first.return_value = None

    result = get_user_settings(db=mock_db, user_id=user_id)

    mock_db.query.assert_called_once_with(UserSettings)
    assert result is None


@patch("resume_editor.app.api.routes.route_logic.settings_crud.encrypt_data")
@patch("resume_editor.app.api.routes.route_logic.settings_crud.get_user_settings")
def test_update_user_settings_no_existing(mock_get_settings, mock_encrypt):
    """Test updating user settings when none exist, creating new settings."""
    mock_db = Mock(spec=Session)
    user_id = 1
    mock_get_settings.return_value = None
    mock_encrypt.return_value = "encrypted_key"

    update_data = UserSettingsUpdateRequest(
        llm_endpoint="http://new.com",
        api_key="new_key",
    )

    result = update_user_settings(
        db=mock_db,
        user_id=user_id,
        settings_data=update_data,
    )

    mock_get_settings.assert_called_once_with(db=mock_db, user_id=user_id)
    mock_db.add.assert_called_once()
    new_settings = mock_db.add.call_args[0][0]
    assert isinstance(new_settings, UserSettings)
    assert new_settings.user_id == user_id
    assert new_settings.llm_endpoint == "http://new.com"
    mock_encrypt.assert_called_once_with(data="new_key")
    assert new_settings.encrypted_api_key == "encrypted_key"

    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(new_settings)
    assert result == new_settings


@patch("resume_editor.app.api.routes.route_logic.settings_crud.encrypt_data")
@patch("resume_editor.app.api.routes.route_logic.settings_crud.get_user_settings")
def test_update_user_settings_with_existing(mock_get_settings, mock_encrypt):
    """Test updating existing user settings with new values."""
    mock_db = Mock(spec=Session)
    user_id = 1
    existing_settings = UserSettings(
        user_id=1,
        llm_endpoint="http://old.com",
        encrypted_api_key="old_encrypted_key",
    )
    mock_get_settings.return_value = existing_settings
    mock_encrypt.return_value = "encrypted_new_key"

    update_data = UserSettingsUpdateRequest(
        llm_endpoint="http://new.com",
        api_key="new_key",
    )

    result = update_user_settings(
        db=mock_db,
        user_id=user_id,
        settings_data=update_data,
    )

    mock_get_settings.assert_called_once_with(db=mock_db, user_id=user_id)
    mock_db.add.assert_not_called()

    assert existing_settings.llm_endpoint == "http://new.com"
    mock_encrypt.assert_called_once_with(data="new_key")
    assert existing_settings.encrypted_api_key == "encrypted_new_key"

    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(existing_settings)
    assert result == existing_settings


@patch("resume_editor.app.api.routes.route_logic.settings_crud.encrypt_data")
@patch("resume_editor.app.api.routes.route_logic.settings_crud.get_user_settings")
def test_update_user_settings_clear_values(mock_get_settings, mock_encrypt):
    """Test clearing user settings by providing empty strings."""
    mock_db = Mock(spec=Session)
    user_id = 1
    existing_settings = UserSettings(
        user_id=1,
        llm_endpoint="http://old.com",
        encrypted_api_key="old_encrypted_key",
    )
    mock_get_settings.return_value = existing_settings

    update_data = UserSettingsUpdateRequest(llm_endpoint="", api_key="")

    result = update_user_settings(
        db=mock_db,
        user_id=user_id,
        settings_data=update_data,
    )

    mock_get_settings.assert_called_once_with(db=mock_db, user_id=user_id)
    assert existing_settings.llm_endpoint is None
    assert existing_settings.encrypted_api_key is None
    mock_encrypt.assert_not_called()

    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(existing_settings)
    assert result == existing_settings


@patch("resume_editor.app.api.routes.route_logic.settings_crud.encrypt_data")
@patch("resume_editor.app.api.routes.route_logic.settings_crud.get_user_settings")
def test_update_user_settings_partial_update_key(mock_get_settings, mock_encrypt):
    """Test updating only the api_key."""
    mock_db = Mock(spec=Session)
    user_id = 1
    existing_settings = UserSettings(
        user_id=1,
        llm_endpoint="http://old.com",
        encrypted_api_key="old_encrypted_key",
    )
    mock_get_settings.return_value = existing_settings
    mock_encrypt.return_value = "encrypted_new_key"

    # Update only api_key
    update_data = UserSettingsUpdateRequest(api_key="new_key")

    result = update_user_settings(
        db=mock_db,
        user_id=user_id,
        settings_data=update_data,
    )

    assert existing_settings.llm_endpoint == "http://old.com"  # Should not change
    mock_encrypt.assert_called_once_with(data="new_key")
    assert existing_settings.encrypted_api_key == "encrypted_new_key"

    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(existing_settings)
    assert result == existing_settings


@patch("resume_editor.app.api.routes.route_logic.settings_crud.encrypt_data")
@patch("resume_editor.app.api.routes.route_logic.settings_crud.get_user_settings")
def test_update_user_settings_partial_update_endpoint(mock_get_settings, mock_encrypt):
    """Test updating only the llm_endpoint."""
    mock_db = Mock(spec=Session)
    user_id = 1
    existing_settings = UserSettings(
        user_id=1,
        llm_endpoint="http://old.com",
        encrypted_api_key="old_encrypted_key",
    )
    mock_get_settings.return_value = existing_settings

    # Update only llm_endpoint
    update_data = UserSettingsUpdateRequest(llm_endpoint="http://verynew.com")
    result = update_user_settings(
        db=mock_db,
        user_id=user_id,
        settings_data=update_data,
    )

    assert existing_settings.llm_endpoint == "http://verynew.com"
    assert (
        existing_settings.encrypted_api_key == "old_encrypted_key"
    )  # Should not change
    mock_encrypt.assert_not_called()

    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(existing_settings)
    assert result == existing_settings
