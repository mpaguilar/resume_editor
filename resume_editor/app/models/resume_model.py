import logging
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from resume_editor.app.models import Base

log = logging.getLogger(__name__)


class Resume(Base):
    """
    Resume model for storing user resumes.

    Attributes:
        id (int): Unique identifier for the resume.
        user_id (int): Foreign key to User model, identifying the user who owns the resume.
        name (str): User-assigned descriptive name for the resume, must be non-empty.
        content (str): The Markdown text content of the resume, must be non-empty.
        created_at (datetime): Timestamp when the resume was created.
        updated_at (datetime): Timestamp when the resume was last updated.
        is_active (bool): Whether the resume is currently active.

    """

    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationship to User
    user = relationship("User", back_populates="resumes")

    def __init__(
        self,
        user_id: int,
        name: str,
        content: str,
        is_active: bool = True,
    ):
        """
        Initialize a Resume instance.

        Args:
            user_id (int): The unique identifier of the user who owns the resume.
            name (str): A descriptive name assigned by the user for the resume; must be non-empty.
            content (str): The Markdown-formatted text content of the resume; must be non-empty.
            is_active (bool): A flag indicating whether the resume is currently active; defaults to True.

        Returns:
            None

        Raises:
            ValueError: If user_id is not an integer, name is empty, content is empty, or is_active is not a boolean.

        Notes:
            1. Validate that user_id is an integer.
            2. Validate that name is a non-empty string.
            3. Validate that content is a non-empty string.
            4. Validate that is_active is a boolean.
            5. Assign all values to instance attributes.
            6. Log the initialization of the resume with its name.
            7. This function performs no database access.

        """
        _msg = f"Initializing Resume with name: {name}"
        log.debug(_msg)

        self.user_id = user_id
        self.name = name
        self.content = content
        self.is_active = is_active
