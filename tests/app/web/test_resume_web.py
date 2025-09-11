import logging
from unittest.mock import MagicMock, patch

from bs4 import BeautifulSoup
from fastapi import HTTPException
from fastapi.testclient import TestClient

from resume_editor.app.core.auth import get_current_user_from_cookie
from resume_editor.app.database.database import get_db
from resume_editor.app.main import create_app
from resume_editor.app.models.resume_model import Resume as DatabaseResume
from resume_editor.app.models.user import User

log = logging.getLogger(__name__)


def test_resume_editor_page_loads_correctly():
    """
    GIVEN an authenticated user and a resume
    WHEN they navigate to the dedicated editor page for that resume
    THEN the page loads with the correct resume content and links.
    """
    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    mock_user = User(
        id=1,
        username="testuser",
        email="test@test.com",
        hashed_password="hashed",
    )
    mock_resume = DatabaseResume(
        user_id=1,
        name="My Test Resume",
        content="# My Resume Content",
    )
    mock_resume.id = 1

    def get_mock_user():
        return mock_user

    mock_db_session = MagicMock()

    def get_mock_db():
        yield mock_db_session

    app.dependency_overrides[get_current_user_from_cookie] = get_mock_user
    app.dependency_overrides[get_db] = get_mock_db

    with patch(
        "resume_editor.app.main.get_resume_by_id_and_user", return_value=mock_resume
    ) as mock_get_resume:
        response = client.get("/resumes/1/edit")
        assert response.status_code == 200

        soup = BeautifulSoup(response.content, "html.parser")
        header = soup.find("h1")
        assert "Editing: My Test Resume" in header.text

        content_pre = soup.find("pre")
        assert "# My Resume Content" in content_pre.text

        refine_link = soup.find("a", href="/resumes/1/refine")
        assert refine_link is not None
        assert "Refine with AI" in refine_link.text

        dashboard_link = soup.find("a", href="/dashboard")
        assert dashboard_link is not None

        mock_get_resume.assert_called_once_with(mock_db_session, 1, 1)

    app.dependency_overrides.clear()


def test_resume_editor_page_not_found():
    """
    GIVEN an authenticated user
    WHEN they navigate to an editor page for a non-existent resume
    THEN a 404 error is returned.
    """
    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    mock_user = User(
        id=1,
        username="testuser",
        email="test@test.com",
        hashed_password="hashed",
    )

    def get_mock_user():
        return mock_user

    app.dependency_overrides[get_current_user_from_cookie] = get_mock_user

    mock_db_session = MagicMock()

    def get_mock_db():
        yield mock_db_session

    app.dependency_overrides[get_db] = get_mock_db

    with patch("resume_editor.app.main.get_resume_by_id_and_user") as mock_get_resume:
        mock_get_resume.side_effect = HTTPException(
            status_code=404, detail="Resume not found"
        )
        response = client.get("/resumes/999/edit")
        assert response.status_code == 404
        assert response.json()["detail"] == "Resume not found"
        mock_get_resume.assert_called_once_with(mock_db_session, 999, 1)

    app.dependency_overrides.clear()


def test_resume_editor_page_unauthenticated():
    """Test that an unauthenticated user is redirected to the login page."""
    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    response = client.get("/resumes/1/edit", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "http://testserver/login"
