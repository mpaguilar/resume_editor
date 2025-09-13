from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from resume_editor.app.main import create_app
from resume_editor.app.models.resume_model import Resume as DatabaseResume
from resume_editor.app.models.user import User as DBUser


@pytest.fixture
def app():
    """Create a new app for each test."""
    app = create_app()
    return app


def setup_dependency_overrides(
    app: FastAPI, mock_db: MagicMock, mock_user: DBUser | None
):
    """Set up dependency overrides for the test client."""
    from resume_editor.app.core.auth import get_current_user_from_cookie
    from resume_editor.app.database.database import get_db

    def get_mock_db():
        yield mock_db

    def get_mock_user():
        return mock_user

    app.dependency_overrides[get_db] = get_mock_db
    app.dependency_overrides[get_current_user_from_cookie] = get_mock_user


@pytest.fixture
def client(app):
    """Fixture for a test client."""
    return TestClient(app)


@pytest.fixture
def test_user():
    """Fixture for a test user."""
    user = DBUser(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        id=1,
    )
    return user


@pytest.fixture
def test_resume(test_user):
    """Fixture for a test resume."""
    resume = DatabaseResume(
        user_id=test_user.id,
        name="Test Resume",
        content="some content",
    )
    resume.id = 1
    return resume


@patch("resume_editor.app.api.routes.resume_ai._generate_resume_detail_html")
@patch("resume_editor.app.api.dependencies.get_resume_by_id_and_user")
def test_discard_refined_resume(
    mock_get_resume, mock_generate_html, app: FastAPI, client, test_user, test_resume
):
    """Test that the discard endpoint returns the resume detail HTML."""
    mock_db = MagicMock()
    setup_dependency_overrides(app, mock_db, test_user)

    mock_get_resume.return_value = test_resume
    mock_generate_html.return_value = "<div>Resume Detail HTML</div>"

    response = client.post(f"/api/resumes/{test_resume.id}/refine/discard")

    assert response.status_code == 200
    assert response.text == "<div>Resume Detail HTML</div>"
    mock_get_resume.assert_called_once_with(
        mock_db, resume_id=test_resume.id, user_id=test_user.id
    )
    mock_generate_html.assert_called_once_with(test_resume)

    app.dependency_overrides.clear()
