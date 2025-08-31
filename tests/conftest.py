import sys
from unittest.mock import MagicMock, patch

import pytest

# Add the resume_editor directory to the path
sys.path.insert(0, "resume_editor")


def update_sys_path():
    sys.path.insert(0, "resume_editor")


@pytest.fixture
def mock_db_engine():
    """Fixture to provide a mock database engine."""
    with patch(
        "resume_editor.app.database.database.create_engine",
    ) as mock_create_engine:
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        yield mock_engine


@pytest.fixture
def mock_db_session_local():
    """Fixture to provide a mock session factory."""
    with patch("resume_editor.app.database.database.sessionmaker") as mock_sessionmaker:
        mock_session_local = MagicMock()
        mock_sessionmaker.return_value = mock_session_local
        yield mock_session_local


@pytest.fixture
def mock_db_base():
    """Fixture to provide a mock base model class."""
    with patch("sqlalchemy.orm.declarative_base") as mock_declarative_base:
        mock_base = MagicMock()
        mock_declarative_base.return_value = mock_base
        yield mock_base


@pytest.fixture
def mock_db_session():
    """Fixture to provide a mock database session."""
    return MagicMock()


@pytest.fixture(autouse=True)
def mock_database_imports():
    """Auto-used fixture to mock database imports and prevent actual database connections."""
    with (
        patch("resume_editor.app.database.database.create_engine"),
        patch("resume_editor.app.database.database.sessionmaker"),
        patch("resume_editor.app.core.config.get_settings") as mock_get_settings,
        patch(
            "resume_editor.app.core.security.get_settings",
        ) as mock_get_settings_security,
        patch("resume_editor.app.core.auth.get_settings") as mock_get_settings_auth,
    ):
        # Create a mock settings object with valid values
        mock_settings = MagicMock()
        mock_settings.database_url = (
            "postgresql://testuser:testpass@localhost:5432/testdb"
        )
        mock_settings.access_token_expire_minutes = 30
        mock_settings.algorithm = "HS256"
        mock_settings.secret_key = "test-secret-key"
        mock_get_settings.return_value = mock_settings
        mock_get_settings_security.return_value = mock_settings
        mock_get_settings_auth.return_value = mock_settings
        yield
