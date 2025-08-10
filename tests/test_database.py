import logging
import sys
from unittest.mock import MagicMock, patch


log = logging.getLogger(__name__)


class TestDatabase:
    """Test cases for database functionality."""

    def test_database_connection(self):
        """Test that database engine is created."""
        # Remove module from cache to force re-import
        modules_to_remove = [
            key
            for key in sys.modules.keys()
            if key.startswith("resume_editor.app.database")
        ]
        for module in modules_to_remove:
            del sys.modules[module]

        with patch(
            "resume_editor.app.database.database.create_engine",
        ) as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine

            # Import to trigger engine creation
            from resume_editor.app.database.database import get_engine

            engine = get_engine()
            assert engine is not None
            # Since engine is created at module level, create_engine should have been called
            mock_create_engine.assert_called_once()

    def test_session_local(self):
        """Test that session factory is created."""
        # Remove module from cache to force re-import
        modules_to_remove = [
            key
            for key in sys.modules.keys()
            if key.startswith("resume_editor.app.database")
        ]
        for module in modules_to_remove:
            del sys.modules[module]

        with (
            patch(
                "resume_editor.app.database.database.sessionmaker",
            ) as mock_sessionmaker,
            patch("resume_editor.app.database.database.create_engine"),
        ):
            mock_session_local = MagicMock()
            mock_sessionmaker.return_value = mock_session_local

            # Import to trigger session local creation
            from resume_editor.app.database.database import get_session_local

            session_local = get_session_local()
            assert session_local is not None
            mock_sessionmaker.assert_called_once()

    def test_get_db_dependency(self):
        """Test the get_db dependency function."""
        # Remove module from cache to force re-import
        modules_to_remove = [
            key
            for key in sys.modules.keys()
            if key.startswith("resume_editor.app.database")
        ]
        for module in modules_to_remove:
            del sys.modules[module]

        with patch(
            "resume_editor.app.database.database.get_session_local",
        ) as mock_get_session_local:
            # Setup mock
            mock_session_local = MagicMock()
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            mock_get_session_local.return_value = mock_session_local

            # Import after patching
            from resume_editor.app.database.database import get_db

            # Get generator
            db_generator = get_db()

            # Test that we can get a session from the generator
            db_session = next(db_generator)
            assert db_session == mock_session

            # Test that closing works
            try:
                next(db_generator)
            except StopIteration:
                pass  # Expected when generator is exhausted

            # Verify session close was called
            mock_session.close.assert_called_once()
