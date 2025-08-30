import logging

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from resume_editor.app.models import Base

log = logging.getLogger(__name__)


class Role(Base):
    """
    Role model for user authorization.

    Attributes:
        id (int): Unique identifier for the role.
        name (str): Unique name for the role (e.g., 'admin', 'user').
        users (list["User"]): The users associated with this role.

    """

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

    users = relationship("User", secondary="user_roles", back_populates="roles")
