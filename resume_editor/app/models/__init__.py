import logging

from sqlalchemy.orm import declarative_base

log = logging.getLogger(__name__)

# Base model that other models will inherit from
Base = declarative_base()

# Import all models here to ensure they are registered with SQLAlchemy's metadata
from .resume_model import Resume  # noqa
from .role import Role  # noqa
from .user import User  # noqa
from .user_settings import UserSettings  # noqa
