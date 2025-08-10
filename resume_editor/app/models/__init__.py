import logging

from sqlalchemy.orm import declarative_base

log = logging.getLogger(__name__)

# Base model that other models will inherit from
Base = declarative_base()
