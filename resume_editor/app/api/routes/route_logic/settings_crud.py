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
        db (Session): The database session.
        user_id (int): The ID of the user.

    Returns:
        UserSettings | None: The user settings if found, otherwise None.
    """
    _msg = f"Getting settings for user_id: {user_id}"
    log.debug(_msg)
    return db.query(UserSettings).filter(UserSettings.user_id == user_id).first()


def update_user_settings(
    db: Session, user_id: int, settings_data: "UserSettingsUpdateRequest"
) -> UserSettings:
    """Creates or updates settings for a user.

    Args:
        db (Session): The database session.
        user_id (int): The ID of the user.
        settings_data (UserSettingsUpdateRequest): The settings data to update.

    Returns:
        UserSettings: The updated user settings.
    """
    _msg = f"Updating settings for user_id: {user_id}"
    log.debug(_msg)

    settings = get_user_settings(db, user_id)
    if not settings:
        _msg = f"No settings found for user_id: {user_id}. Creating new settings."
        log.debug(_msg)
        settings = UserSettings(user_id=user_id)
        db.add(settings)

    if settings_data.llm_endpoint is not None:
        settings.llm_endpoint = settings_data.llm_endpoint

    if settings_data.api_key is not None:
        if settings_data.api_key:
            settings.encrypted_api_key = encrypt_data(settings_data.api_key)
        else:
            settings.encrypted_api_key = None

    db.commit()
    db.refresh(settings)
    return settings
