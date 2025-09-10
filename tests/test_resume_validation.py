from unittest.mock import ANY, Mock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from resume_editor.app.api.routes.route_logic.resume_validation import (
    perform_pre_save_validation,
)
from resume_editor.app.core.auth import get_current_user_from_cookie
from resume_editor.app.database.database import get_db
from resume_editor.app.main import create_app
from resume_editor.app.models.resume_model import Resume as DatabaseResume
from resume_editor.app.models.user import User


@pytest.fixture
def authenticated_client_and_db():
    app = create_app()
    mock_user = User(id=1, username="testuser", email="test@email.com", hashed_password="hashed")
    mock_db = Mock()

    def get_mock_user():
        return mock_user

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_current_user_from_cookie] = get_mock_user
    app.dependency_overrides[get_db] = get_mock_db

    with TestClient(app) as client:
        yield client, mock_db

    app.dependency_overrides.clear()


def test_perform_pre_save_validation_success():
    """Test that pre-save validation passes with valid content."""
    content = """# Personal
## Contact Information
Name: John Doe"""
    with patch(
        "resume_editor.app.api.routes.route_logic.resume_validation.validate_resume_content"
    ) as mock_validate:
        mock_validate.return_value = None
        perform_pre_save_validation(content)
        mock_validate.assert_called_once_with(content)


def test_perform_pre_save_validation_failure():
    """Test that pre-save validation raises HTTPException with invalid content."""
    content = "Invalid content"
    with patch(
        "resume_editor.app.api.routes.route_logic.resume_validation.validate_resume_content"
    ) as mock_validate:
        mock_validate.side_effect = HTTPException(status_code=422, detail="Invalid")
        with pytest.raises(HTTPException) as exc_info:
            perform_pre_save_validation(content)
        assert exc_info.value.status_code == 422
        assert "Invalid" in exc_info.value.detail


