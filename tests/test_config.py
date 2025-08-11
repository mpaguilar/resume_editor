import os
from unittest.mock import patch

import pytest

from resume_editor.app.core.config import Settings, get_settings


def test_settings_default_values():
    """Test that Settings loads default values correctly."""
    with patch.dict(os.environ, {}, clear=True):
        settings = Settings()

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
        "DATABASE_URL": "postgresql://testuser:testpass@localhost:5433/testdb",
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
            == "postgresql://testuser:testpass@localhost:5433/testdb"
        )

        # Test security settings
        assert settings.secret_key == "test-secret-key"
        assert settings.algorithm == "HS512"
        assert settings.access_token_expire_minutes == 60

        # Test API keys
        assert settings.llm_api_key == "test-llm-key"


def test_settings_invalid_database_url():
    """Test that Settings handles invalid database URLs."""
    env_vars = {"DATABASE_URL": "invalid-url"}

    with patch.dict(os.environ, env_vars):
        with pytest.raises(ValueError):
            Settings()


def test_settings_extra_fields_allowed():
    """Test that Settings allows extra environment variables."""
    env_vars = {
        "DATABASE_URL": "postgresql://testuser:testpass@localhost:5433/testdb",
        "SECRET_KEY": "test-secret-key",
        "OPENAI_API_KEY": "test-openai-key",  # Extra field
        "SOME_OTHER_VAR": "some-value",  # Extra field
    }

    with patch.dict(os.environ, env_vars):
        # This should not raise an exception
        settings = Settings()

        # Test that our settings are loaded
        assert (
            str(settings.database_url)
            == "postgresql://testuser:testpass@localhost:5433/testdb"
        )
        assert settings.secret_key == "test-secret-key"

        # The extra fields are allowed but not accessible as attributes


def test_get_settings_function():
    """Test that get_settings function returns a Settings instance."""
    with patch.dict(os.environ, {}, clear=True):
        settings = get_settings()

        assert isinstance(settings, Settings)
        assert (
            str(settings.database_url)
            == "postgresql://postgres@localhost:5432/resume_editor"
        )
