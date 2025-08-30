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
        1. Attempts to retrieve existing settings for the given user_id using get_user_settings.
        2. If no settings are found, creates a new UserSettings object with the provided user_id and adds it to the session.
        3. Updates the llm_endpoint field if settings_data.llm_endpoint is provided and not None.
        4. If settings_data.api_key is provided and not empty, encrypts the API key using encrypt_data and stores it in encrypted_api_key; otherwise, sets encrypted_api_key to None.
        5. Commits the transaction to the database.
        6. Refreshes the session to ensure the returned object has the latest data from the database.
        7. This function performs a database read and possibly a write operation.
    """
    _msg = f"Updating settings for user_id: {user_id}"
    log.debug(_msg)

    settings = get_user_settings(db=db, user_id=user_id)
    if not settings:
        _msg = f"No settings found for user_id: {user_id}. Creating new settings."
        log.debug(_msg)
        settings = UserSettings(user_id=user_id)
        db.add(settings)

    if settings_data.llm_endpoint is not None:
        if settings_data.llm_endpoint:
            settings.llm_endpoint = settings_data.llm_endpoint
        else:
            settings.llm_endpoint = None

    if settings_data.api_key is not None:
        if settings_data.api_key:
            settings.encrypted_api_key = encrypt_data(data=settings_data.api_key)
        else:
            settings.encrypted_api_key = None

    db.commit()
    db.refresh(settings)
    return settings
