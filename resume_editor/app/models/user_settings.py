import logging

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from resume_editor.app.models import Base

log = logging.getLogger(__name__)


class UserSettings(Base):
    """
    Stores user-specific settings, such as LLM configurations.

    Attributes:
        id (int): Primary key.
        user_id (int): Foreign key to the user.
        llm_endpoint (str | None): Custom LLM API endpoint URL.
        llm_model_name (str | None): The user-specified LLM model name.
        encrypted_api_key (str | None): Encrypted API key for the LLM service.
        user (User): Relationship to the User model.

    """

    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    llm_endpoint = Column(String, nullable=True)
    llm_model_name = Column(String, nullable=True)
    encrypted_api_key = Column(String, nullable=True)

    user = relationship("User", back_populates="settings")

    def __init__(
        self,
        user_id: int,
        llm_endpoint: str | None = None,
        llm_model_name: str | None = None,
        encrypted_api_key: str | None = None,
    ):
        """
        Initialize a UserSettings instance.

        Args:
            user_id (int): The ID of the user these settings belong to.
            llm_endpoint (str | None): Custom LLM API endpoint URL.
            llm_model_name (str | None): The user-specified LLM model name.
            encrypted_api_key (str | None): Encrypted API key for the LLM service.

        Returns:
            None

        Notes:
            1. Assign all values to instance attributes.
            2. Log the initialization of the user settings.
            3. This operation does not involve network, disk, or database access.

        """
        _msg = f"Initializing UserSettings for user_id: {user_id}"
        log.debug(_msg)

        self.user_id = user_id
        self.llm_endpoint = llm_endpoint
        self.llm_model_name = llm_model_name
        self.encrypted_api_key = encrypted_api_key
