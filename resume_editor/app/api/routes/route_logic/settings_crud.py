import logging
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from resume_editor.app.core.security import encrypt_data
from resume_editor.app.models.user_settings import UserSettings

if TYPE_CHECKING:
    from resume_editor.app.schemas.user import UserSettingsUpdateRequest


log = logging.getLogger(__name__)


def get_user_settings(db: Session, user_id: int) -> UserSettings | None:
    """Retrieves the settings for a given user.

    Args:
        db (Session): The database session used to query the database.
        user_id (int): The unique identifier of the user whose settings are being retrieved.

    Returns:
        UserSettings | None: The user's settings if found, otherwise None.

    Notes:
        1. Queries the database for a UserSettings record where user_id matches the provided user_id.
        2. Returns the first matching record or None if no record is found.
        3. This function performs a single database read operation.

    """
    _msg = f"Getting settings for user_id: {user_id}"
    log.debug(_msg)
    return db.query(UserSettings).filter(UserSettings.user_id == user_id).first()


def _get_or_create_user_settings(
    db: Session,
    user_id: int,
) -> UserSettings:
    """Get existing settings or create new ones for a user.

    Args:
        db (Session): The database session.
        user_id (int): The user ID to get or create settings for.

    Returns:
        UserSettings: The existing or newly created settings object.

    Notes:
        1. Attempt to retrieve existing settings using get_user_settings.
        2. If not found, create a new UserSettings object and add to session.
        3. Return the settings object.

    """
    settings = get_user_settings(db=db, user_id=user_id)
    if not settings:
        _msg = f"No settings found for user_id: {user_id}. Creating new settings."
        log.debug(_msg)
        settings = UserSettings(user_id=user_id)
        db.add(settings)
    return settings


def _update_optional_string_field(
    settings: UserSettings,
    field_name: str,
    value: str | None,
) -> None:
    """Update a string field if value is not None.

    Args:
        settings (UserSettings): The settings object to update.
        field_name (str): The name of the field to update.
        value (str | None): The new value, or None to skip.

    Notes:
        1. If value is None, do nothing (field remains unchanged).
        2. If value is an empty string, set field to None.
        3. Otherwise, set field to the value.

    """
    if value is not None:
        if value:
            setattr(settings, field_name, value)
        else:
            setattr(settings, field_name, None)


def _update_api_key_if_present(
    settings: UserSettings,
    api_key: str | None,
) -> None:
    """Update the encrypted API key if a non-empty value is provided.

    Args:
        settings (UserSettings): The settings object to update.
        api_key (str | None): The API key to encrypt and store.

    Notes:
        1. If api_key is None or empty, do nothing.
        2. Otherwise, encrypt the API key and store it.

    """
    if api_key:
        settings.encrypted_api_key = encrypt_data(data=api_key)


def update_user_settings(
    db: Session,
    user_id: int,
    settings_data: "UserSettingsUpdateRequest",
) -> UserSettings:
    """Creates or updates settings for a user.

    Args:
        db (Session): The database session used to perform database operations.
        user_id (int): The unique identifier of the user whose settings are being updated.
        settings_data (UserSettingsUpdateRequest): The data containing the updated settings.

    Returns:
        UserSettings: The updated or newly created UserSettings object.

    Notes:
        1. Get or create settings using _get_or_create_user_settings.
        2. Update llm_endpoint using _update_optional_string_field.
        3. Update llm_model_name using _update_optional_string_field if present.
        4. Update API key using _update_api_key_if_present.
        5. Commit the transaction and refresh the settings object.
        6. This function performs a database read and possibly a write operation.

    """
    _msg = f"Updating settings for user_id: {user_id}"
    log.debug(_msg)

    settings = _get_or_create_user_settings(db, user_id)

    _update_optional_string_field(settings, "llm_endpoint", settings_data.llm_endpoint)

    if hasattr(settings_data, "llm_model_name"):
        _update_optional_string_field(
            settings,
            "llm_model_name",
            settings_data.llm_model_name,
        )

    _update_api_key_if_present(settings, settings_data.api_key)

    db.commit()
    db.refresh(settings)
    return settings
