import os
from functools import lru_cache
from unittest.mock import patch

import pytest

from resume_editor.app.core.config import Settings, get_settings
from resume_editor.app.core.config import Settings as RealSettings


def test_settings_default_values():
    """Test that Settings loads default values correctly."""
    with patch.dict(os.environ, {"ENCRYPTION_KEY": "test-key"}, clear=True):
        # Prevent loading .env file by passing _env_file=None
        settings = Settings(_env_file=None)

        # Test database settings
        assert (
            str(settings.database_url)
            == "postgresql://postgres@localhost:5432/resume_editor"
        )

        # Test security settings
        assert settings.secret_key == "your-secret-key-change-in-production"
        assert settings.algorithm == "HS256"
        assert settings.access_token_expire_minutes == 30

        # Test API keys
        assert settings.llm_api_key is None


def test_settings_from_environment():
    """Test that Settings loads values from environment variables."""
    env_vars = {
        "DB_HOST": "testhost",
        "DB_PORT": "5433",
        "DB_NAME": "testdb",
        "DB_USER": "testuser",
        "DB_PASSWORD": "testpassword",
        "SECRET_KEY": "test-secret-key",
        "ALGORITHM": "HS512",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
        "LLM_API_KEY": "test-llm-key",
    }

    with patch.dict(os.environ, env_vars):
        settings = Settings()

        # Test database settings
        assert (
            str(settings.database_url)
            == "postgresql://testuser:testpassword@testhost:5433/testdb"
        )

        # Test security settings
        assert settings.secret_key == "test-secret-key"
        assert settings.algorithm == "HS512"
        assert settings.access_token_expire_minutes == 60

        # Test API keys
        assert settings.llm_api_key == "test-llm-key"


def test_settings_missing_required_env_vars():
    """Test that Settings raises an error if a required env var is missing."""
    with patch.dict(
        os.environ,
        {
            "DB_HOST": "localhost",
            "DB_USER": "postgres",
            "DB_PASSWORD": "",
            "DB_NAME": "resume_editor",
            "DB_PORT": "5432",
        },
        clear=True,
    ):
        with pytest.raises(ValueError) as excinfo:
            # ENCRYPTION_KEY is required and has no default.
            # We pass _env_file=None to ensure we are not loading it from a file.
            Settings(_env_file=None)
        assert "validation error for Settings" in str(excinfo.value)
        assert "ENCRYPTION_KEY" in str(excinfo.value)




@patch("resume_editor.app.core.config.Settings")
def test_get_settings_function(MockSettings):
    """Test that get_settings uses default values in an isolated environment."""
    # Configure the mock to return a real Settings instance,
    # but one created with _env_file=None to prevent loading .env files.
    MockSettings.side_effect = lambda **kwargs: RealSettings(_env_file=None, **kwargs)

    # Clear the lru_cache on the real get_settings function
    get_settings.cache_clear()

    with patch.dict(os.environ, {"ENCRYPTION_KEY": "test-key"}, clear=True):
        # Call the function that we are testing
        settings = get_settings()

        # get_settings should have called our mock
        MockSettings.assert_called_once()

        # The returned object should be a real Settings instance
        assert isinstance(settings, RealSettings)

        # And it should have the default values
        assert (
            str(settings.database_url)
            == "postgresql://postgres@localhost:5432/resume_editor"
        )
