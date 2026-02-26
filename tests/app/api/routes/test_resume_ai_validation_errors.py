"""Tests for validation error paths in resume_ai routes."""

from unittest.mock import MagicMock, patch

import pytest

from resume_editor.app.api.routes.resume_ai import (
    refine_resume_stream_get,
    refine_resume_stream,
    _make_early_error_stream_response,
    RefineStreamQueryParams,
    RefineStreamOptionalParams,
)
from resume_editor.app.api.routes.route_models import RefineForm
from resume_editor.app.models.resume_model import Resume as DatabaseResume
from resume_editor.app.models.resume_model import ResumeData
from resume_editor.app.models.user import User, UserData


@pytest.fixture
def test_user():
    """Create a test user."""
    return User(
        data=UserData(
            id_=1,
            username="testuser",
            email="test@test.com",
            hashed_password="hashed_password",
        )
    )


@pytest.fixture
def test_resume():
    """Create a test resume."""
    data = ResumeData(
        user_id=1,
        name="Test Resume",
        content="# Test Resume\n\n## Personal\nName: Test User",
    )
    resume = DatabaseResume(data=data)
    resume.id = 1
    resume.is_base = True
    return resume


class TestMakeEarlyErrorStreamResponse:
    """Tests for _make_early_error_stream_response helper."""

    def test_returns_sse_stream_with_error(self):
        """Test that the helper returns a proper SSE error stream."""
        response = _make_early_error_stream_response("Test error message")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"


class TestRefineStreamGetValidationErrors:
    """Tests for validation error handling in GET refine stream endpoint."""

    @pytest.mark.asyncio
    async def test_refine_stream_get_returns_sse_error_on_long_company(
        self, test_user, test_resume
    ):
        """Test that GET refine stream returns SSE error when company validation fails."""
        mock_db = MagicMock()
        long_company = "A" * 300
        query = RefineStreamQueryParams(
            job_description="Test job",
            limit_refinement_years=None,
        )
        optional = RefineStreamOptionalParams(
            company=long_company,
            notes=None,
        )

        response = await refine_resume_stream_get(
            db=mock_db,
            current_user=test_user,
            resume=test_resume,
            query=query,
            optional=optional,
        )

        # Should return SSE error response
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    @pytest.mark.asyncio
    async def test_refine_stream_get_returns_sse_error_on_long_notes(
        self, test_user, test_resume
    ):
        """Test that GET refine stream returns SSE error when notes validation fails."""
        mock_db = MagicMock()
        long_notes = "A" * 5001
        query = RefineStreamQueryParams(
            job_description="Test job",
            limit_refinement_years=None,
        )
        optional = RefineStreamOptionalParams(
            company=None,
            notes=long_notes,
        )

        response = await refine_resume_stream_get(
            db=mock_db,
            current_user=test_user,
            resume=test_resume,
            query=query,
            optional=optional,
        )

        # Should return SSE error response
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"


class TestRefineStreamPostValidationErrors:
    """Tests for validation error handling in POST refine stream endpoint."""

    @pytest.mark.asyncio
    async def test_refine_stream_post_returns_html_error_on_long_company_htmx(
        self, test_user, test_resume
    ):
        """Test that POST refine stream returns HTML error for HTMX when company validation fails."""
        mock_db = MagicMock()
        mock_request = MagicMock()
        mock_request.headers = {"HX-Request": "true"}

        long_company = "A" * 300
        form_data = RefineForm(
            job_description="Test job",
            company=long_company,
            notes="",
        )

        response = await refine_resume_stream(
            http_request=mock_request,
            db=mock_db,
            current_user=test_user,
            resume=test_resume,
            form_data=form_data,
        )

        # Should return HTML error response
        assert response.status_code == 200
        response_text = response.body.decode("utf-8")
        assert "text-red-500" in response_text
        assert "Company name must be 255 characters or less" in response_text

    @pytest.mark.asyncio
    async def test_refine_stream_post_returns_sse_error_on_long_notes_non_htmx(
        self, test_user, test_resume
    ):
        """Test that POST refine stream returns SSE error for non-HTMX when notes validation fails."""
        mock_db = MagicMock()
        mock_request = MagicMock()
        mock_request.headers = {}  # No HX-Request header

        long_notes = "A" * 5001
        form_data = RefineForm(
            job_description="Test job",
            company="",
            notes=long_notes,
        )

        response = await refine_resume_stream(
            http_request=mock_request,
            db=mock_db,
            current_user=test_user,
            resume=test_resume,
            form_data=form_data,
        )

        # Should return SSE error response
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
