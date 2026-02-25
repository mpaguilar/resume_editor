"""Tests for CRUD logic with company field."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from resume_editor.app.api.routes.route_logic.resume_crud import (
    ResumeCreateParams,
    ResumeUpdateParams,
    apply_resume_filter,
    create_resume,
    update_resume,
)
from resume_editor.app.models.resume_model import (
    Resume as DatabaseResume,
    ResumeData,
)


class TestResumeCreateParams:
    def test_create_params_with_company(self):
        params = ResumeCreateParams(
            user_id=1, name="Test Resume", content="Content", company="Acme Corp"
        )
        assert params.company == "Acme Corp"

    def test_create_params_with_notes(self):
        params = ResumeCreateParams(
            user_id=1, name="Test Resume", content="Content", notes="Some notes"
        )
        assert params.notes == "Some notes"

    def test_create_params_company_defaults_to_none(self):
        params = ResumeCreateParams(user_id=1, name="Test Resume", content="Content")
        assert params.company is None


class TestResumeUpdateParams:
    def test_update_params_with_company(self):
        params = ResumeUpdateParams(company="New Company")
        assert params.company == "New Company"

    def test_update_params_company_optional(self):
        params = ResumeUpdateParams()
        assert params.company is None


class TestCreateResume:
    @patch("resume_editor.app.api.routes.route_logic.resume_crud.DatabaseResume")
    def test_create_resume_with_company(self, mock_db_resume):
        mock_db = Mock(spec=Session)
        mock_instance = Mock()
        mock_db_resume.return_value = mock_instance

        params = ResumeCreateParams(
            user_id=1,
            name="Refined Resume",
            content="Content",
            is_base=False,
            parent_id=123,
            company="Acme Corp",
            notes="Notes here",
        )
        result = create_resume(db=mock_db, params=params)

        mock_db_resume.assert_called_once()
        actual_data = mock_db_resume.call_args[1]["data"]
        assert actual_data.company == "Acme Corp"
        assert actual_data.notes == "Notes here"


class TestUpdateResume:
    def test_update_resume_company(self):
        mock_db = Mock(spec=Session)
        mock_resume = Mock(spec=DatabaseResume)

        params = ResumeUpdateParams(company="New Company")
        result = update_resume(db=mock_db, resume=mock_resume, params=params)

        assert result.company == "New Company"
        mock_db.commit.assert_called_once()

    def test_update_resume_company_none_no_change(self):
        mock_db = Mock(spec=Session)
        mock_resume = Mock(spec=DatabaseResume)
        mock_resume.company = "Existing Company"

        params = ResumeUpdateParams(name="New Name")
        result = update_resume(db=mock_db, resume=mock_resume, params=params)

        assert result.company == "Existing Company"


class TestApplyResumeFilter:
    def test_apply_filter_searches_company(self):
        mock_query = Mock()
        mock_filtered = Mock()
        mock_query.filter.return_value = mock_filtered

        result = apply_resume_filter(mock_query, "Acme")
        mock_query.filter.assert_called_once()

    def test_apply_filter_empty_query_returns_unfiltered(self):
        mock_query = Mock()
        result = apply_resume_filter(mock_query, "")
        assert result == mock_query
        mock_query.filter.assert_not_called()

    def test_apply_filter_none_query_returns_unfiltered(self):
        mock_query = Mock()
        result = apply_resume_filter(mock_query, None)
        assert result == mock_query
        mock_query.filter.assert_not_called()
