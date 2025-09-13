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


def test_start_refinement_returns_progress_container():
    """
    GIVEN a POST request to the start refinement endpoint
    WHEN the user submits a job description
    THEN an HTML partial is returned that sets up an SSE connection.
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

    job_desc = "A job with spaces & special characters\nand newlines."
    expected_encoded_desc = (
        "A+job+with+spaces+%26+special+characters%0Aand+newlines."
    )
    resume_id = 1

    response = client.post(
        f"/resumes/{resume_id}/refine/start",
        data={"job_description": job_desc},
    )

    assert response.status_code == 200
    soup = BeautifulSoup(response.content, "html.parser")

    container_div = soup.find("div", {"id": "refinement-container"})
    assert container_div is not None

    assert container_div["hx-ext"] == "sse"
    expected_sse_connect = (
        f"/resumes/{resume_id}/refine/stream?job_description={expected_encoded_desc}"
    )
    assert container_div["sse-connect"] == expected_sse_connect

    progress_list_ul = container_div.find("ul", {"id": "progress-list"})
    assert progress_list_ul is not None
    assert progress_list_ul["sse-swap"] == "progress"
    assert progress_list_ul["hx-swap"] == "beforeend"

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


def test_create_resume_page_loads():
    """
    GIVEN an authenticated user
    WHEN they navigate to the create resume page
    THEN the page loads correctly.
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

    response = client.get("/resumes/create")
    assert response.status_code == 200
    soup = BeautifulSoup(response.content, "html.parser")
    assert "Create New Resume" in soup.find("h1").text

    app.dependency_overrides.clear()


def test_handle_create_resume_success():
    """
    GIVEN an authenticated user submitting a valid new resume
    WHEN the form is posted
    THEN the resume is created and the user is redirected to the editor page.
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

    mock_db_session = MagicMock()

    def get_mock_db():
        yield mock_db_session

    app.dependency_overrides[get_current_user_from_cookie] = get_mock_user
    app.dependency_overrides[get_db] = get_mock_db

    mock_new_resume = DatabaseResume(
        user_id=1, name="New Resume", content="Some content"
    )
    mock_new_resume.id = 2

    with patch(
        "resume_editor.app.main.validate_resume_content"
    ) as mock_validate, patch(
        "resume_editor.app.main.create_resume_db", return_value=mock_new_resume
    ) as mock_create_resume:
        response = client.post(
            "/resumes/create",
            data={"name": "New Resume", "content": "Some content"},
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/resumes/2/edit"
        mock_validate.assert_called_once_with("Some content")
        mock_create_resume.assert_called_once_with(
            db=mock_db_session, user_id=1, name="New Resume", content="Some content"
        )

    app.dependency_overrides.clear()


def test_handle_create_resume_validation_error():
    """
    GIVEN an authenticated user submitting a new resume with invalid content
    WHEN the form is posted
    THEN a 422 error is returned and the form is re-rendered with an error message.
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

    mock_db_session = MagicMock()

    def get_mock_db():
        yield mock_db_session

    app.dependency_overrides[get_current_user_from_cookie] = get_mock_user
    app.dependency_overrides[get_db] = get_mock_db

    with patch(
        "resume_editor.app.main.validate_resume_content"
    ) as mock_validate, patch(
        "resume_editor.app.main.create_resume_db"
    ) as mock_create_resume:
        mock_validate.side_effect = HTTPException(
            status_code=422, detail="Invalid Markdown"
        )
        response = client.post(
            "/resumes/create",
            data={"name": "Bad Resume", "content": "bad content"},
        )

        assert response.status_code == 422
        mock_validate.assert_called_once_with("bad content")
        mock_create_resume.assert_not_called()

        soup = BeautifulSoup(response.content, "html.parser")
        assert "Invalid Markdown" in soup.text
        assert soup.find("input", {"name": "name"})["value"] == "Bad Resume"
        assert soup.find("textarea", {"name": "content"}).text == "bad content"

    app.dependency_overrides.clear()


def test_refine_resume_page_loads_correctly():
    """
    GIVEN an authenticated user and a resume
    WHEN they navigate to the refinement page for that resume
    THEN the page loads with the correct resume content and form.
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
        response = client.get("/resumes/1/refine")
        assert response.status_code == 200

        soup = BeautifulSoup(response.content, "html.parser")
        header = soup.find("h1")
        assert "Refine Resume: My Test Resume" in header.text

        back_link = soup.find("a", href="/resumes/1/edit")
        assert back_link is not None

        form = soup.find("form")
        assert form is not None
        assert form["hx-post"] == "/resumes/1/refine/start"
        assert form.find("textarea", {"name": "job_description"}) is not None

        mock_get_resume.assert_called_once_with(mock_db_session, 1, 1)

    app.dependency_overrides.clear()


def test_handle_save_resume_success():
    """
    GIVEN a POST request to the save endpoint with valid data
    WHEN the user saves refined content
    THEN the resume is updated and the user is redirected.
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
    mock_resume = DatabaseResume(user_id=1, name="Test", content="Old Content")
    mock_resume.id = 123

    def get_mock_user():
        return mock_user

    mock_db_session = MagicMock()

    def get_mock_db():
        yield mock_db_session

    app.dependency_overrides[get_current_user_from_cookie] = get_mock_user
    app.dependency_overrides[get_db] = get_mock_db

    with patch(
        "resume_editor.app.main.get_resume_by_id_and_user", return_value=mock_resume
    ) as mock_get_resume, patch(
        "resume_editor.app.main.update_resume"
    ) as mock_update_resume:
        new_content = "This is the new refined content."
        response = client.post(
            f"/resumes/{mock_resume.id}/save",
            data={"content": new_content},
        )

        assert response.status_code == 200
        assert response.headers["HX-Redirect"] == f"/resumes/{mock_resume.id}/edit"

        mock_get_resume.assert_called_once_with(
            mock_db_session, mock_resume.id, mock_user.id
        )
        mock_update_resume.assert_called_once_with(
            db=mock_db_session, resume=mock_resume, content=new_content
        )

    app.dependency_overrides.clear()


def test_handle_save_resume_not_found():
    """
    GIVEN a POST request for a resume the user doesn't own
    WHEN the user tries to save
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

    mock_db_session = MagicMock()

    def get_mock_db():
        yield mock_db_session

    app.dependency_overrides[get_current_user_from_cookie] = get_mock_user
    app.dependency_overrides[get_db] = get_mock_db

    with patch(
        "resume_editor.app.main.get_resume_by_id_and_user"
    ) as mock_get_resume, patch(
        "resume_editor.app.main.update_resume"
    ) as mock_update_resume:
        mock_get_resume.side_effect = HTTPException(
            status_code=404, detail="Resume not found"
        )

        response = client.post(
            "/resumes/999/save",
            data={"content": "some content"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Resume not found"
        mock_update_resume.assert_not_called()

    app.dependency_overrides.clear()


def test_handle_save_resume_unauthenticated():
    """
    GIVEN an unauthenticated user
    WHEN they try to save a resume
    THEN they are redirected to the login page.
    """
    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    response = client.post(
        "/resumes/123/save",
        data={"content": "new content"},
        follow_redirects=False,
    )

    assert response.status_code == 307
    assert response.headers["location"] == "http://testserver/login"
