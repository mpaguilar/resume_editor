import logging
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from resume_editor.app.api.routes.user import get_current_user
from resume_editor.app.core.config import get_settings
from resume_editor.app.database.database import get_db
from resume_editor.app.main import create_app
from resume_editor.app.models.user import User
from resume_editor.app.models.user_settings import UserSettings

log = logging.getLogger(__name__)


def test_user_settings_endpoints(monkeypatch):
    """Test user settings endpoints."""
    get_settings.cache_clear()
    monkeypatch.setenv("ENCRYPTION_KEY", "dGVzdF9rZXlfbXVzdF9iZV8zMl9ieXRlc19sb25n")
    app = create_app()
    client = TestClient(app)

    mock_db = MagicMock()

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db

    mock_user = User(username="testuser", email="test@test.com", hashed_password="pw")
    mock_user.id = 1

    def get_mock_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = get_mock_current_user

    # Test GET when no settings exist
    mock_db.reset_mock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    response = client.get("/api/users/settings")
    assert response.status_code == 200
    assert response.json() == {"llm_endpoint": None, "api_key_is_set": False}

    # Test PUT to create settings
    mock_db.reset_mock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    with patch(
        "resume_editor.app.api.routes.route_logic.settings_crud.encrypt_data",
    ) as mock_encrypt:
        mock_encrypt.return_value = "encrypted_key"
        response = client.put(
            "/api/users/settings",
            json={"llm_endpoint": "http://test.com", "api_key": "mykey"},
        )
        assert response.status_code == 200
        mock_encrypt.assert_called_with(data="mykey")
        added_instance = mock_db.add.call_args[0][0]
        assert isinstance(added_instance, UserSettings)
        assert added_instance.user_id == 1
        assert added_instance.llm_endpoint == "http://test.com"
        assert added_instance.encrypted_api_key == "encrypted_key"

    # Test GET when settings exist
    mock_db.reset_mock()
    mock_settings = UserSettings(
        user_id=1,
        llm_endpoint="http://existing.com",
        encrypted_api_key="existing_key",
    )
    mock_db.query.return_value.filter.return_value.first.return_value = mock_settings
    response = client.get("/api/users/settings")
    assert response.status_code == 200
    assert response.json() == {
        "llm_endpoint": "http://existing.com",
        "api_key_is_set": True,
    }

    # Test PUT to update both fields
    mock_db.reset_mock()
    mock_settings = UserSettings(
        user_id=1,
        llm_endpoint="http://existing.com",
        encrypted_api_key="existing_key",
    )
    mock_db.query.return_value.filter.return_value.first.return_value = mock_settings
    with patch(
        "resume_editor.app.api.routes.route_logic.settings_crud.encrypt_data",
    ) as mock_encrypt:
        mock_encrypt.return_value = "new_encrypted_key"
        response = client.put(
            "/api/users/settings",
            json={"llm_endpoint": "http://new.com", "api_key": "newkey"},
        )
        assert response.status_code == 200
        assert mock_settings.llm_endpoint == "http://new.com"
        assert mock_settings.encrypted_api_key == "new_encrypted_key"
        mock_encrypt.assert_called_once_with(data="newkey")

    # Test PUT to preserve API key when sending empty string
    mock_db.reset_mock()
    mock_settings = UserSettings(
        user_id=1,
        llm_endpoint="http://existing.com",
        encrypted_api_key="existing_key",
    )
    mock_db.query.return_value.filter.return_value.first.return_value = mock_settings
    with patch(
        "resume_editor.app.api.routes.route_logic.settings_crud.encrypt_data",
    ) as mock_encrypt:
        response = client.put(
            "/api/users/settings",
            json={"api_key": ""},
        )
        assert response.status_code == 200
        assert mock_settings.llm_endpoint == "http://existing.com"  # Unchanged
        assert mock_settings.encrypted_api_key == "existing_key"  # Unchanged
        mock_encrypt.assert_not_called()

    # Test PUT to update only endpoint
    mock_db.reset_mock()
    mock_settings = UserSettings(
        user_id=1,
        llm_endpoint="http://existing.com",
        encrypted_api_key="existing_key",
    )
    mock_db.query.return_value.filter.return_value.first.return_value = mock_settings
    with patch(
        "resume_editor.app.api.routes.route_logic.settings_crud.encrypt_data",
    ) as mock_encrypt:
        response = client.put(
            "/api/users/settings",
            json={"llm_endpoint": "http://only-endpoint.com"},
        )
        assert response.status_code == 200
        assert mock_settings.llm_endpoint == "http://only-endpoint.com"
        assert mock_settings.encrypted_api_key == "existing_key"  # Unchanged
        mock_encrypt.assert_not_called()

    # Test PUT to update only API key
    mock_db.reset_mock()
    mock_settings = UserSettings(
        user_id=1,
        llm_endpoint="http://existing.com",
        encrypted_api_key="existing_key",
    )
    mock_db.query.return_value.filter.return_value.first.return_value = mock_settings
    with patch(
        "resume_editor.app.api.routes.route_logic.settings_crud.encrypt_data",
    ) as mock_encrypt:
        mock_encrypt.return_value = "only-key-encrypted"
        response = client.put(
            "/api/users/settings",
            json={"api_key": "only-key"},
        )
        assert response.status_code == 200
        assert mock_settings.llm_endpoint == "http://existing.com"  # Unchanged
        assert mock_settings.encrypted_api_key == "only-key-encrypted"
        mock_encrypt.assert_called_once_with(data="only-key")

    # Clean up dependency overrides
    app.dependency_overrides.clear()


