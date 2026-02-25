"""Tests for pages.py view page with company field."""

import logging
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from resume_editor.app.core.auth import get_current_user_from_cookie
from resume_editor.app.database.database import get_db
from resume_editor.app.main import app
from resume_editor.app.models.user import User

# Set up logging for tests
logging.basicConfig(level=logging.DEBUG)


class TestViewResumePost:
    """Test cases for view page POST handler with company field updates."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user for testing."""
        user = Mock(spec=User)
        user.id = 1
        user.username = "testuser"
        user.is_admin = False
        user.hashed_password = "hashed_password"
        return user

    @pytest.fixture
    def mock_resume(self):
        """Create a mock resume for testing."""
        resume = Mock()
        resume.id = 1
        resume.name = "Test Resume"
        resume.content = "# Test Resume\n\n## Introduction\nTest intro\n\n## Experience\nTest experience"
        resume.introduction = None
        resume.notes = None
        resume.company = None
        resume.user_id = 1
        resume.is_base = True
        return resume

    @pytest.fixture
    def client(self, mock_user, mock_resume):
        """Create a test client with mocked dependencies."""
        mock_db = Mock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

        def get_mock_db():
            yield mock_db

        def get_mock_user():
            yield mock_user

        app.dependency_overrides[get_db] = get_mock_db
        app.dependency_overrides[get_current_user_from_cookie] = get_mock_user

        # Create client that follows redirects by default
        yield TestClient(app)

        app.dependency_overrides.clear()

    @pytest.fixture
    def client_no_redirects(self, mock_user, mock_resume):
        """Create a test client that doesn't follow redirects."""
        mock_db = Mock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

        def get_mock_db():
            yield mock_db

        def get_mock_user():
            yield mock_user

        app.dependency_overrides[get_db] = get_mock_db
        app.dependency_overrides[get_current_user_from_cookie] = get_mock_user

        # Create client that does NOT follow redirects
        yield TestClient(app, follow_redirects=False)

        app.dependency_overrides.clear()

    @patch("resume_editor.app.web.pages.validate_company_and_notes")
    @patch("resume_editor.app.web.pages.update_resume")
    @patch("resume_editor.app.web.pages.reconstruct_resume_with_new_introduction")
    def test_updates_company_and_notes(
        self,
        mock_reconstruct,
        mock_update,
        mock_validate,
        client_no_redirects,
        mock_resume,
    ):
        """Test that company and notes are updated successfully."""
        # Setup mocks
        mock_validate.return_value = Mock(is_valid=True, errors={})
        mock_reconstruct.return_value = "# Updated Resume Content"
        mock_update.return_value = mock_resume

        # Make request
        response = client_no_redirects.post(
            "/resumes/1/view",
            data={
                "introduction": "Updated intro",
                "notes": "Updated notes",
                "company": "Test Company Inc",
            },
        )

        # Assert
        assert response.status_code == 303
        assert response.headers["location"] == "/resumes/1/view"

        # Verify validation was called
        mock_validate.assert_called_once_with("Test Company Inc", "Updated notes")

        # Verify update was called with correct params
        mock_update.assert_called_once()
        call_args = mock_update.call_args
        assert call_args.kwargs["params"].introduction == "Updated intro"
        assert call_args.kwargs["params"].notes == "Updated notes"
        assert call_args.kwargs["params"].company == "Test Company Inc"

    @patch("resume_editor.app.web.pages.validate_company_and_notes")
    def test_validation_failure_returns_error(self, mock_validate, client):
        """Test that validation failure returns error HTML for HTMX requests."""
        mock_validate.return_value = Mock(
            is_valid=False,
            errors={"company": "Company name must be 255 characters or less"},
        )

        # Make HTMX request
        response = client.post(
            "/resumes/1/view",
            data={"company": "x" * 300, "notes": ""},
            headers={"HX-Request": "true"},
        )

        # Assert
        assert response.status_code == 200
        assert "text-red-500" in response.text
        assert "Company name must be 255 characters or less" in response.text

    @patch("resume_editor.app.web.pages.validate_company_and_notes")
    def test_validation_failure_redirects_for_regular_request(
        self, mock_validate, client_no_redirects
    ):
        """Test that validation failure redirects for regular (non-HTMX) requests."""
        mock_validate.return_value = Mock(
            is_valid=False,
            errors={"company": "Company name must be 255 characters or less"},
        )

        # Make regular request (no HX-Request header)
        response = client_no_redirects.post(
            "/resumes/1/view",
            data={"company": "x" * 300, "notes": ""},
        )

        # Assert
        assert response.status_code == 303
        assert response.headers["location"] == "/resumes/1/view"

    @patch("resume_editor.app.web.pages.validate_company_and_notes")
    @patch("resume_editor.app.web.pages.update_resume")
    @patch("resume_editor.app.web.pages.reconstruct_resume_with_new_introduction")
    def test_optional_fields_can_be_null(
        self,
        mock_reconstruct,
        mock_update,
        mock_validate,
        client_no_redirects,
        mock_resume,
    ):
        """Test that all form fields can be null/optional."""
        mock_validate.return_value = Mock(is_valid=True, errors={})
        mock_reconstruct.return_value = "# Updated Resume"
        mock_update.return_value = mock_resume

        # Make request with no data
        response = client_no_redirects.post("/resumes/1/view", data={})

        # Assert
        assert response.status_code == 303

        # Verify validation was called with None values
        mock_validate.assert_called_once_with(None, None)

    @patch("resume_editor.app.web.pages.validate_company_and_notes")
    @patch("resume_editor.app.web.pages.update_resume")
    @patch("resume_editor.app.web.pages.reconstruct_resume_with_new_introduction")
    def test_notes_validation_failure(
        self,
        mock_reconstruct,
        mock_update,
        mock_validate,
        client,
    ):
        """Test that notes validation errors are returned properly."""
        mock_validate.return_value = Mock(
            is_valid=False, errors={"notes": "Notes must be 5000 characters or less"}
        )

        response = client.post(
            "/resumes/1/view",
            data={"notes": "x" * 5001},
            headers={"HX-Request": "true"},
        )

        assert response.status_code == 200
        assert "Notes must be 5000 characters or less" in response.text

    @patch("resume_editor.app.web.pages.validate_company_and_notes")
    @patch("resume_editor.app.web.pages.update_resume")
    @patch("resume_editor.app.web.pages.reconstruct_resume_with_new_introduction")
    def test_multiple_validation_errors(
        self,
        mock_reconstruct,
        mock_update,
        mock_validate,
        client,
    ):
        """Test that multiple validation errors are all displayed."""
        mock_validate.return_value = Mock(
            is_valid=False,
            errors={
                "company": "Company name must be 255 characters or less",
                "notes": "Notes must be 5000 characters or less",
            },
        )

        response = client.post(
            "/resumes/1/view",
            data={"company": "x" * 300, "notes": "x" * 5001},
            headers={"HX-Request": "true"},
        )

        assert response.status_code == 200
        assert "Company name must be 255 characters or less" in response.text
        assert "Notes must be 5000 characters or less" in response.text
