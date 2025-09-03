import logging
from unittest.mock import MagicMock, patch

from resume_editor.app.api.routes.route_logic.settings_crud import (
    get_user_settings,
    update_user_settings,
)
from resume_editor.app.models.user_settings import UserSettings
from resume_editor.app.schemas.user import UserSettingsUpdateRequest

log = logging.getLogger(__name__)


def test_get_user_settings_found():
    """
    Test Case: Retrieve existing user settings.
    """
    # Arrange
    db = MagicMock()
    user_id = 1
    expected_settings = UserSettings(user_id=user_id)
    db.query.return_value.filter.return_value.first.return_value = expected_settings

    # Act
    settings = get_user_settings(db=db, user_id=user_id)

    # Assert
    assert settings == expected_settings
    db.query.assert_called_once_with(UserSettings)
    db.query.return_value.filter.assert_called_once()
    db.query.return_value.filter.return_value.first.assert_called_once()


def test_get_user_settings_not_found():
    """
    Test Case: Attempt to retrieve settings for a user who has none.
    """
    # Arrange
    db = MagicMock()
    user_id = 1
    db.query.return_value.filter.return_value.first.return_value = None

    # Act
    settings = get_user_settings(db=db, user_id=user_id)

    # Assert
    assert settings is None
    db.query.assert_called_once_with(UserSettings)
    db.query.return_value.filter.assert_called_once()
    db.query.return_value.filter.return_value.first.assert_called_once()


@patch("resume_editor.app.api.routes.route_logic.settings_crud.get_user_settings")
def test_update_user_settings_create_new_with_llm_model_name(mock_get_settings):
    """
    Test Case 2: llm_model_name is correctly saved when update_user_settings is called
    for a user who does not have any settings yet, causing a new record to be created.
    """
    # Arrange
    db = MagicMock()
    user_id = 1
    mock_get_settings.return_value = None
    settings_data = type(
        "MockSettings", (), {"llm_model_name": "new-model", "llm_endpoint": None, "api_key": None}
    )()

    # Act
    result = update_user_settings(db=db, user_id=user_id, settings_data=settings_data)

    # Assert
    mock_get_settings.assert_called_once_with(db=db, user_id=user_id)
    db.add.assert_called_once()
    created_settings = db.add.call_args[0][0]
    assert isinstance(created_settings, UserSettings)
    assert created_settings.user_id == user_id
    assert created_settings.llm_model_name == "new-model"
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(created_settings)
    assert result == created_settings


@patch("resume_editor.app.api.routes.route_logic.settings_crud.get_user_settings")
def test_update_user_settings_update_existing_llm_model_name(mock_get_settings):
    """
    Test Case 1 (Update existing): Test that calling update_user_settings with a new
    llm_model_name successfully updates the field for a user with pre-existing settings.
    """
    # Arrange
    db = MagicMock()
    user_id = 1
    existing_settings = UserSettings(user_id=user_id, llm_model_name="old-model")
    mock_get_settings.return_value = existing_settings
    settings_data = type(
        "MockSettings", (), {"llm_model_name": "new-model", "llm_endpoint": None, "api_key": None}
    )()

    # Act
    result = update_user_settings(db=db, user_id=user_id, settings_data=settings_data)

    # Assert
    mock_get_settings.assert_called_once_with(db=db, user_id=user_id)
    assert existing_settings.llm_model_name == "new-model"
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(existing_settings)
    assert result == existing_settings


@patch("resume_editor.app.api.routes.route_logic.settings_crud.get_user_settings")
def test_update_user_settings_clear_llm_model_name(mock_get_settings):
    """
    Test Case 3 (Clear value): Test that providing an empty string for llm_model_name
    in the payload results in the database field being set to NULL.
    """
    # Arrange
    db = MagicMock()
    user_id = 1
    existing_settings = UserSettings(user_id=user_id, llm_model_name="some-model")
    mock_get_settings.return_value = existing_settings
    settings_data = type(
        "MockSettings", (), {"llm_model_name": "", "llm_endpoint": None, "api_key": None}
    )()

    # Act
    result = update_user_settings(db=db, user_id=user_id, settings_data=settings_data)

    # Assert
    mock_get_settings.assert_called_once_with(db=db, user_id=user_id)
    assert existing_settings.llm_model_name is None
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(existing_settings)
    assert result == existing_settings


