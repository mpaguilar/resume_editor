"""Tests for resume template UI elements (Refine button and New refinement button)."""

import datetime
import logging
from unittest.mock import MagicMock, patch

from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from resume_editor.app.core.auth import get_current_user_from_cookie
from resume_editor.app.database.database import get_db
from resume_editor.app.main import create_app
from resume_editor.app.models.resume_model import (
    Resume as DatabaseResume,
    ResumeData,
)
from resume_editor.app.models.user import User, UserData

log = logging.getLogger(__name__)


def create_mock_user():
    """Create a mock user for testing."""
    return User(
        data=UserData(
            id_=1,
            username="testuser",
            email="test@test.com",
            hashed_password="hashed",
        )
    )


def setup_mock_db_with_resumes(mock_db, base_resumes=None, refined_resumes=None):
    """Set up mock database to return the specified resumes."""
    # Create mock query chain for base_resumes
    base_query = MagicMock()
    base_query.filter.return_value = base_query
    base_query.order_by.return_value = base_query
    base_query.all.return_value = base_resumes or []

    # Create mock query chain for refined_resumes
    refined_query = MagicMock()
    refined_query.filter.return_value = refined_query
    refined_query.order_by.return_value = refined_query
    refined_query.all.return_value = refined_resumes or []

    def mock_query_side_effect(model):
        """Return appropriate query based on is_base filter."""
        if base_resumes is not None and refined_resumes is not None:
            # This is a simplified mock - in reality, the filter would determine which list
            # For testing purposes, we return the base query and handle both lists
            return base_query
        return base_query

    mock_db.query.side_effect = mock_query_side_effect
    return mock_db


def test_base_resume_shows_refine_button_in_dashboard():
    """
    Test that base resumes show the 'Refine' button in the dashboard list.

    Args: None

    Returns: None (asserts test conditions)

    Notes:
        1. Create mock user and app
        2. Set up mock base resume with is_base=True
        3. Mock database to return base resumes
        4. Make HTMX request to /api/resumes
        5. Assert 'Refine' link exists with correct URL pattern
        6. Assert purple styling classes are present
    """
    log.debug("test_base_resume_shows_refine_button_in_dashboard starting")

    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    mock_user = create_mock_user()

    # Create mock base resume
    resume_data = ResumeData(
        user_id=1,
        name="My Base Resume",
        content="# Base Resume Content",
        is_base=True,
    )
    mock_resume = DatabaseResume(data=resume_data)
    mock_resume.id = 1
    mock_resume.created_at = datetime.datetime.now(datetime.UTC)
    mock_resume.updated_at = datetime.datetime.now(datetime.UTC)

    # Patch the get_user_resumes_with_pagination function to return our mock data
    # This is simpler than trying to mock the complex SQLAlchemy query chain
    mock_date_range = MagicMock()
    mock_date_range.start_date = datetime.datetime.now() - datetime.timedelta(days=7)
    mock_date_range.end_date = datetime.datetime.now()

    def get_mock_user():
        return mock_user

    app.dependency_overrides[get_current_user_from_cookie] = get_mock_user

    with patch(
        "resume_editor.app.api.routes.resume.get_oldest_resume_date",
        return_value=datetime.datetime.now(),
    ):
        with patch(
            "resume_editor.app.api.routes.resume.get_user_resumes_with_pagination",
            return_value=([mock_resume], mock_date_range),
        ):
            response = client.get("/api/resumes", headers={"HX-Request": "true"})

        assert response.status_code == 200

        soup = BeautifulSoup(response.content, "html.parser")

        # Find the Refine link
        refine_link = soup.find("a", href="/resumes/1/refine")
        assert refine_link is not None, "Refine link should exist for base resume"
        assert "Refine" in refine_link.text, "Refine link should have 'Refine' text"

        # Check purple styling classes
        assert "bg-purple-500" in refine_link.get("class", []), (
            "Should have bg-purple-500 class"
        )
        assert "hover:bg-purple-600" in refine_link.get("class", []), (
            "Should have hover:bg-purple-600 class"
        )
        assert "text-white" in refine_link.get("class", []), (
            "Should have text-white class"
        )

    log.debug("test_base_resume_shows_refine_button_in_dashboard returning")
    app.dependency_overrides.clear()


