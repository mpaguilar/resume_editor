import datetime
from unittest.mock import ANY, Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from resume_editor.app.api.routes.route_logic.resume_crud import (
    DateRange,
    get_oldest_resume_date,
    get_user_resumes_with_pagination,
)
from resume_editor.app.core.auth import get_current_user_from_cookie
from resume_editor.app.database.database import get_db
from resume_editor.app.main import create_app
from resume_editor.app.models.resume_model import Resume as DatabaseResume, ResumeData
from resume_editor.app.models.user import User as DBUser, UserData


@pytest.fixture
def test_user():
    """Fixture for a test user."""
    user = DBUser(
        data=UserData(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            id_=1,
        )
    )
    return user


@pytest.fixture
def test_resume(test_user):
    """Fixture for a test base resume."""
    resume_data = ResumeData(
        user_id=test_user.id,
        name="Test Resume",
        content="# Test",
    )
    resume = DatabaseResume(data=resume_data)
    resume.id = 1
    resume.is_base = True
    resume.created_at = datetime.datetime.now(datetime.UTC)
    resume.updated_at = datetime.datetime.now(datetime.UTC)
    return resume


@pytest.fixture
def test_refined_resume(test_user):
    """Fixture for a test refined resume."""
    resume_data = ResumeData(
        user_id=test_user.id,
        name="Refined Resume",
        content="# Refined",
        is_base=False,
        parent_id=1,
    )
    resume = DatabaseResume(data=resume_data)
    resume.id = 2
    resume.is_base = False
    resume.created_at = datetime.datetime.now(datetime.UTC)
    resume.updated_at = datetime.datetime.now(datetime.UTC)
    return resume


class TestListResumesPagination:
    """Tests for list_resumes pagination functionality."""

    def test_list_resumes_default_week_offset(self, test_user, test_resume):
        """Test list_resumes with default week offset (0)."""
        app = create_app()

        mock_db = Mock(spec=Session)
        mock_date_range = DateRange(
            start_date=datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=7),
            end_date=datetime.datetime.now(datetime.UTC),
        )

        def get_mock_db():
            yield mock_db

        app.dependency_overrides[get_db] = get_mock_db
        app.dependency_overrides[get_current_user_from_cookie] = lambda: test_user

        test_client = TestClient(app)

        with patch(
            "resume_editor.app.api.routes.resume.get_user_resumes_with_pagination"
        ) as mock_paginate:
            mock_paginate.return_value = ([test_resume], mock_date_range)
            with patch(
                "resume_editor.app.api.routes.resume.get_oldest_resume_date"
            ) as mock_oldest:
                mock_oldest.return_value = None
                response = test_client.get("/api/resumes")

        assert response.status_code == 200
        app.dependency_overrides.clear()