@patch("resume_editor.app.api.routes.route_logic.settings_crud.encrypt_data")
@patch("resume_editor.app.api.routes.route_logic.settings_crud.get_user_settings")
def test_update_user_settings_no_change_to_llm_model_name(
    mock_get_settings, mock_encrypt
):
    """
    Test Case 4 (No change): Test that updating other settings (e.g., api_key)
    does not inadvertently change an existing llm_model_name.
    """
    # Arrange
    db = MagicMock()
    user_id = 1
    existing_settings = UserSettings(user_id=user_id, llm_model_name="stable-model")
    mock_get_settings.return_value = existing_settings
    mock_encrypt.return_value = "encrypted-key"

    # llm_model_name is not provided in a real request, so it will not be in the pydantic model
    settings_data = UserSettingsUpdateRequest(
        api_key="new-api-key", llm_model_name=None
    )

    # Act
    result = update_user_settings(db=db, user_id=user_id, settings_data=settings_data)

    # Assert
    mock_get_settings.assert_called_once_with(db=db, user_id=user_id)
    assert existing_settings.llm_model_name == "stable-model"
    assert existing_settings.encrypted_api_key == "encrypted-key"
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(existing_settings)
    assert result == existing_settings


@patch("resume_editor.app.api.routes.route_logic.settings_crud.get_user_settings")
def test_update_user_settings_update_llm_endpoint(mock_get_settings):
    """
    Test Case: Update existing user settings with a new llm_endpoint.
    """
    # Arrange
    db = MagicMock()
    user_id = 1
    existing_settings = UserSettings(user_id=user_id, llm_endpoint="old-endpoint")
    mock_get_settings.return_value = existing_settings
    settings_data = UserSettingsUpdateRequest(llm_endpoint="new-endpoint")

    # Act
    result = update_user_settings(db=db, user_id=user_id, settings_data=settings_data)

    # Assert
    mock_get_settings.assert_called_once_with(db=db, user_id=user_id)
    assert existing_settings.llm_endpoint == "new-endpoint"
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(existing_settings)
    assert result == existing_settings


@patch("resume_editor.app.api.routes.route_logic.settings_crud.get_user_settings")
def test_update_user_settings_clear_llm_endpoint(mock_get_settings):
    """
    Test Case: Clear llm_endpoint by providing an empty string.
    """
    # Arrange
    db = MagicMock()
    user_id = 1
    existing_settings = UserSettings(user_id=user_id, llm_endpoint="old-endpoint")
    mock_get_settings.return_value = existing_settings
    settings_data = UserSettingsUpdateRequest(llm_endpoint="")

    # Act
    result = update_user_settings(db=db, user_id=user_id, settings_data=settings_data)

    # Assert
    mock_get_settings.assert_called_once_with(db=db, user_id=user_id)
    assert existing_settings.llm_endpoint is None
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(existing_settings)
    assert result == existing_settings


@patch("resume_editor.app.api.routes.route_logic.settings_crud.encrypt_data")
@patch("resume_editor.app.api.routes.route_logic.settings_crud.get_user_settings")
def test_update_user_settings_clear_api_key(mock_get_settings, mock_encrypt):
    """
    Test Case: Clear api_key by providing an empty string.
    """
    # Arrange
    db = MagicMock()
    user_id = 1
    existing_settings = UserSettings(user_id=user_id, encrypted_api_key="old-key")
    mock_get_settings.return_value = existing_settings
    settings_data = UserSettingsUpdateRequest(api_key="")

    # Act
    result = update_user_settings(db=db, user_id=user_id, settings_data=settings_data)

    # Assert
    mock_get_settings.assert_called_once_with(db=db, user_id=user_id)
    assert existing_settings.encrypted_api_key is None
    mock_encrypt.assert_not_called()
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(existing_settings)
    assert result == existing_settings
