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

        form = soup.find("form")
        assert form is not None
        assert form["hx-put"] == "/api/resumes/1"

        name_input = form.find("input", {"name": "name"})
        assert name_input is not None
        assert name_input["value"] == "My Test Resume"

        content_textarea = form.find("textarea", {"name": "content"})
        assert content_textarea is not None
        assert content_textarea.text == "# My Resume Content"

        refine_link = soup.find("a", href="/resumes/1/refine")
        assert refine_link is not None
        assert "Refine with AI" in refine_link.text

        dashboard_link = soup.find("a", href="/dashboard")
        assert dashboard_link is not None

        mock_get_resume.assert_called_once_with(
            db=mock_db_session, resume_id=1, user_id=1
        )

    app.dependency_overrides.clear()


def test_resume_editor_page_no_refine_for_refined_resume():
    """
    GIVEN an authenticated user and a refined (non-base) resume
    WHEN they navigate to the dedicated editor page for that resume
    THEN the 'Refine with AI' link is NOT present.
    """
    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    mock_user = User(
        id=1, username="testuser", email="test@test.com", hashed_password="hashed"
    )
    mock_resume = DatabaseResume(
        user_id=1, name="My Test Resume", content="# My Resume Content", is_base=False
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
        refine_link = soup.find("a", string=lambda t: t and "Refine with AI" in t)
        assert refine_link is None
        mock_get_resume.assert_called_once_with(
            db=mock_db_session, resume_id=1, user_id=1
        )

    app.dependency_overrides.clear()


def test_get_resume_view_page_loads_correctly():
    """
    GIVEN an authenticated user and a resume
    WHEN they navigate to the view page for that resume
    THEN the page loads with the correct resume content.
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
        job_description="Sample job description",
        introduction="Sample AI introduction",
        notes="Sample user notes",
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
        response = client.get("/resumes/1/view")
        assert response.status_code == 200

        soup = BeautifulSoup(response.content, "html.parser")
        # Check page title
        assert "Viewing Resume: My Test Resume" in soup.title.string

        # Check header
        header = soup.find("h1")
        assert "Viewing Resume: My Test Resume" in header.text

        # Check read-only fields
        content_ta = soup.find("textarea", {"id": "content"})
        assert content_ta is not None
        assert content_ta.text == "# My Resume Content"
        assert content_ta.has_attr("disabled")

        jd_ta = soup.find("textarea", {"id": "job_description"})
        assert jd_ta is not None
        assert jd_ta.text == "Sample job description"
        assert jd_ta.has_attr("disabled")

        # Check form and editable fields
        form = soup.find("form")
        assert form is not None

        intro_ta = form.find("textarea", {"name": "introduction"})
        assert intro_ta is not None
        assert intro_ta.text == "Sample AI introduction"

        notes_ta = form.find("textarea", {"name": "notes"})
        assert notes_ta is not None
        assert notes_ta.text == "Sample user notes"

        save_button = form.find("button", {"type": "submit"})
        assert save_button is not None
        assert "Save" in save_button.text

        # Check for export button
        export_button = soup.find(
            "button", string=lambda t: t and "Export" in t.strip()
        )
        assert export_button is not None
        assert (
            export_button["onclick"]
            == "document.getElementById('export-modal-1').classList.remove('hidden')"
        )

        # Check for export modal
        modal = soup.find("div", id="export-modal-1")
        assert modal is not None
        assert modal.find("form", id="export-form-1") is not None

        mock_get_resume.assert_called_once_with(
            db=mock_db_session, resume_id=1, user_id=1
        )

    app.dependency_overrides.clear()


def test_resume_view_page_not_found():
    """
    GIVEN an authenticated user
    WHEN they navigate to a view page for a non-existent resume
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
        response = client.get("/resumes/999/view")
        assert response.status_code == 404
        assert response.json()["detail"] == "Resume not found"
        mock_get_resume.assert_called_once_with(
            db=mock_db_session, resume_id=999, user_id=1
        )

    app.dependency_overrides.clear()


def test_resume_view_page_unauthenticated():
    """Test that an unauthenticated user is redirected to the login page."""
    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    response = client.get("/resumes/1/view", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "http://testserver/login"


def test_update_resume_view_page_post():
    """
    GIVEN an authenticated user and a resume
    WHEN they submit the form on the view page
    THEN the resume is updated and they are redirected back to the view page.
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
    ) as mock_get_resume, patch(
        "resume_editor.app.main.update_resume"
    ) as mock_update_resume:
        response = client.post(
            "/resumes/1/view",
            data={"introduction": "New Intro", "notes": "New Notes"},
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/resumes/1/view"

        mock_get_resume.assert_called_once_with(
            db=mock_db_session, resume_id=1, user_id=1
        )
        mock_update_resume.assert_called_once_with(
            db=mock_db_session,
            resume=mock_resume,
            introduction="New Intro",
            notes="New Notes",
        )

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
        mock_get_resume.assert_called_once_with(
            db=mock_db_session, resume_id=999, user_id=1
        )

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
        assert form["hx-post"] == "/api/resumes/1/refine"
        assert form.find("textarea", {"name": "job_description"}) is not None

        mock_get_resume.assert_called_once_with(mock_db_session, 1, 1)

    app.dependency_overrides.clear()


def test_resume_editor_page_has_correct_export_modal():
    """
    GIVEN an authenticated user and a resume
    WHEN they navigate to the dedicated editor page for that resume
    THEN the page contains the correct export modal form.
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
        response = client.get(f"/resumes/{mock_resume.id}/edit")
        assert response.status_code == 200

        soup = BeautifulSoup(response.content, "html.parser")

        # Find the export modal and the form inside it
        modal = soup.find("div", id=f"export-modal-{mock_resume.id}")
        assert modal is not None

        export_form = modal.find("form", id=f"export-form-{mock_resume.id}")
        assert export_form is not None
        assert export_form.get("method") == "GET"
        assert export_form.get("action") == f"/api/resumes/{mock_resume.id}/download"

        # Check for Markdown download button
        markdown_button = export_form.find(
            "button", {"formaction": f"/api/resumes/{mock_resume.id}/export/markdown"}
        )
        assert markdown_button is not None
        assert markdown_button.text.strip() == "Download Markdown"

        # Check for DOCX download button
        docx_button = export_form.find(
            "button", string=lambda t: t and "Download DOCX" in t
        )
        assert docx_button is not None
        assert docx_button.get("formaction") is None

        # Check for date inputs
        assert export_form.find("input", {"name": "start_date"}) is not None
        assert export_form.find("input", {"name": "end_date"}) is not None

        # Check for select dropdowns
        render_format_select = export_form.find("select", {"name": "render_format"})
        assert render_format_select is not None
        assert render_format_select.find("option", {"value": "plain"})
        assert render_format_select.find("option", {"value": "ats"})

        settings_name_select = export_form.find("select", {"name": "settings_name"})
        assert settings_name_select is not None
        assert settings_name_select.find("option", {"value": "general"})
        assert settings_name_select.find("option", {"value": "executive_summary"})

        mock_get_resume.assert_called_once_with(
            db=mock_db_session, resume_id=1, user_id=1
        )

    app.dependency_overrides.clear()