def test_update_settings_preserves_api_key_across_requests(monkeypatch):
    """
    Integration test to ensure that the API key is preserved across multiple
    settings updates when an empty string is provided for the key.
    """
    # 1. Setup
    get_settings.cache_clear()
    monkeypatch.setenv("ENCRYPTION_KEY", "dGVzdF9rZXlfbXVzdF9iZV8zMl9ieXRlc19sb25n")
    app = create_app()
    client = TestClient(app)

    mock_db = MagicMock()
    mock_user = User(username="testuser", email="test@test.com", hashed_password="pw", id=1)

    def get_mock_db():
        yield mock_db

    def get_mock_current_user():
        return mock_user

    app.dependency_overrides[get_db] = get_mock_db
    app.dependency_overrides[get_current_user] = get_mock_current_user

    with patch(
        "resume_editor.app.api.routes.route_logic.settings_crud.encrypt_data"
    ) as mock_encrypt:
        # Step 2: Create settings and set initial API key.
        # This simulates the DB call finding nothing.
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_encrypt.return_value = "encrypted-initial-key"

        response_one = client.put(
            "/api/users/settings",
            json={"llm_endpoint": "http://initial.com", "api_key": "initial_key"},
        )
        assert response_one.status_code == 200

        # Step 3: Assert that the key was stored in the object passed to `db.add`.
        mock_encrypt.assert_called_once_with(data="initial_key")
        mock_db.add.assert_called_once()
        # Grab the object that was "saved" to the database.
        saved_settings = mock_db.add.call_args[0][0]
        assert isinstance(saved_settings, UserSettings)
        assert saved_settings.encrypted_api_key == "encrypted-initial-key"
        assert saved_settings.llm_endpoint == "http://initial.com"

        # Step 4: Make a second PUT request to update only the llm_endpoint.
        mock_db.reset_mock()
        mock_encrypt.reset_mock()

        # Now, when the endpoint is called again, it should "find" the settings we just created.
        mock_db.query.return_value.filter.return_value.first.return_value = (
            saved_settings
        )

        response_two = client.put(
            "/api/users/settings",
            json={"llm_endpoint": "http://updated.com", "api_key": ""},
        )
        assert response_two.status_code == 200

        # Step 5: Assert that the key was preserved.
        mock_encrypt.assert_not_called()
        mock_db.add.assert_not_called()  # Should not create a new one
        assert saved_settings.encrypted_api_key == "encrypted-initial-key"
        assert saved_settings.llm_endpoint == "http://updated.com"

    # Cleanup
    app.dependency_overrides.clear()
