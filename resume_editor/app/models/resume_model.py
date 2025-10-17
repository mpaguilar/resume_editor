import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from resume_editor.app.models import Base

log = logging.getLogger(__name__)


@dataclass
class ResumeData:
    """Dataclass to hold data for Resume initialization."""

    user_id: int
    name: str
    content: str
    is_active: bool = True
    is_base: bool = True
    job_description: str | None = None
    parent_id: int | None = None
    notes: str | None = None
    introduction: str | None = None
    export_settings_include_projects: bool = True
    export_settings_render_projects_first: bool = True
    export_settings_include_education: bool = True


class Resume(Base):
    """Resume model for storing user resumes.

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
        notes (str | None): User-provided notes for the resume.
        introduction (str | None): AI-generated introduction for the resume.

    """

    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
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
    notes = Column(Text, nullable=True)
    introduction = Column(Text, nullable=True)

    export_settings_include_projects = Column(
        Boolean,
        default=True,
        server_default=sa.true(),
        nullable=False,
    )
    export_settings_render_projects_first = Column(
        Boolean,
        default=True,
        server_default=sa.true(),
        nullable=False,
    )
    export_settings_include_education = Column(
        Boolean,
        default=True,
        server_default=sa.true(),
        nullable=False,
    )

    # Relationship to User
    user = relationship("User", back_populates="resumes")

    # Self-referencing relationship for refined resumes
    parent = relationship("Resume", remote_side=[id], back_populates="children")
    children = relationship(
        "Resume",
        back_populates="parent",
        cascade="all, delete-orphan",
    )

    def __init__(self, data: ResumeData):
        """Initialize a Resume instance.

        Args:
            data (ResumeData): An object containing the data for the new resume.

        Returns:
            None

        Notes:
            1. Assigns attributes from the `data` object to the `Resume` instance.
            2. This constructor does not perform validation. It assumes `data` is a valid `ResumeData` object.
            3. Logs the initialization of the resume.
            4. This function does not perform disk, network, or database access.

        """
        _msg = f"Initializing Resume with name: {data.name}"
        log.debug(_msg)

        self.user_id = data.user_id
        self.name = data.name
        self.content = data.content
        self.is_active = data.is_active
        self.is_base = data.is_base
        self.job_description = data.job_description
        self.parent_id = data.parent_id
        self.notes = data.notes
        self.introduction = data.introduction
        self.export_settings_include_projects = data.export_settings_include_projects
        self.export_settings_render_projects_first = (
            data.export_settings_render_projects_first
        )
        self.export_settings_include_education = data.export_settings_include_education
