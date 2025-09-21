import logging
from datetime import datetime, timezone

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
        is_base (bool): True if this is a base resume, False if it is a refined version.
        job_description (str | None): The job description associated with a refined resume.
        parent_id (int | None): A self-referencing foreign key to link a refined resume to its base resume.
        parent (Resume): The parent resume relationship.
        children (list[Resume]): The child resumes relationship.
    """

    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    is_active = Column(Boolean, default=True, nullable=False)
    is_base = Column(Boolean, default=True, nullable=False)
    job_description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)

    # Relationship to User
    user = relationship("User", back_populates="resumes")

    # Self-referencing relationship for refined resumes
    parent = relationship("Resume", remote_side=[id], back_populates="children")
    children = relationship(
        "Resume", back_populates="parent", cascade="all, delete-orphan"
    )

    def __init__(
        self,
        user_id: int,
        name: str,
        content: str,
        is_active: bool = True,
        is_base: bool = True,
        job_description: str | None = None,
        parent_id: int | None = None,
    ):
        """
        Initialize a Resume instance.

        Args:
            user_id (int): The unique identifier of the user who owns the resume.
            name (str): A descriptive name assigned by the user for the resume; must be non-empty.
            content (str): The Markdown-formatted text content of the resume; must be non-empty.
            is_active (bool): A flag indicating whether the resume is currently active; defaults to True.
            is_base (bool): Whether this is a base resume. Defaults to True.
            job_description (str | None): The job description for a refined resume.
            parent_id (int | None): The ID of the parent resume if this is a refined resume.

        Returns:
            None

        Raises:
            ValueError: If user_id is not an integer, name is empty, content is empty, or is_active is not a boolean.

        Notes:
            1. Validate that user_id is an integer.
            2. Validate that name is a non-empty string.
            3. Validate that content is a non-empty string.
            4. Validate that is_active is a boolean.
            5. Assign user_id, name, content, is_active, is_base, job_description, and parent_id to instance attributes.
            6. Log the initialization of the resume with its name.
            7. This function performs no database access.

        """
        _msg = f"Initializing Resume with name: {name}"
        log.debug(_msg)

        self.user_id = user_id
        self.name = name
        self.content = content
        self.is_active = is_active
        self.is_base = is_base
        self.job_description = job_description
        self.parent_id = parent_id