def test_refined_resume_does_not_show_refine_button_in_dashboard():
    """
    Test that refined resumes do NOT show the 'Refine' button in the dashboard list.

    Args: None

    Returns: None (asserts test conditions)

    Notes:
        1. Create mock user and app
        2. Set up mock refined resume with is_base=False
        3. Mock database to return refined resumes
        4. Make HTMX request to /api/resumes
        5. Assert 'Refine' link does NOT exist
        6. Assert 'View' button is present instead
    """
    log.debug("test_refined_resume_does_not_show_refine_button_in_dashboard starting")

    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    mock_user = create_mock_user()

    # Create mock refined resume (is_base=False)
    resume_data = ResumeData(
        user_id=1,
        name="My Refined Resume",
        content="# Refined Resume Content",
        is_base=False,
        parent_id=1,
    )
    mock_resume = DatabaseResume(data=resume_data)
    mock_resume.id = 2
    mock_resume.created_at = datetime.datetime.now(datetime.UTC)
    mock_resume.updated_at = datetime.datetime.now(datetime.UTC)

    # Patch the get_user_resumes_with_pagination function to return our mock data
    # This is simpler than trying to mock the complex SQLAlchemy query chain
    mock_date_range = MagicMock()
    mock_date_range.start_date = datetime.datetime.now() - datetime.timedelta(days=7)
    mock_date_range.end_date = datetime.datetime.now()

    def get_mock_user():
        return mock_user

    app.dependency_overrides[get_current_user_from_cookie] = get_mock_user
    # Don't override get_db - let the route use the real dependency
    # but patch the function that uses it

    with patch(
        "resume_editor.app.api.routes.resume.get_oldest_resume_date",
        return_value=datetime.datetime.now(),
    ):
        with patch(
            "resume_editor.app.api.routes.resume.get_user_resumes_with_pagination",
            return_value=([mock_resume], mock_date_range),
        ):
            response = client.get("/api/resumes", headers={"HX-Request": "true"})

        assert response.status_code == 200

        soup = BeautifulSoup(response.content, "html.parser")

        # Find all links - there should be no Refine link for refined resume
        refine_links = soup.find_all("a", href="/resumes/2/refine")
        assert len(refine_links) == 0, "Refine link should NOT exist for refined resume"

        # But there should be a View link
        view_link = soup.find("a", href="/resumes/2/view")
        assert view_link is not None, "View link should exist for refined resume"
        assert "View" in view_link.text, "View link should have 'View' text"

        # Check blue styling for View button
        assert "bg-blue-500" in view_link.get("class", []), (
            "View button should have bg-blue-500 class"
        )

    log.debug("test_refined_resume_does_not_show_refine_button_in_dashboard returning")
    app.dependency_overrides.clear()


def test_refined_resume_with_parent_shows_new_refinement_button():
    """
    Test that refined resumes with parent_id show the 'New refinement' button on view page.

    Args: None

    Returns: None (asserts test conditions)

    Notes:
        1. Create mock user and app
        2. Set up mock refined resume with is_base=False, parent_id=123
        3. Mock database to return resume by ID
        4. Request /resumes/{id}/view
        5. Assert 'New refinement' link exists
        6. Assert link goes to /resumes/123/refine
        7. Assert blue styling classes are present
    """
    log.debug("test_refined_resume_with_parent_shows_new_refinement_button starting")

    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    mock_user = create_mock_user()

    # Create mock refined resume with parent_id
    resume_data = ResumeData(
        user_id=1,
        name="Refined Resume with Parent",
        content="# Refined Content",
        is_base=False,
        parent_id=123,
    )
    mock_resume = DatabaseResume(data=resume_data)
    mock_resume.id = 456

    def get_mock_user():
        return mock_user

    mock_db_session = MagicMock()

    def get_mock_db():
        yield mock_db_session

    app.dependency_overrides[get_current_user_from_cookie] = get_mock_user
    app.dependency_overrides[get_db] = get_mock_db

    with patch(
        "resume_editor.app.web.pages.get_resume_by_id_and_user",
        return_value=mock_resume,
    ) as mock_get_resume:
        response = client.get("/resumes/456/view")

        assert response.status_code == 200

        soup = BeautifulSoup(response.content, "html.parser")

        # Find the 'New refinement' link - should link to parent resume's refine page
        new_refinement_link = soup.find("a", href="/resumes/123/refine")
        assert new_refinement_link is not None, "New refinement link should exist"
        assert "New refinement" in new_refinement_link.text, (
            "Link should have 'New refinement' text"
        )

        # Check blue styling classes
        assert "bg-blue-500" in new_refinement_link.get("class", []), (
            "Should have bg-blue-500 class"
        )
        assert "hover:bg-blue-600" in new_refinement_link.get("class", []), (
            "Should have hover:bg-blue-600 class"
        )
        assert "text-white" in new_refinement_link.get("class", []), (
            "Should have text-white class"
        )

        mock_get_resume.assert_called_once_with(
            db=mock_db_session, resume_id=456, user_id=1
        )

    log.debug("test_refined_resume_with_parent_shows_new_refinement_button returning")
    app.dependency_overrides.clear()


