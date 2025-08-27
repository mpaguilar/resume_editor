import pytest

# We need to access the module to reset its global state
from resume_editor.app.database import database


@pytest.fixture(autouse=True)
def reset_db_module_globals():
    """Fixture to reset the database module's global variables before each test."""
    database._engine = None
    database._SessionLocal = None
    yield


def test_get_session_local_creates_factory_once():
    """
    Test that get_session_local creates the session factory on the first call
    and reuses it on subsequent calls.
    It relies on mocks from conftest.py.
    """
    from resume_editor.app.database.database import (
        get_engine,
        get_session_local,
        sessionmaker,
    )

    # First call should create the session factory
    factory1 = get_session_local()
    sessionmaker.assert_called_once_with(
        autocommit=False, autoflush=False, bind=get_engine()
    )
    assert factory1 is not None

    # Second call should return the same instance
    factory2 = get_session_local()
    assert factory1 is factory2
    sessionmaker.assert_called_once()  # Should not be called again
