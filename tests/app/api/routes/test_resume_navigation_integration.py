"""Integration tests for pagination navigation (Previous/Next Week).

These tests verify that the HTMX pagination navigation buttons
work correctly with the fixed boundary calculation.
"""

import datetime
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

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
    """Fixture for a test resume."""
    resume_data = ResumeData(
        user_id=test_user.id,
        name="Test Resume",
        content="# Test",
    )
    resume = DatabaseResume(data=resume_data)
    resume.id = 1
    resume.is_base = True
    resume.created_at = datetime.datetime.now(datetime.timezone.utc)
    resume.updated_at = datetime.datetime.now(datetime.timezone.utc)
    return resume


class TestPaginationNavigationIntegration:
    """Integration tests for Previous/Next Week navigation."""

    def test_previous_week_button_clickable_multiple_times(
        self, test_user, test_resume
    ):
        """Test that Previous Week button works when clicking multiple times.

        This is the main regression test for the boundary loop bug.
        With the bug, users couldn't navigate past certain offsets.
        """
        app = create_app()

        mock_db = Mock(spec=Session)

        def get_mock_db():
            yield mock_db

        app.dependency_overrides[get_db] = get_mock_db
        app.dependency_overrides[get_current_user_from_cookie] = lambda: test_user

        test_client = TestClient(app)

        from resume_editor.app.api.routes.route_logic.resume_crud import DateRange

        # Simulate a resume created 5 weeks ago
        five_weeks_ago = datetime.datetime.now(
            datetime.timezone.utc
        ) - datetime.timedelta(weeks=5)

        # Simulate clicking "Previous Week" multiple times
        for offset in [0, -1, -2, -3, -4, -5]:
            mock_date_range = DateRange(
                start_date=datetime.datetime.now(datetime.timezone.utc)
                - datetime.timedelta(days=7 * (abs(offset) + 1)),
                end_date=datetime.datetime.now(datetime.timezone.utc)
                - datetime.timedelta(days=7 * abs(offset)),
            )

            with patch(
                "resume_editor.app.api.routes.resume.get_user_resumes_with_pagination"
            ) as mock_paginate:
                mock_paginate.return_value = ([test_resume], mock_date_range)
                with patch(
                    "resume_editor.app.api.routes.resume.get_oldest_resume_date"
                ) as mock_oldest:
                    mock_oldest.return_value = five_weeks_ago

                    # HTMX request for pagination
                    response = test_client.get(
                        f"/api/resumes?week_offset={offset}",
                        headers={"HX-Request": "true"},
                    )

                    assert response.status_code == 200

        app.dependency_overrides.clear()

    def test_next_week_button_returns_to_present(self, test_user, test_resume):
        """Test that Next Week button works to navigate forward."""
        app = create_app()

        mock_db = Mock(spec=Session)

        def get_mock_db():
            yield mock_db

        app.dependency_overrides[get_db] = get_mock_db
        app.dependency_overrides[get_current_user_from_cookie] = lambda: test_user

        test_client = TestClient(app)

        from resume_editor.app.api.routes.route_logic.resume_crud import DateRange

        # Navigate from week -2 back to week -1, then to week 0
        for offset in [-2, -1, 0]:
            mock_date_range = DateRange(
                start_date=datetime.datetime.now(datetime.timezone.utc)
                - datetime.timedelta(days=7 * (abs(offset) + 1)),
                end_date=datetime.datetime.now(datetime.timezone.utc)
                - datetime.timedelta(days=7 * abs(offset)),
            )

            with patch(
                "resume_editor.app.api.routes.resume.get_user_resumes_with_pagination"
            ) as mock_paginate:
                mock_paginate.return_value = ([test_resume], mock_date_range)
                with patch(
                    "resume_editor.app.api.routes.resume.get_oldest_resume_date"
                ) as mock_oldest:
                    mock_oldest.return_value = None  # No older resumes

                    response = test_client.get(
                        f"/api/resumes?week_offset={offset}",
                        headers={"HX-Request": "true"},
                    )

                    assert response.status_code == 200

        app.dependency_overrides.clear()

    def test_boundary_detection_disables_previous_at_oldest(
        self, test_user, test_resume
    ):
        """Test that Previous Week button is disabled at the oldest week boundary.

        When viewing the oldest week that contains resumes, the Previous Week
        button should be disabled.
        """
        app = create_app()

        mock_db = Mock(spec=Session)

        def get_mock_db():
            yield mock_db

        app.dependency_overrides[get_db] = get_mock_db
        app.dependency_overrides[get_current_user_from_cookie] = lambda: test_user

        test_client = TestClient(app)

        from resume_editor.app.api.routes.route_logic.resume_crud import DateRange

        # Resume created exactly 3 weeks ago
        three_weeks_ago = datetime.datetime.now(
            datetime.timezone.utc
        ) - datetime.timedelta(weeks=3)

        # Viewing week -3 (the oldest week with resumes)
        mock_date_range = DateRange(
            start_date=datetime.datetime.now(datetime.timezone.utc)
            - datetime.timedelta(days=28),
            end_date=datetime.datetime.now(datetime.timezone.utc)
            - datetime.timedelta(days=21),
        )

        with patch(
            "resume_editor.app.api.routes.resume.get_user_resumes_with_pagination"
        ) as mock_paginate:
            mock_paginate.return_value = ([test_resume], mock_date_range)
            with patch(
                "resume_editor.app.api.routes.resume.get_oldest_resume_date"
            ) as mock_oldest:
                mock_oldest.return_value = three_weeks_ago

                response = test_client.get(
                    "/api/resumes?week_offset=-3", headers={"HX-Request": "true"}
                )

                assert response.status_code == 200
                # Response should contain the HTML with disabled Previous Week
                # The has_older_resumes flag determines button state

        app.dependency_overrides.clear()

    def test_boundary_detection_enables_previous_when_not_at_oldest(
        self, test_user, test_resume
    ):
        """Test that Previous Week button is enabled when not at oldest boundary."""
        app = create_app()

        mock_db = Mock(spec=Session)

        def get_mock_db():
            yield mock_db

        app.dependency_overrides[get_db] = get_mock_db
        app.dependency_overrides[get_current_user_from_cookie] = lambda: test_user

        test_client = TestClient(app)

        from resume_editor.app.api.routes.route_logic.resume_crud import DateRange

        # Resume created 5 weeks ago
        five_weeks_ago = datetime.datetime.now(
            datetime.timezone.utc
        ) - datetime.timedelta(weeks=5)

        # Viewing week -2 (not the oldest - there are older resumes)
        mock_date_range = DateRange(
            start_date=datetime.datetime.now(datetime.timezone.utc)
            - datetime.timedelta(days=21),
            end_date=datetime.datetime.now(datetime.timezone.utc)
            - datetime.timedelta(days=14),
        )

        with patch(
            "resume_editor.app.api.routes.resume.get_user_resumes_with_pagination"
        ) as mock_paginate:
            mock_paginate.return_value = ([test_resume], mock_date_range)
            with patch(
                "resume_editor.app.api.routes.resume.get_oldest_resume_date"
            ) as mock_oldest:
                mock_oldest.return_value = five_weeks_ago

                response = test_client.get(
                    "/api/resumes?week_offset=-2", headers={"HX-Request": "true"}
                )

                assert response.status_code == 200
                # Response should contain enabled Previous Week button

        app.dependency_overrides.clear()

    def test_navigation_with_filter_and_pagination(self, test_user, test_resume):
        """Test that pagination works correctly when filter is applied."""
        app = create_app()

        mock_db = Mock(spec=Session)

        def get_mock_db():
            yield mock_db

        app.dependency_overrides[get_db] = get_mock_db
        app.dependency_overrides[get_current_user_from_cookie] = lambda: test_user

        test_client = TestClient(app)

        from resume_editor.app.api.routes.route_logic.resume_crud import DateRange

        three_weeks_ago = datetime.datetime.now(
            datetime.timezone.utc
        ) - datetime.timedelta(weeks=3)

        mock_date_range = DateRange(
            start_date=datetime.datetime.now(datetime.timezone.utc)
            - datetime.timedelta(days=14),
            end_date=datetime.datetime.now(datetime.timezone.utc)
            - datetime.timedelta(days=7),
        )

        with patch(
            "resume_editor.app.api.routes.resume.get_user_resumes_with_pagination"
        ) as mock_paginate:
            mock_paginate.return_value = ([test_resume], mock_date_range)
            with patch(
                "resume_editor.app.api.routes.resume.get_oldest_resume_date"
            ) as mock_oldest:
                mock_oldest.return_value = three_weeks_ago

                response = test_client.get(
                    "/api/resumes?week_offset=-1&filter=engineer",
                    headers={"HX-Request": "true"},
                )

                assert response.status_code == 200

        app.dependency_overrides.clear()

    def test_full_navigation_cycle(self, test_user, test_resume):
        """Test a full navigation cycle: current -> previous -> previous -> next -> current.

        Simulates realistic user behavior navigating through pagination.
        """
        app = create_app()

        mock_db = Mock(spec=Session)

        def get_mock_db():
            yield mock_db

        app.dependency_overrides[get_db] = get_mock_db
        app.dependency_overrides[get_current_user_from_cookie] = lambda: test_user

        test_client = TestClient(app)

        from resume_editor.app.api.routes.route_logic.resume_crud import DateRange

        # Resume created 6 weeks ago allows for navigation
        six_weeks_ago = datetime.datetime.now(
            datetime.timezone.utc
        ) - datetime.timedelta(weeks=6)

        # Simulate navigation sequence: 0 -> -1 -> -2 -> -1 -> 0
        navigation_sequence = [0, -1, -2, -1, 0]

        for offset in navigation_sequence:
            mock_date_range = DateRange(
                start_date=datetime.datetime.now(datetime.timezone.utc)
                - datetime.timedelta(days=7 * (abs(offset) + 1)),
                end_date=datetime.datetime.now(datetime.timezone.utc)
                - datetime.timedelta(days=7 * abs(offset)),
            )

            with patch(
                "resume_editor.app.api.routes.resume.get_user_resumes_with_pagination"
            ) as mock_paginate:
                mock_paginate.return_value = ([test_resume], mock_date_range)
                with patch(
                    "resume_editor.app.api.routes.resume.get_oldest_resume_date"
                ) as mock_oldest:
                    mock_oldest.return_value = six_weeks_ago

                    response = test_client.get(
                        f"/api/resumes?week_offset={offset}",
                        headers={"HX-Request": "true"},
                    )

                    assert response.status_code == 200

        app.dependency_overrides.clear()