def test_refined_resume_without_parent_shows_disabled_button():
    """
    Test that refined resumes without parent_id show a disabled 'New refinement' button.

    Args: None

    Returns: None (asserts test conditions)

    Notes:
        1. Create mock user and app
        2. Set up mock refined resume with is_base=False, parent_id=None
        3. Mock database to return resume by ID
        4. Request /resumes/{id}/view
        5. Assert disabled button exists with 'disabled' attribute
        6. Assert tooltip text is present
        7. Assert gray styling classes are present
    """
    log.debug("test_refined_resume_without_parent_shows_disabled_button starting")

    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    mock_user = create_mock_user()

    # Create mock refined resume WITHOUT parent_id
    resume_data = ResumeData(
        user_id=1,
        name="Orphan Refined Resume",
        content="# Orphan Content",
        is_base=False,
        parent_id=None,
    )
    mock_resume = DatabaseResume(data=resume_data)
    mock_resume.id = 789

    def get_mock_user():
        return mock_user

    mock_db_session = MagicMock()

    def get_mock_db():
        yield mock_db_session

    app.dependency_overrides[get_current_user_from_cookie] = get_mock_user
    app.dependency_overrides[get_db] = get_mock_db

    with patch(
        "resume_editor.app.web.pages.get_resume_by_id_and_user",
        return_value=mock_resume,
    ) as mock_get_resume:
        response = client.get("/resumes/789/view")

        assert response.status_code == 200

        soup = BeautifulSoup(response.content, "html.parser")

        # Find the disabled button
        disabled_button = soup.find(
            "button", string=lambda t: t and "New refinement" in t
        )
        assert disabled_button is not None, (
            "Disabled New refinement button should exist"
        )
        assert disabled_button.has_attr("disabled"), (
            "Button should have disabled attribute"
        )

        # Check tooltip text
        tooltip = disabled_button.get("title", "")
        assert "No base resume available" in tooltip, (
            f"Tooltip should indicate no base resume, got: {tooltip}"
        )

        # Check gray styling classes
        assert "bg-gray-400" in disabled_button.get("class", []), (
            "Should have bg-gray-400 class"
        )
        assert "cursor-not-allowed" in disabled_button.get("class", []), (
            "Should have cursor-not-allowed class"
        )
        assert "text-white" in disabled_button.get("class", []), (
            "Should have text-white class"
        )

        mock_get_resume.assert_called_once_with(
            db=mock_db_session, resume_id=789, user_id=1
        )

    log.debug("test_refined_resume_without_parent_shows_disabled_button returning")
    app.dependency_overrides.clear()


def test_base_resume_does_not_show_new_refinement_button():
    """
    Test that base resumes do NOT show the 'New refinement' button on view page.

    Args: None

    Returns: None (asserts test conditions)

    Notes:
        1. Create mock user and app
        2. Set up mock base resume with is_base=True
        3. Mock database to return resume by ID
        4. Request /resumes/{id}/view
        5. Assert 'New refinement' button/link does NOT exist
    """
    log.debug("test_base_resume_does_not_show_new_refinement_button starting")

    app = create_app()
    client = TestClient(app)
    app.dependency_overrides.clear()

    mock_user = create_mock_user()

    # Create mock base resume
    resume_data = ResumeData(
        user_id=1,
        name="Base Resume",
        content="# Base Content",
        is_base=True,
        parent_id=None,
    )
    mock_resume = DatabaseResume(data=resume_data)
    mock_resume.id = 100

    def get_mock_user():
        return mock_user

    mock_db_session = MagicMock()

    def get_mock_db():
        yield mock_db_session

    app.dependency_overrides[get_current_user_from_cookie] = get_mock_user
    app.dependency_overrides[get_db] = get_mock_db

    with patch(
        "resume_editor.app.web.pages.get_resume_by_id_and_user",
        return_value=mock_resume,
    ) as mock_get_resume:
        response = client.get("/resumes/100/view")

        assert response.status_code == 200

        soup = BeautifulSoup(response.content, "html.parser")

        # Check that there's no 'New refinement' link or button
        # Look for links with "refine" in href
        refine_links = soup.find_all("a", href=lambda h: h and "refine" in h)
        for link in refine_links:
            # Links to other pages like /resumes/100/edit are OK, just not refine links
            if "New refinement" in link.text:
                assert False, "Base resume should not have 'New refinement' link"

        # Look for any button with "New refinement" text
        buttons = soup.find_all("button")
        for button in buttons:
            button_text = button.get_text(strip=True)
            if "New refinement" in button_text:
                assert False, "Base resume should not have 'New refinement' button"

        mock_get_resume.assert_called_once_with(
            db=mock_db_session, resume_id=100, user_id=1
        )

    log.debug("test_base_resume_does_not_show_new_refinement_button returning")
    app.dependency_overrides.clear()