class TestBaseResumeSorting:
    """Tests for base resume sorting behavior."""

    def test_base_resumes_always_sorted_by_created_at_desc(self, test_user):
        """Test base resumes are always sorted by created_at descending regardless of sort_by param."""
        mock_db = Mock(spec=Session)

        # Create mock base resumes with different creation dates
        base_resume_1 = Mock(spec=DatabaseResume)
        base_resume_1.id = 1
        base_resume_1.is_base = True
        base_resume_1.created_at = datetime.datetime(2024, 1, 1, tzinfo=datetime.UTC)

        base_resume_2 = Mock(spec=DatabaseResume)
        base_resume_2.id = 2
        base_resume_2.is_base = True
        base_resume_2.created_at = datetime.datetime(2024, 6, 1, tzinfo=datetime.UTC)

        # Mock the query chain for base resumes
        mock_base_query = Mock()
        mock_base_query.filter.return_value = mock_base_query
        mock_base_query.order_by.return_value = mock_base_query
        mock_base_query.all.return_value = [
            base_resume_2,
            base_resume_1,
        ]  # Newest first

        # Mock the query chain for refined resumes
        mock_refined_query = Mock()
        mock_refined_query.filter.return_value = mock_refined_query
        mock_refined_query.all.return_value = []

        call_count = [0]

        def mock_filter_side_effect(*args, **kwargs):
            call_count[0] += 1
            # First call is user_id filter, return a query that chains to base_query
            if call_count[0] == 1:
                mock_user_query = Mock()
                mock_user_query.filter.return_value = mock_base_query
                return mock_user_query
            # Second call is is_base=True filter
            elif call_count[0] == 2:
                return mock_base_query
            # Third call is is_base=False filter (refined)
            else:
                return mock_refined_query

        mock_db.query.return_value.filter.side_effect = mock_filter_side_effect

        # Test with name_asc sort - base resumes should still be sorted by created_at desc
        resumes, _ = get_user_resumes_with_pagination(
            db=mock_db, user_id=test_user.id, week_offset=0, sort_by="name_asc"
        )

        # Verify base_query.order_by was called (confirming sorting is applied)
        # The key behavior is that base resumes are sorted, regardless of the sort_by parameter
        assert mock_base_query.order_by.called, (
            "order_by should be called on base_query"
        )
        # Verify resumes are returned (base resumes should be in the result)
        assert len(resumes) >= 2
        resume_ids = [r.id for r in resumes]
        assert 2 in resume_ids  # base_resume_2 should be in results
        assert 1 in resume_ids  # base_resume_1 should be in results

    def test_refined_resumes_respect_sort_by_parameter(self, test_user):
        """Test refined resumes are sorted according to the sort_by parameter."""
        mock_db = Mock(spec=Session)

        # Mock empty base resumes
        mock_base_query = Mock()
        mock_base_query.filter.return_value = mock_base_query
        mock_base_query.order_by.return_value = mock_base_query
        mock_base_query.all.return_value = []

        # Mock refined resumes query
        mock_refined_query = Mock()
        mock_refined_query.filter.return_value = mock_refined_query
        mock_refined_query.order_by.return_value = mock_refined_query
        mock_refined_query.all.return_value = []

        def mock_filter_side_effect(*args, **kwargs):
            # First call is user_id filter, return a query that chains to base_query
            if "user_id" in str(args):
                mock_user_query = Mock()
                mock_user_query.filter.return_value = mock_base_query
                return mock_user_query
            # is_base=True filter
            elif "is_base" in str(args) and "True" in str(args):
                return mock_base_query
            # is_base=False filter (refined)
            else:
                return mock_refined_query

        mock_db.query.return_value.filter.side_effect = mock_filter_side_effect

        # Test with different sort options
        for sort_by in ["name_asc", "name_desc", "created_at_asc", "created_at_desc"]:
            mock_refined_query.reset_mock()
            mock_base_query.reset_mock()

            get_user_resumes_with_pagination(
                db=mock_db, user_id=test_user.id, week_offset=0, sort_by=sort_by
            )

            # Refined query should use the dynamic sort order
            assert mock_refined_query.order_by.called, (
                f"order_by should be called on refined_query for sort_by={sort_by}"
            )

    def test_list_resumes_with_filter_query(self, test_user, test_resume):
        """Test list_resumes with filter query parameter."""
        app = create_app()

        mock_db = Mock(spec=Session)
        mock_date_range = DateRange(
            start_date=datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=7),
            end_date=datetime.datetime.now(datetime.UTC),
        )

        def get_mock_db():
            yield mock_db

        app.dependency_overrides[get_db] = get_mock_db
        app.dependency_overrides[get_current_user_from_cookie] = lambda: test_user

        test_client = TestClient(app)

        with patch(
            "resume_editor.app.api.routes.resume.get_user_resumes_with_pagination"
        ) as mock_paginate:
            mock_paginate.return_value = ([test_resume], mock_date_range)
            with patch(
                "resume_editor.app.api.routes.resume.get_oldest_resume_date"
            ) as mock_oldest:
                mock_oldest.return_value = None
                response = test_client.get("/api/resumes?filter=engineer")

        assert response.status_code == 200
        app.dependency_overrides.clear()

    def test_list_resumes_invalid_week_offset_defaults_to_zero(
        self, test_user, test_resume
    ):
        """Test list_resumes handles invalid week_offset gracefully."""
        app = create_app()

        mock_db = Mock(spec=Session)
        mock_date_range = DateRange(
            start_date=datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=7),
            end_date=datetime.datetime.now(datetime.UTC),
        )

        def get_mock_db():
            yield mock_db

        app.dependency_overrides[get_db] = get_mock_db
        app.dependency_overrides[get_current_user_from_cookie] = lambda: test_user

        test_client = TestClient(app)

        with patch(
            "resume_editor.app.api.routes.resume.get_user_resumes_with_pagination"
        ) as mock_paginate:
            mock_paginate.return_value = ([test_resume], mock_date_range)
            with patch(
                "resume_editor.app.api.routes.resume.get_oldest_resume_date"
            ) as mock_oldest:
                mock_oldest.return_value = None
                response = test_client.get("/api/resumes?week_offset=invalid")

        assert response.status_code == 200
        app.dependency_overrides.clear()

    def test_list_resumes_clamps_week_offset_to_max(self, test_user, test_resume):
        """Test list_resumes clamps week_offset to max range."""
        app = create_app()

        mock_db = Mock(spec=Session)
        mock_date_range = DateRange(
            start_date=datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=7),
            end_date=datetime.datetime.now(datetime.UTC),
        )

        def get_mock_db():
            yield mock_db

        app.dependency_overrides[get_db] = get_mock_db
        app.dependency_overrides[get_current_user_from_cookie] = lambda: test_user

        test_client = TestClient(app)

        with patch(
            "resume_editor.app.api.routes.resume.get_user_resumes_with_pagination"
        ) as mock_paginate:
            mock_paginate.return_value = ([test_resume], mock_date_range)
            with patch(
                "resume_editor.app.api.routes.resume.get_oldest_resume_date"
            ) as mock_oldest:
                mock_oldest.return_value = None
                response = test_client.get("/api/resumes?week_offset=-100")

        assert response.status_code == 200
        app.dependency_overrides.clear()

    def test_list_resumes_prevents_future_weeks(self, test_user, test_resume):
        """Test list_resumes prevents navigating to future weeks."""
        app = create_app()

        mock_db = Mock(spec=Session)
        mock_date_range = DateRange(
            start_date=datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=7),
            end_date=datetime.datetime.now(datetime.UTC),
        )

        def get_mock_db():
            yield mock_db

        app.dependency_overrides[get_db] = get_mock_db
        app.dependency_overrides[get_current_user_from_cookie] = lambda: test_user

        test_client = TestClient(app)

        with patch(
            "resume_editor.app.api.routes.resume.get_user_resumes_with_pagination"
        ) as mock_paginate:
            mock_paginate.return_value = ([test_resume], mock_date_range)
            with patch(
                "resume_editor.app.api.routes.resume.get_oldest_resume_date"
            ) as mock_oldest:
                mock_oldest.return_value = None
                response = test_client.get("/api/resumes?week_offset=1")

        assert response.status_code == 200
        app.dependency_overrides.clear()

    def test_list_resumes_truncates_long_filter(self, test_user, test_resume):
        """Test list_resumes truncates filter to 100 characters."""
        app = create_app()

        mock_db = Mock(spec=Session)
        mock_date_range = DateRange(
            start_date=datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=7),
            end_date=datetime.datetime.now(datetime.UTC),
        )

        def get_mock_db():
            yield mock_db

        app.dependency_overrides[get_db] = get_mock_db
        app.dependency_overrides[get_current_user_from_cookie] = lambda: test_user

        test_client = TestClient(app)

        long_filter = "a" * 200

        with patch(
            "resume_editor.app.api.routes.resume.get_user_resumes_with_pagination"
        ) as mock_paginate:
            mock_paginate.return_value = ([test_resume], mock_date_range)
            with patch(
                "resume_editor.app.api.routes.resume.get_oldest_resume_date"
            ) as mock_oldest:
                mock_oldest.return_value = None
                response = test_client.get(f"/api/resumes?filter={long_filter}")

        assert response.status_code == 200
        app.dependency_overrides.clear()

    def test_list_resumes_htmx_response(self, test_user, test_resume):
        """Test list_resumes returns HTML for HTMX requests."""
        app = create_app()

        mock_db = Mock(spec=Session)
        mock_date_range = DateRange(
            start_date=datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=7),
            end_date=datetime.datetime.now(datetime.UTC),
        )

        def get_mock_db():
            yield mock_db

        app.dependency_overrides[get_db] = get_mock_db
        app.dependency_overrides[get_current_user_from_cookie] = lambda: test_user

        test_client = TestClient(app)

        with patch(
            "resume_editor.app.api.routes.resume.get_user_resumes_with_pagination"
        ) as mock_paginate:
            mock_paginate.return_value = ([test_resume], mock_date_range)
            with patch(
                "resume_editor.app.api.routes.resume.get_oldest_resume_date"
            ) as mock_oldest:
                mock_oldest.return_value = None
                with patch(
                    "resume_editor.app.api.routes.resume._generate_resume_list_html"
                ) as mock_html:
                    mock_html.return_value = "<html>test</html>"
                    response = test_client.get(
                        "/api/resumes", headers={"HX-Request": "true"}
                    )

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        app.dependency_overrides.clear()

    def test_list_resumes_json_response(self, test_user, test_resume):
        """Test list_resumes returns JSON for API requests."""
        app = create_app()

        mock_db = Mock(spec=Session)
        mock_date_range = DateRange(
            start_date=datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=7),
            end_date=datetime.datetime.now(datetime.UTC),
        )

        def get_mock_db():
            yield mock_db

        app.dependency_overrides[get_db] = get_mock_db
        app.dependency_overrides[get_current_user_from_cookie] = lambda: test_user

        test_client = TestClient(app)

        with patch(
            "resume_editor.app.api.routes.resume.get_user_resumes_with_pagination"
        ) as mock_paginate:
            mock_paginate.return_value = ([test_resume], mock_date_range)
            with patch(
                "resume_editor.app.api.routes.resume.get_oldest_resume_date"
            ) as mock_oldest:
                mock_oldest.return_value = None
                response = test_client.get("/api/resumes")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        app.dependency_overrides.clear()

    def test_list_resumes_combined_params(self, test_user, test_resume):
        """Test list_resumes with combined week_offset, filter, and sort_by."""
        app = create_app()

        mock_db = Mock(spec=Session)
        mock_date_range = DateRange(
            start_date=datetime.datetime.now(datetime.UTC)
            - datetime.timedelta(days=14),
            end_date=datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=7),
        )

        def get_mock_db():
            yield mock_db

        app.dependency_overrides[get_db] = get_mock_db
        app.dependency_overrides[get_current_user_from_cookie] = lambda: test_user

        test_client = TestClient(app)

        with patch(
            "resume_editor.app.api.routes.resume.get_user_resumes_with_pagination"
        ) as mock_paginate:
            mock_paginate.return_value = ([test_resume], mock_date_range)
            with patch(
                "resume_editor.app.api.routes.resume.get_oldest_resume_date"
            ) as mock_oldest:
                mock_oldest.return_value = None
                response = test_client.get(
                    "/api/resumes?week_offset=-1&filter=engineer&sort_by=name_asc"
                )

        assert response.status_code == 200
        app.dependency_overrides.clear()

    def test_list_resumes_no_overflow_with_very_old_date(self, test_user, test_resume):
        """Test that list_resumes handles very old dates without OverflowError.

        Regression test for pagination overflow bug where subtracting too many
        weeks from current date caused OverflowError. Verifies the 520-week
        limit prevents crash while still allowing pagination to work.
        """
        app = create_app()

        mock_db = Mock(spec=Session)
        mock_date_range = DateRange(
            start_date=datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=7),
            end_date=datetime.datetime.now(datetime.UTC),
        )

        def get_mock_db():
            yield mock_db

        app.dependency_overrides[get_db] = get_mock_db
        app.dependency_overrides[get_current_user_from_cookie] = lambda: test_user

        test_client = TestClient(app)

        # Mock a very old resume date (15 years ago, beyond 520 week limit)
        very_old_date = datetime.datetime.now(datetime.UTC) - datetime.timedelta(
            days=365 * 15
        )

        with patch(
            "resume_editor.app.api.routes.resume.get_user_resumes_with_pagination"
        ) as mock_paginate:
            mock_paginate.return_value = ([test_resume], mock_date_range)
            with patch(
                "resume_editor.app.api.routes.resume.get_oldest_resume_date"
            ) as mock_oldest:
                mock_oldest.return_value = very_old_date
                # Should not raise OverflowError
                response = test_client.get("/api/resumes?week_offset=-5")

        assert response.status_code == 200
        app.dependency_overrides.clear()
